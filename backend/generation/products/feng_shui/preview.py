from __future__ import annotations

from datetime import datetime, timezone

from .mapper import map_feng_shui_preview


def build_feng_shui_preview_payload(
    *,
    normalized,
    metadata,
    analysis,
    product_id: str,
    entitlements: dict,
    price_amount: float,
):
    mapped = map_feng_shui_preview(normalized, analysis=analysis or {})
    return {
        "teaser_text": mapped["teaser_text"],
        "analysis_type": (analysis or {}).get("analysis_type") or "single_room",
        "unlock_price": {
            "currency": "USD",
            "amount": 0.0 if (entitlements or {}).get("included") else price_amount,
        },
        "product_id": product_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entitlements": entitlements or {},
        "meta": {
            "persona_id": metadata.persona_id,
            "llm_profile_id": metadata.llm_profile_id,
            "prompt_version": metadata.prompt_version,
            "theme_tags": metadata.theme_tags,
            "headline": mapped["headline"] or metadata.headline,
        },
    }
