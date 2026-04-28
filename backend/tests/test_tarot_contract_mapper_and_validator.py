import json

from generation.parser import parse_normalized_output
from generation.product_contracts import get_product_contract
from generation.products.tarot.mapper import map_tarot_reading
from generation.products.tarot.reading import build_tarot_reading_payload
from generation.validators import validate_product_payload
from generation.types import GenerationMetadata, NormalizedMysticOutput


def test_tarot_contract_uses_tarot_specific_prompt_ids() -> None:
    contract = get_product_contract('tarot')
    assert contract is not None
    assert contract.prompt_ids == {
        'preview': 'tarot_preview',
        'reading': 'tarot_reading',
    }



def test_tarot_mapper_prefers_tarot_specific_fields_over_generic_fallbacks() -> None:
    mapped = map_tarot_reading(
        NormalizedMysticOutput(
            opening_hook='Generic opening hook.',
            current_pattern='Generic current pattern.',
            emotional_truth='Generic emotional truth.',
            practical_guidance='Generic practical guidance.',
            reading_opening='Tarot-specific opening invocation.',
            tarot_message='The Hermit in the spread asks for a slower, more discerning pace.',
            signals_agree='The cards and the wider pattern agree that solitude is clarifying, not punishing.',
            what_this_is_asking_of_you='Let space become part of the answer instead of a sign that nothing is happening.',
            your_next_move='Block one quiet hour and write down what becomes obvious when urgency leaves the room.',
            next_return_invitation='Return after the stillness has had time to speak.',
        )
    )

    assert mapped['opening_invocation'] == 'Tarot-specific opening invocation.'
    assert mapped['tarot_narrative'] == 'The Hermit in the spread asks for a slower, more discerning pace.'
    assert mapped['integrated_synthesis'] == 'The cards and the wider pattern agree that solitude is clarifying, not punishing.'
    assert mapped['reflective_guidance'] == 'Let space become part of the answer instead of a sign that nothing is happening.'
    assert mapped['closing_prompt'] == 'Return after the stillness has had time to speak.'



def test_tarot_validator_rejects_missing_guidance() -> None:
    payload = {
        'sections': [
            {'id': 'opening_invocation', 'text': 'The spread opens with a quiet but serious threshold.'},
            {'id': 'tarot_narrative', 'text': 'The Hermit in the guidance position and the Moon beneath it show a card-led spread where discernment matters more than speed.'},
        ]
    }

    result = validate_product_payload('tarot', payload)

    assert result.passed is False
    assert 'tarot_missing_guidance_section' in result.issues
    assert result.retry_hint is not None



def test_tarot_validator_rejects_duplicate_opening_and_narrative() -> None:
    repeated = 'The Hermit in the spread asks you to slow down, trust solitude, and listen for what urgency is drowning out.'
    payload = {
        'sections': [
            {'id': 'opening_invocation', 'text': repeated},
            {'id': 'tarot_narrative', 'text': repeated + ' The card symbolism points to retreat becoming revelation.'},
            {'id': 'reflective_guidance', 'text': 'Protect one pocket of silence today and let that become your next true decision point.'},
        ]
    }

    result = validate_product_payload('tarot', payload)

    assert result.passed is False
    assert 'tarot_opening_narrative_repetition' in result.issues



def test_tarot_validator_rejects_shallow_narrative_and_guidance() -> None:
    payload = {
        'sections': [
            {'id': 'opening_invocation', 'text': 'The spread opens on a threshold.'},
            {'id': 'tarot_narrative', 'text': 'The Hermit card suggests reflection in this spread.'},
            {'id': 'reflective_guidance', 'text': 'Stay open and trust the universe.'},
        ]
    }

    result = validate_product_payload('tarot', payload)

    assert result.passed is False
    assert 'tarot_narrative_too_shallow' in result.issues
    assert 'tarot_guidance_too_shallow' in result.issues
    assert 'tarot_guidance_generic_filler' in result.issues
    assert 'tarot_guidance_missing_action' in result.issues
    assert 'tarot_narrative_missing_card_contribution_depth' in result.issues



def test_tarot_validator_rejects_light_repetitive_card_restatement() -> None:
    payload = {
        'sections': [
            {
                'id': 'opening_invocation',
                'text': 'The spread opens with pressure around a decision that already has emotional weight.',
            },
            {
                'id': 'tarot_narrative',
                'text': 'The Chariot and Two of Swords appear in the spread. The Chariot means movement and Two of Swords means hesitation. The spread is about movement and hesitation.',
            },
            {
                'id': 'integrated_synthesis',
                'text': 'Together the cards point to a decision you keep delaying because acting would make the truth visible.',
            },
            {
                'id': 'reflective_guidance',
                'text': 'Name the decision in one sentence, then send one message before tonight ends so delay stops pretending to be wisdom.',
            },
        ]
    }

    result = validate_product_payload('tarot', payload)

    assert result.passed is False
    assert 'tarot_narrative_missing_card_contribution_depth' in result.issues



def _metadata() -> GenerationMetadata:
    return GenerationMetadata(
        persona_id='ancient_tarot_reader',
        llm_profile_id='tarot_reading',
        prompt_version='test',
        model_id='test-model',
        theme_tags=['tarot'],
        headline='Tarot',
    )


def _tarot_payload() -> dict:
    return {
        'spread': 'Past / Present / Guidance',
        'cards': [
            {
                'card': 'The Hermit',
                'position': 'Past',
                'orientation': 'upright',
                'interpretation': 'discernment, solitude, and refusing noisy answers',
                'question_link': 'your question is shaped by a prior season of stepping back to hear yourself clearly',
            },
            {
                'card': 'Two of Wands',
                'position': 'Present',
                'orientation': 'upright',
                'interpretation': 'planning, tension between known ground and a wider horizon',
                'question_link': 'you are standing between staying safe and choosing a direction that asks for visible commitment',
            },
            {
                'card': 'The Moon',
                'position': 'Guidance',
                'orientation': 'reversed',
                'interpretation': 'confusion beginning to drain away, but only if fear is named directly',
                'question_link': 'the answer depends on separating intuition from anxiety before you act',
            },
        ],
    }


def test_parse_normalized_output_accepts_tarot_card_chapters() -> None:
    normalized = parse_normalized_output(
        json.dumps(
            {
                'opening_hook': 'The spread opens around a choice that deserves quieter attention.',
                'current_pattern': 'The cards show a move from solitude into deliberate direction.',
                'emotional_truth': 'The deeper pressure is the fear of choosing before every uncertainty has cleared.',
                'practical_guidance': 'Write the choice plainly, name the fear underneath it, and take one low-risk step before the day ends.',
                'tarot_spread_overview': 'This Past, Present, Guidance spread reads like a lantern, a map, and a mist lifting.',
                'tarot_card_chapters': [
                    {
                        'card': 'The Hermit',
                        'position': 'Past',
                        'orientation': 'upright',
                        'card_meaning': 'solitude that sharpens discernment',
                        'position_meaning': 'In the past position, The Hermit describes the pattern that prepared the current choice.',
                        'question_relevance': 'your question has already been shaped by what became obvious in private',
                        'personal_implication': 'You do not need to apologize for needing quiet before movement.',
                    }
                ],
                'tarot_spread_story': 'The spread moves from withdrawal, into planning, then into fear becoming visible enough to work with.',
                'theme_tags': ['tarot'],
            }
        )
    )

    assert normalized.tarot_spread_overview.startswith('This Past, Present, Guidance spread')
    assert normalized.tarot_card_chapters == [
        {
            'card': 'The Hermit',
            'position': 'Past',
            'orientation': 'upright',
            'card_meaning': 'solitude that sharpens discernment',
            'position_meaning': 'In the past position, The Hermit describes the pattern that prepared the current choice.',
            'question_relevance': 'your question has already been shaped by what became obvious in private',
            'personal_implication': 'You do not need to apologize for needing quiet before movement.',
        }
    ]
    assert normalized.tarot_spread_story.startswith('The spread moves from withdrawal')


def test_tarot_reading_payload_splits_summary_from_deeper_body() -> None:
    payload = build_tarot_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='A tarot threshold is opening.',
            current_pattern='A pause is becoming preparation.',
            emotional_truth='You already know the pace needs to change.',
            reading_opening='The spread opens like a lantern being raised in a dark room. It clarifies the choice without pretending the choice is easy.',
            tarot_message='The Hermit in the present position slows the whole spread down and asks for deliberate distance from noise. Beside it, the Two of Wands shifts the message from withdrawal to planning, showing that solitude is meant to sharpen choice rather than delay it.',
            signals_agree='Taken together, the cards show that clarity arrives when you stop treating urgency as proof and start treating perspective as evidence.',
            what_this_is_asking_of_you='Let the pause become preparation instead of avoidance.',
            next_return_invitation='Return after the stillness has had time to speak.',
        ),
        metadata=_metadata(),
    )

    narrative = next(section for section in payload['sections'] if section['id'] == 'tarot_narrative')
    assert narrative['text'] == 'The Hermit in the present position slows the whole spread down and asks for deliberate distance from noise.'
    assert 'Two of Wands shifts the message from withdrawal to planning' in narrative['detail']
    assert narrative['detail'] != narrative['text']


def test_tarot_reading_payload_builds_three_card_chapter_flow() -> None:
    payload = build_tarot_reading_payload(
        normalized=NormalizedMysticOutput(
            opening_hook='The spread opens around a choice that deserves quieter attention.',
            current_pattern='The cards show a move from solitude into deliberate direction.',
            emotional_truth='The deeper pressure is the fear of choosing before every uncertainty has cleared.',
            practical_guidance='Write the choice plainly, name the fear underneath it, and take one low-risk step before the day ends.',
            tarot_spread_overview='This Past, Present, Guidance spread reads like a lantern, a map, and a mist lifting: first what prepared you, then what asks for commitment, then what must be named before you move.',
            tarot_card_chapters=[
                {
                    'card': 'The Hermit',
                    'position': 'Past',
                    'orientation': 'upright',
                    'card_meaning': 'solitude that sharpens discernment',
                    'position_meaning': 'In the past position, The Hermit describes the pattern that prepared this question by teaching you to distrust noisy answers.',
                    'reversal_message': 'Because it is upright, its lantern is available as a clear method rather than a blocked retreat.',
                    'question_relevance': 'your question has already been shaped by what became obvious in private',
                    'personal_implication': 'You are not starting from nothing; you are carrying evidence gathered in quiet, and that evidence deserves more authority than the loudest pressure in the room.',
                },
                {
                    'card': 'Two of Wands',
                    'position': 'Present',
                    'orientation': 'upright',
                    'card_meaning': 'planning at the edge of a wider horizon',
                    'position_meaning': 'In the present position, Two of Wands makes the card role practical: it asks you to turn private clarity into an actual direction.',
                    'reversal_message': 'Because it is upright, the choice can be organised instead of dramatised.',
                    'question_relevance': 'you are choosing between known safety and a direction that asks for visible commitment',
                    'personal_implication': 'The task is not to leap blindly; it is to pick the path you can support with one concrete move.',
                },
                {
                    'card': 'The Moon',
                    'position': 'Guidance',
                    'orientation': 'reversed',
                    'card_meaning': 'confusion draining away once fear is named',
                    'position_meaning': 'In the guidance position, The Moon reversed shows the spread steering you toward honest sorting rather than fantasy or panic.',
                    'reversal_message': 'Because it is reversed, the orientation points to a blocked fog beginning to clear, but only when anxiety is not allowed to masquerade as intuition.',
                    'question_relevance': 'the answer depends on separating intuition from anxiety before you act',
                    'personal_implication': 'Do not wait for perfect certainty; wait only long enough to name the fear, then let the next move be modest and real.',
                },
            ],
            tarot_spread_story='The Hermit gives the past its lantern, Two of Wands turns that light toward a choice, and The Moon reversed warns that the final obstacle is not mystery but unlabelled fear. Together the cards tell a coherent story: private knowing is ready to become planned movement, as long as anxiety is named before it is obeyed.',
        ),
        metadata=_metadata(),
        tarot_payload=_tarot_payload(),
        question='What am I not admitting about this decision?',
    )

    section_ids = [section['id'] for section in payload['sections']]
    assert section_ids[:5] == ['spread_overview', 'card_1', 'card_2', 'card_3', 'spread_story']
    assert 'The Moon reversed in the Guidance position' in payload['sections'][3]['headline']
    assert 'anxiety is not allowed to masquerade as intuition' in payload['sections'][3]['detail']
    assert payload['metadata']['evidence']['tarot']['cards'][2]['orientation'] == 'reversed'
    assert payload['metadata']['evidence']['tarot']['combined_interpretation'].startswith('The Hermit gives the past')

    result = validate_product_payload('tarot', payload)
    assert result.valid is True


def test_tarot_validator_accepts_detailed_card_led_payload() -> None:
    payload = {
        'sections': [
            {
                'id': 'opening_invocation',
                'text': 'The spread opens like a lantern being raised in a dark room: not dramatic, but unmistakably clarifying.',
            },
            {
                'id': 'tarot_narrative',
                'text': 'The Hermit in the present position slows the whole spread down and asks for deliberate distance from noise. Beside it, the Two of Wands shifts the message from withdrawal to planning, showing that solitude is meant to sharpen choice rather than delay it. Together these cards create a spread logic of pause first, direction second, so the reading is less about hiding and more about selecting the path that still feels true when pressure falls away.',
            },
            {
                'id': 'integrated_synthesis',
                'text': 'Taken together, the cards show that clarity arrives when you stop treating urgency as proof and start treating perspective as evidence.',
            },
            {
                'id': 'reflective_guidance',
                'text': 'Block thirty quiet minutes tonight, write down the two options still standing, and circle the one that feels stronger once the room is calm. Then send one message or take one small administrative step that commits you to that direction before tomorrow gets noisy again.',
            },
        ]
    }

    result = validate_product_payload('tarot', payload)

    assert result.valid is True


def test_tarot_validator_rejects_internal_duplication_even_when_card_names_are_present() -> None:
    payload = {
        'sections': [
            {'id': 'opening_invocation', 'text': 'The spread opens on a decision that already has weight.'},
            {
                'id': 'tarot_narrative',
                'text': 'The Hermit in the present position asks for distance from noise. The Hermit in the present position asks for distance from noise. Two of Wands in the future position suggests planning, and together the spread shows perspective turning into deliberate direction.',
            },
            {'id': 'reflective_guidance', 'text': 'Block one quiet hour tonight, write down the two live options, and send one message that commits you to the direction that still feels true after the room settles.'},
        ]
    }

    result = validate_product_payload('tarot', payload)

    assert result.passed is False
    assert 'tarot_narrative_internal_duplication' in result.issues
