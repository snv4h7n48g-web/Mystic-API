from __future__ import annotations

from .mapper import map_tarot_reading


def _clean(text: str | None) -> str:
    return ' '.join((text or '').split()).strip()


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


def build_tarot_reading_payload(*, normalized, metadata):
    mapped = map_tarot_reading(normalized)
    sections = [
        _build_section('opening_invocation', 'OPENING', mapped['opening_invocation'], 'The cards open on a clear threshold.'),
        _build_section('tarot_narrative', 'TAROT NARRATIVE', mapped['tarot_narrative'], 'The spread is asking to be read card by card.'),
        _build_section('integrated_synthesis', 'SYNTHESIS', mapped['integrated_synthesis'], 'The card pattern points to one shared theme.'),
        _build_section('reflective_guidance', 'GUIDANCE', mapped['reflective_guidance'], 'The reading now asks for a grounded next step.'),
        _build_section('closing_prompt', 'CLOSING', mapped['closing_prompt'], 'Return when the pattern has moved.'),
    ]
    sections = [section for section in sections if section['text'] and section['text'].strip()]
    return {
        'sections': sections,
        'full_text': '\n\n'.join(section['text'] for section in sections),
        'metadata': {
            'persona_id': metadata.persona_id,
            'llm_profile_id': metadata.llm_profile_id,
            'prompt_version': metadata.prompt_version,
            'theme_tags': metadata.theme_tags,
            'headline': metadata.headline,
            'model': metadata.model_id,
            'flow_type': 'tarot_solo',
        },
    }
