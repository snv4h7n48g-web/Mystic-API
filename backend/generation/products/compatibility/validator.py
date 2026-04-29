from __future__ import annotations

RELATIONAL_MARKERS = [
    "together",
    "between you",
    "between them",
    "each other",
    "you both",
    "you two",
    "relationship",
    "dynamic",
    "connection",
    "bond",
    "chemistry",
    "partnership",
    "magnetic pull",
    "spark",
]
TENSION_MARKERS = ["tension", "friction", "clash", "misread", "conflict", "trigger"]
STRENGTH_MARKERS = ["strength", "support", "ease", "harmony", "draw", "trust"]
PAIR_MARKERS = ["both", "each of you", "person one", "person two", "partner", "you two"]
SOLO_DRIFT_MARKERS = ["your personal journey", "your path alone", "just for you", "solo"]


def validate_compatibility_payload(payload: dict) -> list[str]:
    text = "\n".join(section.get("text", "") for section in payload.get("sections", []))
    lowered = text.casefold()
    issues: list[str] = []
    if not any(marker in lowered for marker in RELATIONAL_MARKERS):
        issues.append("compatibility_missing_relationship_framing")
    if not any(marker in lowered for marker in TENSION_MARKERS + STRENGTH_MARKERS):
        issues.append("compatibility_missing_strength_or_tension_language")
    if not any(marker in lowered for marker in PAIR_MARKERS):
        issues.append("compatibility_missing_two_person_structure")
    if any(marker in lowered for marker in SOLO_DRIFT_MARKERS):
        issues.append("compatibility_solo_reading_drift")
    return issues
