from __future__ import annotations


def _clean(text: str | None) -> str:
    return ' '.join((text or '').split()).strip()


def _first_non_empty(normalized, *field_names: str) -> str:
    for field_name in field_names:
        value = _clean(getattr(normalized, field_name, ''))
        if value:
            return value
    return ''


def map_tarot_preview(normalized) -> dict:
    headline = _first_non_empty(normalized, 'reading_opening', 'opening_hook')
    narrative = _first_non_empty(normalized, 'tarot_message', 'current_pattern')
    guidance = _first_non_empty(normalized, 'what_this_is_asking_of_you', 'your_next_move', 'practical_guidance')
    closing = _clean(getattr(normalized, 'next_return_invitation', ''))
    return {
        'headline': headline,
        'card_message': narrative,
        'guidance_teaser': guidance,
        'deeper_layer_teaser': closing,
    }


def map_tarot_reading(normalized) -> dict:
    opening = _first_non_empty(normalized, 'reading_opening', 'opening_hook')
    narrative = _first_non_empty(normalized, 'tarot_message', 'current_pattern')
    synthesis = _first_non_empty(normalized, 'signals_agree', 'emotional_truth')
    guidance = _first_non_empty(normalized, 'what_this_is_asking_of_you', 'your_next_move', 'practical_guidance')
    closing = _clean(getattr(normalized, 'next_return_invitation', ''))
    return {
        'opening_invocation': opening,
        'tarot_narrative': narrative,
        'integrated_synthesis': synthesis,
        'reflective_guidance': guidance,
        'closing_prompt': closing,
    }
