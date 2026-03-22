from __future__ import annotations

from .continuity.builder import build_continuity_context
from .formatting.preview_formatter import build_preview_payload
from .personas import get_persona
from .profiles import get_llm_profile
from .prompts.composer import PROMPT_VERSION, compose_generation_prompt
from .routing.persona_router import choose_persona
from .types import GenerationContext, GenerationMetadata, NormalizedMysticOutput, OrchestrationResult


class MysticGenerationOrchestrator:
    """Phase-1 scaffolding for persona-based Bedrock orchestration.

    This class intentionally keeps behavior minimal until individual endpoints
    are cut over behind feature flags.
    """

    def build_session_preview_result(
        self,
        *,
        session: dict,
        user: dict | None,
        astrology_facts: dict,
        tarot_payload: dict,
        unlock_price: dict,
        product_id: str,
        entitlements: dict,
    ) -> OrchestrationResult:
        inputs = session.get("inputs") or {}
        flow_type = inputs.get("flow_type") or "combined"
        context = GenerationContext(
            object_id=str(session["id"]),
            object_type="session",
            flow_type=flow_type,
            surface="preview",
            user_id=str(user["id"]) if user else None,
            session_id=str(session["id"]),
            question=inputs.get("question_intention"),
            locale=session.get("locale") or "en-AU",
            timezone=session.get("timezone") or "Australia/Melbourne",
            style=session.get("style"),
            unlocked=bool(entitlements.get("subscription_active")),
        )
        continuity_context = build_continuity_context(
            user_id=context.user_id,
            session_id=context.session_id,
        )
        persona_id = choose_persona(context, continuity_context)
        persona = get_persona(persona_id)
        profile = get_llm_profile("preview_mystic" if persona.default_profile == "full_premium" else persona.default_profile)
        prompt = compose_generation_prompt(
            persona_id=persona.id,
            flow_id="session_preview",
            continuity_context=continuity_context,
            domain_context={
                "question": context.question,
                "flow_type": flow_type,
                "astrology_facts": astrology_facts,
                "tarot": tarot_payload,
            },
        )
        normalized = NormalizedMysticOutput(
            opening_hook="A pattern is beginning to gather around this question.",
            current_pattern="The symbols point to a quieter but meaningful shift already underway.",
            emotional_truth="Part of the tension comes from sensing change before you fully trust it.",
            practical_guidance="Stay with the clearest signal instead of chasing every possibility.",
            continuity_callback=None,
            next_return_invitation="Come back tomorrow and see what sharpens once the pattern settles.",
            premium_teaser="There is a deeper layer beneath this spread if you want the fuller reading.",
            theme_tags=["change", "clarity"],
        )
        metadata = GenerationMetadata(
            persona_id=persona.id,
            llm_profile_id=profile.id,
            prompt_version=prompt["prompt_version"],
            model_id=profile.model_id,
            theme_tags=normalized.theme_tags,
            headline=normalized.opening_hook,
        )
        payload = build_preview_payload(
            normalized=normalized,
            metadata=metadata,
            flow_type=flow_type,
            unlock_price=unlock_price,
            product_id=product_id,
            entitlements=entitlements,
            astrology_facts=astrology_facts,
            tarot_payload=tarot_payload,
        )
        return OrchestrationResult(payload=payload, metadata=metadata, cost_usd=0.0)


_generation_orchestrator: MysticGenerationOrchestrator | None = None


def get_generation_orchestrator() -> MysticGenerationOrchestrator:
    global _generation_orchestrator
    if _generation_orchestrator is None:
        _generation_orchestrator = MysticGenerationOrchestrator()
    return _generation_orchestrator
