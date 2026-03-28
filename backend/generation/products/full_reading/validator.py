from __future__ import annotations

import re

_STUB_PATTERN = re.compile(r'^\s*(?:\d+[.):-]?|[-*])\s*$')
_DANGLING_LIST_PATTERN = re.compile(r'(?:steps?|guidance|next steps?|next move)\s*:\s*1\.?\s*$', re.IGNORECASE)
_TRUNCATED_ENDING_PATTERN = re.compile(r'(?:[:;,-]|\b(?:and|or|to|with|consider|including|like|such as|for example)\s*)$', re.IGNORECASE)


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

    return issues
