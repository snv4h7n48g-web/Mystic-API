from bedrock_service import BedrockService
from generation.formatting.reading_formatter import build_reading_payload
from generation.parser import GenerationParseError, parse_normalized_output
from generation.prompts.composer import compose_generation_prompt
from generation.routing.persona_router import choose_persona
from generation.types import GenerationContext, GenerationMetadata


def test_compose_generation_prompt_includes_persona_flow_and_schema() -> None:
    prompt = compose_generation_prompt(
        persona_id="ancient_tarot_reader",
        flow_id="tarot_preview",
        continuity_context={"latest": "something real"},
        domain_context={"question": "What is shifting?"},
        retry_instruction="Be more card-specific.",
    )

    assert "system_prompt" in prompt
    assert prompt["prompt_version"] == "mystic-v1"
    assert any("PERSONA:" in message for message in prompt["messages"])
    assert any("FLOW:" in message for message in prompt["messages"])
    assert any("Return JSON" in message for message in prompt["messages"])


def test_compose_generation_prompt_compacts_context_json() -> None:
    prompt = compose_generation_prompt(
        persona_id="ancient_tarot_reader",
        flow_id="tarot_reading",
        continuity_context={"recent": ["tarot_solo"], "latest_flow_type": "tarot_solo"},
        domain_context={"question": "Should I move forward?", "tarot": {"cards": ["The Chariot", "Two of Swords"]}},
        contract_instruction="tarot contract",
    )

    continuity_message = next(message for message in prompt["messages"] if message.startswith("CONTINUITY_CONTEXT:\n"))
    domain_message = next(message for message in prompt["messages"] if message.startswith("DOMAIN_CONTEXT:\n"))

    assert "\n  " not in continuity_message
    assert "\n  " not in domain_message
    assert '{"latest_flow_type":"tarot_solo","recent":["tarot_solo"]}' in continuity_message


def test_parse_normalized_output_accepts_valid_json() -> None:
    output = parse_normalized_output(
        """
        {
          "opening_hook": "A pattern is gathering.",
          "current_pattern": "You are between hesitation and action.",
          "emotional_truth": "You already know what matters.",
          "practical_guidance": "Choose the clearest next step.",
          "continuity_callback": null,
          "next_return_invitation": "Come back tomorrow.",
          "premium_teaser": "There is another layer here.",
          "theme_tags": ["clarity", "change"]
        }
        """
    )

    assert output.opening_hook == "A pattern is gathering."
    assert output.theme_tags == ["clarity", "change"]


def test_parse_normalized_output_rejects_missing_keys() -> None:
    try:
        parse_normalized_output('{"opening_hook":"x"}')
    except GenerationParseError as exc:
        assert "Missing required keys" in str(exc)
    else:
        raise AssertionError("Expected GenerationParseError")


def test_choose_persona_routes_feng_shui_to_practical_astrologer() -> None:
    persona = choose_persona(
        GenerationContext(
            object_id="a1",
            object_type="feng_shui",
            flow_type="feng_shui",
            surface="preview",
        )
    )

    assert persona == "practical_astrologer"


def test_choose_persona_routes_compatibility_to_flirty_cosmic_guide() -> None:
    persona = choose_persona(
        GenerationContext(
            object_id="c1",
            object_type="compatibility",
            flow_type="compatibility",
            surface="preview",
        )
    )

    assert persona == "flirty_cosmic_guide"


def test_choose_persona_routes_feng_shui_preview_to_practical_astrologer() -> None:
    persona = choose_persona(
        GenerationContext(
            object_id="f1",
            object_type="feng_shui",
            flow_type="feng_shui",
            surface="preview",
        )
    )

    assert persona == "practical_astrologer"


def test_choose_persona_routes_full_reading_to_flagship_mystic() -> None:
    persona = choose_persona(
        GenerationContext(
            object_id="r1",
            object_type="reading",
            flow_type="combined",
            surface="reading",
        )
    )

    assert persona == "flagship_mystic"


def test_choose_persona_keeps_daily_on_refined_psychic_best_friend() -> None:
    persona = choose_persona(
        GenerationContext(
            object_id="d1",
            object_type="horoscope",
            flow_type="daily_horoscope",
            surface="reading",
        )
    )

    assert persona == "psychic_best_friend"


def test_invoke_text_uses_bedrock_converse_and_returns_usage() -> None:
    service = BedrockService.__new__(BedrockService)
    service.costs = {
        "test-model": {"input": 0.001, "output": 0.002},
    }

    class FakeClient:
        def converse(self, **kwargs):
            assert kwargs["modelId"] == "test-model"
            assert kwargs["inferenceConfig"]["temperature"] == 0.8
            return {
                "output": {"message": {"content": [{"text": '{"opening_hook":"A","current_pattern":"B","emotional_truth":"C","practical_guidance":"D","continuity_callback":null,"next_return_invitation":"E","premium_teaser":"F","theme_tags":["x"]}'}]}},
                "usage": {"inputTokens": 12, "outputTokens": 34},
            }

    service.client = FakeClient()

    result = service.invoke_text(
        model_id="test-model",
        system_prompt="system",
        user_messages=["one", "two"],
        temperature=0.8,
        top_p=0.9,
        max_tokens=123,
    )

    assert result["model"] == "test-model"
    assert result["input_tokens"] == 12
    assert result["output_tokens"] == 34
    assert result["text"].startswith('{"opening_hook"')


def test_invoke_text_omits_top_p_for_anthropic_opus_profiles() -> None:
    service = BedrockService.__new__(BedrockService)
    service.costs = {
        "us.anthropic.claude-opus-4-6-v1": {"input": 0.001, "output": 0.002},
    }

    class FakeClient:
        def converse(self, **kwargs):
            assert kwargs["modelId"] == "us.anthropic.claude-opus-4-6-v1"
            assert kwargs["inferenceConfig"]["temperature"] == 0.8
            assert "topP" not in kwargs["inferenceConfig"]
            return {
                "output": {"message": {"content": [{"text": '{"opening_hook":"A","current_pattern":"B","emotional_truth":"C","practical_guidance":"D","continuity_callback":null,"next_return_invitation":"E","premium_teaser":"F","theme_tags":["x"]}'}]}},
                "usage": {"inputTokens": 12, "outputTokens": 34},
            }

    service.client = FakeClient()

    result = service.invoke_text(
        model_id="us.anthropic.claude-opus-4-6-v1",
        system_prompt="system",
        user_messages=["one"],
        temperature=0.8,
        top_p=0.9,
        max_tokens=123,
    )

    assert result["model"] == "us.anthropic.claude-opus-4-6-v1"


def test_build_reading_payload_includes_continuity_and_metadata() -> None:
    normalized = parse_normalized_output(
        """
        {
          "opening_hook": "A pattern is gathering.",
          "current_pattern": "You are between hesitation and action.",
          "emotional_truth": "You already know what matters.",
          "practical_guidance": "Choose the clearest next step.",
          "continuity_callback": "This echoes your last theme of clarity.",
          "next_return_invitation": "Come back tomorrow.",
          "premium_teaser": "There is another layer here.",
          "theme_tags": ["clarity", "change"]
        }
        """
    )
    metadata = GenerationMetadata(
        persona_id="ancient_tarot_reader",
        llm_profile_id="full_premium",
        prompt_version="mystic-v1",
        model_id="claude-opus",
        theme_tags=["clarity", "change"],
        headline="A pattern is gathering.",
    )

    payload = build_reading_payload(normalized=normalized, metadata=metadata)

    assert payload["sections"][0]["id"] == "opening_hook"
    assert any(section["id"] == "continuity_callback" for section in payload["sections"])
    assert payload["metadata"]["persona_id"] == "ancient_tarot_reader"
    assert payload["metadata"]["llm_profile_id"] == "full_premium"
