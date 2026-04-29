from __future__ import annotations

import re

from .mapper import map_tarot_reading
from ..full_reading.formatter import (
    _build_tarot_story,
    _dedupe_sentences,
    _enrich_tarot_cards,
    _tarot_cards,
    _tarot_cards_summary,
    _tarot_reference_meaning,
    _tarot_role_hint,
)


def _clean(text: str | None) -> str:
    return ' '.join((text or '').split()).strip()


_WORD_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by', 'for', 'from', 'if', 'in', 'into', 'is', 'it', 'its',
    'of', 'on', 'or', 'so', 'than', 'that', 'the', 'their', 'there', 'these', 'this', 'to', 'up', 'with', 'you', 'your',
}


def _content_tokens(text: str) -> set[str]:
    return {
        token
        for token in _WORD_RE.findall(_clean(text).casefold())
        if token not in _STOPWORDS
    }


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(_clean(text)))


def _too_similar(a: str, b: str) -> bool:
    tokens_a = _content_tokens(a)
    tokens_b = _content_tokens(b)
    if not tokens_a or not tokens_b:
        return False
    shortest = min(len(tokens_a), len(tokens_b))
    overlap = len(tokens_a & tokens_b)
    return overlap >= max(5, int(shortest * 0.75))


def _split_layered_text(text: str, fallback_headline: str) -> tuple[str, str]:
    cleaned = _clean(text)
    if not cleaned:
        return fallback_headline, ''
    head, _, tail = cleaned.partition('. ')
    headline = f'{head}.' if tail and not head.endswith(('.', '!', '?')) else head
    detail = tail.strip() if tail else ''
    if not detail or detail.casefold() == headline.casefold():
        return headline or fallback_headline, cleaned
    return headline or fallback_headline, detail


def _build_section(section_id: str, title: str, text: str, fallback_headline: str) -> dict:
    headline, detail = _split_layered_text(text, fallback_headline)
    return {
        'id': section_id,
        'title': title,
        'text': headline or detail,
        'headline': headline,
        'detail': detail or headline,
        'default_expanded': bool(detail),
    }


def _join_paragraphs(*parts: str) -> str:
    paragraphs: list[str] = []
    for part in parts:
        cleaned = _dedupe_sentences(_clean(part))
        if not cleaned:
            continue
        if any(_too_similar(cleaned, existing) for existing in paragraphs):
            continue
        paragraphs.append(cleaned)
    return '\n\n'.join(paragraphs).strip()


def _orientation_label(orientation: str) -> str:
    return 'Reversed' if _clean(orientation).casefold() == 'reversed' else 'Upright'


def _chapter_for_card(chapters: list[dict[str, str]], *, index: int, card: dict) -> dict[str, str]:
    if index < len(chapters):
        candidate = chapters[index]
        if not candidate.get('card') or candidate.get('card', '').casefold() == card.get('card', '').casefold():
            return candidate

    card_name = _clean(card.get('card')).casefold()
    for candidate in chapters:
        if _clean(candidate.get('card')).casefold() == card_name:
            return candidate
    return {}


def _card_chapter_text(card: dict, chapter: dict[str, str], *, index: int) -> tuple[str, str]:
    card_name = _clean(card.get('card')) or _clean(chapter.get('card')) or f'Card {index + 1}'
    position = _clean(card.get('position') or chapter.get('position'))
    orientation = _clean(card.get('orientation') or chapter.get('orientation') or 'upright').lower()
    orientation_label = _orientation_label(orientation)
    card_label = f'{card_name} reversed' if orientation == 'reversed' else card_name
    position_label = f' in the {position} position' if position else ''

    card_meaning = _clean(chapter.get('card_meaning')) or _clean(card.get('interpretation')) or _tarot_reference_meaning(card)
    position_meaning = _clean(chapter.get('position_meaning')) or f'Here, the card is working as {_tarot_role_hint(position, index)}.'
    reversal_message = _clean(chapter.get('reversal_message'))
    if not reversal_message and orientation == 'reversed':
        reversal_message = f'Because it is reversed, {card_name} is less about clean expression and more about where the pattern is blocked, delayed, or being overcorrected.'
    elif not reversal_message:
        reversal_message = f'Because it is upright, {card_name} can be read through its clearer expression rather than its blocked or distorted edge.'
    question_relevance = _clean(chapter.get('question_relevance')) or _clean(card.get('question_link'))
    personal_implication = _clean(chapter.get('personal_implication'))

    headline = f'{card_label}{position_label}: {card_meaning}'
    body = _join_paragraphs(
        position_meaning,
        reversal_message,
        f'For your question, this matters because {question_relevance.rstrip(".")}.' if question_relevance else '',
        personal_implication,
    )
    return headline, body


def _build_spread_overview(*, mapped: dict, tarot_payload: dict | None, tarot_cards: list[dict], normalized) -> dict:
    spread = _clean((tarot_payload or {}).get('spread')) or ('3-card spread' if len(tarot_cards) >= 3 else 'tarot draw')
    card_summary = _tarot_cards_summary(tarot_payload)
    overview = _join_paragraphs(
        _clean(getattr(normalized, 'tarot_spread_overview', '')),
        mapped['opening_invocation'],
        f'The spread in view is {spread}: {card_summary}.' if card_summary else '',
    )
    return _build_section(
        'spread_overview',
        'SPREAD OVERVIEW',
        overview,
        'The spread opens the question before the individual cards speak.',
    )


def _build_card_sections(*, normalized, tarot_cards: list[dict]) -> list[dict]:
    chapters = getattr(normalized, 'tarot_card_chapters', []) or []
    sections: list[dict] = []
    for index, card in enumerate(tarot_cards):
        chapter = _chapter_for_card(chapters, index=index, card=card)
        headline, detail = _card_chapter_text(card, chapter, index=index)
        section = _build_section(
            f'card_{index + 1}',
            f'CARD {index + 1}',
            _join_paragraphs(headline, detail),
            headline,
        )
        section['headline'] = headline
        section['detail'] = detail or headline
        section['evidence'] = {
            'items': [
                item
                for item in [
                    _clean(card.get('position')),
                    _orientation_label(_clean(card.get('orientation') or 'upright')),
                ]
                if item
            ],
            'tarot': {
                'spread': '',
                'combined_interpretation': '',
                'cards': [card],
            },
        }
        sections.append(section)
    return sections


def _build_spread_story(*, mapped: dict, normalized, tarot_cards: list[dict], tarot_payload: dict | None, question: str | None) -> dict:
    model_story = _clean(getattr(normalized, 'tarot_spread_story', ''))
    deterministic_story = _build_tarot_story(tarot_cards, _clean((tarot_payload or {}).get('spread')), question)
    needs_fallback = _word_count(model_story) < 35
    story = _join_paragraphs(
        model_story,
        mapped['integrated_synthesis'],
        deterministic_story if needs_fallback else '',
    )
    return _build_section(
        'spread_story',
        'SPREAD STORY',
        story,
        'The cards now gather into one story.',
    )


def build_tarot_reading_payload(*, normalized, metadata, tarot_payload=None, question: str | None = None):
    mapped = map_tarot_reading(normalized)
    tarot_payload = tarot_payload or {}
    tarot_cards = _enrich_tarot_cards(_tarot_cards(tarot_payload), question)
    if tarot_cards:
        sections = [
            _build_spread_overview(
                mapped=mapped,
                tarot_payload=tarot_payload,
                tarot_cards=tarot_cards,
                normalized=normalized,
            ),
            *_build_card_sections(normalized=normalized, tarot_cards=tarot_cards),
            _build_spread_story(
                mapped=mapped,
                normalized=normalized,
                tarot_cards=tarot_cards,
                tarot_payload=tarot_payload,
                question=question,
            ),
            _build_section('reflective_guidance', 'GUIDANCE', mapped['reflective_guidance'], 'The reading now asks for a grounded next step.'),
        ]
        if mapped['closing_prompt']:
            sections.append(_build_section('closing_prompt', 'CLOSING', mapped['closing_prompt'], 'Return when the pattern has moved.'))
    else:
        sections = [
            _build_section('opening_invocation', 'OPENING', mapped['opening_invocation'], 'The cards open on a clear threshold.'),
            _build_section('tarot_narrative', 'TAROT NARRATIVE', mapped['tarot_narrative'], 'The spread is asking to be read card by card.'),
            _build_section('integrated_synthesis', 'SYNTHESIS', mapped['integrated_synthesis'], 'The card pattern points to one shared theme.'),
            _build_section('reflective_guidance', 'GUIDANCE', mapped['reflective_guidance'], 'The reading now asks for a grounded next step.'),
            _build_section('closing_prompt', 'CLOSING', mapped['closing_prompt'], 'Return when the pattern has moved.'),
        ]
    sections = [section for section in sections if section['text'] and section['text'].strip()]
    spread_story_section = next((section for section in sections if section.get('id') == 'spread_story'), None)
    spread_story = (
        _join_paragraphs(
            spread_story_section.get('headline', ''),
            spread_story_section.get('detail') or spread_story_section.get('text', ''),
        )
        if spread_story_section
        else ''
    )
    return {
        'sections': sections,
        'full_text': '\n\n'.join(_join_paragraphs(section.get('headline', ''), section.get('detail', '')) for section in sections),
        'metadata': {
            'persona_id': metadata.persona_id,
            'llm_profile_id': metadata.llm_profile_id,
            'prompt_version': metadata.prompt_version,
            'theme_tags': metadata.theme_tags,
            'headline': metadata.headline,
            'model': metadata.model_id,
            'flow_type': 'tarot_solo',
            'evidence': {
                'tarot_cards': _tarot_cards_summary(tarot_payload),
                'tarot': {
                    'spread': _clean(tarot_payload.get('spread')) or ('3-card spread' if len(tarot_cards) >= 3 else 'tarot draw'),
                    'combined_interpretation': spread_story,
                    'cards': tarot_cards,
                },
            },
        },
    }
