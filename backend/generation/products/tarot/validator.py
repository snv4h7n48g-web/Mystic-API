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
            headline = str(section.get("headline") or section.get("text", "") or "").strip()
            detail = str(section.get("detail") or "").strip()
            if headline and detail and headline.casefold() != detail.casefold() and not detail.casefold().startswith(headline.casefold()):
                return f"{headline} {detail}".strip()
            return detail or headline
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
    interpretation_hits = sum(1 for marker in ['suggests', 'reveals', 'asks', 'warns', 'shows', 'showing', 'points', 'because', 'together', 'while', 'whereas', 'contributes', 'interaction', 'tension'] if marker in lowered)
    sentences = _sentence_count(text)
    unique_sentences = {part.strip().casefold() for part in re.split(r'(?<=[.!?])\s+', (text or '').strip()) if part.strip()}
    if len(unique_sentences) < max(2, sentences):
        return False
    if card_hits >= 2 and position_hits >= 2 and interpretation_hits >= 3 and sentences >= 3 and _word_count(text) >= 35:
        return True
    if card_hits >= 2 and position_hits >= 2 and interpretation_hits >= 2 and _word_count(text) >= 24 and sentences >= 2:
        return True
    return card_hits >= 1 and position_hits >= 2 and interpretation_hits >= 1 and _word_count(text) >= 18 and sentences >= 2


def _has_structural_duplication(text: str) -> bool:
    sentences = [part.strip().casefold() for part in re.split(r'(?<=[.!?])\s+', (text or '').strip()) if part.strip()]
    if len(sentences) < 2:
        return False
    seen: set[str] = set()
    stems: set[str] = set()
    for sentence in sentences:
        normalized = re.sub(r'\W+', ' ', sentence).strip()
        if not normalized:
            continue
        stem = ' '.join(_content_tokens(sentence)[:6])
        if normalized in seen or (stem and stem in stems):
            return True
        seen.add(normalized)
        if stem:
            stems.add(stem)
    return False


def validate_tarot_payload(payload: dict) -> list[str]:
    sections = payload.get("sections", [])
    issues: list[str] = []
    opening = _text_for(sections, "opening_invocation", "spread_overview")
    card_sections = [
        section
        for section in sections
        if str(section.get("id") or "").startswith("card_")
    ]
    card_chapter_text = " ".join(
        _text_for([section], str(section.get("id") or ""))
        for section in card_sections
    ).strip()
    narrative = _text_for(sections, "tarot_narrative") or card_chapter_text
    synthesis = _text_for(sections, "spread_story", "integrated_synthesis", "current_pattern")
    guidance = _text_for(sections, "reflective_guidance", "practical_guidance")

    if not narrative.strip():
        issues.append("tarot_missing_narrative_section")
        return issues

    if not guidance.strip():
        issues.append("tarot_missing_guidance_section")

    lowered = narrative.casefold()
    card_hits = sum(1 for marker in CARD_MARKERS if marker in lowered)
    structure_hits = sum(1 for marker in SYMBOLIC_MARKERS if marker in lowered)

    if card_sections:
        if not _text_for(sections, "spread_overview").strip():
            issues.append("tarot_missing_spread_overview")
        if not _text_for(sections, "spread_story").strip():
            issues.append("tarot_missing_spread_story")
        for section in card_sections:
            section_id = str(section.get("id") or "")
            card_text = _text_for([section], section_id)
            lowered_card = card_text.casefold()
            if _word_count(card_text) < 35:
                issues.append(f"tarot_card_chapter_too_shallow:{section_id}")
            if not any(marker in lowered_card for marker in ["position", "past", "present", "guidance", "card role", "spread"]):
                issues.append(f"tarot_card_chapter_missing_position_logic:{section_id}")
            if not any(marker in lowered_card for marker in ["upright", "reversed", "orientation", "blocked", "clearer expression"]):
                issues.append(f"tarot_card_chapter_missing_orientation_logic:{section_id}")
            if not any(marker in lowered_card for marker in ["question", "you", "your"]):
                issues.append(f"tarot_card_chapter_missing_question_link:{section_id}")
        if synthesis and _is_too_similar(card_chapter_text, synthesis):
            issues.append("tarot_card_story_repetition")

    if not any(marker in lowered for marker in CARD_MARKERS):
        issues.append("tarot_missing_card_specific_language")
    if not any(marker in lowered for marker in SYMBOLIC_MARKERS):
        issues.append("tarot_missing_symbolic_structure")
    if _word_count(narrative) < 18:
        issues.append("tarot_narrative_too_shallow")
    if card_hits < 2 and structure_hits < 2:
        issues.append("tarot_narrative_under_grounded")
    if not _has_card_level_depth(narrative):
        issues.append("tarot_narrative_missing_card_contribution_depth")
    if any(marker in guidance.casefold() for marker in _GENERIC_FILLER_MARKERS):
        issues.append("tarot_guidance_generic_filler")
    if guidance and _word_count(guidance) < 12:
        issues.append("tarot_guidance_too_shallow")
    if guidance and not _has_actionable_guidance(guidance):
        issues.append("tarot_guidance_missing_action")
    if _has_structural_duplication(narrative):
        issues.append("tarot_narrative_internal_duplication")
    if opening and _is_too_similar(opening, narrative):
        issues.append("tarot_opening_narrative_repetition")
    if synthesis and _is_too_similar(narrative, synthesis):
        issues.append("tarot_narrative_synthesis_repetition")
    if guidance and synthesis and _is_too_similar(guidance, synthesis):
        issues.append("tarot_guidance_synthesis_repetition")
    return issues
