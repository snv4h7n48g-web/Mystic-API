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
INTERPRETIVE_MARKERS = ["suggests", "points to", "reveals", "shows that", "means", "speaks to", "indicates", "because"]
LITERALISM_MARKERS = ["visible", "appears", "is long", "is short", "is deep", "is curved", "detected", "photo", "image", "ocr"]


def validate_palm_payload(payload: dict) -> list[str]:
    text = "\n".join(str(section.get("detail") or section.get("text", "")) for section in payload.get("sections", []))
    lowered = text.casefold()
    issues: list[str] = []
    if not any(marker in lowered for marker in PALM_MARKERS):
        issues.append("palm_missing_feature_led_language")
    if any(marker in lowered for marker in DRIFT_MARKERS):
        issues.append("palm_generic_divination_drift")
    if not any(marker in lowered for marker in INTERPRETIVE_MARKERS):
        issues.append("palm_missing_interpretive_meaning")
    literal_hits = sum(1 for marker in LITERALISM_MARKERS if marker in lowered)
    if literal_hits >= 3 and not any(marker in lowered for marker in INTERPRETIVE_MARKERS):
        issues.append("palm_overly_literal_supporting_detail")
    return issues
