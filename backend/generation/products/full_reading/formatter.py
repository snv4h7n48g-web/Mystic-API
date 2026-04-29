from __future__ import annotations

import re
from datetime import datetime, timezone

from tarot_knowledge import tarot_reference_for_card

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
_QUESTION_LINK_PREFIX_PATTERN = re.compile(
    r'^\s*(?:(?:for this|in this|for your)\s+question,\s*)?(?:it\s+)?matters\s+because\s+',
    re.IGNORECASE,
)

_PALM_LABEL_MAP = {
    'heart_line': 'Heart Line',
    'heart line': 'Heart Line',
    'life_line': 'Life Line',
    'life line': 'Life Line',
    'head_line': 'Head Line',
    'head line': 'Head Line',
    'fate_line': 'Fate Line',
    'fate line': 'Fate Line',
    'sun_line': 'Sun Line',
    'sun line': 'Sun Line',
    'marriage_line': 'Relationship Line',
    'marriage line': 'Relationship Line',
    'palm_shape': 'Palm Shape',
    'hand_shape': 'Overall Palm Impression',
    'hand shape': 'Overall Palm Impression',
    'overall_palm_impression': 'Overall Palm Impression',
    'mount_of_venus': 'Mount of Venus',
    'mount_of_moon': 'Mount of Moon',
}
_PALM_ICON_MAP = {
    'Heart Line': 'heart_line',
    'Life Line': 'life_line',
    'Head Line': 'head_line',
    'Fate Line': 'fate_line',
    'Sun Line': 'sun_line',
    'Relationship Line': 'relationship_line',
    'Palm Shape': 'palm_shape',
    'Overall Palm Impression': 'overall_palm',
}
_PALM_MEANING_HINTS = {
    'Heart Line': 'emotional expression, trust, and the way you let connection move through you',
    'Head Line': 'decision-making style, mental pacing, and how tightly you manage uncertainty',
    'Life Line': 'stamina, recovery, and how steadily you hold yourself through pressure',
    'Fate Line': 'direction, duty, and the relationship between choice and external demands',
    'Sun Line': 'visibility, confidence, and the way recognition affects your momentum',
    'Relationship Line': 'intimacy patterns, attachment habits, and what partnership tends to mirror back',
    'Palm Shape': 'your default temperament and the way you meet experience overall',
    'Overall Palm Impression': 'your overall way of carrying stress, openness, and self-protection',
    'Mount of Venus': 'warmth, attachment, appetite, and how strongly desire shapes your choices',
    'Mount of Moon': 'imagination, sensitivity, and what your system absorbs from its environment',
}
_SECTION_DETAIL_FALLBACKS = {
    'reading_opening': 'It sets up the larger pattern the rest of the reading will unpack.',
    'astrological_foundation': 'It grounds the reading in the natal chart factors that shape how this pattern tends to move.',
    'palm_revelation': 'It turns the visible hand signals into a lived pattern and shows why they matter here.',
    'tarot_message': 'It expands the cards into a spread-level pattern instead of isolated symbols.',
    'signals_agree': 'It names the overlap between the signals without repeating the earlier sections.',
    'what_this_is_asking_of_you': 'It points to the inner adjustment the question is asking for.',
    'your_next_move': 'It turns that insight into a concrete step you can actually take.',
    'next_return_invitation': 'It gives the reading a clean place to close and return later.',
}
_ACTION_MARKERS = ('choose', 'send', 'ask', 'name', 'make', 'begin', 'start', 'stop', 'schedule', 'say', 'write', 'set', 'clear', 'take')


def _clean(text: str | None) -> str:
    return (text or '').strip()


def _normalize_whitespace(text: str | None) -> str:
    return re.sub(r'\s+', ' ', _clean(text)).strip()


def _normalize_for_compare(text: str) -> str:
    return re.sub(r'\W+', ' ', _normalize_whitespace(text).casefold()).strip()


def _content_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", _normalize_whitespace(text).casefold())


def _content_token_count(text: str) -> int:
    return len(_content_tokens(text))


def _is_too_similar(left: str, right: str) -> bool:
    left_tokens = set(_content_tokens(left))
    right_tokens = set(_content_tokens(right))
    shortest = min(len(left_tokens), len(right_tokens))
    if shortest == 0:
        return False
    overlap = len(left_tokens & right_tokens)
    return overlap >= max(5, int(shortest * 0.75))


def _dedupe_sentences(text: str) -> str:
    cleaned = _normalize_whitespace(text)
    if not cleaned:
        return ''
    seen: set[str] = set()
    unique: list[str] = []
    for sentence in [segment.strip() for segment in _SENTENCE_SPLIT_PATTERN.split(cleaned) if segment.strip()]:
        marker = _normalize_for_compare(sentence)
        if marker and marker not in seen:
            seen.add(marker)
            unique.append(sentence)
    return ' '.join(unique).strip()


def _split_first_clause(text: str) -> tuple[str, str]:
    cleaned = _normalize_whitespace(text)
    if not cleaned:
        return '', ''
    for delimiter in ('; ', ': ', ' - ', ' — ', ', '):
        if delimiter in cleaned:
            left, right = cleaned.split(delimiter, 1)
            left = left.strip(' \n:-')
            right = right.strip(' \n:-')
            if left and right:
                return left, right
    lowered = cleaned.casefold()
    for pivot in (' instead of ', ' rather than ', ' before ', ' after ', ' because ', ' so that ', ' while ', ' when ', ' until ', ' unless '):
        if pivot in lowered:
            index = lowered.find(pivot)
            left = cleaned[:index].strip(' \n:-,')
            right = cleaned[index:].strip(' \n:-,')
            if left and right:
                return left, right
    return cleaned, ''


def _question_focus_phrase(question: str | None) -> str:
    cleaned = _normalize_whitespace(question).rstrip('?.!')
    if not cleaned:
        return ''
    lowered = cleaned.casefold()
    if lowered.startswith('should i '):
        return f"whether you should {cleaned[9:]}"
    if lowered.startswith('what should i '):
        return f"what you should {cleaned[14:]}"
    if lowered.startswith('what is '):
        return cleaned[8:]
    if lowered.startswith('how should i '):
        return f"how you should {cleaned[13:]}"
    if lowered.startswith('how do i '):
        return f"how to {cleaned[9:]}"
    if lowered.startswith('will i '):
        return f"whether you will {cleaned[7:]}"
    if lowered.startswith('am i '):
        return f"whether you are {cleaned[5:]}"
    if lowered.startswith('is this '):
        return f"whether this is {cleaned[8:]}"
    return cleaned


def _looks_like_question(text: str) -> bool:
    lowered = _normalize_whitespace(text).casefold()
    return lowered.endswith('?') or lowered.startswith(
        (
            'should i ',
            'what ',
            'why ',
            'how ',
            'will i ',
            'am i ',
            'is this ',
            'do i ',
        )
    )


def _humanize_label(label: str) -> str:
    cleaned = _clean(label)
    if not cleaned:
        return ''
    mapped = _PALM_LABEL_MAP.get(cleaned.casefold())
    if mapped:
        return mapped
    cleaned = cleaned.replace('_', ' ').replace('-', ' ')
    return ' '.join(part.capitalize() if part.lower() not in {'of', 'and'} else part.lower() for part in cleaned.split())


def _icon_key_for_label(label: str) -> str:
    pretty = _humanize_label(label)
    return _PALM_ICON_MAP.get(pretty, pretty.casefold().replace(' ', '_')) if pretty else 'palm_signal'


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
        orientation = _clean(card.get('orientation') or 'upright').lower()
        meaning = _clean(card.get('meaning') or card.get('interpretation') or card.get('summary'))
        question_link = _clean(card.get('question_link') or card.get('how_it_relates') or card.get('relevance'))
        if name:
            parsed.append(
                {
                    'card': name,
                    'position': position,
                    'orientation': orientation,
                    'interpretation': meaning,
                    'question_link': question_link,
                }
            )
    return parsed


def _tarot_default_question_link(card: dict, index: int, question: str | None) -> str:
    focus = _question_focus_phrase(question)
    role_hint = _tarot_role_hint(_clean(card.get('position')), index)
    if focus:
        return f"{role_hint} around {focus}"
    return role_hint


def _enrich_tarot_cards(tarot_cards: list[dict], question: str | None) -> list[dict]:
    enriched: list[dict] = []
    for index, raw_card in enumerate(tarot_cards):
        card = dict(raw_card)
        interpretation = _clean(card.get('interpretation')) or _tarot_reference_meaning(card)
        if _content_token_count(interpretation) < 12:
            role_hint = _tarot_role_hint(_clean(card.get('position')), index)
            focus = _question_focus_phrase(question)
            suffix = (
                f" It shows how {role_hint} is shaping {focus}."
                if focus
                else f" It shows how {role_hint} is shaping the reading."
            )
            interpretation = f"{interpretation.rstrip('.')}." if interpretation else "This card is active in the spread."
            interpretation = f"{interpretation.rstrip('.')} {suffix.strip()}".strip()
        question_link = _clean(card.get('question_link'))
        if not question_link:
            question_link = _tarot_default_question_link(card, index, question)
        card['interpretation'] = _dedupe_sentences(interpretation).strip()
        card['question_link'] = _dedupe_sentences(question_link).strip()
        enriched.append(card)
    return enriched


def _tarot_cards_summary(tarot_payload: dict | None) -> str:
    labels = []
    for card in _tarot_cards(tarot_payload):
        name = card['card']
        position = card['position']
        orientation = card.get('orientation', '')
        orientation_suffix = f", {orientation}" if orientation and orientation != 'upright' else ''
        labels.append(f"{name} ({position}{orientation_suffix})" if position else f"{name}{orientation_suffix}")
    return ', '.join(labels)


def _tarot_role_hint(position: str, index: int) -> str:
    normalized = position.casefold().strip()
    if normalized in {'past', 'root', 'foundation'}:
        return 'the pattern that has already been shaping this question'
    if normalized in {'present', 'current', 'now'}:
        return 'the live pressure point in the present moment'
    if normalized in {'guidance', 'advice', 'outcome', 'future', 'next'}:
        return 'the response the spread is steering you toward'
    if normalized in {'crossing', 'challenge', 'obstacle'}:
        return 'the friction or resistance complicating the decision'
    if index == 0:
        return 'the opening note of the spread'
    if index == 1:
        return 'the tension that changes how the first card reads'
    return 'the direction the spread gathers into'


def _tarot_position_text(position: str, index: int) -> str:
    return f' in the {position} position' if position else f' in card role {index + 1}'


def _tarot_orientation_nuance(name: str, orientation: str, reference: dict) -> str:
    if orientation != 'reversed':
        return ''
    guidebook_reversed = _clean(reference.get('guidebook_reversed'))
    if guidebook_reversed:
        return guidebook_reversed.rstrip('.')
    shadow = _clean(reference.get('shadow'))
    if shadow:
        return shadow.rstrip('.')
    if name:
        return f'{name} is showing its blocked, distorted, or overcorrected side rather than its clean expression'
    return 'the card is showing its blocked or inverted side rather than its clean expression'


def _tarot_reference_meaning(card: dict) -> str:
    reference = tarot_reference_for_card(card.get('card', ''))
    position = _clean(card.get('position')).lower()
    orientation = _clean(card.get('orientation') or 'upright').lower()

    if orientation != 'reversed':
        guidebook_upright = _clean(reference.get('guidebook_upright'))
        if guidebook_upright:
            return guidebook_upright

    if orientation == 'reversed':
        nuance = _tarot_orientation_nuance(card.get('card', ''), orientation, reference)
        if nuance:
            return nuance

    if position == 'past' and _clean(reference.get('past')):
        return _clean(reference.get('past'))
    if position == 'present' and _clean(reference.get('present')):
        return _clean(reference.get('present'))
    if position == 'guidance' and _clean(reference.get('guidance')):
        return _clean(reference.get('guidance'))

    return _clean(reference.get('core') or reference.get('meaning') or reference.get('balanced'))


def _tarot_reference_symbol(card: dict) -> str:
    reference = tarot_reference_for_card(card.get('card', ''))
    traditional = _clean(reference.get('traditional'))
    if traditional:
        return traditional.rstrip('.')
    return ''


def _tarot_question_link_sentence(question_link: str) -> str:
    cleaned = _QUESTION_LINK_PREFIX_PATTERN.sub('', _normalize_whitespace(question_link)).strip()
    if not cleaned:
        return ''
    if cleaned[:1].isupper() and cleaned.endswith(('.', '!', '?')):
        return cleaned
    lowered = cleaned.casefold()
    if lowered.startswith(('it ', 'this ', 'that ', 'the ', 'you ', 'your ', 'part of you ')):
        return cleaned[:1].upper() + cleaned[1:].rstrip('.') + '.'
    return f"In context, this points to {cleaned.rstrip('.')}."


def _tarot_card_line(card: dict, index: int) -> str:
    name = card.get('card', '')
    position = _clean(card.get('position'))
    orientation = _clean(card.get('orientation') or 'upright').lower()
    interpretation = _clean(card.get('interpretation')) or _tarot_reference_meaning(card)
    question_link = _clean(card.get('question_link'))
    if not name:
        return ''

    position_text = _tarot_position_text(position, index)
    role_hint = _tarot_role_hint(position, index)
    orientation_phrase = ' reversed' if orientation == 'reversed' else ''
    symbol = _tarot_reference_symbol(card)

    opening = f"{name}{orientation_phrase}{position_text} lands as {role_hint}"
    if interpretation:
        opening += f", speaking to {interpretation.rstrip('.')}"
    opening = opening.rstrip('.') + '.'

    follow_parts: list[str] = []
    if question_link:
        follow_parts.append(_tarot_question_link_sentence(question_link))
    if symbol:
        follow_parts.append(f"The card image carries {symbol}.")
    if orientation == 'reversed':
        follow_parts.append("That reversal makes the message feel less like clean movement and more like a snag you can no longer romanticise.")

    return ' '.join([opening, *follow_parts]).strip()


def _tarot_story_lead(tarot_cards: list[dict], question: str | None) -> str:
    if not tarot_cards:
        return ''
    first = tarot_cards[0]
    first_name = _clean(first.get('card'))
    first_orientation = _clean(first.get('orientation') or 'upright').lower()
    first_label = f"{first_name} reversed" if first_name and first_orientation == 'reversed' else first_name
    focus = _question_focus_phrase(question)
    if first_label and focus:
        return f"The spread opens with {first_label}, which tells you this is not really a question about surface options so much as a question about {focus}."
    if first_label:
        return f"The spread opens with {first_label}, which tells you the cards are trying to get underneath the polite version of the story."
    return ''


def _build_tarot_story(tarot_cards: list[dict], tarot_spread: str, question: str | None) -> str:
    if not tarot_cards:
        return ''

    fragments: list[str] = []
    for index, card in enumerate(tarot_cards[:3]):
        name = card.get('card', '')
        position = _clean(card.get('position'))
        orientation = _clean(card.get('orientation') or 'upright').lower()
        role_hint = _tarot_role_hint(position, index)
        question_link = _QUESTION_LINK_PREFIX_PATTERN.sub('', _clean(card.get('question_link'))).strip()
        signal = question_link or _clean(card.get('interpretation')) or _tarot_reference_meaning(card)
        if question_link and signal.casefold().startswith(role_hint.casefold()):
            signal = signal[len(role_hint):].strip(' ,:-')
        if signal.casefold().startswith('around '):
            signal = f"it concentrates the question {signal}"
        if not signal:
            signal = _clean(card.get('interpretation')) or _tarot_reference_meaning(card)
        if not name or not signal:
            continue
        card_label = f"{name} reversed" if orientation == 'reversed' else name
        fragments.append(f"{card_label} brings {role_hint}: {signal.rstrip('.')}")

    if not fragments:
        return ''

    lead = _tarot_story_lead(tarot_cards, question)
    if len(fragments) == 1:
        middle = f"The overall story is concentrated rather than diffuse: {fragments[0]}."
    elif len(fragments) == 2:
        middle = f"Taken together, the cards create one movement rather than two separate ideas: {fragments[0]}, while {fragments[1]}."
    else:
        middle = (
            f"Taken together, the spread reads like a sequence: {fragments[0]}; "
            f"{fragments[1]}; and {fragments[2]}."
        )

    closing_parts: list[str] = []
    if tarot_spread:
        closing_parts.append(f"The {tarot_spread} layout gives the story momentum, so each card changes how the next one lands.")
    if question:
        closing_parts.append('The real answer here is not hidden in prediction. It sits in the tension the cards keep circling and the kind of truth they are pushing you to stop diluting.')

    return _dedupe_sentences(' '.join(part for part in [lead, middle, ' '.join(closing_parts)] if part)).strip()


def _tarot_card_name_hits(text: str, tarot_cards: list[dict]) -> int:
    lowered = _normalize_whitespace(text).casefold()
    hits = 0
    for card in tarot_cards:
        name = _clean(card.get('card')).casefold()
        if name and name in lowered:
            hits += 1
    return hits


def _tarot_base_has_spread_depth(text: str, tarot_cards: list[dict]) -> bool:
    if not text or not tarot_cards:
        return False
    lowered = _normalize_whitespace(text).casefold()
    card_hits = _tarot_card_name_hits(text, tarot_cards)
    required_hits = min(2, len(tarot_cards))
    if card_hits < required_hits:
        return False
    if _content_token_count(text) < 55:
        return False
    structure_markers = (
        'past position',
        'present position',
        'guidance position',
        'position',
        'spread',
        'together',
        'reversed',
        'upright',
        'card',
    )
    return any(marker in lowered for marker in structure_markers)


def _tarot_card_covered_by_base(text: str, card: dict) -> bool:
    lowered = _normalize_whitespace(text).casefold()
    name = _clean(card.get('card')).casefold()
    if name and name in lowered:
        return True
    interpretation = _clean(card.get('interpretation'))
    return bool(interpretation and _is_too_similar(text, interpretation))


def _build_tarot_narrative(tarot_cards: list[dict], tarot_spread: str, question: str | None, tarot_message: str) -> str:
    base = _dedupe_sentences(tarot_message)
    if _tarot_base_has_spread_depth(base, tarot_cards):
        return base

    card_lines = [
        _tarot_card_line(card, index)
        for index, card in enumerate(tarot_cards[:3])
        if not _tarot_card_covered_by_base(base, card)
    ]
    card_lines = [line for line in card_lines if line]
    story = _build_tarot_story(tarot_cards, tarot_spread, question)

    paragraphs: list[str] = []
    if base:
        paragraphs.append(base)
    if card_lines:
        paragraphs.append(' '.join(card_lines))
    if story:
        paragraphs.append(story)

    normalized: list[str] = []
    seen: set[str] = set()
    for paragraph in paragraphs:
        cleaned = _dedupe_sentences(paragraph)
        marker = _normalize_for_compare(cleaned)
        if cleaned and marker and marker not in seen:
            seen.add(marker)
            normalized.append(cleaned)
    return '\n\n'.join(normalized).strip()


def _astrology_anchor_lines(astrology_facts: dict | None) -> list[str]:
    if not isinstance(astrology_facts, dict):
        return []
    lines: list[str] = []
    sun_sign = _clean(astrology_facts.get('sun_sign'))
    moon_sign = _clean(astrology_facts.get('moon_sign'))
    rising_sign = _clean(astrology_facts.get('rising_sign'))
    dominant_element = _clean(astrology_facts.get('dominant_element'))
    dominant_planet = _clean(astrology_facts.get('dominant_planet'))
    top_aspects = astrology_facts.get('top_aspects') if isinstance(astrology_facts.get('top_aspects'), list) else []

    if sun_sign and moon_sign:
        lines.append(f"Your chart leads with {sun_sign} Sun and {moon_sign} Moon, which says the outer self and inner needs are already carrying a built-in tension.")
    elif sun_sign:
        lines.append(f"Your chart leads with a {sun_sign} Sun signature, so identity and instinct matter to how this question is being handled.")
    elif moon_sign:
        lines.append(f"Your chart leans heavily on a {moon_sign} Moon signature, so emotional needs and nervous-system truth matter here as much as logic.")

    if rising_sign:
        lines.append(f"The {rising_sign} rising layer shapes how you approach pressure in real time, especially in how you present control, caution, or confidence.")
    if dominant_element:
        lines.append(f"The dominant {dominant_element} emphasis shows the style your system defaults to when life gets serious.")
    if dominant_planet:
        lines.append(f"{dominant_planet} feels especially loud in this chart, so its themes are part of what keeps repeating underneath the question.")

    for aspect in top_aspects[:2]:
        if not isinstance(aspect, dict):
            continue
        a = _clean(aspect.get('a'))
        aspect_type = _clean(aspect.get('type'))
        b = _clean(aspect.get('b'))
        if a and aspect_type and b:
            lines.append(f"The {a} {aspect_type} {b} aspect adds real friction or chemistry, which helps explain why this pattern feels active instead of theoretical.")

    deduped: list[str] = []
    seen: set[str] = set()
    for line in lines:
        marker = _normalize_for_compare(line)
        if marker and marker not in seen:
            seen.add(marker)
            deduped.append(line)
    return deduped[:4]


def _enrich_astrological_foundation(*, astrology_message: str, astrology_facts: dict | None, question: str | None) -> str:
    base = _dedupe_sentences(astrology_message)
    anchors = _astrology_anchor_lines(astrology_facts)
    if not base and not anchors:
        return ''
    if not base:
        base = ' '.join(anchors)
    elif anchors:
        joined_anchors = ' '.join(anchors)
        if len(base.split()) < 55 or _normalize_for_compare(joined_anchors) not in _normalize_for_compare(base):
            base = _dedupe_sentences(f"{base.rstrip('.')} {joined_anchors}").strip()
    if question and 'question' not in base.casefold():
        base = _dedupe_sentences(
            f"{base.rstrip('.')} In relation to your question, the chart helps explain why this issue lands the way it does instead of only describing your personality in the abstract."
        ).strip()
    return base


def _palm_signal_meaning(label: str, observation: str, relevance: str) -> str:
    meaning = _PALM_MEANING_HINTS.get(label, 'a deeper pattern in how this question is being carried')
    observed = observation.casefold()
    relevance_clean = _normalize_whitespace(relevance)
    if any(token in observed for token in ['deep', 'clear', 'strong', 'long', 'defined']):
        tone = 'shows the pattern is pronounced rather than faint'
    elif any(token in observed for token in ['faint', 'light', 'fine', 'broken', 'fragmented', 'chained']):
        tone = 'suggests the pattern is present but under strain or inconsistency'
    elif any(token in observed for token in ['curved', 'open', 'wide', 'full', 'broad']):
        tone = 'leans toward openness, response, and visible engagement'
    elif any(token in observed for token in ['straight', 'tight', 'flat', 'narrow', 'stiff']):
        tone = 'leans toward control, restraint, or emotional economy'
    else:
        tone = 'adds texture to the pattern rather than acting as neutral description'

    if relevance_clean:
        if _looks_like_question(relevance_clean):
            relation = 'It matters because it points to the same underlying tension the question is circling.'
        else:
            relation = f'In this question, it matters because {relevance_clean.rstrip(".")}.'
        return f'{label} speaks to {meaning}; this {tone}. {relation}'
    return f"{label} speaks to {meaning}; this {tone}."


def _palm_signals(palm_features: list[dict] | None) -> list[dict]:
    summaries: list[dict] = []
    seen: set[str] = set()
    for feature in palm_features or []:
        if not isinstance(feature, dict):
            continue
        raw_label = _clean(feature.get('label') or feature.get('feature') or feature.get('name') or feature.get('type'))
        pretty_label = _humanize_label(raw_label)
        value = _clean(
            feature.get('value')
            or feature.get('attribute')
            or feature.get('state')
            or feature.get('description')
            or feature.get('reading')
            or feature.get('summary')
        )
        relevance = _clean(feature.get('relevance') or feature.get('question_relevance') or feature.get('why_it_matters'))
        confidence = _clean(feature.get('confidence_label') or feature.get('confidence'))
        interpretation = _palm_signal_meaning(pretty_label or raw_label, value, relevance) if (pretty_label or raw_label) else relevance
        dedupe_key = _normalize_for_compare(' '.join(part for part in [pretty_label, value, relevance] if part))
        if (pretty_label or value or relevance) and dedupe_key not in seen:
            seen.add(dedupe_key)
            summaries.append(
                {
                    'feature': pretty_label,
                    'display_name': pretty_label,
                    'icon_key': _icon_key_for_label(pretty_label or raw_label),
                    'observation': value,
                    'attribute': value,
                    'relevance': relevance,
                    'interpretation': interpretation,
                    'confidence': confidence,
                }
            )
    return summaries[:5]


def _palm_features_summary(palm_features: list[dict] | None) -> list[str]:
    summaries: list[str] = []
    for signal in _palm_signals(palm_features):
        meaning = _clean(signal.get('interpretation'))
        if meaning:
            summaries.append(meaning)
            continue
        parts = [
            signal.get('display_name', '') or signal.get('feature', ''),
            signal.get('observation', ''),
            f"confidence: {signal['confidence']}" if signal.get('confidence') else '',
        ]
        parts = [part for part in parts if part]
        if parts:
            summaries.append(' - '.join(parts))

    deduped: list[str] = []
    seen: set[str] = set()
    for summary in summaries:
        marker = _normalize_for_compare(summary)
        if marker and marker not in seen:
            seen.add(marker)
            deduped.append(summary)
    return deduped[:5]


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


def _section_detail_fallback(*, section_id: str, headline: str, body: str, fallback_headline: str) -> str:
    base = _SECTION_DETAIL_FALLBACKS.get(section_id)
    if base:
        return base
    if body and _normalize_for_compare(body) != _normalize_for_compare(headline):
        return 'It adds the next layer of meaning instead of repeating the opening line.'
    return f'It extends {fallback_headline.lower()} into a clearer reading of the pattern.'


def _headline_and_detail(text: str, *, fallback_headline: str, section_id: str = '') -> tuple[str, str]:
    cleaned = _dedupe_sentences(text)
    if not cleaned:
        return fallback_headline, ''
    headline = _first_sentence(cleaned)
    detail = _remaining_sentences(cleaned)
    if not detail or _normalize_for_compare(detail) == _normalize_for_compare(headline):
        clause_headline, clause_detail = _split_first_clause(cleaned)
        if clause_detail:
            headline = clause_headline or headline
            detail = clause_detail
    if not detail or _normalize_for_compare(detail) == _normalize_for_compare(headline):
        detail = _section_detail_fallback(section_id=section_id, headline=headline or fallback_headline, body=cleaned, fallback_headline=fallback_headline)
    if _normalize_for_compare(headline).startswith(_normalize_for_compare(detail)) and len(cleaned) > 120:
        headline = cleaned[:120].rsplit(' ', 1)[0].strip() + '...'
        detail = _section_detail_fallback(section_id=section_id, headline=headline, body=cleaned, fallback_headline=fallback_headline)
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
) -> dict:
    headline, detail = _headline_and_detail(body, fallback_headline=fallback_headline, section_id=section_id)
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
    if evidence:
        payload['evidence'] = evidence
    return payload


def _palm_question_relevance(*, question: str | None, palm_signals: list[dict], palm_revelation: str) -> str:
    interpretive_lines = [
        _normalize_whitespace(signal.get('interpretation'))
        for signal in palm_signals
        if _normalize_whitespace(signal.get('interpretation'))
    ]
    synthesis = _dedupe_sentences(palm_revelation) or ' '.join(interpretive_lines[:2]).strip()
    if not synthesis and question:
        synthesis = 'the way this pattern is being carried right now'
    if question:
        focus = _question_focus_phrase(question)
        if synthesis:
            return f'This is really about {focus}; the hand suggests {synthesis.rstrip(".")}.'
        return f'This is really about {focus}; the hand points to a pattern that is still unfolding.'
    if synthesis:
        return synthesis.rstrip('.')
    return 'The hand points to a live pattern rather than a fixed answer.'


def _enrich_palm_revelation(*, palm_revelation: str, palm_signals: list[dict], question: str | None) -> str:
    cleaned = _dedupe_sentences(palm_revelation)
    if not palm_signals:
        return cleaned
    interpretive_lines = [
        _normalize_whitespace(signal.get('interpretation'))
        for signal in palm_signals
        if _normalize_whitespace(signal.get('interpretation'))
    ]
    if not cleaned:
        base = _dedupe_sentences(' '.join(interpretive_lines[:2]).strip())
        if len(interpretive_lines) > 2:
            base += ' Together, these signs describe the pattern your hand is repeating rather than a fixed fate.'
        if question:
            base += ' In relation to your question, the hand reads more like a mirror of your current pattern than a promise carved in stone.'
        return base.strip()

    lowered = cleaned.casefold()
    has_interpretive_language = any(
        phrase.casefold() in lowered
        for phrase in ['suggests', 'speaks to', 'matters because', 'points toward', 'shows the pattern', 'means', 'indicates', 'reveals']
    )
    if interpretive_lines and (len(cleaned.split()) < 35 or not has_interpretive_language):
        cleaned = f"{cleaned.rstrip('.')} {' '.join(interpretive_lines[:2])}".strip()
    if question and 'question' not in lowered and 'matters because' not in lowered:
        cleaned = f"{cleaned.rstrip('.')} In relation to your question, these palm features matter because they show how this pattern is being carried in real time."
    return _dedupe_sentences(cleaned).strip()


def _build_tarot_expansion(tarot_cards: list[dict], tarot_spread: str, question: str | None) -> str:
    if not tarot_cards:
        return ''
    lines: list[str] = []
    for index, card in enumerate(tarot_cards[:3]):
        line = _tarot_card_line(card, index)
        if line:
            lines.append(line)
    story = _build_tarot_story(tarot_cards, tarot_spread, question)
    if story:
        lines.append(story)
    return _dedupe_sentences(' '.join(lines).strip())


def _enrich_tarot_message(*, tarot_message: str, tarot_cards: list[dict], tarot_spread: str, question: str | None) -> str:
    narrative = _build_tarot_narrative(
        tarot_cards=tarot_cards,
        tarot_spread=tarot_spread,
        question=question,
        tarot_message=tarot_message,
    )
    return narrative or _dedupe_sentences(tarot_message)


def _has_action_marker(text: str) -> bool:
    lowered = _normalize_whitespace(text).casefold()
    return any(marker in lowered for marker in _ACTION_MARKERS)


def _enrich_next_move(next_move: str, *, question: str | None, tarot_cards: list[dict]) -> str:
    cleaned = _dedupe_sentences(next_move)
    if not cleaned:
        return ''

    focus = _question_focus_phrase(question)
    if focus:
        action_line = (
            f"Start by naming the clearest decision you can make about {focus}, then take one visible step today that turns the reading into a lived change instead of another private loop."
        )
    elif tarot_cards:
        lead_card = _clean(tarot_cards[0].get('card'))
        action_line = (
            f"Start by taking one visible step that honours what {lead_card or 'the cards'} is already making obvious, rather than waiting for the feeling to become easier or cleaner."
        )
    else:
        action_line = "Start by taking one visible step today that turns this insight into a concrete change instead of leaving it as a thought."

    if not _has_action_marker(cleaned):
        return action_line
    if _content_token_count(cleaned) >= 12:
        return cleaned
    if not cleaned:
        return action_line
    return _dedupe_sentences(f"{cleaned.rstrip('.')} {action_line}").strip()


def build_full_reading_payload(
    *,
    normalized: NormalizedMysticOutput,
    metadata: GenerationMetadata,
    question: str | None = None,
    astrology_facts: dict | None = None,
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
    astrological_foundation = _clean(normalized.astrological_foundation) or _clean(normalized.current_pattern)
    synthesis = _clean(normalized.signals_agree) or _clean(normalized.emotional_truth) or _clean(normalized.current_pattern)
    tarot_message = _clean(normalized.tarot_message) or _clean(normalized.emotional_truth)
    palm_revelation = _clean(normalized.palm_revelation)

    snapshot = {
        'core_theme': _clean(normalized.snapshot_core_theme) or _first_sentence(normalized.current_pattern),
        'main_tension': _clean(normalized.snapshot_main_tension) or _first_sentence(normalized.emotional_truth),
        'best_next_move': _clean(normalized.snapshot_best_next_move) or _first_sentence(next_move or normalized.practical_guidance),
    }

    tarot_cards = _enrich_tarot_cards(_tarot_cards(tarot_payload), question)
    tarot_cards_summary = _tarot_cards_summary(tarot_payload)
    tarot_spread = _clean((tarot_payload or {}).get('spread') if isinstance(tarot_payload, dict) else '')
    palm_signals = _palm_signals(palm_features)
    palm_feature_summaries = _palm_features_summary(palm_features)
    include_palm_section = include_palm or bool(palm_feature_summaries) or bool(palm_revelation)

    if not palm_revelation and include_palm_section:
        if palm_feature_summaries:
            palm_revelation = ' '.join(palm_feature_summaries[:2]).strip()
            if len(palm_feature_summaries) > 2:
                palm_revelation += ' Together, these signs suggest the hand is describing a lived pattern, not just listing physical traits.'
            if question:
                palm_revelation += ' In relation to your question, these features point toward how you are carrying this pattern rather than promising fixed certainty.'
        else:
            palm_revelation = 'Your palm adds a subtle layer here rather than a dramatic override. The visible hand signals are suggestive, not absolute, so this reading treats palm as supporting evidence instead of forced precision.'
    palm_revelation = _enrich_palm_revelation(palm_revelation=palm_revelation, palm_signals=palm_signals, question=question)
    palm_question_relevance = _palm_question_relevance(question=question, palm_signals=palm_signals, palm_revelation=palm_revelation)
    astrological_foundation = _enrich_astrological_foundation(
        astrology_message=astrological_foundation,
        astrology_facts=astrology_facts,
        question=question,
    )

    tarot_message = _enrich_tarot_message(tarot_message=tarot_message, tarot_cards=tarot_cards, tarot_spread=tarot_spread, question=question)
    tarot_story = _build_tarot_story(tarot_cards, tarot_spread, question)
    next_move = _enrich_next_move(next_move, question=question, tarot_cards=tarot_cards)

    sections = [
        _build_section(
            section_id='reading_opening',
            title='OPENING',
            body=opening,
            fallback_headline=snapshot['core_theme'] or 'A meaningful pattern is taking shape.',
            default_expanded=True,
        ),
        _build_section(
            section_id='astrological_foundation',
            title='ASTROLOGICAL FOUNDATION',
            body=astrological_foundation,
            fallback_headline='The chart shows the deeper temperament underneath this question.',
            default_expanded=False,
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
                evidence_title='Supporting palm details',
                evidence_items=palm_feature_summaries,
            )
        )
    sections.extend(
        [
            _build_section(
                section_id='tarot_message',
                title='WHAT THE CARDS ARE SAYING',
                body=tarot_message,
                fallback_headline='The cards are concentrating the emotional pattern into something readable.',
                default_expanded=True,
                tarot_cards=tarot_cards,
                spread=tarot_spread,
                combined_interpretation=tarot_story,
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
        ]
    )

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
                    'combined_interpretation': tarot_story,
                },
                'palm': {
                    'signals': palm_signals,
                    'question_relevance': palm_question_relevance,
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
