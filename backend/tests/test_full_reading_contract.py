from generation.product_contracts import get_product_contract


def test_full_reading_contract_is_registered():
    contract = get_product_contract('full_reading')

    assert contract is not None
    assert contract.prompt_ids['reading'] == 'session_reading'
    assert 'practical_guidance' in contract.expected_section_ids
