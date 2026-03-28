from generation.products.full_reading.formatter import build_full_reading_payload
from generation.types import GenerationMetadata, NormalizedMysticOutput


def _metadata() -> GenerationMetadata:
    return GenerationMetadata(
        persona_id='premium_mystic',
        llm_profile_id='full_premium',
        prompt_version='mystic-v1',
        model_id='test-model',
        theme_tags=['clarity'],
        headline='A pattern is gathering.',
    )


def test_build_full_reading_payload_uses_explicit_two_part_payoff() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A pattern is gathering.',
            current_pattern='You are being asked to stop orbiting the same uncertainty.',
            emotional_truth='The real pressure comes from knowing what matters and delaying the choice anyway.',
            what_this_is_asking_of_you='This is asking you to trust your own discernment instead of outsourcing it to timing, signs, or other people\'s comfort.',
            your_next_move='Name the one decision you already know is overdue, then take the smallest irreversible step toward it before the day ends.',
            practical_guidance='Legacy fallback text.',
            next_return_invitation='Come back tomorrow.',
            premium_teaser='There is another layer here.',
        ),
        metadata=_metadata(),
    )

    section_ids = [section['id'] for section in payload['sections']]
    assert 'what_this_is_asking_of_you' in section_ids
    assert 'your_next_move' in section_ids
    assert 'practical_guidance' not in section_ids
    assert payload['metadata']['payoff_contract']['what_this_is_asking_of_you']
    assert payload['metadata']['payoff_contract']['your_next_move']


def test_build_full_reading_payload_splits_legacy_guidance_for_compatibility() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A pattern is gathering.',
            current_pattern='You are being asked to stop orbiting the same uncertainty.',
            emotional_truth='The real pressure comes from knowing what matters and delaying the choice anyway.',
            practical_guidance='What this is asking of you: stop waiting for perfect certainty before you honour what you already know. Your next move: send the message, make the boundary, or clear the commitment that has been lingering in draft form.',
            next_return_invitation='Come back tomorrow.',
            premium_teaser='There is another layer here.',
        ),
        metadata=_metadata(),
    )

    sections_by_id = {section['id']: section['text'] for section in payload['sections']}
    assert sections_by_id['what_this_is_asking_of_you'].startswith('stop waiting for perfect certainty')
    assert sections_by_id['your_next_move'].startswith('send the message')
