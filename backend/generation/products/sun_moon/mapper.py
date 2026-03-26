from __future__ import annotations


def _clean(text: str | None) -> str:
    return ' '.join((text or '').split()).strip()


def map_sun_moon_preview(normalized) -> dict:
    opening = _clean(getattr(normalized, 'opening_hook', ''))
    foundation = _clean(getattr(normalized, 'current_pattern', ''))
    synthesis = _clean(getattr(normalized, 'emotional_truth', ''))
    guidance = _clean(getattr(normalized, 'practical_guidance', ''))
    return {
        'headline': opening,
        'foundation_teaser': foundation,
        'synthesis_teaser': synthesis,
        'guidance_teaser': guidance,
    }


def map_sun_moon_reading(normalized) -> dict:
    opening = _clean(getattr(normalized, 'opening_hook', ''))
    foundation = _clean(getattr(normalized, 'current_pattern', ''))
    synthesis = _clean(getattr(normalized, 'emotional_truth', ''))
    guidance = _clean(getattr(normalized, 'practical_guidance', ''))
    closing = _clean(getattr(normalized, 'next_return_invitation', ''))
    return {
        'opening_invocation': opening,
        'astrological_foundation': foundation,
        'integrated_synthesis': synthesis,
        'reflective_guidance': guidance,
        'closing_prompt': closing,
    }
