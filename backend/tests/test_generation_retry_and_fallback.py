from __future__ import annotations

import json
import logging

from generation.orchestration import MysticGenerationOrchestrator
from generation.types import GenerationContext, GenerationMetadata, NormalizedMysticOutput, OrchestrationResult


class StubRetryOrchestrator(MysticGenerationOrchestrator):
    def __init__(self, responses: list[dict]):
        self.responses = responses
        self.retry_instructions: list[str | None] = []

    def _invoke_normalized_generation(self, **kwargs):
        self.retry_instructions.append(kwargs.get("retry_instruction"))
        response = self.responses.pop(0)
        return response["normalized"], response["metadata"], response["result"]


class StubBedrockService:
    def __init__(self, responses_by_model: dict[str, list[dict | Exception]]):
        self.responses_by_model = {key: list(value) for key, value in responses_by_model.items()}
        self.calls: list[dict] = []

    def invoke_text(self, **kwargs):
        self.calls.append(kwargs)
        model_id = kwargs["model_id"]
        response = self.responses_by_model[model_id].pop(0)
        if isinstance(response, Exception):
            raise response
        response.setdefault("duration_ms", 123.0)
        response.setdefault("timeout_ms", kwargs.get("timeout_ms"))
        return response


class ValidatorSpy:
    def __init__(self, results):
        self.results = list(results)
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, product_key: str, payload: dict):
        self.calls.append((product_key, payload))
        return self.results.pop(0)


def _response(*, opening: str, current: str, emotional: str, guidance: str, closing: str, generation_metrics: dict | None = None):
    normalized = NormalizedMysticOutput(
        opening_hook=opening,
        current_pattern=current,
        emotional_truth=emotional,
        practical_guidance=guidance,
        continuity_callback=None,
        next_return_invitation=closing,
        premium_teaser="Another layer.",
        theme_tags=["test"],
    )
    metadata = GenerationMetadata(
        persona_id="ancient_tarot_reader",
        llm_profile_id="full_premium",
        prompt_version="mystic-v1",
        model_id="test-model",
        theme_tags=["test"],
        headline=opening,
    )
    result = OrchestrationResult(
        payload={},
        metadata=metadata,
        input_tokens=10,
        output_tokens=20,
        cost_usd=0.5,
        generation_metrics=generation_metrics or {},
    )
    return {"normalized": normalized, "metadata": metadata, "result": result}


def _normalized_json(*, opening: str, current: str, emotional: str, guidance: str, closing: str) -> str:
    return json.dumps(
        {
            "opening_hook": opening,
            "current_pattern": current,
            "emotional_truth": emotional,
            "practical_guidance": guidance,
            "continuity_callback": None,
            "next_return_invitation": closing,
            "premium_teaser": "Another layer.",
            "theme_tags": ["test"],
        }
    )


def test_retry_correction_applies_once_and_returns_corrected_payload(monkeypatch) -> None:
    from generation.validators import ValidationResult

    orchestrator = StubRetryOrchestrator(
        responses=[
            _response(
                opening="Trust the moment.",
                current="Stay positive.",
                emotional="Keep going.",
                guidance="Let the day unfold.",
                closing="Return soon.",
            ),
            _response(
                opening="The Hermit opens the spread.",
                current="The Hermit in the guidance position asks for retreat; the card's symbolism points to discernment before action.",
                emotional="The spread shows that solitude is a tool, not a wall.",
                guidance="Use the card's lantern image as your cue to move one clear step at a time.",
                closing="Return when the next card is ready.",
            ),
        ]
    )
    validation_spy = ValidatorSpy(
        [
            ValidationResult(
                product_key="tarot",
                passed=False,
                issues=["tarot_missing_card_specific_language"],
                retry_hint="Correct the output into a card-led tarot reading. Name the actual cards, card positions, or spread logic; tie each claim back to that card/spread evidence; deepen the tarot narrative instead of restating the summary; stop repeating phrasing across opening, narrative, synthesis, and guidance; and make the guidance concrete, specific, and actionable rather than abstract filler.",
            ),
            ValidationResult(product_key="tarot", passed=True, issues=[]),
        ]
    )
    monkeypatch.setattr("generation.orchestration.validate_product_payload", validation_spy)

    context = GenerationContext(object_id="1", object_type="session", flow_type="tarot_solo", surface="full")
    result = orchestrator._generate_with_quality_gate(
        context=context,
        persona_id="ancient_tarot_reader",
        flow_id="tarot_reading",
        continuity_context={},
        domain_context={},
        contract_instruction="tarot contract",
        payload_builder_kwargs={},
    )

    assert orchestrator.retry_instructions == [
        None,
        "Correct the output into a card-led tarot reading. Name the actual cards, card positions, or spread logic; tie each claim back to that card/spread evidence; deepen the tarot narrative instead of restating the summary; stop repeating phrasing across opening, narrative, synthesis, and guidance; and make the guidance concrete, specific, and actionable rather than abstract filler.",
    ]
    assert len(validation_spy.calls) == 2
    assert result.payload["sections"][0]["text"] == "The Hermit opens the spread."
    assert result.payload["metadata"]["validation"]["attempts"] == 2
    assert result.payload["metadata"]["validation"]["valid"] is True
    assert result.payload["metadata"]["generation_timing"]["retry_count"] == 1
    assert len(result.payload["metadata"]["generation_timing"]["attempts"]) == 2
    assert result.input_tokens == 20
    assert result.output_tokens == 40


def test_exhausted_retry_returns_best_available_full_payload_with_validation_metadata(monkeypatch) -> None:
    from generation.validators import ValidationResult

    orchestrator = StubRetryOrchestrator(
        responses=[
            _response(
                opening="Trust the moment.",
                current="Stay positive.",
                emotional="Keep going.",
                guidance="Let the day unfold.",
                closing="Return soon.",
            ),
            _response(
                opening="Still vague.",
                current="Listen inward.",
                emotional="A message is near.",
                guidance="Be open.",
                closing="Return soon.",
            ),
        ]
    )
    validation_spy = ValidatorSpy(
        [
            ValidationResult(
                product_key="tarot",
                passed=False,
                issues=["tarot_missing_card_specific_language"],
                retry_hint="Correct the output into a card-led tarot reading. Name the actual cards, card positions, or spread logic; tie each claim back to that card/spread evidence; deepen the tarot narrative instead of restating the summary; stop repeating phrasing across opening, narrative, synthesis, and guidance; and make the guidance concrete, specific, and actionable rather than abstract filler.",
            ),
            ValidationResult(
                product_key="tarot",
                passed=False,
                issues=["tarot_missing_card_specific_language", "tarot_missing_spread_context"],
                retry_hint="Correct the output into a card-led tarot reading. Name the actual cards, card positions, or spread logic; tie each claim back to that card/spread evidence; deepen the tarot narrative instead of restating the summary; stop repeating phrasing across opening, narrative, synthesis, and guidance; and make the guidance concrete, specific, and actionable rather than abstract filler.",
            ),
        ]
    )
    monkeypatch.setattr("generation.orchestration.validate_product_payload", validation_spy)

    context = GenerationContext(object_id="1", object_type="session", flow_type="tarot_solo", surface="full")
    result = orchestrator._generate_with_quality_gate(
        context=context,
        persona_id="ancient_tarot_reader",
        flow_id="tarot_reading",
        continuity_context={},
        domain_context={},
        contract_instruction="tarot contract",
        payload_builder_kwargs={},
    )

    assert len(orchestrator.retry_instructions) == 2
    assert len(validation_spy.calls) == 2
    assert result.payload["sections"][0]["text"] == "Still vague."
    assert result.payload["metadata"]["validation"]["attempts"] == 2
    assert result.payload["metadata"]["validation"]["valid"] is False
    assert result.payload["metadata"]["validation"]["issues"] == [
        "tarot_missing_card_specific_language",
        "tarot_missing_spread_context",
    ]


def test_exhausted_retry_preview_payload_does_not_leak_validation_metadata(monkeypatch) -> None:
    from generation.validators import ValidationResult

    orchestrator = StubRetryOrchestrator(
        responses=[
            _response(
                opening="Trust the moment.",
                current="Stay positive.",
                emotional="Keep going.",
                guidance="Let the day unfold.",
                closing="Return soon.",
            ),
            _response(
                opening="Still vague.",
                current="Listen inward.",
                emotional="A message is near.",
                guidance="Be open.",
                closing="Return soon.",
            ),
        ]
    )
    validation_spy = ValidatorSpy(
        [
            ValidationResult(
                product_key="tarot",
                passed=False,
                issues=["tarot_missing_card_specific_language"],
                retry_hint="Correct the output into a card-led tarot reading. Name the actual cards, card positions, or spread logic; tie each claim back to that card/spread evidence; deepen the tarot narrative instead of restating the summary; stop repeating phrasing across opening, narrative, synthesis, and guidance; and make the guidance concrete, specific, and actionable rather than abstract filler.",
            ),
            ValidationResult(
                product_key="tarot",
                passed=False,
                issues=["tarot_missing_card_specific_language", "tarot_missing_spread_context"],
                retry_hint="Correct the output into a card-led tarot reading. Name the actual cards, card positions, or spread logic; tie each claim back to that card/spread evidence; deepen the tarot narrative instead of restating the summary; stop repeating phrasing across opening, narrative, synthesis, and guidance; and make the guidance concrete, specific, and actionable rather than abstract filler.",
            ),
        ]
    )
    monkeypatch.setattr("generation.orchestration.validate_product_payload", validation_spy)

    context = GenerationContext(object_id="1", object_type="session", flow_type="tarot_solo", surface="preview")
    result = orchestrator._generate_with_quality_gate(
        context=context,
        persona_id="ancient_tarot_reader",
        flow_id="tarot_preview",
        continuity_context={},
        domain_context={},
        contract_instruction="tarot contract",
        payload_builder_kwargs={
            "unlock_price": {"currency": "USD", "amount": 3.99},
            "product_id": "tarot",
            "entitlements": {},
            "astrology_facts": {},
            "tarot_payload": {},
        },
    )

    assert len(orchestrator.retry_instructions) == 2
    assert len(validation_spy.calls) == 2
    assert "validation" not in result.payload["meta"]
    assert "expected_section_ids" not in result.payload["meta"]


def test_anthropic_preferred_route_falls_back_to_configured_model(monkeypatch) -> None:
    context = GenerationContext(object_id="1", object_type="session", flow_type="daily_horoscope", surface="full")
    orchestrator = MysticGenerationOrchestrator()

    primary_model = "us.anthropic.claude-opus-4-1-20250805-v1:0"
    fallback_model = "us.amazon.nova-pro-v1:0"
    bedrock = StubBedrockService(
        {
            primary_model: [RuntimeError("primary provider failed")],
            fallback_model: [
                {
                    "text": _normalized_json(
                        opening="Today starts with clarity.",
                        current="The day is asking for one direct move, not five half-steps.",
                        emotional="You already know what needs trimming.",
                        guidance="Pick the task that clears the most friction before lunch.",
                        closing="Come back tomorrow for the next pulse.",
                    ),
                    "input_tokens": 12,
                    "output_tokens": 34,
                    "cost_usd": 0.12,
                    "model": fallback_model,
                }
            ],
        }
    )

    monkeypatch.setattr("generation.orchestration.get_bedrock_service", lambda: bedrock)
    monkeypatch.setattr(
        "generation.orchestration.get_product_route_for_context",
        lambda _context: type(
            "Route",
            (),
            {
                "product_key": "daily",
                "fallback_model_id": fallback_model,
                "profile_id_for_surface": lambda self, surface: "daily_retention",
                "model_id_for_surface": lambda self, surface: primary_model,
                "max_tokens_for_surface": lambda self, surface: 1600,
            },
        )(),
    )

    normalized, metadata, result = orchestrator._invoke_normalized_generation(
        context=context,
        persona_id="practical_astrologer",
        flow_id="daily_horoscope_reading",
        continuity_context={},
        domain_context={"flow_type": "daily_horoscope"},
    )

    assert [call["model_id"] for call in bedrock.calls] == [primary_model, fallback_model]
    assert all(call["timeout_ms"] == 20000 for call in bedrock.calls)
    assert metadata.model_id == fallback_model
    assert result.metadata.model_id == fallback_model
    assert result.generation_metrics["used_fallback_model"] is True
    assert result.generation_metrics["timeout_ms"] == 20000
    assert normalized.opening_hook == "Today starts with clarity."



def test_generation_timing_summary_is_attached_for_live_triage(monkeypatch, caplog) -> None:
    from generation.validators import ValidationResult

    orchestrator = StubRetryOrchestrator(
        responses=[
            _response(
                opening="Today starts with clarity.",
                current="The day is asking for one direct move, not five half-steps.",
                emotional="You already know what needs trimming.",
                guidance="Pick the task that clears the most friction before lunch.",
                closing="Come back tomorrow for the next pulse.",
                generation_metrics={
                    "attempt_model": "model-a",
                    "attempt_index": 1,
                    "used_fallback_model": False,
                    "attempt_duration_ms": 140.0,
                    "provider_duration_ms": 100.0,
                    "queue_duration_ms": 30.0,
                    "model_duration_ms": 70.0,
                    "time_to_first_output_ms": 70.0,
                    "parse_duration_ms": 15.0,
                    "timeout_ms": 20000,
                    "prompt_chars": 1200,
                    "context_chars": 400,
                },
            ),
            _response(
                opening="Now the pattern sharpens.",
                current="The second pass tightens the reading around one clear move.",
                emotional="The signal was there; it just needed less drift.",
                guidance="Finish the one thing that turns noise into momentum.",
                closing="Return when you want the next layer.",
                generation_metrics={
                    "attempt_model": "model-b",
                    "attempt_index": 2,
                    "used_fallback_model": True,
                    "attempt_duration_ms": 210.0,
                    "provider_duration_ms": 160.0,
                    "queue_duration_ms": 40.0,
                    "model_duration_ms": 120.0,
                    "time_to_first_output_ms": 120.0,
                    "parse_duration_ms": 20.0,
                    "timeout_ms": 20000,
                    "prompt_chars": 1500,
                    "context_chars": 450,
                },
            ),
        ]
    )
    validation_spy = ValidatorSpy(
        [
            ValidationResult(product_key="tarot", passed=False, issues=["needs_retry"], retry_hint="retry"),
            ValidationResult(product_key="tarot", passed=True, issues=[]),
        ]
    )
    monkeypatch.setattr("generation.orchestration.validate_product_payload", validation_spy)

    context = GenerationContext(object_id="1", object_type="session", flow_type="tarot_solo", surface="full")
    with caplog.at_level(logging.WARNING, logger="mystic.orchestration"):
        result = orchestrator._generate_with_quality_gate(
            context=context,
            persona_id="ancient_tarot_reader",
            flow_id="tarot_reading",
            continuity_context={},
            domain_context={},
            contract_instruction="tarot contract",
            payload_builder_kwargs={},
        )

    timing = result.payload["metadata"]["generation_timing"]
    assert timing["attempt_count"] == 2
    assert timing["provider_total_ms"] == 260.0
    assert timing["queue_total_ms"] == 70.0
    assert timing["model_total_ms"] == 190.0
    assert timing["time_to_first_output_ms"] == 70.0
    assert timing["parse_total_ms"] == 35.0
    assert timing["attempt_total_ms"] == 350.0
    assert timing["orchestration_overhead_ms"] >= 0.0
    assert timing["attempt_models"] == ["model-a", "model-b"]
    assert "total=" in timing["summary"]
    assert "provider=260.0ms" in timing["summary"]
    assert "queue=70.0ms" in timing["summary"]
    assert "model=190.0ms" in timing["summary"]
    assert "ttfo=70.0ms" in timing["summary"]
    assert "parse=35.0ms" in timing["summary"]
    assert "models=model-a,model-b" in timing["summary"]
    assert any("generation_latency_breakdown" in record.message for record in caplog.records)



def test_quality_gate_uses_policy_max_attempts(monkeypatch) -> None:
    from generation.orchestration import MysticGenerationOrchestrator
    from generation.types import GenerationContext
    from generation.validators import ValidationResult

    orchestrator = MysticGenerationOrchestrator()
    call_count = {'count': 0}

    def fake_invoke(**kwargs):
        call_count['count'] += 1
        return (
            object(),
            type('Meta', (), {'persona_id': 'x', 'llm_profile_id': 'y', 'prompt_version': 'z', 'theme_tags': [], 'headline': '', 'model_id': 'm'})(),
            type('Result', (), {'generation_metrics': {'attempt_model': 'model-a', 'used_fallback_model': False}, 'input_tokens': 1, 'output_tokens': 1, 'cost_usd': 0.1, 'payload': {}, 'metadata': None})(),
        )

    monkeypatch.setattr(orchestrator, '_invoke_normalized_generation', fake_invoke)
    monkeypatch.setattr(orchestrator, '_build_payload_for_context', lambda **kwargs: {'sections': [], 'metadata': {}})
    monkeypatch.setattr('generation.orchestration.get_product_route_for_context', lambda _context: type('Route', (), {'product_key': 'tarot'})())
    monkeypatch.setattr('generation.orchestration.get_product_contract', lambda _product_key: type('Contract', (), {'product_key': 'tarot'})())
    monkeypatch.setattr('generation.orchestration.validate_product_payload', lambda product_key, payload: ValidationResult(product_key='tarot', passed=False, issues=['tarot_missing_card_specific_language'], retry_hint='retry'))
    monkeypatch.setattr(orchestrator, '_quality_gate_policy', lambda **kwargs: {'max_attempts': 1, 'attach_validation_metadata': True, 'hard_fail_on_exhausted_validation': False})
    monkeypatch.setattr(orchestrator, '_attach_generation_metrics', lambda **kwargs: None)
    monkeypatch.setattr(orchestrator, '_attach_contract_metadata', lambda **kwargs: None)

    context = GenerationContext(object_id='1', object_type='session', flow_type='tarot_solo', surface='preview')
    orchestrator._generate_with_quality_gate(
        context=context,
        persona_id='ancient_tarot_reader',
        flow_id='tarot_preview',
        continuity_context={},
        domain_context={'flow_type': 'tarot_solo'},
    )

    assert call_count['count'] == 1
