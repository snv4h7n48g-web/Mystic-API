from __future__ import annotations

from datetime import datetime, timezone

from .mapper import map_feng_shui_analysis


def build_feng_shui_analysis_payload(*, normalized, metadata, analysis=None, vision_result=None):
    mapped = map_feng_shui_analysis(
        normalized,
        analysis=analysis or {},
        vision_result=vision_result or {},
    )
    sections = [
        {"id": "overview", "title": "ROOM OVERVIEW", "text": mapped["overview"]},
        {"id": "what_helps", "title": "WHAT HELPS", "text": mapped["what_helps"]},
        {"id": "what_blocks", "title": "WHAT BLOCKS", "text": mapped["what_blocks"]},
        {"id": "practical_fixes", "title": "PRACTICAL FIXES", "text": mapped["practical_fixes"]},
        {"id": "action_plan", "title": "ACTION PLAN", "text": mapped["action_plan"]},
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
            "flow_type": "feng_shui",
        },
    }
