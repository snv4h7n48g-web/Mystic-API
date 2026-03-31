from __future__ import annotations

import re
from collections import Counter

_STUB_PATTERN = re.compile(r'^\s*(?:\d+[.):-]?|[-*])\s*$')
_DANGLING_LIST_PATTERN = re.compile(r'(?:steps?|guidance|next steps?|next move)\s*:\s*1\.?\s*$', re.IGNORECASE)
_TRUNCATED_ENDING_PATTERN = re.compile(r'(?:[:;,-]|\b(?:and|or|to|with|consider|including|like|such as|for example)\s*)$', re.IGNORECASE)
_WORD_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by', 'for', 'from', 'if', 'in', 'into', 'is', 'it', 'its',
    'of', 'on', 'or', 'so', 'than', 'that', 'the', 'their', 'there', 'these', 'this', 'to', 'up', 'with', 'you', 'your',
}
_CARD_MARKERS = [
    'the fool', 'the magician', 'the high priestess', 'the empress', 'the emperor', 'the hierophant', 'the lovers',
    'the chariot', 'strength', 'the hermit', 'wheel of fortune', 'justice', 'the hanged man', 'death', 'temperance',
    'the devil', 'the tower', 'the star', 'the moon', 'the sun', 'judgement', 'the world', 'ace of', 'two of',
    'three of', 'four of', 'five of', 'six of', 'seven of', 'eight of', 'nine of', 'ten of', 'page of', 'knight of',
    'queen of', 'king of',
]
_PALM_MARKERS = ['palm', 'life line', 'heart line', 'head line', 'fate line', 'mount', 'thumb', 'finger', 'hand shape', 'texture']
_TAROT_STRUCTURE_MARKERS = ['card', 'cards', 'spread', 'position', 'together', 'interaction', 'interact']


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


def validate_full_reading_payload(payload: dict) -> list[str]:
    sections = payload.get('sections', [])
    issues: list[str] = []
    metadata = payload.get('metadata') if isinstance(payload.get('metadata'), dict) else {}
    snapshot = payload.get('snapshot') if isinstance(payload.get('snapshot'), dict) else {}
    include_palm = metadata.get('includes_palm') is True or (metadata.get('modalities') or {}).get('includes_palm') is True

    asking = _text_for(sections, 'what_this_is_asking_of_you')
    next_move = _text_for(sections, 'your_next_move')
    legacy_guidance = _text_for(sections, 'practical_guidance', 'reflective_guidance')
    opening = _text_for(sections, 'reading_opening', 'opening_hook', 'opening_invocation')
    palm = _text_for(sections, 'palm_revelation', 'palm_insight')
    tarot = _text_for(sections, 'tarot_message', 'tarot_narrative')
    synthesis = _text_for(sections, 'signals_agree', 'integrated_synthesis', 'current_pattern')

    if not asking and not next_move and legacy_guidance:
        cleaned = legacy_guidance.strip()
        if not cleaned:
            issues.append('full_reading_missing_payoff')
        elif _looks_stubbed(cleaned) or len(cleaned) < 60:
            issues.append('full_reading_stub_guidance')
        return issues

    if not opening:
        issues.append('full_reading_missing_opening')
    if include_palm and not palm:
        issues.append('full_reading_missing_palm_section')
    if not tarot:
        issues.append('full_reading_missing_tarot_section')
    if not synthesis:
        issues.append('full_reading_missing_synthesis_section')
    if not asking:
        issues.append('full_reading_missing_asking_section')
    if not next_move:
        issues.append('full_reading_missing_next_move_section')

    for section_id, text in {
        'reading_opening': opening,
        'palm_revelation': palm,
        'tarot_message': tarot,
        'signals_agree': synthesis,
        'what_this_is_asking_of_you': asking,
        'your_next_move': next_move,
    }.items():
        if text and _looks_stubbed(text):
            issues.append(f'full_reading_stub_section:{section_id}')

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

    if include_palm and palm:
        lowered = palm.casefold()
        if not any(marker in lowered for marker in _PALM_MARKERS):
            issues.append('full_reading_palm_section_missing_feature_evidence')

    if tarot:
        lowered = tarot.casefold()
        if not any(marker in lowered for marker in _CARD_MARKERS):
            issues.append('full_reading_tarot_missing_card_specific_language')
        if not any(marker in lowered for marker in _TAROT_STRUCTURE_MARKERS):
            issues.append('full_reading_tarot_missing_spread_interpretation')
        if _is_too_similar(tarot, synthesis):
            issues.append('full_reading_tarot_synthesis_repetition')

    if palm and synthesis and _is_too_similar(palm, synthesis):
        issues.append('full_reading_palm_synthesis_repetition')
    if opening and synthesis and _is_too_similar(opening, synthesis):
        issues.append('full_reading_opening_synthesis_repetition')

    snapshot_values = [
        str(snapshot.get('core_theme', '') or '').strip(),
        str(snapshot.get('main_tension', '') or '').strip(),
        str(snapshot.get('best_next_move', '') or '').strip(),
    ]
    if any(snapshot_values):
        if not all(snapshot_values):
            issues.append('full_reading_incomplete_snapshot')
        body_sections = [text for text in [opening, palm, tarot, synthesis, asking, next_move] if text]
        for key, value in [('core_theme', snapshot_values[0]), ('main_tension', snapshot_values[1]), ('best_next_move', snapshot_values[2])]:
            if not value:
                continue
            if len(value) > 220:
                issues.append(f'full_reading_snapshot_too_long:{key}')
            if any(_is_too_similar(value, body) for body in body_sections):
                issues.append(f'full_reading_snapshot_body_repetition:{key}')

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
                issues.append(f'full_reading_repeated_opening_line:{first_sentences[first_sentence]}:{section_id}')
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
