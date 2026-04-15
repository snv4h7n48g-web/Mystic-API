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
DRIFT_MARKERS = ["your heart", "your soul", "tarot", "birth chart", "spread"]
EXPECTED_SECTION_IDS = {
    "overview",
    "bagua_map",
    "energy_flow",
    "priority_actions",
    "recommendations",
    "guidance",
}
GENERIC_SECTION_IDS = {
    "opening_hook",
    "current_pattern",
    "emotional_truth",
    "practical_guidance",
    "next_return_invitation",
    "continuity_callback",
}


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
    priority_section = next((section for section in sections if section.get("id") == "priority_actions"), None)
    recommendations_section = next((section for section in sections if section.get("id") == "recommendations"), None)
    if not priority_section or not str(priority_section.get("text") or "").strip():
        issues.append("feng_shui_missing_priority_actions")
    if not recommendations_section or not str(recommendations_section.get("text") or "").strip():
        issues.append("feng_shui_missing_recommendations")
    return issues
