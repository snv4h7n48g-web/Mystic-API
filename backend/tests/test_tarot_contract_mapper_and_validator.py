from generation.product_contracts import get_product_contract
from generation.products.tarot.mapper import map_tarot_reading
from generation.validators import validate_product_payload
from generation.types import NormalizedMysticOutput


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
