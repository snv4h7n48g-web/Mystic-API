from __future__ import annotations

SPACE_MARKERS = [
    "room",
    "space",
    "entry",
    "bed",
    "desk",
    "door",
    "window",
    "layout",
    "placement",
    "corner",
    "flow",
    "clutter",
    "direction",
]
ACTION_MARKERS = ["move", "place", "clear", "adjust", "add", "remove", "shift", "keep"]
FIX_ACTION_MARKERS = [
    "move",
    "place",
    "clear",
    "adjust",
    "add",
    "remove",
    "shift",
    "open",
    "anchor",
    "soften",
    "relocate",
]
DRIFT_MARKERS = ["your heart", "your soul", "tarot", "birth chart", "spread"]
EXPECTED_SECTION_IDS = {
    "overview",
    "what_helps",
    "what_blocks",
    "practical_fixes",
    "action_plan",
}
GENERIC_SECTION_IDS = {
    "opening_hook",
    "current_pattern",
    "emotional_truth",
    "practical_guidance",
    "next_return_invitation",
    "continuity_callback",
}


def _word_count(text: str) -> int:
    return len([word for word in text.split() if word.strip()])


def _section_text(sections: list[dict], section_id: str) -> str:
    section = next((item for item in sections if item.get("id") == section_id), None)
    return str((section or {}).get("text") or "").strip()


def _action_marker_count(text: str) -> int:
    lowered = text.casefold()
    return sum(1 for marker in FIX_ACTION_MARKERS if marker in lowered)


def validate_feng_shui_payload(payload: dict) -> list[str]:
    sections = payload.get("sections", [])
    section_ids = {str(section.get("id") or "") for section in sections}
    text = "\n".join(section.get("text", "") for section in sections)
    lowered = text.casefold()
    issues: list[str] = []
    if not EXPECTED_SECTION_IDS.issubset(section_ids):
        issues.append("feng_shui_missing_product_sections")
    if section_ids & GENERIC_SECTION_IDS:
        issues.append("feng_shui_generic_section_ids_leaked")
    if not any(marker in lowered for marker in SPACE_MARKERS):
        issues.append("feng_shui_missing_space_analysis_language")
    if not any(marker in lowered for marker in ACTION_MARKERS):
        issues.append("feng_shui_missing_recommendation_language")
    if any(marker in lowered for marker in DRIFT_MARKERS):
        issues.append("feng_shui_generic_reading_drift")
    for section_id in EXPECTED_SECTION_IDS:
        text_value = _section_text(sections, section_id)
        if not text_value:
            issues.append(f"feng_shui_missing_section:{section_id}")
        elif _word_count(text_value) < 28:
            issues.append(f"feng_shui_shallow_section:{section_id}")
    practical_fixes = _section_text(sections, "practical_fixes")
    action_plan = _section_text(sections, "action_plan")
    if _action_marker_count(practical_fixes) < 3:
        issues.append("feng_shui_practical_fixes_not_actionable")
    if _word_count(action_plan) < 35:
        issues.append("feng_shui_action_plan_too_thin")
    return issues
