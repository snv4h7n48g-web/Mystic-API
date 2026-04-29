from __future__ import annotations

from datetime import datetime, timezone

from .mapper import format_action_plan_text, format_practical_fixes_text, map_feng_shui_analysis


def repair_feng_shui_analysis_payload(payload: dict) -> tuple[dict, bool]:
    if not isinstance(payload, dict):
        return payload, False

    sections = payload.get("sections")
    if not isinstance(sections, list):
        return payload, False

    repaired_sections: list[dict] = []
    changed = False
    for raw_section in sections:
        if not isinstance(raw_section, dict):
            repaired_sections.append(raw_section)
            continue
        section = dict(raw_section)
        section_id = section.get("id")
        text = str(section.get("text") or "")
        if section_id == "practical_fixes":
            repaired_text = format_practical_fixes_text(text)
        elif section_id == "action_plan":
            repaired_text = format_action_plan_text(text)
        else:
            repaired_text = text
        if repaired_text and repaired_text != text:
            section["text"] = repaired_text
            changed = True
        repaired_sections.append(section)

    if not changed:
        return payload, False

    repaired_payload = dict(payload)
    repaired_payload["sections"] = repaired_sections
    repaired_payload["full_text"] = "\n\n".join(
        str(section.get("text") or "")
        for section in repaired_sections
        if isinstance(section, dict) and section.get("text")
    )
    return repaired_payload, True


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
