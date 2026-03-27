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


def validate_feng_shui_payload(payload: dict) -> list[str]:
    text = "\n".join(section.get("text", "") for section in payload.get("sections", []))
    lowered = text.casefold()
    issues: list[str] = []
    if not any(marker in lowered for marker in SPACE_MARKERS):
        issues.append("feng_shui_missing_space_analysis_language")
    if not any(marker in lowered for marker in ACTION_MARKERS):
        issues.append("feng_shui_missing_recommendation_language")
    if any(marker in lowered for marker in DRIFT_MARKERS):
        issues.append("feng_shui_generic_reading_drift")
    return issues
