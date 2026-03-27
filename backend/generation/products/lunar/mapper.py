from __future__ import annotations


def _clean(text: str | None) -> str:
    return ' '.join((text or '').split()).strip()


def _pick(used: set[str], *candidates: str) -> str:
    for candidate in candidates:
        cleaned = _clean(candidate)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in used:
            continue
        used.add(key)
        return cleaned
    return ''


def map_lunar_preview(normalized) -> dict:
    used: set[str] = set()
    cycle_theme = _pick(used, getattr(normalized, 'opening_hook', ''))
    year_symbolism = _pick(
        used,
        getattr(normalized, 'current_pattern', ''),
        getattr(normalized, 'premium_teaser', ''),
        getattr(normalized, 'practical_guidance', ''),
    )
    welcome_release = _pick(
        used,
        getattr(normalized, 'emotional_truth', ''),
        getattr(normalized, 'practical_guidance', ''),
        getattr(normalized, 'next_return_invitation', ''),
    )
    movement_guidance = _pick(
        used,
        getattr(normalized, 'practical_guidance', ''),
        getattr(normalized, 'next_return_invitation', ''),
        getattr(normalized, 'premium_teaser', ''),
    )
    return {
        'headline': cycle_theme,
        'cycle_theme_teaser': cycle_theme,
        'year_symbolism_teaser': year_symbolism,
        'welcome_release_teaser': welcome_release,
        'movement_guidance_teaser': movement_guidance,
    }


def map_lunar_reading(normalized) -> dict:
    used: set[str] = set()
    cycle_theme = _pick(used, getattr(normalized, 'opening_hook', ''))
    year_symbolism = _pick(
        used,
        getattr(normalized, 'current_pattern', ''),
        getattr(normalized, 'premium_teaser', ''),
        getattr(normalized, 'practical_guidance', ''),
    )
    welcome_release = _pick(
        used,
        getattr(normalized, 'emotional_truth', ''),
        getattr(normalized, 'premium_teaser', ''),
        getattr(normalized, 'next_return_invitation', ''),
    )
    movement_guidance = _pick(
        used,
        getattr(normalized, 'practical_guidance', ''),
        getattr(normalized, 'next_return_invitation', ''),
        getattr(normalized, 'premium_teaser', ''),
    )
    closing = _pick(
        used,
        getattr(normalized, 'next_return_invitation', ''),
        getattr(normalized, 'premium_teaser', ''),
        getattr(normalized, 'practical_guidance', ''),
    )
    return {
        'opening_invocation': cycle_theme,
        'lunar_forecast': year_symbolism,
        'integrated_synthesis': welcome_release,
        'reflective_guidance': movement_guidance,
        'closing_prompt': closing,
    }
