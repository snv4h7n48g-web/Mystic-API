from __future__ import annotations

import json
from datetime import datetime, timezone

from ..types import GenerationMetadata, NormalizedMysticOutput


def _clean_continuity_callback(value: str | None) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        return ""
    try:
        parsed = json.loads(cleaned)
    except (TypeError, ValueError):
        return cleaned
    if isinstance(parsed, dict) and parsed.get("type") == "no_history":
        return ""
    if isinstance(parsed, dict) and not parsed.get("message"):
        return ""
    return cleaned


def build_reading_payload(*, normalized: NormalizedMysticOutput, metadata: GenerationMetadata) -> dict:
    continuity_callback = _clean_continuity_callback(normalized.continuity_callback)
    sections = [
        {"id": "opening_hook", "title": "OPENING", "text": normalized.opening_hook},
        {"id": "current_pattern", "title": "CURRENT PATTERN", "text": normalized.current_pattern},
        {"id": "emotional_truth", "title": "EMOTIONAL TRUTH", "text": normalized.emotional_truth},
        {"id": "practical_guidance", "title": "GUIDANCE", "text": normalized.practical_guidance},
        {
            "id": "next_return_invitation",
            "title": "NEXT RETURN",
            "text": normalized.next_return_invitation,
        },
    ]
    if continuity_callback:
        sections.insert(
            3,
            {
                "id": "continuity_callback",
                "title": "CONTINUITY",
                "text": continuity_callback,
            },
        )

    full_text = "\n\n".join(section["text"] for section in sections if str(section["text"]).strip())

    return {
        "sections": sections,
        "full_text": full_text,
        "metadata": {
            "persona_id": metadata.persona_id,
            "llm_profile_id": metadata.llm_profile_id,
            "prompt_version": metadata.prompt_version,
            "theme_tags": metadata.theme_tags,
            "headline": metadata.headline,
            "model": metadata.model_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
