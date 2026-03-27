from __future__ import annotations

PALM_MARKERS = [
    "palm",
    "life line",
    "heart line",
    "head line",
    "fate line",
    "mount",
    "thumb",
    "finger",
    "hand shape",
    "palmistry",
    "line",
]
DRIFT_MARKERS = ["tarot", "zodiac forecast", "horoscope", "birth chart", "spread"]


def validate_palm_payload(payload: dict) -> list[str]:
    text = "\n".join(section.get("text", "") for section in payload.get("sections", []))
    lowered = text.casefold()
    issues: list[str] = []
    if not any(marker in lowered for marker in PALM_MARKERS):
        issues.append("palm_missing_feature_led_language")
    if any(marker in lowered for marker in DRIFT_MARKERS):
        issues.append("palm_generic_divination_drift")
    return issues
