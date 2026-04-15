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
        {"id": "overview", "title": "OVERVIEW", "text": mapped["overview"]},
        {"id": "bagua_map", "title": "BAGUA MAP", "text": mapped["bagua_map"]},
        {"id": "energy_flow", "title": "ENERGY FLOW", "text": mapped["energy_flow"]},
        {"id": "priority_actions", "title": "PRIORITY ACTIONS", "text": mapped["priority_actions"]},
        {"id": "recommendations", "title": "RECOMMENDATIONS", "text": mapped["recommendations"]},
        {"id": "guidance", "title": "GUIDANCE", "text": mapped["guidance"]},
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
