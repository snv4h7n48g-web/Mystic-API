from __future__ import annotations


def _clean(text: str | None) -> str:
    return ' '.join((text or '').split()).strip()


def map_tarot_preview(normalized) -> dict:
    headline = _clean(getattr(normalized, 'opening_hook', ''))
    narrative = _clean(getattr(normalized, 'current_pattern', ''))
    guidance = _clean(getattr(normalized, 'practical_guidance', ''))
    closing = _clean(getattr(normalized, 'next_return_invitation', ''))
    return {
        'headline': headline,
        'card_message': narrative,
        'guidance_teaser': guidance,
        'deeper_layer_teaser': closing,
    }


def map_tarot_reading(normalized) -> dict:
    opening = _clean(getattr(normalized, 'opening_hook', ''))
    narrative = _clean(getattr(normalized, 'current_pattern', ''))
    synthesis = _clean(getattr(normalized, 'emotional_truth', ''))
    guidance = _clean(getattr(normalized, 'practical_guidance', ''))
    closing = _clean(getattr(normalized, 'next_return_invitation', ''))
    return {
        'opening_invocation': opening,
        'tarot_narrative': narrative,
        'integrated_synthesis': synthesis,
        'reflective_guidance': guidance,
        'closing_prompt': closing,
    }
