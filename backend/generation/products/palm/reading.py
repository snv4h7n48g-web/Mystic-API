from __future__ import annotations

from datetime import datetime, timezone

from .mapper import map_palm_reading


def build_palm_reading_payload(*, normalized, metadata, palm_features: list[dict] | None = None) -> dict:
    mapped = map_palm_reading(normalized, palm_features=palm_features or [])
    sections = [
        {"id": "opening_invocation", "title": "OPENING", "text": mapped["opening_invocation"]},
        {"id": "palm_insight", "title": "PALM INSIGHT", "text": mapped["palm_insight"]},
        {"id": "integrated_synthesis", "title": "SYNTHESIS", "text": mapped["integrated_synthesis"]},
        {"id": "reflective_guidance", "title": "GUIDANCE", "text": mapped["reflective_guidance"]},
        {"id": "closing_prompt", "title": "CLOSING", "text": mapped["closing_prompt"]},
    ]
    sections = [section for section in sections if section["text"] and section["text"].strip()]
    return {
        "sections": sections,
        "full_text": "\n\n".join(section["text"] for section in sections),
        "metadata": {
            "persona_id": metadata.persona_id,
            "llm_profile_id": metadata.llm_profile_id,
            "prompt_version": metadata.prompt_version,
            "theme_tags": metadata.theme_tags,
            "headline": metadata.headline,
            "model": metadata.model_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "flow_type": "palm_solo",
            "palm_feature_count": len(palm_features or []),
        },
    }
