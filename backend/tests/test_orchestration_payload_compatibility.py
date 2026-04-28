from __future__ import annotations

from generation.orchestration import MysticGenerationOrchestrator
from generation.types import (
    GenerationContext,
    GenerationMetadata,
    NormalizedMysticOutput,
    OrchestrationResult,
)


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


def test_daily_session_reading_passes_astrology_facts_to_payload_builder(monkeypatch) -> None:
    orchestrator = MysticGenerationOrchestrator()
    captured = {}

    def _fake_generate_with_quality_gate(**kwargs):
        captured.update(kwargs["payload_builder_kwargs"])
        return OrchestrationResult(payload={"metadata": {}}, metadata=_metadata())

    monkeypatch.setattr(
        orchestrator,
        "_generate_with_quality_gate",
        _fake_generate_with_quality_gate,
    )

    result = orchestrator.build_session_reading_result(
        session={
            "id": "daily-session",
            "inputs": {
                "flow_type": "daily_horoscope",
                "question_intention": "What should I focus on today?",
            },
            "locale": "en-AU",
            "timezone": "Australia/Sydney",
            "style": "grounded",
        },
        user=None,
        astrology_facts={"sun_sign": "Virgo", "moon_sign": "Capricorn"},
        tarot_payload={},
        palm_features=[],
        include_palm=False,
        deep_access=True,
        content_contract={},
    )

    assert result.metadata.continuity_source_session_id == "daily-session"
    assert captured["astrology_facts"]["sun_sign"] == "Virgo"
    assert captured["astrology_facts"]["moon_sign"] == "Capricorn"


def test_combined_full_payload_uses_two_part_payoff_contract() -> None:
    orchestrator = MysticGenerationOrchestrator()
    context = GenerationContext(object_id="1", object_type="session", flow_type="combined", surface="full")

    payload = orchestrator._build_payload_for_context(
        context=context,
        normalized=NormalizedMysticOutput(
            opening_hook="A pattern is gathering.",
            current_pattern="You are circling the same truth.",
            emotional_truth="Part of you already knows the answer.",
            what_this_is_asking_of_you="This is asking you to stop negotiating with the truth you have already reached internally.",
            your_next_move="Choose one small but irreversible act that proves you are no longer delaying the obvious.",
            practical_guidance="Legacy fallback guidance.",
            continuity_callback=None,
            next_return_invitation="Come back tomorrow.",
            premium_teaser="There is another layer here.",
            theme_tags=["clarity"],
        ),
        metadata=_metadata(),
    )

    sections = {section["id"]: section["text"] for section in payload["sections"]}
    assert "what_this_is_asking_of_you" in sections
    assert "your_next_move" in sections
    assert "practical_guidance" not in sections
    assert payload["metadata"]["payoff_contract"]["your_next_move"]


def test_lunar_domain_context_uses_guest_lunar_birth_year_when_birth_date_missing() -> None:
    orchestrator = MysticGenerationOrchestrator()

    context = orchestrator._build_lunar_domain_context(
        session={
            "inputs": {
                "flow_type": "lunar_new_year_solo",
                "lunar_birth_year": 1990,
            }
        }
    )

    assert context["birth_zodiac"]["animal"] == "Horse"
    assert context["birth_zodiac"]["combined"]
