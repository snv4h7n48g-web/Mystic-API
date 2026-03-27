from __future__ import annotations

CARD_MARKERS = [
    "the fool", "the magician", "the high priestess", "the empress", "the emperor",
    "the hierophant", "the lovers", "the chariot", "strength", "the hermit",
    "wheel of fortune", "justice", "the hanged man", "death", "temperance",
    "the devil", "the tower", "the star", "the moon", "the sun", "judgement",
    "the world", "ace of", "two of", "three of", "four of", "five of", "six of",
    "seven of", "eight of", "nine of", "ten of", "page of", "knight of", "queen of", "king of",
]
SYMBOLIC_MARKERS = ["card", "cards", "spread", "symbol", "symbolism", "arcana", "position"]


def validate_tarot_payload(payload: dict) -> list[str]:
    sections = payload.get("sections", [])
    issues: list[str] = []
    narrative = next((section.get("text", "") for section in sections if section.get("id") == "tarot_narrative"), "")
    if not narrative.strip():
        issues.append("tarot_missing_narrative_section")
        return issues
    lowered = narrative.casefold()
    if not any(marker in lowered for marker in CARD_MARKERS):
        issues.append("tarot_missing_card_specific_language")
    if not any(marker in lowered for marker in SYMBOLIC_MARKERS):
        issues.append("tarot_missing_symbolic_structure")
    return issues
