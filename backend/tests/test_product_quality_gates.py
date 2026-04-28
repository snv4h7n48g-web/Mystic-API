from __future__ import annotations

from generation.orchestration import MysticGenerationOrchestrator
from generation.types import GenerationContext, GenerationMetadata, OrchestrationResult
from generation.validators import RETRY_HINTS


class StubOrchestrator(MysticGenerationOrchestrator):
    def __init__(self, responses: list[dict]):
        self.responses = responses
        self.calls: list[str | None] = []

    def _invoke_normalized_generation(self, **kwargs):
        self.calls.append(kwargs.get("retry_instruction"))
        response = self.responses.pop(0)
        return response["normalized"], response["metadata"], response["result"]


def _response(*, opening: str, current: str, emotional: str, guidance: str, closing: str, tarot_message: str | None = None):
    from generation.types import NormalizedMysticOutput

    normalized = NormalizedMysticOutput(
        opening_hook=opening,
        current_pattern=current,
        emotional_truth=emotional,
        tarot_message=tarot_message or current,
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
                current="The spread shows that solitude is a tool, not a wall.",
                emotional="The spread shows that solitude is a tool, not a wall.",
                tarot_message="The Hermit in the guidance position asks for retreat, while Two of Wands in the outcome position turns that retreat into discernment before action and shows why silence clarifies the next choice. Together, The Hermit and Two of Wands create card symbolism that turns perspective into movement, so the spread is about choosing with clarity rather than calling delay wisdom.",
                guidance="Block one quiet hour tonight, write the choice in plain language, and make one concrete move before tomorrow so the lantern image becomes a real decision instead of a mood.",
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

    assert orchestrator.calls == [None, RETRY_HINTS["tarot"]]
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
