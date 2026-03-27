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
    assert mapped['closing_prompt'] == ''
