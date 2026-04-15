from generation.types import NormalizedMysticOutput
from generation.products.lunar.mapper import map_lunar_reading


def test_lunar_mapper_uses_fallbacks_to_reduce_duplicate_sections():
    normalized = NormalizedMysticOutput(
        opening_hook='A threshold year is opening.',
        current_pattern='A threshold year is opening.',
        emotional_truth='A threshold year is opening.',
        practical_guidance='1. Protect your time. 2. Back the steady path. 3. Leave old noise behind.',
        continuity_callback=None,
        next_return_invitation='Carry only what still belongs in this next cycle.',
        premium_teaser='The year rewards disciplined movement over reactive motion.',
        theme_tags=['lunar', 'year-ahead'],
    )

    mapped = map_lunar_reading(normalized)

    assert mapped['opening_invocation'] == 'A threshold year is opening.'
    assert mapped['lunar_forecast'] == 'The year rewards disciplined movement over reactive motion.'
    assert mapped['integrated_synthesis'] == 'Carry only what still belongs in this next cycle.'
    assert mapped['reflective_guidance'] == '1. Protect your time. 2. Back the steady path. 3. Leave old noise behind.'
    assert mapped['closing_prompt']
    assert "threshold marker" in mapped['opening_invocation_detail']
    assert mapped['lunar_forecast_detail'] != mapped['lunar_forecast']


def test_lunar_mapper_can_build_distinct_sections_from_lunar_context_when_model_is_thin():
    normalized = NormalizedMysticOutput(
        opening_hook='',
        current_pattern='',
        emotional_truth='',
        practical_guidance='',
        continuity_callback=None,
        next_return_invitation='',
        premium_teaser='',
        theme_tags=['lunar', 'year-ahead'],
    )

    mapped = map_lunar_reading(
        normalized,
        lunar_context={
            "birth_zodiac": {
                "combined": "Wood Tiger",
                "archetype": "courageous catalyst",
                "gifts": "breaking deadlock and restoring movement",
                "cautions": "confusing urgency with truth",
                "move_well": "choose a worthy fight and act cleanly",
            },
            "current_year": {
                "year_label": "2026: Year of the Fire Horse",
                "year_animal": {
                    "combined": "Fire Horse",
                    "headline": "a year that rewards motion, courage, and visible aliveness",
                    "symbolism": "The Horse year asks whether your momentum is truly liberating you or merely keeping you busy.",
                    "opportunity": "Fresh starts and bold pivots are amplified.",
                    "caution": "Restlessness and scattered effort can cost more than expected.",
                },
                "year_element": {
                    "element": "Fire",
                    "tone": "visibility, passion, and animated momentum",
                    "move_well": "let passion light the path, but keep enough discipline to sustain what begins",
                },
            },
            "interaction": {
                "type": "allied",
                "reading": "This year animal tends to work with your nature, so support and momentum may be easier to access.",
            },
        },
    )

    assert "2026: Year of the Fire Horse" in mapped["opening_invocation"]
    assert "Fresh starts and bold pivots are amplified" in mapped["lunar_forecast"]
    assert "Release the pattern of confusing urgency with truth" in mapped["integrated_synthesis"]
    assert "choose a worthy fight and act cleanly" in mapped["reflective_guidance"]
    assert "Fire Horse" in mapped["closing_prompt"]
    assert "work with your nature" in mapped["opening_invocation_detail"]
    assert "The Fire element brings a tone of visibility, passion, and animated momentum" in mapped["lunar_forecast_detail"]
