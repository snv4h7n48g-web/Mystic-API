from __future__ import annotations

import logging
import time
from typing import Any

from bedrock_service import get_bedrock_service

from .continuity.builder import build_continuity_context
from .formatting.preview_formatter import build_preview_payload
from .formatting.reading_formatter import build_reading_payload
from .parser import parse_normalized_output
from .personas import get_persona
from .product_contracts import get_product_contract
from .product_routing import get_product_route_for_context
from .products.daily_horoscope.continuity import filter_daily_continuity
from .products.daily_horoscope.reading import build_daily_horoscope_reading_payload
from .products.full_reading.formatter import build_full_reading_payload
from .products.lunar.continuity import filter_lunar_continuity
from .products.lunar.reading import build_lunar_reading_payload
from .products.sun_moon.continuity import filter_sun_moon_continuity
from .products.sun_moon.reading import build_sun_moon_reading_payload
from .products.tarot.continuity import filter_tarot_continuity
from .products.tarot.reading import build_tarot_reading_payload
from .profiles import LlmProfile, get_llm_profile
from .prompts.composer import compose_generation_prompt
from .routing.persona_router import choose_persona
from .types import GenerationContext, GenerationMetadata, NormalizedMysticOutput, OrchestrationResult
from .validators import ValidationResult, validate_product_payload


logger = logging.getLogger("mystic.orchestration")


class MysticGenerationOrchestrator:
    """Phase-3 product-aware orchestration with bounded validation retries."""

    def _summarize_generation_metrics(self, *, attempt_metrics: list[dict[str, Any]], total_duration_ms: float) -> dict[str, Any]:
        provider_total_ms = round(
            sum((metric.get("provider_duration_ms") or 0) for metric in attempt_metrics),
            2,
        )
        parse_total_ms = round(
            sum((metric.get("parse_duration_ms") or 0) for metric in attempt_metrics),
            2,
        )
        attempt_total_ms = round(
            sum((metric.get("attempt_duration_ms") or 0) for metric in attempt_metrics),
            2,
        )
        orchestration_overhead_ms = round(max(0.0, total_duration_ms - provider_total_ms - parse_total_ms), 2)
        attempt_models = [metric.get("attempt_model") for metric in attempt_metrics if metric.get("attempt_model")]
        summary = (
            f"total={total_duration_ms}ms "
            f"provider={provider_total_ms}ms "
            f"parse={parse_total_ms}ms "
            f"overhead={orchestration_overhead_ms}ms "
            f"attempts={len(attempt_metrics)} "
            f"models={','.join(attempt_models) if attempt_models else 'unknown'}"
        )
        return {
            "provider_total_ms": provider_total_ms,
            "parse_total_ms": parse_total_ms,
            "attempt_total_ms": attempt_total_ms,
            "orchestration_overhead_ms": orchestration_overhead_ms,
            "attempt_models": attempt_models,
            "summary": summary,
        }

    def _quality_gate_policy(self, *, context: GenerationContext, product_key: str | None) -> dict:
        return {
            "max_attempts": 2 if product_key else 1,
            "attach_validation_metadata": context.surface == "full",
            "hard_fail_on_exhausted_validation": False,
        }

    def _invoke_normalized_generation(
        self,
        *,
        context: GenerationContext,
        persona_id: str,
        flow_id: str,
        continuity_context: dict | None,
        domain_context: dict,
        contract_instruction: str | None = None,
        retry_instruction: str | None = None,
    ) -> tuple[dict, GenerationMetadata, OrchestrationResult]:
        persona = get_persona(persona_id)
        route = get_product_route_for_context(context)
        base_profile = get_llm_profile(route.profile_id_for_surface(context.surface))
        prompt = compose_generation_prompt(
            persona_id=persona.id,
            flow_id=flow_id,
            continuity_context=continuity_context,
            domain_context=domain_context,
            contract_instruction=contract_instruction,
            retry_instruction=retry_instruction,
        )
        bedrock = get_bedrock_service()

        candidate_model_ids = [route.model_id_for_surface(context.surface)]
        fallback_model_id = route.fallback_model_id
        if fallback_model_id and fallback_model_id not in candidate_model_ids:
            candidate_model_ids.append(fallback_model_id)

        last_error: Exception | None = None
        for candidate_index, candidate_model_id in enumerate(candidate_model_ids, start=1):
            profile = LlmProfile(
                id=base_profile.id,
                model_id=candidate_model_id,
                temperature=base_profile.temperature,
                top_p=base_profile.top_p,
                max_tokens=route.max_tokens_for_surface(context.surface),
                timeout_ms=base_profile.timeout_ms,
            )
            attempt_started = time.perf_counter()
            try:
                llm_result = bedrock.invoke_text(
                    model_id=profile.model_id,
                    system_prompt=prompt["system_prompt"],
                    user_messages=prompt["messages"],
                    temperature=profile.temperature,
                    top_p=profile.top_p,
                    max_tokens=profile.max_tokens,
                    timeout_ms=profile.timeout_ms,
                )
                parse_started = time.perf_counter()
                normalized = parse_normalized_output(llm_result["text"])
                parse_duration_ms = round((time.perf_counter() - parse_started) * 1000, 2)
                total_attempt_ms = round((time.perf_counter() - attempt_started) * 1000, 2)
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
                    generation_metrics={
                        "attempt_model": candidate_model_id,
                        "attempt_index": candidate_index,
                        "used_fallback_model": candidate_index > 1,
                        "attempt_duration_ms": total_attempt_ms,
                        "provider_duration_ms": llm_result.get("duration_ms"),
                        "parse_duration_ms": parse_duration_ms,
                        "timeout_ms": profile.timeout_ms,
                        "prompt_chars": prompt.get("prompt_chars", 0),
                        "prompt_message_count": len(prompt.get("messages", [])),
                        "context_chars": prompt.get("context_chars", 0),
                    },
                )
                logger.info(
                    "generation_attempt_success flow=%s surface=%s product=%s attempt=%s/%s model=%s fallback=%s duration_ms=%s provider_ms=%s parse_ms=%s timeout_ms=%s prompt_chars=%s",
                    context.flow_type,
                    context.surface,
                    route.product_key,
                    candidate_index,
                    len(candidate_model_ids),
                    candidate_model_id,
                    candidate_index > 1,
                    total_attempt_ms,
                    llm_result.get("duration_ms"),
                    parse_duration_ms,
                    profile.timeout_ms,
                    prompt.get("prompt_chars", 0),
                )
                return normalized, metadata, result
            except Exception as exc:
                last_error = exc
                elapsed_ms = round((time.perf_counter() - attempt_started) * 1000, 2)
                logger.warning(
                    "generation_attempt_failed flow=%s surface=%s product=%s attempt=%s/%s model=%s fallback=%s duration_ms=%s timeout_ms=%s error=%s",
                    context.flow_type,
                    context.surface,
                    route.product_key,
                    candidate_index,
                    len(candidate_model_ids),
                    candidate_model_id,
                    candidate_index > 1,
                    elapsed_ms,
                    profile.timeout_ms,
                    exc,
                )

        assert last_error is not None
        raise last_error

    def _attach_contract_metadata(self, *, context: GenerationContext, payload: dict, validation: ValidationResult | None = None, attempts: int = 1) -> None:
        contract = get_product_contract(get_product_route_for_context(context).product_key)
        policy = self._quality_gate_policy(context=context, product_key=(contract.product_key if contract else None))
        if not contract or not policy["attach_validation_metadata"]:
            return
        if validation is None:
            validation = validate_product_payload(contract.product_key, payload)
        metadata = payload.setdefault("metadata", payload.setdefault("meta", {}))
        metadata["validation"] = {
            "product_key": validation.product_key,
            "valid": validation.valid,
            "passed": validation.passed,
            "issues": validation.issues,
            "retry_hint": validation.retry_hint,
            "attempts": attempts,
        }
        metadata["expected_section_ids"] = contract.expected_section_ids

    def _attach_generation_metrics(self, *, payload: dict, metrics: dict[str, Any]) -> None:
        metadata = payload.setdefault("metadata", payload.setdefault("meta", {}))
        metadata["generation_timing"] = metrics

    def _build_payload_for_context(self, *, context: GenerationContext, normalized: NormalizedMysticOutput, metadata: GenerationMetadata, unlock_price: dict | None = None, product_id: str | None = None, entitlements: dict | None = None, astrology_facts: dict | None = None, tarot_payload: dict | None = None, palm_features: list[dict] | None = None, include_palm: bool = False, deep_access: bool = False, content_contract: dict | None = None, person1: dict | None = None, person2: dict | None = None, chart1: dict | None = None, chart2: dict | None = None, zodiac1: dict | None = None, zodiac2: dict | None = None, synastry: dict | None = None, zodiac_harmony: dict | None = None, analysis: dict | None = None, price_amount: float = 0.0) -> dict:
        if context.object_type == "session" and context.surface == "preview":
            return build_preview_payload(
                normalized=normalized,
                metadata=metadata,
                flow_type=context.flow_type,
                unlock_price=unlock_price or {},
                product_id=product_id or "",
                entitlements=entitlements or {},
                astrology_facts=astrology_facts or {},
                tarot_payload=tarot_payload or {},
            )
        if context.object_type == "session" and context.surface == "full":
            payload = (
                build_daily_horoscope_reading_payload(normalized=normalized, metadata=metadata)
                if context.flow_type == "daily_horoscope"
                else build_lunar_reading_payload(normalized=normalized, metadata=metadata)
                if context.flow_type == "lunar_new_year_solo"
                else build_tarot_reading_payload(normalized=normalized, metadata=metadata)
                if context.flow_type == "tarot_solo"
                else build_sun_moon_reading_payload(normalized=normalized, metadata=metadata)
                if context.flow_type == "sun_moon_solo"
                else build_full_reading_payload(
                    normalized=normalized,
                    metadata=metadata,
                    question=context.question,
                    tarot_payload=tarot_payload or {},
                    palm_features=palm_features or [],
                    include_palm=include_palm,
                    content_contract=content_contract or {},
                )
                if context.flow_type == "combined"
                else build_reading_payload(normalized=normalized, metadata=metadata)
            )
            payload["metadata"].update({
                "includes_palm": include_palm,
                "deep_access": deep_access,
                "flow_type": context.flow_type,
                "content_contract": content_contract or {},
            })
            return payload
        if context.object_type == "compatibility" and context.surface == "preview":
            return {
                "teaser_text": " ".join(part.strip() for part in [normalized.opening_hook, normalized.current_pattern, normalized.premium_teaser] if part and part.strip()),
                "person1": {"profile": person1, "chart": chart1, "zodiac": zodiac1},
                "person2": {"profile": person2, "chart": chart2, "zodiac": zodiac2},
                "synastry": synastry,
                "unlock_price": {"currency": "USD", "amount": 0.0 if (entitlements or {}).get("included") else 3.99},
                "product_id": "compatibility",
                "entitlements": entitlements or {},
                "meta": {
                    "persona_id": metadata.persona_id,
                    "llm_profile_id": metadata.llm_profile_id,
                    "prompt_version": metadata.prompt_version,
                    "theme_tags": metadata.theme_tags,
                    "headline": metadata.headline,
                },
                "sections": [
                    {"id": "opening_hook", "text": normalized.opening_hook},
                    {"id": "current_pattern", "text": normalized.current_pattern},
                    {"id": "emotional_truth", "text": normalized.emotional_truth},
                    {"id": "practical_guidance", "text": normalized.practical_guidance},
                    {"id": "next_return_invitation", "text": normalized.next_return_invitation},
                ],
            }
        if context.object_type == "compatibility" and context.surface == "full":
            payload = build_reading_payload(normalized=normalized, metadata=metadata)
            payload["metadata"].update({"flow_type": "compatibility"})
            return payload
        if context.object_type == "feng_shui" and context.surface == "preview":
            return {
                "teaser_text": " ".join(part.strip() for part in [normalized.opening_hook, normalized.current_pattern, normalized.premium_teaser] if part and part.strip()),
                "analysis_type": (analysis or {}).get("analysis_type") or "single_room",
                "unlock_price": {"currency": "USD", "amount": 0.0 if (entitlements or {}).get("included") else 0.0},
                "product_id": product_id or "",
                "entitlements": entitlements or {},
                "meta": {
                    "persona_id": metadata.persona_id,
                    "llm_profile_id": metadata.llm_profile_id,
                    "prompt_version": metadata.prompt_version,
                    "theme_tags": metadata.theme_tags,
                    "headline": metadata.headline,
                },
                "sections": [
                    {"id": "opening_hook", "text": normalized.opening_hook},
                    {"id": "current_pattern", "text": normalized.current_pattern},
                    {"id": "emotional_truth", "text": normalized.emotional_truth},
                    {"id": "practical_guidance", "text": normalized.practical_guidance},
                    {"id": "next_return_invitation", "text": normalized.next_return_invitation},
                ],
            }
        if context.object_type == "feng_shui" and context.surface == "full":
            payload = build_reading_payload(normalized=normalized, metadata=metadata)
            payload["metadata"].update({"flow_type": "feng_shui"})
            return payload
        return build_reading_payload(normalized=normalized, metadata=metadata)

    def _generate_with_quality_gate(self, *, context: GenerationContext, persona_id: str, flow_id: str, continuity_context: dict | None, domain_context: dict, contract_instruction: str | None = None, payload_builder_kwargs: dict | None = None) -> OrchestrationResult:
        payload_builder_kwargs = payload_builder_kwargs or {}
        route = get_product_route_for_context(context)
        contract = get_product_contract(route.product_key)
        attempts: list[tuple[NormalizedMysticOutput, GenerationMetadata, OrchestrationResult, dict, ValidationResult]] = []
        retry_instruction: str | None = None
        generation_started = time.perf_counter()
        policy = self._quality_gate_policy(context=context, product_key=(contract.product_key if contract else None))
        max_attempts = max(1, int(policy.get('max_attempts', 1)))

        for _ in range(max_attempts):
            normalized, metadata, result = self._invoke_normalized_generation(
                context=context,
                persona_id=persona_id,
                flow_id=flow_id,
                continuity_context=continuity_context,
                domain_context=domain_context,
                contract_instruction=contract_instruction,
                retry_instruction=retry_instruction,
            )
            payload = self._build_payload_for_context(
                context=context,
                normalized=normalized,
                metadata=metadata,
                **payload_builder_kwargs,
            )
            validation = validate_product_payload(contract.product_key, payload) if contract else ValidationResult(product_key="unknown", passed=True)
            attempts.append((normalized, metadata, result, payload, validation))
            if validation.passed or not contract or not validation.retry_hint:
                break
            retry_instruction = validation.retry_hint

        _, _, final_result, final_payload, final_validation = attempts[-1]
        final_attempt_count = len(attempts)
        total_duration_ms = round((time.perf_counter() - generation_started) * 1000, 2)
        attempt_metrics = [attempt[2].generation_metrics for attempt in attempts]
        timing_summary = self._summarize_generation_metrics(
            attempt_metrics=attempt_metrics,
            total_duration_ms=total_duration_ms,
        )
        generation_metrics = {
            "total_duration_ms": total_duration_ms,
            "retry_count": max(0, final_attempt_count - 1),
            "attempt_count": final_attempt_count,
            "used_fallback_model": any(metric.get("used_fallback_model") for metric in attempt_metrics),
            "fallback_models_used": [metric.get("attempt_model") for metric in attempt_metrics if metric.get("used_fallback_model")],
            "prompt_chars": max((metric.get("prompt_chars") or 0) for metric in attempt_metrics) if attempt_metrics else 0,
            "context_chars": max((metric.get("context_chars") or 0) for metric in attempt_metrics) if attempt_metrics else 0,
            "provider_total_ms": timing_summary["provider_total_ms"],
            "parse_total_ms": timing_summary["parse_total_ms"],
            "attempt_total_ms": timing_summary["attempt_total_ms"],
            "orchestration_overhead_ms": timing_summary["orchestration_overhead_ms"],
            "attempt_models": timing_summary["attempt_models"],
            "summary": timing_summary["summary"],
            "attempts": attempt_metrics,
        }
        self._attach_generation_metrics(payload=final_payload, metrics=generation_metrics)
        self._attach_contract_metadata(context=context, payload=final_payload, validation=final_validation, attempts=final_attempt_count)
        final_guidance_text = next((section.get("text", "") for section in final_payload.get("sections", []) if section.get("id") in {"practical_guidance", "reflective_guidance"}), "")
        logger.warning(
            "quality_gate_final product=%s flow=%s surface=%s attempts=%s retries=%s fallback=%s total_duration_ms=%s passed=%s issues=%s guidance=%r timing_summary=%s",
            route.product_key,
            context.flow_type,
            context.surface,
            final_attempt_count,
            generation_metrics["retry_count"],
            generation_metrics["used_fallback_model"],
            total_duration_ms,
            final_validation.passed,
            final_validation.issues,
            final_guidance_text[:240],
            generation_metrics["summary"],
        )
        logger.warning(
            "generation_latency_breakdown object_type=%s object_id=%s flow=%s surface=%s summary=%s",
            context.object_type,
            context.object_id,
            context.flow_type,
            context.surface,
            generation_metrics["summary"],
        )
        final_result.payload = final_payload
        final_result.generation_metrics = generation_metrics
        if final_attempt_count > 1:
            final_result.input_tokens = sum(attempt[2].input_tokens for attempt in attempts)
            final_result.output_tokens = sum(attempt[2].output_tokens for attempt in attempts)
            final_result.cost_usd = sum(attempt[2].cost_usd for attempt in attempts)
        return final_result

    def _build_session_context(self, *, session: dict, user: dict | None, surface: str, unlocked: bool) -> GenerationContext:
        inputs = session.get("inputs") or {}
        return GenerationContext(
            object_id=str(session["id"]),
            object_type="session",
            flow_type=inputs.get("flow_type") or "combined",
            surface=surface,
            user_id=str(user["id"]) if user else None,
            session_id=str(session["id"]),
            question=inputs.get("question_intention"),
            locale=session.get("locale") or "en-AU",
            timezone=session.get("timezone") or "Australia/Melbourne",
            style=session.get("style"),
            unlocked=unlocked,
        )

    def _build_compatibility_context(self, *, compat: dict, user: dict | None, surface: str, question: str | None = None) -> GenerationContext:
        return GenerationContext(
            object_id=str(compat["id"]),
            object_type="compatibility",
            flow_type="compatibility",
            surface=surface,
            user_id=str(user["id"]) if user else None,
            session_id=str(compat["id"]),
            question=question,
        )

    def _build_feng_shui_context(self, *, analysis: dict, user: dict | None, surface: str) -> GenerationContext:
        return GenerationContext(
            object_id=str(analysis["id"]),
            object_type="feng_shui",
            flow_type="feng_shui",
            surface=surface,
            user_id=str(user["id"]) if user else None,
            session_id=str(analysis["id"]),
            question=analysis.get("user_goals"),
        )

    def build_session_preview_result(self, *, session: dict, user: dict | None, astrology_facts: dict, tarot_payload: dict, unlock_price: dict, product_id: str, entitlements: dict) -> OrchestrationResult:
        context = self._build_session_context(session=session, user=user, surface="preview", unlocked=bool(entitlements.get("subscription_active")))
        continuity_context = build_continuity_context(
            user_id=context.user_id,
            session_id=context.session_id,
            current_flow_type=context.flow_type,
            current_object_type=context.object_type,
        )
        persona_id = choose_persona(context, continuity_context)
        contract = get_product_contract(get_product_route_for_context(context).product_key)
        flow_id = contract.prompt_ids["preview"] if contract else ("daily_horoscope_preview" if context.flow_type == "daily_horoscope" else "lunar_new_year_preview" if context.flow_type == "lunar_new_year_solo" else "session_preview")
        return self._generate_with_quality_gate(
            context=context,
            persona_id=persona_id,
            flow_id=flow_id,
            continuity_context=continuity_context,
            domain_context={
                "question": context.question,
                "flow_type": context.flow_type,
                "astrology_facts": astrology_facts,
                "tarot": tarot_payload,
            },
            contract_instruction=(contract.contract_instruction if contract else None),
            payload_builder_kwargs={
                "unlock_price": unlock_price,
                "product_id": product_id,
                "entitlements": entitlements,
                "astrology_facts": astrology_facts,
                "tarot_payload": tarot_payload,
            },
        )

    def build_session_reading_result(self, *, session: dict, user: dict | None, astrology_facts: dict, tarot_payload: dict, palm_features: list[dict] | None, include_palm: bool, deep_access: bool, content_contract: dict) -> OrchestrationResult:
        context = self._build_session_context(session=session, user=user, surface="full", unlocked=True)
        continuity_context = build_continuity_context(
            user_id=context.user_id,
            session_id=context.session_id,
            current_flow_type=context.flow_type,
            current_object_type=context.object_type,
        )
        if context.flow_type == "daily_horoscope":
            continuity_context = filter_daily_continuity(continuity_context)
        elif context.flow_type == "lunar_new_year_solo":
            continuity_context = filter_lunar_continuity(continuity_context)
        elif context.flow_type == "sun_moon_solo":
            continuity_context = filter_sun_moon_continuity(continuity_context)
        elif context.flow_type == "tarot_solo":
            continuity_context = filter_tarot_continuity(continuity_context)
        persona_id = choose_persona(context, continuity_context)
        contract = get_product_contract(get_product_route_for_context(context).product_key)
        flow_id = contract.prompt_ids["reading"] if contract else ("daily_horoscope_reading" if context.flow_type == "daily_horoscope" else "lunar_new_year_reading" if context.flow_type == "lunar_new_year_solo" else "session_reading")
        result = self._generate_with_quality_gate(
            context=context,
            persona_id=persona_id,
            flow_id=flow_id,
            continuity_context=continuity_context,
            domain_context={
                "question": context.question,
                "flow_type": context.flow_type,
                "style": context.style,
                "astrology_facts": astrology_facts,
                "tarot": tarot_payload,
                "palm_features": palm_features or [],
                "include_palm": include_palm,
                "deep_access": deep_access,
                "content_contract": content_contract,
            },
            contract_instruction=(contract.contract_instruction if contract else None),
            payload_builder_kwargs={
                "tarot_payload": tarot_payload,
                "palm_features": palm_features or [],
                "include_palm": include_palm,
                "deep_access": deep_access,
                "content_contract": content_contract,
            },
        )
        result.metadata.continuity_source_session_id = context.session_id
        return result

    def build_compatibility_preview_result(self, *, compat: dict, user: dict | None, person1: dict, person2: dict, chart1: dict, chart2: dict, zodiac1: dict, zodiac2: dict, synastry: dict, zodiac_harmony: dict, entitlements: dict) -> OrchestrationResult:
        context = self._build_compatibility_context(compat=compat, user=user, surface="preview")
        continuity_context = build_continuity_context(user_id=context.user_id, session_id=context.session_id)
        persona_id = choose_persona(context, continuity_context)
        contract = get_product_contract(get_product_route_for_context(context).product_key)
        return self._generate_with_quality_gate(
            context=context,
            persona_id=persona_id,
            flow_id=(contract.prompt_ids["preview"] if contract else "compatibility_preview"),
            continuity_context=continuity_context,
            domain_context={
                "person1": {"profile": person1, "chart": chart1, "zodiac": zodiac1},
                "person2": {"profile": person2, "chart": chart2, "zodiac": zodiac2},
                "synastry": synastry,
                "zodiac_compatibility": zodiac_harmony,
            },
            contract_instruction=(contract.contract_instruction if contract else None),
            payload_builder_kwargs={
                "person1": person1,
                "person2": person2,
                "chart1": chart1,
                "chart2": chart2,
                "zodiac1": zodiac1,
                "zodiac2": zodiac2,
                "synastry": synastry,
                "zodiac_harmony": zodiac_harmony,
                "entitlements": entitlements,
            },
        )

    def build_compatibility_reading_result(self, *, compat: dict, user: dict | None, person1: dict, person2: dict, chart1: dict, chart2: dict, synastry: dict, zodiac_harmony: dict) -> OrchestrationResult:
        context = self._build_compatibility_context(compat=compat, user=user, surface="full")
        continuity_context = build_continuity_context(user_id=context.user_id, session_id=context.session_id)
        persona_id = choose_persona(context, continuity_context)
        contract = get_product_contract(get_product_route_for_context(context).product_key)
        result = self._generate_with_quality_gate(
            context=context,
            persona_id=persona_id,
            flow_id=(contract.prompt_ids["reading"] if contract else "compatibility_reading"),
            continuity_context=continuity_context,
            domain_context={
                "person1": {"profile": person1, "chart": chart1},
                "person2": {"profile": person2, "chart": chart2},
                "synastry": synastry,
                "zodiac_compatibility": zodiac_harmony,
            },
            contract_instruction=(contract.contract_instruction if contract else None),
        )
        result.metadata.continuity_source_session_id = context.session_id
        return result

    def build_feng_shui_preview_result(self, *, analysis: dict, user: dict | None, entitlements: dict, product_id: str, price_amount: float) -> OrchestrationResult:
        context = self._build_feng_shui_context(analysis=analysis, user=user, surface="preview")
        continuity_context = build_continuity_context(user_id=context.user_id, session_id=context.session_id)
        persona_id = choose_persona(context, continuity_context)
        contract = get_product_contract(get_product_route_for_context(context).product_key)
        return self._generate_with_quality_gate(
            context=context,
            persona_id=persona_id,
            flow_id=(contract.prompt_ids["preview"] if contract else "feng_shui_preview"),
            continuity_context=continuity_context,
            domain_context={
                "analysis_type": analysis.get("analysis_type"),
                "room_purpose": analysis.get("room_purpose"),
                "user_goals": analysis.get("user_goals"),
                "compass_direction": analysis.get("compass_direction"),
            },
            contract_instruction=(contract.contract_instruction if contract else None),
            payload_builder_kwargs={
                "analysis": analysis,
                "entitlements": entitlements,
                "product_id": product_id,
            },
        )

    def build_feng_shui_analysis_result(self, *, analysis: dict, user: dict | None, vision_result: dict) -> OrchestrationResult:
        context = self._build_feng_shui_context(analysis=analysis, user=user, surface="full")
        continuity_context = build_continuity_context(user_id=context.user_id, session_id=context.session_id)
        persona_id = choose_persona(context, continuity_context)
        contract = get_product_contract(get_product_route_for_context(context).product_key)
        result = self._generate_with_quality_gate(
            context=context,
            persona_id=persona_id,
            flow_id=(contract.prompt_ids["reading"] if contract else "feng_shui_analysis"),
            continuity_context=continuity_context,
            domain_context={
                "analysis_type": analysis.get("analysis_type"),
                "room_purpose": analysis.get("room_purpose"),
                "user_goals": analysis.get("user_goals"),
                "compass_direction": analysis.get("compass_direction"),
                "vision_analysis": vision_result,
            },
            contract_instruction=(contract.contract_instruction if contract else None),
        )
        result.metadata.continuity_source_session_id = context.session_id
        return result


_generation_orchestrator: MysticGenerationOrchestrator | None = None


def get_generation_orchestrator() -> MysticGenerationOrchestrator:
    global _generation_orchestrator
    if _generation_orchestrator is None:
        _generation_orchestrator = MysticGenerationOrchestrator()
    return _generation_orchestrator
