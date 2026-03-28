from generation.product_contracts import get_product_contract


def test_full_reading_contract_is_registered():
    contract = get_product_contract('full_reading')

    assert contract is not None
    assert contract.prompt_ids['reading'] == 'session_reading'
    assert 'what_this_is_asking_of_you' in contract.expected_section_ids
    assert 'your_next_move' in contract.expected_section_ids
    assert 'practical_guidance' not in contract.expected_section_ids
