from __future__ import annotations

from datetime import datetime, timezone

from ..types import GenerationMetadata, NormalizedMysticOutput


def build_preview_payload(
    *,
    normalized: NormalizedMysticOutput,
    metadata: GenerationMetadata,
    flow_type: str,
    unlock_price: dict,
    product_id: str,
    entitlements: dict,
    astrology_facts: dict,
    tarot_payload: dict,
) -> dict:
    teaser_parts = [normalized.opening_hook, normalized.current_pattern]
    if normalized.premium_teaser:
        teaser_parts.append(normalized.premium_teaser)

    return {
        "flow_type": flow_type,
        "astrology_facts": astrology_facts,
        "tarot": tarot_payload,
        "teaser_text": " ".join(part.strip() for part in teaser_parts if part and part.strip()),
        "unlock_price": unlock_price,
        "product_id": product_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entitlements": entitlements,
        "meta": {
            "persona_id": metadata.persona_id,
            "llm_profile_id": metadata.llm_profile_id,
            "prompt_version": metadata.prompt_version,
            "theme_tags": metadata.theme_tags,
            "headline": metadata.headline,
            "model": metadata.model_id,
        },
    }
