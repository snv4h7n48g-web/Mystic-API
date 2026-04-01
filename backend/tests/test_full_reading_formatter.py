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


def test_build_full_reading_payload_emits_layered_sections_and_modality_evidence() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A threshold is here.',
            current_pattern='You are outgrowing the version of this question that let you stall.',
            emotional_truth='Part of you wants proof before movement, but the pressure is already the proof.',
            reading_opening='A threshold is here. The reading points to a choice that already has emotional weight.',
            palm_revelation='Your heart line and head line show intensity held under control. In your question, that suggests restraint is part wisdom and part fear.',
            tarot_message='The Chariot in the present position pushes movement, while the Two of Swords in the crossing position shows the split that keeps delaying it. Together the spread says your clarity is blocked more by self-protection than lack of options.',
            signals_agree='Palm and tarot both point to disciplined self-control becoming overcontrol. The pattern is not confusion so much as reluctance to commit to what you already see.',
            what_this_is_asking_of_you='Let certainty become a practice instead of a prerequisite.',
            your_next_move='Name the decision in one sentence and send the first message before tonight ends.',
            next_return_invitation='Return after the first move lands.',
            snapshot_core_theme='Clarity is here before comfort is.',
            snapshot_main_tension='You know the direction, but keep negotiating with it.',
            snapshot_best_next_move='Make the first irreversible move now.',
        ),
        metadata=_metadata(),
        question='Should I move forward?',
        tarot_payload={
            'spread': 'present / crossing',
            'cards': [
                {'card': 'The Chariot', 'position': 'present', 'meaning': 'Momentum wants a direction.'},
                {'card': 'Two of Swords', 'position': 'crossing', 'meaning': 'Indecision is becoming a shield.'},
            ],
        },
        palm_features=[
            {'label': 'Heart line', 'description': 'deep and curved', 'relevance': 'shows emotional investment', 'confidence_label': 'high'},
        ],
        include_palm=True,
    )

    tarot_section = next(section for section in payload['sections'] if section['id'] == 'tarot_message')
    palm_section = next(section for section in payload['sections'] if section['id'] == 'palm_revelation')
    opening_section = next(section for section in payload['sections'] if section['id'] == 'reading_opening')

    assert opening_section['headline']
    assert opening_section['detail']
    assert opening_section['default_expanded'] is True
    assert tarot_section['evidence']['tarot']['spread'] == 'present / crossing'
    assert len(tarot_section['evidence']['tarot']['cards']) == 2
    assert palm_section['evidence']['palm']['signals'][0]['feature'] == 'Heart line'
    assert payload['metadata']['evidence']['tarot']['cards'][0]['card'] == 'The Chariot'
