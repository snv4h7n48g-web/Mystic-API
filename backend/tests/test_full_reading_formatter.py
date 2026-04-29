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

    sections_by_id = {section['id']: section for section in payload['sections']}
    assert sections_by_id['what_this_is_asking_of_you']['headline'].startswith('stop waiting for perfect certainty')
    assert sections_by_id['what_this_is_asking_of_you']['detail'].startswith('before you honour what you already know')
    assert sections_by_id['your_next_move']['headline'].startswith('send the message')


def test_build_full_reading_payload_emits_layered_sections_and_modality_evidence() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A threshold is here.',
            current_pattern='You are outgrowing the version of this question that let you stall.',
            emotional_truth='Part of you wants proof before movement, but the pressure is already the proof.',
            reading_opening='A threshold is here. The reading points to a choice that already has emotional weight.',
            astrological_foundation='Your Virgo Sun and Capricorn Moon make this a question where discernment and emotional restraint easily turn into over-management.',
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
        astrology_facts={
            'sun_sign': 'Virgo',
            'moon_sign': 'Capricorn',
            'rising_sign': 'Leo',
            'dominant_element': 'Earth',
        },
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
    astro_section = next(section for section in payload['sections'] if section['id'] == 'astrological_foundation')

    assert opening_section['headline']
    assert opening_section['detail']
    assert astro_section['headline']
    assert 'Virgo Sun and Capricorn Moon' in f"{astro_section['headline']} {astro_section['text']}"
    assert opening_section['default_expanded'] is True
    assert tarot_section['evidence']['tarot']['spread'] == 'present / crossing'
    assert len(tarot_section['evidence']['tarot']['cards']) == 2
    assert palm_section['evidence']['title'] == 'Supporting palm details'
    assert 'Heart Line speaks to emotional expression' in palm_section['evidence']['items'][0]
    assert payload['metadata']['evidence']['palm']['signals'][0]['feature'] == 'Heart Line'
    assert payload['metadata']['evidence']['tarot']['cards'][0]['card'] == 'The Chariot'


from generation.products.full_reading.validator import validate_full_reading_payload


def test_build_full_reading_payload_humanizes_palm_signals_and_rich_tarot_evidence() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A threshold is here.',
            current_pattern='A real choice is already active under the surface.',
            emotional_truth='You are split between control and movement.',
            reading_opening='A threshold is here. The question is no longer whether change is coming, but whether you will meet it directly.',
            palm_revelation='Your heart line and head line both show restraint that has become over-management. That matters because your question is less about missing information than how tightly you are holding the decision.',
            tarot_message='The Chariot in the present position shows available momentum. Two of Swords in the crossing position shows the protective stalemate. Together, the spread says movement is possible once you stop treating delay as wisdom.',
            signals_agree='Palm and tarot both point to control becoming a shield. The agreement is not that you lack feeling, but that you keep containing it until timing feels perfect.',
            what_this_is_asking_of_you='Let yourself act from earned clarity instead of waiting for emotional zero-risk conditions.',
            your_next_move='Write the decision in one sentence, then take the first visible step before the day ends.',
            next_return_invitation='Return after the first step lands.',
        ),
        metadata=_metadata(),
        question='Should I move forward?',
        tarot_payload={
            'spread': 'present / crossing',
            'cards': [
                {
                    'card': 'The Chariot',
                    'position': 'present',
                    'meaning': 'Momentum wants direction.',
                    'question_link': 'It shows the path is ready to move if you claim it.',
                },
            ],
        },
        palm_features=[
            {'label': 'heart_line', 'description': 'deep and curved', 'relevance': 'shows strong emotional investment', 'confidence_label': 'high'},
        ],
        include_palm=True,
    )

    palm_signal = payload['metadata']['evidence']['palm']['signals'][0]
    tarot_card = next(section for section in payload['sections'] if section['id'] == 'tarot_message')['evidence']['tarot']['cards'][0]
    assert 'palm' not in next(section for section in payload['sections'] if section['id'] == 'palm_revelation').get('evidence', {})
    assert palm_signal['display_name'] == 'Heart Line'
    assert palm_signal['icon_key'] == 'heart_line'
    assert 'speaks to emotional expression' in palm_signal['interpretation']
    assert tarot_card['question_link'] == 'It shows the path is ready to move if you claim it.'


def test_build_full_reading_payload_does_not_append_template_tarot_when_model_already_interprets_spread() -> None:
    tarot_message = (
        "This card reversed often points to a time when choices about relationships or identity were made under pressure, "
        "or when harmony came at a cost. It may be that your deep investment in Finn's social inclusion is partly shaped "
        "by something you once lacked or lost. The Ace of Pentacles reversed in the Present position is striking. Aces are "
        "seeds, and Pentacles are the material world - health, security, tangible results. Reversed, this card suggests "
        "that the new beginning you are hoping for feels blocked or delayed. This is not a warning of failure; it is a "
        "reflection of timing. The Ten of Wands upright in the Guidance position is the heart of this spread. This card "
        "shows a figure carrying an enormous burden, nearly overwhelmed but still moving forward. As guidance, it does "
        "not tell you to drop everything - it tells you to notice what you are carrying that is not yours to carry."
    )
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A tender question is active.',
            current_pattern='You are trying to hold love and uncertainty at the same time.',
            emotional_truth='The pressure is care becoming responsibility for an outcome you cannot fully control.',
            reading_opening='A tender question is active.',
            tarot_message=tarot_message,
            signals_agree='The cards keep pointing to care without over-carrying.',
            what_this_is_asking_of_you='Stay available without making yourself responsible for every future result.',
            your_next_move='Name the support that is actually yours to offer this week.',
            next_return_invitation='Return when the next concrete social step has happened.',
        ),
        metadata=_metadata(),
        question='Will Finn grow up to be a happy socially included, well rounded individual?',
        tarot_payload={
            'spread': 'past / present / guidance',
            'cards': [
                {'card': 'The Lovers', 'position': 'Past', 'orientation': 'reversed'},
                {'card': 'Ace of Pentacles', 'position': 'Present', 'orientation': 'reversed'},
                {'card': 'Ten of Wands', 'position': 'Guidance', 'orientation': 'upright'},
            ],
        },
    )

    tarot_section = next(section for section in payload['sections'] if section['id'] == 'tarot_message')
    tarot_rendered = f"{tarot_section['headline']} {tarot_section['text']}"

    assert 'The Ace of Pentacles reversed in the Present position is striking' in tarot_rendered
    assert 'The Ten of Wands upright in the Guidance position is the heart of this spread' in tarot_rendered
    assert 'it matters because it matters because' not in tarot_rendered
    assert 'lands as the pattern' not in tarot_rendered
    assert 'For this question, it matters because' not in tarot_rendered
    assert 'Taken together, the spread reads like a sequence' not in tarot_rendered
    assert 'pile of symbols' not in tarot_rendered


def test_build_full_reading_payload_upgrades_raw_palm_and_shallow_tarot_supporting_detail() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A threshold is here.',
            current_pattern='You already know this question is active.',
            emotional_truth='The tension is between caution and momentum.',
            reading_opening='A threshold is here. The pattern is ready to move.',
            palm_revelation='',
            tarot_message='Movement and hesitation are both present.',
            signals_agree='The pattern is asking for a direct step.',
            what_this_is_asking_of_you='Stop treating delay as wisdom.',
            your_next_move='Send the message today.',
            next_return_invitation='Return after the move lands.',
        ),
        metadata=_metadata(),
        question='Should I move forward?',
        tarot_payload={
            'spread': 'present / crossing',
            'cards': [
                {'card': 'The Chariot', 'position': 'present', 'meaning': 'available momentum', 'question_link': 'the path is ready if you claim it'},
                {'card': 'Two of Swords', 'position': 'crossing', 'meaning': 'protective stalemate', 'question_link': 'delay is acting like self-protection'},
            ],
        },
        palm_features=[
            {'label': 'head_line', 'description': 'straight and clear', 'relevance': 'you are controlling uncertainty through analysis', 'confidence_label': 'high'},
        ],
        include_palm=True,
    )

    palm_section = next(section for section in payload['sections'] if section['id'] == 'palm_revelation')
    tarot_section = next(section for section in payload['sections'] if section['id'] == 'tarot_message')
    tarot_rendered = f"{tarot_section['headline']} {tarot_section['text']}"

    assert 'Head Line speaks to decision-making style' in f"{palm_section['headline']} {palm_section['text']}"
    assert palm_section['evidence']['title'] == 'Supporting palm details'
    assert 'Taken together, the cards create one movement rather than two separate ideas' in tarot_rendered
    assert 'The Chariot in the present position lands as the live pressure point in the present moment, speaking to available momentum' in tarot_rendered
    assert 'Cards in view:' not in tarot_rendered
    assert 'items' not in tarot_section.get('evidence', {})


def test_build_full_reading_payload_keeps_tarot_story_distinct_from_card_lines() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='Something important is already moving.',
            current_pattern='The question has passed the point of being theoretical.',
            emotional_truth='You are torn between self-protection and directness.',
            reading_opening='Something important is already moving.',
            tarot_message='The cards show a tension between leaving, evasion, and truth-telling.',
            signals_agree='The deeper pattern is avoidance pretending to be caution.',
            what_this_is_asking_of_you='Stop confusing delay with discernment.',
            your_next_move='Say the truest sentence you have been editing down.',
            next_return_invitation='Come back after the conversation happens.',
        ),
        metadata=_metadata(),
        question='What am I not admitting about this decision?',
        tarot_payload={
            'spread': 'past / present / guidance',
            'cards': [
                {'card': 'Eight of Cups', 'position': 'past', 'meaning': 'walking away from what no longer felt emotionally honest', 'question_link': 'part of you already knows something has been outgrown'},
                {'card': 'Seven of Swords', 'position': 'present', 'meaning': 'strategic avoidance and partial truth', 'question_link': 'you are managing the decision instead of naming it cleanly'},
                {'card': 'The Hierophant', 'position': 'guidance', 'meaning': 'truth, principle, and the structure that keeps you aligned', 'question_link': 'the way through is to act from your real values instead of tactical comfort'},
            ],
        },
    )

    tarot_section = next(section for section in payload['sections'] if section['id'] == 'tarot_message')
    tarot_meta = tarot_section['evidence']['tarot']
    tarot_rendered = f"{tarot_section['headline']} {tarot_section['text']}"
    assert tarot_meta['combined_interpretation']
    assert 'Eight of Cups in the past position lands as the pattern that has already been shaping this question, speaking to walking away from what no longer felt emotionally honest' in tarot_rendered
    assert 'Seven of Swords in the present position lands as the live pressure point in the present moment, speaking to strategic avoidance and partial truth' in tarot_rendered
    assert 'The Hierophant in the guidance position lands as the response the spread is steering you toward, speaking to truth, principle, and the structure that keeps you aligned' in tarot_rendered
    assert 'Taken together, the spread reads like a sequence' in tarot_meta['combined_interpretation']
    assert 'pile of symbols' not in tarot_meta['combined_interpretation']
    assert tarot_meta['combined_interpretation'] != tarot_section['detail']
    assert payload['metadata']['evidence']['tarot']['combined_interpretation'] == tarot_meta['combined_interpretation']


def test_build_full_reading_payload_uses_guidebook_reversed_major_arcana_meaning() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='The pattern is ready to break.',
            current_pattern='You are close to dropping an old attachment.',
            emotional_truth='Part of you knows the grip is weakening.',
            reading_opening='The pattern is ready to break.',
            tarot_message='This spread is about release.',
            signals_agree='The old bind is losing power.',
            what_this_is_asking_of_you='Stop negotiating with what you already know is unhealthy.',
            your_next_move='Name the pattern and interrupt it once today.',
            next_return_invitation='Come back once the spell is weaker.',
        ),
        metadata=_metadata(),
        question='Why am I still stuck here?',
        tarot_payload={
            'spread': 'past / present / guidance',
            'cards': [
                {'card': 'The Devil', 'position': 'past', 'orientation': 'reversed'},
            ],
        },
    )

    tarot_section = next(section for section in payload['sections'] if section['id'] == 'tarot_message')
    tarot_rendered = f"{tarot_section['headline']} {tarot_section['text']}"

    assert 'The Devil reversed in the past position' in tarot_rendered
    assert 'release, liberation, or overcoming addiction' in tarot_rendered


def test_build_full_reading_payload_populates_interpretive_palm_metadata() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A threshold is here.',
            current_pattern='You already know the question is live.',
            emotional_truth='The pressure is about control versus trust.',
            reading_opening='A threshold is here.',
            astrological_foundation='Your Libra rising and Capricorn Moon make you look steadier than you feel, so the tension gets managed before it gets admitted.',
            palm_revelation='',
            tarot_message='Movement and hesitation are both present.',
            signals_agree='The pattern is asking for a direct step.',
            what_this_is_asking_of_you='Stop treating delay as wisdom.',
            your_next_move='Send the message today.',
            next_return_invitation='Return after the move lands.',
        ),
        metadata=_metadata(),
        astrology_facts={
            'moon_sign': 'Capricorn',
            'rising_sign': 'Libra',
        },
        question='Should I move forward?',
        palm_features=[
            {'label': 'heart_line', 'description': 'deep and curved', 'relevance': 'shows strong emotional investment', 'confidence_label': 'high'},
            {'label': 'head_line', 'description': 'straight and clear', 'relevance': 'shows control through analysis', 'confidence_label': 'high'},
        ],
        include_palm=True,
    )

    palm_meta = payload['metadata']['evidence']['palm']
    assert palm_meta['interpretation']
    assert 'speaks to emotional expression' in palm_meta['interpretation']
    assert palm_meta['question_relevance'] != 'Should I move forward?'
    assert 'This is really about whether you should move forward' in palm_meta['question_relevance']


def test_build_full_reading_payload_keeps_single_sentence_headlines_non_duplicate() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A threshold is here.',
            current_pattern='You already know the question is live.',
            emotional_truth='The pressure is about control versus trust.',
            reading_opening='A threshold is here.',
            astrological_foundation='Your Libra rising and Capricorn Moon make you look steadier than you feel, so the tension gets managed before it gets admitted.',
            tarot_message='Movement and hesitation are both present.',
            signals_agree='The pattern is asking for a direct step.',
            what_this_is_asking_of_you='Stop treating delay as wisdom.',
            your_next_move='Send the message today.',
            next_return_invitation='Return after the move lands.',
        ),
        metadata=_metadata(),
        astrology_facts={
            'moon_sign': 'Capricorn',
            'rising_sign': 'Libra',
        },
    )

    opening_section = next(section for section in payload['sections'] if section['id'] == 'reading_opening')
    astro_section = next(section for section in payload['sections'] if section['id'] == 'astrological_foundation')
    assert opening_section['headline'] == 'A threshold is here.'
    assert opening_section['detail'] == 'It sets up the larger pattern the rest of the reading will unpack.'
    assert opening_section['headline'] != opening_section['detail']
    assert astro_section['headline'].startswith('Your Libra rising and Capricorn Moon make you look steadier than you feel')


def test_build_full_reading_payload_enriches_sparse_tarot_cards_and_next_move() -> None:
    payload = build_full_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A threshold is here.',
            current_pattern='The question is already active.',
            emotional_truth='The deeper pressure is clarity without motion.',
            reading_opening='A threshold is here. This reading is trying to turn hesitation into something readable.',
            astrological_foundation='Your Virgo Sun and Capricorn Moon make patience look responsible, even after it becomes delay.',
            tarot_message='The spread is active and already naming the tension.',
            signals_agree='The pattern is less about missing information and more about stopping the drift.',
            what_this_is_asking_of_you='Stop treating the right answer like it needs another round of emotional negotiation.',
            your_next_move='Move with clarity.',
            next_return_invitation='Return after the first move lands.',
        ),
        metadata=_metadata(),
        question='Should I move forward?',
        tarot_payload={
            'spread': 'past / present / guidance',
            'cards': [
                {'card': 'Eight of Cups', 'position': 'past'},
                {'card': 'Seven of Swords', 'position': 'present'},
                {'card': 'The Hierophant', 'position': 'guidance'},
            ],
        },
    )

    tarot_cards = payload['metadata']['evidence']['tarot']['cards']
    next_move_section = next(section for section in payload['sections'] if section['id'] == 'your_next_move')
    next_move_rendered = f"{next_move_section['headline']} {next_move_section['detail']}"

    assert all(card['interpretation'] for card in tarot_cards)
    assert all(card['question_link'] for card in tarot_cards)
    assert 'Start by naming the clearest decision you can make about whether you should move forward' in next_move_rendered
    assert validate_full_reading_payload(payload) == []


def test_validate_full_reading_payload_flags_shallow_tarot_and_raw_palm_labels() -> None:
    payload = {
        'sections': [
            {'id': 'reading_opening', 'headline': 'Opening', 'detail': 'A real threshold is here and it matters now.'},
            {
                'id': 'palm_revelation',
                'headline': 'Palm',
                'detail': 'The palm evidence matters for this question because it shows how you are carrying the pressure.',
                'evidence': {
                    'palm': {
                        'signals': [
                            {'feature': 'heart_line', 'observation': '', 'relevance': '', 'confidence': 'high'},
                        ],
                    },
                },
            },
            {
                'id': 'tarot_message',
                'headline': 'Tarot',
                'detail': 'The Chariot and Two of Swords appear in a spread together around this question.',
                'evidence': {
                    'tarot': {
                        'spread': 'present / crossing',
                        'combined_interpretation': 'The Chariot means motion.',
                        'cards': [
                            {'card': 'The Chariot', 'position': 'present', 'interpretation': 'motion'},
                        ],
                    },
                },
            },
            {'id': 'signals_agree', 'headline': 'Agree', 'detail': 'These signals agree that you need movement without overthinking every variable first.'},
            {'id': 'what_this_is_asking_of_you', 'headline': 'Ask', 'detail': 'Trust the clarity you already earned and stop using delay as emotional protection.'},
            {'id': 'your_next_move', 'headline': 'Move', 'detail': 'Send the message today and set one firm boundary before you revisit the situation.'},
        ],
        'metadata': {'modalities': {'includes_palm': True}},
        'snapshot': {'core_theme': 'Choice is active.', 'main_tension': 'Control versus movement.', 'best_next_move': 'Send the message.'},
    }

    issues = validate_full_reading_payload(payload)
    assert 'full_reading_palm_section_missing_question_link' in issues
    assert 'full_reading_palm_section_missing_signal_state' in issues
    assert 'full_reading_palm_section_non_human_labels' in issues
    assert 'full_reading_tarot_shallow_card_expansion' in issues
    assert 'full_reading_tarot_missing_question_link' in issues
