from __future__ import annotations


def _clean(text: str | None) -> str:
    return ' '.join((text or '').split()).strip()


def map_lunar_preview(normalized) -> dict:
    cycle_theme = _clean(getattr(normalized, 'opening_hook', ''))
    year_symbolism = _clean(getattr(normalized, 'current_pattern', ''))
    welcome_release = _clean(getattr(normalized, 'emotional_truth', ''))
    movement_guidance = _clean(getattr(normalized, 'practical_guidance', ''))
    return {
        'headline': cycle_theme,
        'cycle_theme_teaser': cycle_theme,
        'year_symbolism_teaser': year_symbolism,
        'welcome_release_teaser': welcome_release,
        'movement_guidance_teaser': movement_guidance,
    }


def map_lunar_reading(normalized) -> dict:
    cycle_theme = _clean(getattr(normalized, 'opening_hook', ''))
    year_symbolism = _clean(getattr(normalized, 'current_pattern', ''))
    welcome_release = _clean(getattr(normalized, 'emotional_truth', ''))
    movement_guidance = _clean(getattr(normalized, 'practical_guidance', ''))
    closing = _clean(getattr(normalized, 'next_return_invitation', ''))
    return {
        'opening_invocation': cycle_theme,
        'lunar_forecast': year_symbolism,
        'integrated_synthesis': welcome_release,
        'reflective_guidance': movement_guidance,
        'closing_prompt': closing,
    }
