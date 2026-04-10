from __future__ import annotations

import re

CARD_MARKERS = [
    "the fool", "the magician", "the high priestess", "the empress", "the emperor",
    "the hierophant", "the lovers", "the chariot", "strength", "the hermit",
    "wheel of fortune", "justice", "the hanged man", "death", "temperance",
    "the devil", "the tower", "the star", "the moon", "the sun", "judgement",
    "the world", "ace of", "two of", "three of", "four of", "five of", "six of",
    "seven of", "eight of", "nine of", "ten of", "page of", "knight of", "queen of", "king of",
]
SYMBOLIC_MARKERS = ["card", "cards", "spread", "symbol", "symbolism", "arcana", "position"]
_WORD_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by', 'for', 'from', 'if', 'in', 'into', 'is', 'it', 'its',
    'of', 'on', 'or', 'so', 'than', 'that', 'the', 'their', 'there', 'these', 'this', 'to', 'up', 'with', 'you', 'your',
}


def _text_for(sections: list[dict], *ids: str) -> str:
    for section in sections:
        if section.get("id") in ids:
            return str(section.get("detail") or section.get("text", "") or "").strip()
    return ""



def _content_tokens(text: str) -> list[str]:
    return [token for token in _WORD_RE.findall((text or '').casefold()) if token not in _STOPWORDS]



def _is_too_similar(a: str, b: str) -> bool:
    tokens_a = _content_tokens(a)
    tokens_b = _content_tokens(b)
    if not tokens_a or not tokens_b:
        return False
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    overlap = len(set_a & set_b)
    shortest = min(len(set_a), len(set_b))
    if shortest == 0:
        return False
    return overlap >= max(4, int(shortest * 0.8))



def validate_tarot_payload(payload: dict) -> list[str]:
    sections = payload.get("sections", [])
    issues: list[str] = []
    opening = _text_for(sections, "opening_invocation")
    narrative = _text_for(sections, "tarot_narrative")
    guidance = _text_for(sections, "reflective_guidance", "practical_guidance")

    if not narrative.strip():
        issues.append("tarot_missing_narrative_section")
        return issues

    if not guidance.strip():
        issues.append("tarot_missing_guidance_section")

    lowered = narrative.casefold()
    if not any(marker in lowered for marker in CARD_MARKERS):
        issues.append("tarot_missing_card_specific_language")
    if not any(marker in lowered for marker in SYMBOLIC_MARKERS):
        issues.append("tarot_missing_symbolic_structure")
    if opening and _is_too_similar(opening, narrative):
        issues.append("tarot_opening_narrative_repetition")
    return issues
