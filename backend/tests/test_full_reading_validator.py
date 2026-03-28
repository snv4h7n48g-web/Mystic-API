from generation.validators import validate_product_payload


def test_full_reading_validator_flags_stub_guidance():
    payload = {
        'sections': [
            {'id': 'opening_hook', 'text': 'Opening text'},
            {'id': 'practical_guidance', 'text': '1.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is False
    assert 'full_reading_stub_guidance' in result.issues
    assert result.retry_hint is not None


def test_full_reading_validator_accepts_real_guidance():
    payload = {
        'sections': [
            {'id': 'practical_guidance', 'text': 'Start by naming the pattern without trying to fix it instantly, then choose one small boundary you can actually hold this week.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is True
