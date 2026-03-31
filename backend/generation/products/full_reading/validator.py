from __future__ import annotations

import re
from collections import Counter

_STUB_PATTERN = re.compile(r'^\s*(?:\d+[.):-]?|[-*])\s*$')
_DANGLING_LIST_PATTERN = re.compile(r'(?:steps?|guidance|next steps?|next move)\s*:\s*1\.?\s*$', re.IGNORECASE)
_TRUNCATED_ENDING_PATTERN = re.compile(r'(?:[:;,-]|\b(?:and|or|to|with|consider|including|like|such as|for example)\s*)$', re.IGNORECASE)
_WORD_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "if", "in", "into", "is", "it", "its",
    "of", "on", "or", "so", "than", "that", "the", "their", "there", "this", "to", "up", "with", "you", "your",
}


def _text_for(sections: list[dict], *ids: str) -> str:
    for section in sections:
        if section.get('id') in ids:
            return str(section.get('text', '') or '').strip()
    return ''


def _looks_stubbed(text: str) -> bool:
    return (
        not text
        or _STUB_PATTERN.match(text) is not None
        or _DANGLING_LIST_PATTERN.search(text) is not None
        or _TRUNCATED_ENDING_PATTERN.search(text) is not None
    )


def _normalize_for_compare(text: str) -> str:
    return re.sub(r'\W+', ' ', text.lower()).strip()


def _content_tokens(text: str) -> list[str]:
    return [token for token in _WORD_RE.findall((text or '').casefold()) if token not in _STOPWORDS]


def _leading_stem(text: str, size: int = 5) -> str:
    tokens = _content_tokens(text)
    return ' '.join(tokens[:size])


def _first_sentence(text: str) -> str:
    parts = re.split(r'(?<=[.!?])\s+', text.strip(), maxsplit=1)
    return parts[0].strip() if parts else ''


def _heading_restate_issue(section_id: str, text: str) -> str | None:
    pieces = [piece.strip() for piece in re.split(r'[\n:—-]+', text, maxsplit=1) if piece.strip()]
    if len(pieces) < 2:
        return None
    head, body = pieces[0], pieces[1]
    normalized_head = _normalize_for_compare(head)
    normalized_body = _normalize_for_compare(body)
    if normalized_head and normalized_head == normalized_body:
        return f'full_reading_heading_body_repetition:{section_id}'
    if normalized_head and (normalized_body.startswith(normalized_head) or normalized_head.startswith(normalized_body)):
        return f'full_reading_heading_body_repetition:{section_id}'
    head_tokens = set(_content_tokens(head))
    body_tokens = set(_content_tokens(body))
    if head_tokens and len(head_tokens & body_tokens) >= max(2, len(head_tokens)):
        return f'full_reading_heading_body_repetition:{section_id}'
    return None


def validate_full_reading_payload(payload: dict) -> list[str]:
    sections = payload.get('sections', [])
    issues: list[str] = []

    asking = _text_for(sections, 'what_this_is_asking_of_you')
    next_move = _text_for(sections, 'your_next_move')
    legacy_guidance = _text_for(sections, 'practical_guidance', 'reflective_guidance')

    if not asking and not next_move and legacy_guidance:
        cleaned = legacy_guidance.strip()
        if not cleaned:
            issues.append('full_reading_missing_payoff')
        elif _looks_stubbed(cleaned) or len(cleaned) < 60:
            issues.append('full_reading_stub_guidance')
        return issues

    if not asking:
        issues.append('full_reading_missing_asking_section')
    if not next_move:
        issues.append('full_reading_missing_next_move_section')

    if asking:
        if _looks_stubbed(asking):
            issues.append('full_reading_stub_asking_section')
        elif len(asking) < 60:
            issues.append('full_reading_vague_asking_section')

    if next_move:
        if _looks_stubbed(next_move):
            issues.append('full_reading_stub_next_move_section')
        elif len(next_move) < 60:
            issues.append('full_reading_vague_next_move_section')

    if asking and next_move:
        normalized_asking = _normalize_for_compare(asking)
        normalized_next_move = _normalize_for_compare(next_move)
        if normalized_asking == normalized_next_move:
            issues.append('full_reading_duplicate_payoff_sections')
        elif normalized_asking and normalized_asking in normalized_next_move:
            issues.append('full_reading_overlapping_payoff_sections')
        elif normalized_next_move and normalized_next_move in normalized_asking:
            issues.append('full_reading_overlapping_payoff_sections')

    first_sentences = {}
    stems = []
    for section in sections:
        section_id = str(section.get('id', ''))
        section_text = str(section.get('text', '') or '').strip()
        if not section_text:
            continue
        first_sentence = _normalize_for_compare(_first_sentence(section_text))
        if first_sentence:
            if first_sentence in first_sentences and first_sentences[first_sentence] != section_id:
                issues.append(f"full_reading_repeated_opening_line:{first_sentences[first_sentence]}:{section_id}")
            else:
                first_sentences[first_sentence] = section_id
        stem = _leading_stem(section_text)
        if stem:
            stems.append(stem)
        heading_issue = _heading_restate_issue(section_id, section_text)
        if heading_issue:
            issues.append(heading_issue)

    issues.extend(
        f'full_reading_repeated_section_stem:{stem}'
        for stem, count in Counter(stems).items()
        if count >= 2
    )

    return issues
