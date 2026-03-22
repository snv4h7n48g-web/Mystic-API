from __future__ import annotations

from datetime import datetime, timezone

from ..types import GenerationMetadata, NormalizedMysticOutput


def build_reading_payload(*, normalized: NormalizedMysticOutput, metadata: GenerationMetadata) -> dict:
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
    if normalized.continuity_callback:
        sections.insert(
            3,
            {
                "id": "continuity_callback",
                "title": "CONTINUITY",
                "text": normalized.continuity_callback,
            },
        )

    full_text = "\n\n".join(section["text"] for section in sections if section["text"])

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
