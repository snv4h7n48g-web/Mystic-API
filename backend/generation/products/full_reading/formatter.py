from __future__ import annotations

import re
from datetime import datetime, timezone

from ...types import GenerationMetadata, NormalizedMysticOutput


_SENTENCE_SPLIT_PATTERN = re.compile(r'(?<=[.!?])\s+')
_NUMBERED_SPLIT_PATTERN = re.compile(r'\n\s*(?:2[.)-]|2:)\s*', re.IGNORECASE)
_LABEL_ASKING_PATTERN = re.compile(
    r'(?:^|\n)\s*(?:1[.)-]?\s*)?(?:what this is asking of you|what this asks of you|what it is asking of you)\s*:?\s*',
    re.IGNORECASE,
)
_INLINE_ASKING_PATTERN = re.compile(
    r'^\s*(?:1[.)-]?\s*)?(?:what this is asking of you|what this asks of you|what it is asking of you)\s*:?\s*',
    re.IGNORECASE,
)
_LABEL_NEXT_MOVE_PATTERN = re.compile(
    r'(?:^|\n|\s)(?:2[.)-]?\s*)?(?:your next move|next move)\s*:?\s*',
    re.IGNORECASE,
)


def _clean(text: str | None) -> str:
    return (text or '').strip()


def _split_legacy_guidance(guidance: str) -> tuple[str, str]:
    cleaned = _clean(guidance)
    if not cleaned:
        return '', ''

    asking_match = _LABEL_ASKING_PATTERN.search(cleaned)
    next_move_match = _LABEL_NEXT_MOVE_PATTERN.search(cleaned)
    if next_move_match:
        asking_source = cleaned[:next_move_match.start()].strip()
        asking = _INLINE_ASKING_PATTERN.sub('', asking_source).strip(' \n:-')
        next_move = cleaned[next_move_match.end():].strip(' \n:-')
        if asking and next_move:
            return asking, next_move

    if asking_match and next_move_match and next_move_match.start() > asking_match.end():
        asking = cleaned[asking_match.end():next_move_match.start()].strip(' \n:-')
        next_move = cleaned[next_move_match.end():].strip(' \n:-')
        if asking and next_move:
            return asking, next_move

    numbered_parts = _NUMBERED_SPLIT_PATTERN.split(cleaned, maxsplit=1)
    if len(numbered_parts) == 2:
        first = re.sub(r'^\s*(?:1[.)-]|1:)\s*', '', numbered_parts[0]).strip()
        second = numbered_parts[1].strip()
        if first and second:
            return first, second

    sentences = [segment.strip() for segment in _SENTENCE_SPLIT_PATTERN.split(cleaned) if segment.strip()]
    if len(sentences) >= 3:
        pivot = max(1, len(sentences) // 2)
        return ' '.join(sentences[:pivot]).strip(), ' '.join(sentences[pivot:]).strip()
    if len(sentences) == 2:
        return sentences[0], sentences[1]

    return cleaned, ''


def _tarot_cards(tarot_payload: dict | None) -> list[dict]:
    cards = tarot_payload.get('cards') if isinstance(tarot_payload, dict) else None
    parsed: list[dict] = []
    if not isinstance(cards, list):
        return parsed
    for card in cards:
        if not isinstance(card, dict):
            continue
        name = _clean(card.get('card'))
        position = _clean(card.get('position'))
        meaning = _clean(card.get('meaning') or card.get('interpretation') or card.get('summary'))
        if name:
            parsed.append({'card': name, 'position': position, 'interpretation': meaning})
    return parsed


def _tarot_cards_summary(tarot_payload: dict | None) -> str:
    labels = []
    for card in _tarot_cards(tarot_payload):
        name = card['card']
        position = card['position']
        labels.append(f"{name} ({position})" if position else name)
    return ', '.join(labels)


def _palm_signals(palm_features: list[dict] | None) -> list[dict]:
    summaries: list[dict] = []
    for feature in palm_features or []:
        if not isinstance(feature, dict):
            continue
        label = _clean(feature.get('label') or feature.get('feature') or feature.get('name') or feature.get('type'))
        value = _clean(feature.get('value') or feature.get('description') or feature.get('reading') or feature.get('summary'))
        relevance = _clean(feature.get('relevance') or feature.get('question_relevance') or feature.get('why_it_matters'))
        confidence = _clean(feature.get('confidence_label') or feature.get('confidence'))
        if label or value or relevance:
            summaries.append({
                'feature': label,
                'observation': value,
                'relevance': relevance,
                'confidence': confidence,
            })
    return summaries[:5]


def _palm_features_summary(palm_features: list[dict] | None) -> list[str]:
    summaries: list[str] = []
    for signal in _palm_signals(palm_features):
        parts = [
            signal.get('feature', ''),
            signal.get('observation', ''),
            f"confidence: {signal['confidence']}" if signal.get('confidence') else '',
        ]
        parts = [part for part in parts if part]
        if parts:
            summaries.append(' — '.join(parts))
    return summaries[:5]


def _first_sentence(text: str) -> str:
    cleaned = _clean(text)
    if not cleaned:
        return ''
    pieces = _SENTENCE_SPLIT_PATTERN.split(cleaned, maxsplit=1)
    return pieces[0].strip() if pieces else cleaned


def _remaining_sentences(text: str) -> str:
    cleaned = _clean(text)
    if not cleaned:
        return ''
    pieces = _SENTENCE_SPLIT_PATTERN.split(cleaned, maxsplit=1)
    if len(pieces) < 2:
        return cleaned
    return pieces[1].strip()


def _headline_and_detail(text: str, *, fallback_headline: str) -> tuple[str, str]:
    cleaned = _clean(text)
    if not cleaned:
        return fallback_headline, ''
    headline = _first_sentence(cleaned)
    detail = _remaining_sentences(cleaned)
    if not detail or detail.casefold() == headline.casefold():
        detail = cleaned
    if headline.casefold() == detail.casefold() and len(cleaned) > 140:
        headline = cleaned[:140].rsplit(' ', 1)[0].strip() + '…'
        detail = cleaned
    return headline or fallback_headline, detail or cleaned


def _build_section(
    *,
    section_id: str,
    title: str,
    body: str,
    fallback_headline: str,
    default_expanded: bool,
    evidence_title: str | None = None,
    evidence_items: list[str] | None = None,
    tarot_cards: list[dict] | None = None,
    spread: str | None = None,
    combined_interpretation: str | None = None,
    palm_signals: list[dict] | None = None,
) -> dict:
    headline, detail = _headline_and_detail(body, fallback_headline=fallback_headline)
    payload = {
        'id': section_id,
        'title': title,
        'text': detail or body or headline,
        'headline': headline,
        'detail': detail or body,
        'default_expanded': default_expanded,
    }
    evidence_items = [item for item in (evidence_items or []) if _clean(item)]
    evidence: dict[str, object] = {}
    if evidence_title and evidence_items:
        evidence['title'] = evidence_title
        evidence['items'] = evidence_items
    if tarot_cards:
        evidence['tarot'] = {
            'spread': _clean(spread),
            'cards': tarot_cards,
            'combined_interpretation': _clean(combined_interpretation),
        }
    if palm_signals:
        evidence['palm'] = {
            'signals': palm_signals,
        }
    if evidence:
        payload['evidence'] = evidence
    return payload


def build_full_reading_payload(
    *,
    normalized: NormalizedMysticOutput,
    metadata: GenerationMetadata,
    question: str | None = None,
    tarot_payload: dict | None = None,
    palm_features: list[dict] | None = None,
    include_palm: bool = False,
    content_contract: dict | None = None,
) -> dict:
    asking = _clean(normalized.what_this_is_asking_of_you)
    next_move = _clean(normalized.your_next_move)

    if not asking or not next_move:
        legacy_asking, legacy_next_move = _split_legacy_guidance(normalized.practical_guidance)
        asking = asking or legacy_asking
        next_move = next_move or legacy_next_move

    opening = _clean(normalized.reading_opening) or _clean(normalized.opening_hook)
    synthesis = _clean(normalized.signals_agree) or _clean(normalized.emotional_truth) or _clean(normalized.current_pattern)
    tarot_message = _clean(normalized.tarot_message) or _clean(normalized.emotional_truth)
    palm_revelation = _clean(normalized.palm_revelation)

    snapshot = {
        'core_theme': _clean(normalized.snapshot_core_theme) or _first_sentence(normalized.current_pattern),
        'main_tension': _clean(normalized.snapshot_main_tension) or _first_sentence(normalized.emotional_truth),
        'best_next_move': _clean(normalized.snapshot_best_next_move) or _first_sentence(next_move or normalized.practical_guidance),
    }

    tarot_cards = _tarot_cards(tarot_payload)
    tarot_cards_summary = _tarot_cards_summary(tarot_payload)
    tarot_spread = _clean((tarot_payload or {}).get('spread') if isinstance(tarot_payload, dict) else '')
    palm_signals = _palm_signals(palm_features)
    palm_feature_summaries = _palm_features_summary(palm_features)
    include_palm_section = include_palm or bool(palm_feature_summaries) or bool(palm_revelation)

    if not palm_revelation and include_palm_section:
        if palm_feature_summaries:
            palm_revelation = 'Palm signals that stood out: ' + '; '.join(palm_feature_summaries)
            if question:
                palm_revelation += f". In relation to your question, these features point toward how you are carrying this pattern rather than promising fixed certainty."
        else:
            palm_revelation = 'Your palm adds a subtle layer here rather than a dramatic override. The visible hand signals are suggestive, not absolute, so this reading treats palm as supporting evidence instead of forced precision.'

    if tarot_cards_summary and tarot_cards_summary.casefold() not in tarot_message.casefold():
        tarot_message = f"Cards in view: {tarot_cards_summary}. {tarot_message}".strip()

    sections = [
        _build_section(
            section_id='reading_opening',
            title='OPENING',
            body=opening,
            fallback_headline=snapshot['core_theme'] or 'A meaningful pattern is taking shape.',
            default_expanded=True,
        ),
    ]
    if include_palm_section:
        sections.append(
            _build_section(
                section_id='palm_revelation',
                title='WHAT YOUR PALM REVEALS',
                body=palm_revelation,
                fallback_headline='Your palm shows how this question is being carried in your system.',
                default_expanded=False,
                evidence_title='Palm signals',
                evidence_items=palm_feature_summaries,
                palm_signals=palm_signals,
            )
        )
    sections.extend([
        _build_section(
            section_id='tarot_message',
            title='WHAT THE CARDS ARE SAYING',
            body=tarot_message,
            fallback_headline='The cards are concentrating the emotional pattern into something readable.',
            default_expanded=True,
            evidence_title='Cards in this spread',
            evidence_items=[tarot_cards_summary] if tarot_cards_summary else [],
            tarot_cards=tarot_cards,
            spread=tarot_spread,
            combined_interpretation=tarot_message,
        ),
        _build_section(
            section_id='signals_agree',
            title='WHERE THESE SIGNALS AGREE',
            body=synthesis,
            fallback_headline='The strongest overlap is the pattern you can no longer sidestep.',
            default_expanded=False,
        ),
        _build_section(
            section_id='what_this_is_asking_of_you',
            title='WHAT THIS IS ASKING OF YOU',
            body=asking,
            fallback_headline='The inner ask is more precise than comfort usually allows.',
            default_expanded=False,
        ),
        _build_section(
            section_id='your_next_move',
            title='YOUR NEXT MOVE',
            body=next_move,
            fallback_headline=snapshot['best_next_move'] or 'Take the smallest decisive step that changes the pattern.',
            default_expanded=True,
        ),
        _build_section(
            section_id='next_return_invitation',
            title='RETURN LINE',
            body=normalized.next_return_invitation,
            fallback_headline='Return when the pattern has had time to move.',
            default_expanded=False,
        ),
    ])

    sections = [section for section in sections if _clean(str(section.get('text', '')))]
    full_text = '\n\n'.join(str(section['text']) for section in sections if section['text'])

    return {
        'snapshot': snapshot,
        'sections': sections,
        'full_text': full_text,
        'metadata': {
            'persona_id': metadata.persona_id,
            'llm_profile_id': metadata.llm_profile_id,
            'prompt_version': metadata.prompt_version,
            'theme_tags': metadata.theme_tags,
            'headline': metadata.headline,
            'model': metadata.model_id,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'question': _clean(question),
            'content_contract': content_contract or {},
            'modalities': {
                'includes_palm': include_palm_section,
                'includes_tarot': bool(tarot_cards_summary or tarot_message),
            },
            'evidence': {
                'tarot_cards': tarot_cards_summary,
                'palm_features': palm_feature_summaries,
                'tarot': {
                    'spread': tarot_spread,
                    'cards': tarot_cards,
                    'combined_interpretation': tarot_message,
                },
                'palm': {
                    'signals': palm_signals,
                    'question_relevance': _clean(question),
                    'interpretation': palm_revelation,
                },
            },
            'payoff_contract': {
                'what_this_is_asking_of_you': asking,
                'your_next_move': next_move,
                'practical_guidance_legacy': _clean(normalized.practical_guidance),
            },
        },
    }
