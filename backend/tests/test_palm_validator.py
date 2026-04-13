from generation.validators import validate_product_payload


def test_palm_validator_rejects_literal_uninterpreted_supporting_detail() -> None:
    payload = {
        'sections': [
            {
                'id': 'palm_insight',
                'text': 'The life line is long. The heart line is deep. The head line is curved. These visible lines are detected in the image.',
            },
            {
                'id': 'reflective_guidance',
                'text': 'Notice the hand.',
            },
        ]
    }

    result = validate_product_payload('palm', payload)

    assert result.passed is False
    assert 'palm_missing_interpretive_meaning' in result.issues
    assert 'palm_overly_literal_supporting_detail' in result.issues


def test_palm_validator_accepts_interpretive_feature_led_language() -> None:
    payload = {
        'sections': [
            {
                'id': 'palm_insight',
                'text': 'The deep heart line suggests emotional intensity that is usually managed rather than displayed, while the straighter head line points to a mind that tries to create certainty before it moves.',
            },
            {
                'id': 'reflective_guidance',
                'text': 'Let that combination mean something practical: name the feeling first, then choose the next action.',
            },
        ]
    }

    result = validate_product_payload('palm', payload)

    assert result.passed is True
