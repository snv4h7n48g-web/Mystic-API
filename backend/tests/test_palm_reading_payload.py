from generation.products.palm.reading import build_palm_reading_payload
from generation.types import GenerationMetadata, NormalizedMysticOutput
from generation.validators import validate_product_payload


def _metadata() -> GenerationMetadata:
    return GenerationMetadata(
        persona_id="palm_reader",
        llm_profile_id="test",
        prompt_version="test",
        model_id="test-model",
        theme_tags=["palm"],
        headline="A palm-led reading",
    )


def test_palm_reading_payload_uses_palm_section_contract() -> None:
    normalized = NormalizedMysticOutput(
        opening_hook="The hand is asking you to slow down and read the pressure points.",
        current_pattern="Your life line suggests endurance that has been carrying more than it admits.",
        emotional_truth="The heart line points to feeling that is carefully managed before it is shared.",
        practical_guidance="Choose one honest conversation and one practical boundary this week.",
        next_return_invitation="Return when the same palm signal feels louder or easier to name.",
    )

    payload = build_palm_reading_payload(
        normalized=normalized,
        metadata=_metadata(),
        palm_features=[
            {"feature": "life_line", "value": "long - steady arc"},
            {"feature": "heart_line", "value": "deep - curved"},
        ],
    )

    assert [section["id"] for section in payload["sections"]] == [
        "opening_invocation",
        "palm_insight",
        "integrated_synthesis",
        "reflective_guidance",
        "closing_prompt",
    ]
    assert payload["metadata"]["flow_type"] == "palm_solo"
    assert validate_product_payload("palm", payload).passed is True
