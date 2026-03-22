from __future__ import annotations

from bedrock_service import get_bedrock_service

from .continuity.builder import build_continuity_context
from .formatting.preview_formatter import build_preview_payload
from .formatting.reading_formatter import build_reading_payload
from .parser import parse_normalized_output
from .personas import get_persona
from .profiles import get_llm_profile
from .prompts.composer import compose_generation_prompt
from .routing.persona_router import choose_persona
from .types import GenerationContext, GenerationMetadata, OrchestrationResult


class MysticGenerationOrchestrator:
    """Phase-1 scaffolding for persona-based Bedrock orchestration.

    This class intentionally keeps behavior minimal until individual endpoints
    are cut over behind feature flags.
    """

    def _invoke_normalized_generation(
        self,
        *,
        persona_id: str,
        flow_id: str,
        continuity_context: dict | None,
        domain_context: dict,
        profile_id: str,
    ) -> tuple[dict, GenerationMetadata, OrchestrationResult]:
        persona = get_persona(persona_id)
        profile = get_llm_profile(profile_id)
        prompt = compose_generation_prompt(
            persona_id=persona.id,
            flow_id=flow_id,
            continuity_context=continuity_context,
            domain_context=domain_context,
        )
        bedrock = get_bedrock_service()
        llm_result = bedrock.invoke_text(
            model_id=profile.model_id,
            system_prompt=prompt["system_prompt"],
            user_messages=prompt["messages"],
            temperature=profile.temperature,
            top_p=profile.top_p,
            max_tokens=profile.max_tokens,
        )
        normalized = parse_normalized_output(llm_result["text"])
        metadata = GenerationMetadata(
            persona_id=persona.id,
            llm_profile_id=profile.id,
            prompt_version=prompt["prompt_version"],
            model_id=llm_result["model"],
            theme_tags=normalized.theme_tags,
            headline=normalized.opening_hook,
        )
        result = OrchestrationResult(
            payload={},
            metadata=metadata,
            input_tokens=llm_result["input_tokens"],
            output_tokens=llm_result["output_tokens"],
            cost_usd=llm_result["cost_usd"],
        )
        return normalized, metadata, result

    def _build_session_context(
        self,
        *,
        session: dict,
        user: dict | None,
        surface: str,
        unlocked: bool,
    ) -> GenerationContext:
        inputs = session.get("inputs") or {}
        flow_type = inputs.get("flow_type") or "combined"
        return GenerationContext(
            object_id=str(session["id"]),
            object_type="session",
            flow_type=flow_type,
            surface=surface,
            user_id=str(user["id"]) if user else None,
            session_id=str(session["id"]),
            question=inputs.get("question_intention"),
            locale=session.get("locale") or "en-AU",
            timezone=session.get("timezone") or "Australia/Melbourne",
            style=session.get("style"),
            unlocked=unlocked,
        )

    def _build_compatibility_context(
        self,
        *,
        compat: dict,
        user: dict | None,
        surface: str,
        question: str | None = None,
    ) -> GenerationContext:
        return GenerationContext(
            object_id=str(compat["id"]),
            object_type="compatibility",
            flow_type="compatibility",
            surface=surface,
            user_id=str(user["id"]) if user else None,
            session_id=str(compat["id"]),
            question=question,
        )

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
        context = self._build_session_context(
            session=session,
            user=user,
            surface="preview",
            unlocked=bool(entitlements.get("subscription_active")),
        )
        continuity_context = build_continuity_context(
            user_id=context.user_id,
            session_id=context.session_id,
        )
        persona_id = choose_persona(context, continuity_context)
        normalized, metadata, result = self._invoke_normalized_generation(
            persona_id=persona_id,
            flow_id="session_preview",
            continuity_context=continuity_context,
            domain_context={
                "question": context.question,
                "flow_type": flow_type,
                "astrology_facts": astrology_facts,
                "tarot": tarot_payload,
            },
            profile_id="preview_mystic",
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
        result.payload = payload
        return result

    def build_session_reading_result(
        self,
        *,
        session: dict,
        user: dict | None,
        astrology_facts: dict,
        tarot_payload: dict,
        palm_features: list[dict] | None,
        include_palm: bool,
        deep_access: bool,
        content_contract: dict,
    ) -> OrchestrationResult:
        inputs = session.get("inputs") or {}
        flow_type = inputs.get("flow_type") or "combined"
        context = self._build_session_context(
            session=session,
            user=user,
            surface="full",
            unlocked=True,
        )
        continuity_context = build_continuity_context(
            user_id=context.user_id,
            session_id=context.session_id,
        )
        persona_id = choose_persona(context, continuity_context)
        normalized, metadata, result = self._invoke_normalized_generation(
            persona_id=persona_id,
            flow_id="session_reading",
            continuity_context=continuity_context,
            domain_context={
                "question": context.question,
                "flow_type": flow_type,
                "style": context.style,
                "astrology_facts": astrology_facts,
                "tarot": tarot_payload,
                "palm_features": palm_features or [],
                "include_palm": include_palm,
                "deep_access": deep_access,
                "content_contract": content_contract,
            },
            profile_id="full_premium",
        )
        metadata.continuity_source_session_id = context.session_id
        payload = build_reading_payload(normalized=normalized, metadata=metadata)
        payload["metadata"].update(
            {
                "includes_palm": include_palm,
                "deep_access": deep_access,
                "flow_type": flow_type,
                "content_contract": content_contract,
            }
        )
        result.payload = payload
        return result

    def build_compatibility_preview_result(
        self,
        *,
        compat: dict,
        user: dict | None,
        person1: dict,
        person2: dict,
        chart1: dict,
        chart2: dict,
        zodiac1: dict,
        zodiac2: dict,
        synastry: dict,
        zodiac_harmony: dict,
        entitlements: dict,
    ) -> OrchestrationResult:
        context = self._build_compatibility_context(compat=compat, user=user, surface="preview")
        continuity_context = build_continuity_context(user_id=context.user_id, session_id=context.session_id)
        persona_id = choose_persona(context, continuity_context)
        normalized, metadata, result = self._invoke_normalized_generation(
            persona_id=persona_id,
            flow_id="compatibility_preview",
            continuity_context=continuity_context,
            domain_context={
                "person1": {"profile": person1, "chart": chart1, "zodiac": zodiac1},
                "person2": {"profile": person2, "chart": chart2, "zodiac": zodiac2},
                "synastry": synastry,
                "zodiac_compatibility": zodiac_harmony,
            },
            profile_id="preview_mystic",
        )
        payload = {
            "teaser_text": " ".join(
                part.strip()
                for part in [normalized.opening_hook, normalized.current_pattern, normalized.premium_teaser]
                if part and part.strip()
            ),
            "person1": {"profile": person1, "chart": chart1, "zodiac": zodiac1},
            "person2": {"profile": person2, "chart": chart2, "zodiac": zodiac2},
            "synastry": synastry,
            "unlock_price": {"currency": "USD", "amount": 0.0 if entitlements.get("included") else 3.99},
            "product_id": "compatibility", 
            "entitlements": entitlements,
            "meta": {
                "persona_id": metadata.persona_id,
                "llm_profile_id": metadata.llm_profile_id,
                "prompt_version": metadata.prompt_version,
                "theme_tags": metadata.theme_tags,
                "headline": metadata.headline,
            },
        }
        result.payload = payload
        return result

    def build_compatibility_reading_result(
        self,
        *,
        compat: dict,
        user: dict | None,
        person1: dict,
        person2: dict,
        chart1: dict,
        chart2: dict,
        synastry: dict,
        zodiac_harmony: dict,
    ) -> OrchestrationResult:
        context = self._build_compatibility_context(compat=compat, user=user, surface="full")
        continuity_context = build_continuity_context(user_id=context.user_id, session_id=context.session_id)
        persona_id = choose_persona(context, continuity_context)
        normalized, metadata, result = self._invoke_normalized_generation(
            persona_id=persona_id,
            flow_id="compatibility_reading",
            continuity_context=continuity_context,
            domain_context={
                "person1": {"profile": person1, "chart": chart1},
                "person2": {"profile": person2, "chart": chart2},
                "synastry": synastry,
                "zodiac_compatibility": zodiac_harmony,
            },
            profile_id="full_premium",
        )
        metadata.continuity_source_session_id = context.session_id
        payload = build_reading_payload(normalized=normalized, metadata=metadata)
        payload["metadata"].update({"flow_type": "compatibility"})
        result.payload = payload
        return result


_generation_orchestrator: MysticGenerationOrchestrator | None = None


def get_generation_orchestrator() -> MysticGenerationOrchestrator:
    global _generation_orchestrator
    if _generation_orchestrator is None:
        _generation_orchestrator = MysticGenerationOrchestrator()
    return _generation_orchestrator
