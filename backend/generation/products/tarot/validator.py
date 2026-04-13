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
ACTION_MARKERS = [
    "choose", "send", "ask", "name", "make", "begin", "start", "stop", "schedule", "say", "write", "set", "clear",
    "take", "pause", "notice", "commit", "decline", "reach out", "protect",
]
_GENERIC_FILLER_MARKERS = [
    "trust the universe",
    "the universe has your back",
    "everything happens for a reason",
    "your soul knows",
    "align with your highest self",
    "divine timing",
]
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


def _word_count(text: str) -> int:
    return len(_content_tokens(text))


def _sentence_count(text: str) -> int:
    parts = [part.strip() for part in re.split(r'(?<=[.!?])\s+', (text or '').strip()) if part.strip()]
    return len(parts)


def _has_actionable_guidance(text: str) -> bool:
    lowered = (text or '').casefold()
    if any(marker in lowered for marker in ACTION_MARKERS):
        return True
    return bool(re.search(r'\b(?:try|let|keep|notice|consider|avoid|protect|write|name|ask|choose|take)\b', lowered))


def _has_card_level_depth(text: str) -> bool:
    lowered = (text or '').casefold()
    card_hits = sum(1 for marker in CARD_MARKERS if marker in lowered)
    position_hits = sum(1 for marker in SYMBOLIC_MARKERS if marker in lowered)
    interpretation_hits = sum(1 for marker in ['suggests', 'reveals', 'asks', 'warns', 'shows', 'showing', 'points', 'because', 'together', 'while', 'whereas'] if marker in lowered)
    sentences = _sentence_count(text)
    if card_hits >= 2 and position_hits >= 2 and interpretation_hits >= 3 and sentences >= 3:
        return True
    return card_hits >= 1 and position_hits >= 2 and interpretation_hits >= 1 and _word_count(text) >= 12 and sentences >= 1


def validate_tarot_payload(payload: dict) -> list[str]:
    sections = payload.get("sections", [])
    issues: list[str] = []
    opening = _text_for(sections, "opening_invocation")
    narrative = _text_for(sections, "tarot_narrative")
    synthesis = _text_for(sections, "integrated_synthesis", "current_pattern")
    guidance = _text_for(sections, "reflective_guidance", "practical_guidance")

    if not narrative.strip():
        issues.append("tarot_missing_narrative_section")
        return issues

    if not guidance.strip():
        issues.append("tarot_missing_guidance_section")

    lowered = narrative.casefold()
    card_hits = sum(1 for marker in CARD_MARKERS if marker in lowered)
    structure_hits = sum(1 for marker in SYMBOLIC_MARKERS if marker in lowered)

    if not any(marker in lowered for marker in CARD_MARKERS):
        issues.append("tarot_missing_card_specific_language")
    if not any(marker in lowered for marker in SYMBOLIC_MARKERS):
        issues.append("tarot_missing_symbolic_structure")
    if _word_count(narrative) < 12:
        issues.append("tarot_narrative_too_shallow")
    if card_hits < 2 and structure_hits < 2:
        issues.append("tarot_narrative_under_grounded")
    if not _has_card_level_depth(narrative):
        issues.append("tarot_narrative_missing_card_contribution_depth")
    if any(marker in guidance.casefold() for marker in _GENERIC_FILLER_MARKERS):
        issues.append("tarot_guidance_generic_filler")
    if guidance and _word_count(guidance) < 10:
        issues.append("tarot_guidance_too_shallow")
    if guidance and not _has_actionable_guidance(guidance):
        issues.append("tarot_guidance_missing_action")
    if opening and _is_too_similar(opening, narrative):
        issues.append("tarot_opening_narrative_repetition")
    if synthesis and _is_too_similar(narrative, synthesis):
        issues.append("tarot_narrative_synthesis_repetition")
    if guidance and synthesis and _is_too_similar(guidance, synthesis):
        issues.append("tarot_guidance_synthesis_repetition")
    return issues
