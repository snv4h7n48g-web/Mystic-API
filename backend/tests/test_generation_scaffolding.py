from generation.parser import GenerationParseError, parse_normalized_output
from generation.prompts.composer import compose_generation_prompt
from generation.routing.persona_router import choose_persona
from generation.types import GenerationContext


def test_compose_generation_prompt_includes_persona_flow_and_schema() -> None:
    prompt = compose_generation_prompt(
        persona_id="ancient_tarot_reader",
        flow_id="session_preview",
        continuity_context={"latest": "something real"},
        domain_context={"question": "What is shifting?"},
    )

    assert "system_prompt" in prompt
    assert prompt["prompt_version"] == "mystic-v1"
    assert any("PERSONA:" in message for message in prompt["messages"])
    assert any("FLOW:" in message for message in prompt["messages"])
    assert any("Return JSON" in message for message in prompt["messages"])


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
