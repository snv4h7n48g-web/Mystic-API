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
        eligible_flows=("combined", "tarot_solo", "preview", "blessing_solo"),
        default_profile="preview_mystic",
        mysticism_level="high",
        tone_tags=("mystical", "symbolic", "warm", "evocative"),
        conversion_style="deeper_truth_offer",
        safety_rules=("no_invasive_claims", "no_dependency_language", "no_false_specificity"),
    ),
    "flagship_mystic": PersonaConfig(
        id="flagship_mystic",
        display_name="Flagship Mystic",
        eligible_flows=("combined", "sun_moon_solo"),
        default_profile="full_premium",
        mysticism_level="medium_high",
        tone_tags=("intimate", "layered", "premium", "emotionally_precise", "grounded"),
        conversion_style="premium_depth_synthesis",
        safety_rules=("no_invasive_claims", "no_dependency_language", "no_false_specificity", "no_false_certainty"),
    ),
    "psychic_best_friend": PersonaConfig(
        id="psychic_best_friend",
        display_name="Psychic Best Friend",
        eligible_flows=("daily_horoscope", "account", "shareable"),
        default_profile="grounded_clarity",
        mysticism_level="medium",
        tone_tags=("direct", "warm", "useful", "grounded", "lightly_conversational"),
        conversion_style="clarity_expansion",
        safety_rules=("no_invasive_claims", "no_dependency_language", "no_false_specificity"),
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
        eligible_flows=("sun_moon_solo", "lunar_new_year_solo", "daily_horoscope", "account", "grounded", "feng_shui"),
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
