from generation.validators import validate_product_payload


def test_full_reading_validator_flags_stub_guidance() -> None:
    payload = {
        'sections': [
            {'id': 'opening_hook', 'text': 'Opening text'},
            {'id': 'what_this_is_asking_of_you', 'text': 'This is asking you to slow down and stop negotiating with a truth you already recognise.'},
            {'id': 'your_next_move', 'text': '1.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is False
    assert 'full_reading_stub_next_move_section' in result.issues
    assert result.retry_hint is not None


def test_full_reading_validator_flags_dangling_numbered_guidance() -> None:
    payload = {
        'sections': [
            {'id': 'what_this_is_asking_of_you', 'text': 'This is asking you to honour the discomfort instead of fleeing it the moment it asks something real of you.'},
            {'id': 'your_next_move', 'text': 'To navigate this intricate terrain, consider these steps: 1.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is False
    assert 'full_reading_stub_next_move_section' in result.issues


def test_full_reading_validator_flags_duplicate_payoff_sections() -> None:
    payload = {
        'sections': [
            {'id': 'what_this_is_asking_of_you', 'text': 'Choose the conversation you keep postponing and let honesty lead instead of performance.'},
            {'id': 'your_next_move', 'text': 'Choose the conversation you keep postponing and let honesty lead instead of performance.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is False
    assert 'full_reading_duplicate_payoff_sections' in result.issues


def test_full_reading_validator_accepts_real_two_part_payoff() -> None:
    payload = {
        'sections': [
            {'id': 'what_this_is_asking_of_you', 'text': 'This reading is asking you to stop treating clarity like a luxury and start treating it like a responsibility. The deeper shift here is less about doing more and more about refusing the emotional bargain that keeps you half-committed.'},
            {'id': 'your_next_move', 'text': 'Make one clean decision in the next twenty-four hours that removes ambiguity from the situation you already know is draining you. Keep the move small enough to complete, but definite enough that your nervous system can feel the difference.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is True


def test_full_reading_validator_keeps_legacy_guidance_compatible() -> None:
    payload = {
        'sections': [
            {'id': 'practical_guidance', 'text': 'Start by naming the pattern without trying to fix it instantly, then choose one small boundary you can actually hold this week. Let one decision become the proof that your clarity matters more than your urgency.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is True
