from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PersonaConfig:
    id: str
    display_name: str
    eligible_flows: tuple[str, ...]
    default_profile: str
    mysticism_level: str
    tone_tags: tuple[str, ...]
    conversion_style: str
    safety_rules: tuple[str, ...]


PERSONAS: dict[str, PersonaConfig] = {
    "ancient_tarot_reader": PersonaConfig(
        id="ancient_tarot_reader",
        display_name="Ancient Tarot Reader",
        eligible_flows=("combined", "tarot_solo", "preview", "premium", "daily_horoscope"),
        default_profile="full_premium",
        mysticism_level="high",
        tone_tags=("symbolic", "cryptic", "elegant", "layered"),
        conversion_style="layered_depth",
        safety_rules=("no_false_certainty", "no_fabricated_memory", "no_fear_hooks"),
    ),
    "psychic_best_friend": PersonaConfig(
        id="psychic_best_friend",
        display_name="Psychic Best Friend",
        eligible_flows=("daily_horoscope", "preview", "return_loop"),
        default_profile="daily_retention",
        mysticism_level="medium",
        tone_tags=("warm", "casual", "validating", "light_humour"),
        conversion_style="gentle_deeper_offer",
        safety_rules=("no_dependency_language", "no_fabricated_memory", "no_pressure_upsell"),
    ),
    "shadow_work_oracle": PersonaConfig(
        id="shadow_work_oracle",
        display_name="Shadow Work Oracle",
        eligible_flows=("premium", "self_work", "tarot_solo", "combined"),
        default_profile="full_premium",
        mysticism_level="medium_high",
        tone_tags=("direct", "psychological", "challenging", "clear"),
        conversion_style="deeper_pattern_reveal",
        safety_rules=("no_shaming", "no_harmful_certainty", "no_fear_hooks"),
    ),
    "flirty_cosmic_guide": PersonaConfig(
        id="flirty_cosmic_guide",
        display_name="Flirty Cosmic Guide",
        eligible_flows=("compatibility", "preview", "shareable"),
        default_profile="preview_mystic",
        mysticism_level="medium",
        tone_tags=("playful", "teasing", "romantic", "intriguing"),
        conversion_style="relationship_depth_offer",
        safety_rules=("no_invasive_claims", "no_dependency_language", "no_false_specificity"),
    ),
    "practical_astrologer": PersonaConfig(
        id="practical_astrologer",
        display_name="Practical Astrologer",
        eligible_flows=("sun_moon_solo", "daily_horoscope", "account", "grounded", "feng_shui"),
        default_profile="grounded_clarity",
        mysticism_level="low",
        tone_tags=("calm", "structured", "credible", "practical"),
        conversion_style="clarity_expansion",
        safety_rules=("no_false_certainty", "no_fabricated_memory", "no_manipulative_urgency"),
    ),
}


def get_persona(persona_id: str) -> PersonaConfig:
    try:
        return PERSONAS[persona_id]
    except KeyError as exc:
        raise KeyError(f"Unknown persona: {persona_id}") from exc
