from __future__ import annotations

from generation.orchestration import MysticGenerationOrchestrator
from generation.types import GenerationContext, GenerationMetadata, NormalizedMysticOutput


def _normalized() -> NormalizedMysticOutput:
    return NormalizedMysticOutput(
        opening_hook="A pattern is gathering.",
        current_pattern="Today asks for steadiness.",
        emotional_truth="You already know what matters.",
        practical_guidance="Choose one clear next step.",
        continuity_callback=None,
        next_return_invitation="Come back tomorrow.",
        premium_teaser="There is another layer here.",
        theme_tags=["clarity"],
    )


def _metadata() -> GenerationMetadata:
    return GenerationMetadata(
        persona_id="premium_mystic",
        llm_profile_id="full_premium",
        prompt_version="mystic-v1",
        model_id="test-model",
        theme_tags=["clarity"],
        headline="A pattern is gathering.",
    )


def test_preview_payload_shape_does_not_gain_validation_metadata() -> None:
    orchestrator = MysticGenerationOrchestrator()
    context = GenerationContext(object_id="1", object_type="session", flow_type="daily_horoscope", surface="preview")

    payload = orchestrator._build_payload_for_context(
        context=context,
        normalized=_normalized(),
        metadata=_metadata(),
        unlock_price={"currency": "USD", "amount": 1.99},
        product_id="reading_basic",
        entitlements={},
        astrology_facts={"sun_sign": "Aries"},
        tarot_payload={},
    )
    orchestrator._attach_contract_metadata(context=context, payload=payload)

    assert "validation" not in payload.get("meta", {})
    assert "expected_section_ids" not in payload.get("meta", {})


def test_full_payload_keeps_validation_metadata_for_observability() -> None:
    orchestrator = MysticGenerationOrchestrator()
    context = GenerationContext(object_id="1", object_type="session", flow_type="daily_horoscope", surface="full")

    payload = orchestrator._build_payload_for_context(
        context=context,
        normalized=_normalized(),
        metadata=_metadata(),
    )
    orchestrator._attach_contract_metadata(context=context, payload=payload)

    assert payload["metadata"]["validation"]["product_key"] == "daily"
    assert payload["metadata"]["validation"]["attempts"] == 1
    assert payload["metadata"]["expected_section_ids"]
