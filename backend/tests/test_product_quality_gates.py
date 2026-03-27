from __future__ import annotations

from generation.orchestration import MysticGenerationOrchestrator
from generation.types import GenerationContext, GenerationMetadata, OrchestrationResult


class StubOrchestrator(MysticGenerationOrchestrator):
    def __init__(self, responses: list[dict]):
        self.responses = responses
        self.calls: list[str | None] = []

    def _invoke_normalized_generation(self, **kwargs):
        self.calls.append(kwargs.get("retry_instruction"))
        response = self.responses.pop(0)
        return response["normalized"], response["metadata"], response["result"]


def _response(*, opening: str, current: str, emotional: str, guidance: str, closing: str):
    from generation.types import NormalizedMysticOutput

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
    result = OrchestrationResult(payload={}, metadata=metadata, input_tokens=10, output_tokens=20, cost_usd=0.5)
    return {"normalized": normalized, "metadata": metadata, "result": result}


def test_quality_gate_retries_once_then_passes() -> None:
    orchestrator = StubOrchestrator(
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

    assert orchestrator.calls == [None, "Correct the output into a card-led tarot reading. Name the actual cards or spread logic, explain symbolism, and synthesise the cards into guidance."]
    assert result.payload["metadata"]["validation"]["attempts"] == 2
    assert result.payload["metadata"]["validation"]["valid"] is True
    assert result.input_tokens == 20
    assert result.output_tokens == 40


def test_quality_gate_stops_after_second_failed_attempt() -> None:
    orchestrator = StubOrchestrator(
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

    assert len(orchestrator.calls) == 2
    assert result.payload["metadata"]["validation"]["attempts"] == 2
    assert result.payload["metadata"]["validation"]["valid"] is False
    assert "tarot_missing_card_specific_language" in result.payload["metadata"]["validation"]["issues"]
