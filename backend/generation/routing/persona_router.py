from __future__ import annotations

from ..types import GenerationContext


def choose_persona(context: GenerationContext, continuity_context: dict | None = None) -> str:
    if context.object_type == "feng_shui":
        return "practical_astrologer"
    if context.object_type == "compatibility":
        return "flirty_cosmic_guide" if context.surface == "preview" else "flirty_cosmic_guide"
    if context.flow_type == "daily_horoscope":
        return "psychic_best_friend"
    if context.flow_type in {"sun_moon_solo", "lunar_new_year_solo"}:
        return "practical_astrologer"
    if context.surface == "preview":
        return "ancient_tarot_reader"
    return "ancient_tarot_reader"
