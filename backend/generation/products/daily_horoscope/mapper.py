from __future__ import annotations

from .schema import DAILY_HOROSCOPE_PREVIEW_FIELDS, DAILY_HOROSCOPE_READING_FIELDS


def _clean(text: str | None) -> str:
    return ' '.join((text or '').split()).strip()


def map_daily_preview(normalized) -> dict:
    headline = _clean(getattr(normalized, 'opening_hook', ''))
    energy = _clean(getattr(normalized, 'current_pattern', ''))
    best_move = _clean(getattr(normalized, 'practical_guidance', ''))
    watch_out = _clean(getattr(normalized, 'emotional_truth', ''))
    deeper = _clean(getattr(normalized, 'next_return_invitation', ''))
    return {
        'headline': headline,
        'today_energy': energy,
        'best_move_teaser': best_move,
        'watch_out_teaser': watch_out,
        'deeper_layer_teaser': deeper,
        'schema_fields': DAILY_HOROSCOPE_PREVIEW_FIELDS,
    }


def map_daily_reading(normalized) -> dict:
    theme = _clean(getattr(normalized, 'opening_hook', ''))
    energy = _clean(getattr(normalized, 'current_pattern', ''))
    best_move = _clean(getattr(normalized, 'practical_guidance', ''))
    watch_out = _clean(getattr(normalized, 'emotional_truth', ''))
    closing = _clean(getattr(normalized, 'next_return_invitation', ''))
    return {
        'today_theme': theme,
        'today_energy': energy,
        'best_move': best_move,
        'watch_out_for': watch_out,
        'people_energy': '',
        'work_focus': '',
        'timing': '',
        'closing_guidance': closing,
        'schema_fields': DAILY_HOROSCOPE_READING_FIELDS,
    }
