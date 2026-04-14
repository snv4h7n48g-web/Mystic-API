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


def test_full_reading_validator_flags_repeated_opening_line_across_sections() -> None:
    repeated = 'The real shift begins when you stop calling this confusion.'
    payload = {
        'sections': [
            {'id': 'opening_hook', 'text': repeated + ' It is a threshold moment, not a fog.'},
            {'id': 'current_pattern', 'text': repeated + ' You have been circling the same emotional bargain instead of naming it.'},
            {'id': 'what_this_is_asking_of_you', 'text': 'This is asking you to stop protecting ambiguity when clarity already has a shape.'},
            {'id': 'your_next_move', 'text': 'Name the decision out loud today and remove one habit that keeps the situation conveniently unresolved.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is False
    assert any(issue.startswith('full_reading_repeated_opening_line:') for issue in result.issues)


def test_full_reading_validator_flags_heading_restatement() -> None:
    payload = {
        'sections': [
            {'id': 'what_this_is_asking_of_you', 'text': 'What this is asking of you: what this is asking of you is to trust yourself more deeply and completely.'},
            {'id': 'your_next_move', 'text': 'Choose one direct conversation before tonight and keep it specific enough to finish, not just begin.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is False
    assert 'full_reading_heading_body_repetition:what_this_is_asking_of_you' in result.issues


def test_full_reading_validator_accepts_real_two_part_payoff() -> None:
    payload = {
        'sections': [
            {'id': 'reading_opening', 'headline': 'A threshold is here.', 'detail': 'The pattern has become impossible to keep abstract, and the reading begins where avoidance stops working.'},
            {'id': 'astrological_foundation', 'headline': 'Your chart is already describing the bind.', 'detail': 'The Virgo Sun and Capricorn Moon combination suggests discernment and self-control are strengths here, but they can also turn into over-management when a decision starts to matter emotionally.'},
            {'id': 'tarot_message', 'headline': 'The cards show momentum fighting hesitation.', 'detail': 'The Chariot in the lead position and Two of Swords in tension show momentum fighting hesitation across the spread.'},
            {'id': 'signals_agree', 'headline': 'Every signal points to clarity arriving before comfort.', 'detail': 'Both the symbolic and emotional signals point to clarity already arriving before comfort catches up.'},
            {'id': 'what_this_is_asking_of_you', 'headline': 'Treat clarity like responsibility.', 'detail': 'This reading is asking you to stop treating clarity like a luxury and start treating it like a responsibility. The deeper shift here is less about doing more and more about refusing the emotional bargain that keeps you half-committed.'},
            {'id': 'your_next_move', 'headline': 'Cut the ambiguity within a day.', 'detail': 'Make one clean decision in the next twenty-four hours that removes ambiguity from the situation you already know is draining you. Keep the move small enough to complete, but definite enough that your nervous system can feel the difference.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is True


def test_full_reading_validator_flags_missing_card_level_interpretation_in_layered_evidence() -> None:
    payload = {
        'sections': [
            {'id': 'reading_opening', 'headline': 'A threshold is here.', 'detail': 'A threshold is here, and the pattern is ready to move.'},
            {
                'id': 'tarot_message',
                'headline': 'The cards show movement blocked by avoidance.',
                'detail': 'The Chariot and Two of Swords sit in tension across the spread positions and show motion fighting hesitation.',
                'evidence': {
                    'tarot': {
                        'spread': 'present / crossing',
                        'cards': [
                            {'card': 'The Chariot', 'position': 'present', 'interpretation': ''},
                            {'card': 'Two of Swords', 'position': 'crossing', 'interpretation': ''},
                        ],
                    },
                },
            },
            {'id': 'signals_agree', 'headline': 'Both signals point to overcontrol.', 'detail': 'Both signals point to overcontrol without fully duplicating the tarot section.'},
            {'id': 'what_this_is_asking_of_you', 'headline': 'Stop waiting for certainty.', 'detail': 'Stop waiting for certainty before you honour what you know.'},
            {'id': 'your_next_move', 'headline': 'Send the message.', 'detail': 'Send the message tonight and remove one source of ambiguity from the situation.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is False
    assert 'full_reading_tarot_missing_card_level_interpretation' in result.issues


def test_full_reading_validator_keeps_legacy_guidance_compatible() -> None:
    payload = {
        'sections': [
            {'id': 'practical_guidance', 'text': 'Start by naming the pattern without trying to fix it instantly, then choose one small boundary you can actually hold this week. Let one decision become the proof that your clarity matters more than your urgency.'},
        ]
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is True


def test_full_reading_validator_flags_non_interpretive_palm_section_even_with_metadata_signals() -> None:
    payload = {
        'sections': [
            {'id': 'reading_opening', 'headline': 'A threshold is here.', 'detail': 'A threshold is here and the pattern is ready to move.'},
            {
                'id': 'palm_revelation',
                'headline': 'Palm',
                'detail': 'The heart line is deep and curved. The head line is straight and clear.',
                'evidence': {'title': 'Supporting palm details', 'items': ['Heart Line — deep and curved', 'Head Line — straight and clear']},
            },
            {
                'id': 'tarot_message',
                'headline': 'The cards are active.',
                'detail': 'The Hermit in the present position and Two of Wands in the future position create a spread interaction where perspective becomes planning rather than delay.',
                'evidence': {'tarot': {'spread': 'present / future', 'cards': [
                    {'card': 'The Hermit', 'position': 'present', 'interpretation': 'discernment becomes clearer in solitude', 'question_link': 'you need space before choosing'},
                    {'card': 'Two of Wands', 'position': 'future', 'interpretation': 'planning replaces passive waiting', 'question_link': 'the decision wants direction rather than more speculation'},
                ]}},
            },
            {'id': 'signals_agree', 'headline': 'The overlap is real.', 'detail': 'Palm and tarot both point to hesitation becoming a habit instead of protection.'},
            {'id': 'what_this_is_asking_of_you', 'headline': 'Stop outsourcing clarity.', 'detail': 'This is asking you to trust your own read on the situation instead of waiting for another sign to carry the responsibility for you.'},
            {'id': 'your_next_move', 'headline': 'Act before the window closes.', 'detail': 'Write the decision in one sentence and send one message tonight so the pattern has to become concrete.'},
        ],
        'metadata': {
            'modalities': {'includes_palm': True},
            'evidence': {
                'palm': {
                    'signals': [
                        {'display_name': 'Heart Line', 'observation': 'deep and curved', 'relevance': 'shows strong emotional investment'},
                        {'display_name': 'Head Line', 'observation': 'straight and clear', 'relevance': 'shows control through analysis'},
                    ]
                }
            }
        },
        'snapshot': {'core_theme': 'Choice is active.', 'main_tension': 'Control versus movement.', 'best_next_move': 'Send the message.'},
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is False
    assert 'full_reading_palm_section_missing_interpretive_meaning' in result.issues


def test_full_reading_validator_flags_literal_palm_question_relevance() -> None:
    payload = {
        'sections': [
            {'id': 'reading_opening', 'headline': 'A threshold is here.', 'detail': 'A threshold is here and the pattern is ready to move.'},
            {
                'id': 'palm_revelation',
                'headline': 'Palm',
                'detail': 'The palm suggests control is shaping how you hold this decision, which matters because it mirrors the same hesitation that keeps the question alive.',
                'evidence': {'title': 'Supporting palm details', 'items': ['Heart Line - emotional control', 'Head Line - tight analysis']},
            },
            {
                'id': 'tarot_message',
                'headline': 'The cards are active.',
                'detail': 'The Hermit in the present position and Two of Wands in the future position create a spread interaction where perspective becomes planning rather than delay.',
                'evidence': {'tarot': {'spread': 'present / future', 'cards': [
                    {'card': 'The Hermit', 'position': 'present', 'interpretation': 'discernment becomes clearer in solitude', 'question_link': 'you need space before choosing'},
                    {'card': 'Two of Wands', 'position': 'future', 'interpretation': 'planning replaces passive waiting', 'question_link': 'the decision wants direction rather than more speculation'},
                ]}},
            },
            {'id': 'signals_agree', 'headline': 'The overlap is real.', 'detail': 'Palm and tarot both point to hesitation becoming a habit instead of protection.'},
            {'id': 'what_this_is_asking_of_you', 'headline': 'Stop outsourcing clarity.', 'detail': 'This is asking you to trust your own read on the situation instead of waiting for another sign to carry the responsibility for you.'},
            {'id': 'your_next_move', 'headline': 'Act before the window closes.', 'detail': 'Write the decision in one sentence and send one message tonight so the pattern has to become concrete.'},
        ],
        'metadata': {
            'modalities': {'includes_palm': True},
            'question': 'Should I move forward?',
            'evidence': {
                'palm': {
                    'question_relevance': 'Should I move forward?',
                    'signals': [
                        {'display_name': 'Heart Line', 'observation': 'deep and curved', 'relevance': 'shows strong emotional investment'},
                        {'display_name': 'Head Line', 'observation': 'straight and clear', 'relevance': 'shows control through analysis'},
                    ]
                }
            }
        },
        'snapshot': {'core_theme': 'Choice is active.', 'main_tension': 'Control versus movement.', 'best_next_move': 'Send the message.'},
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is False
    assert 'full_reading_palm_question_relevance_too_literal' in result.issues


def test_full_reading_validator_flags_missing_astrology_section() -> None:
    payload = {
        'sections': [
            {'id': 'reading_opening', 'headline': 'A threshold is here.', 'detail': 'A threshold is here and it already has emotional weight.'},
            {
                'id': 'tarot_message',
                'headline': 'The cards are active.',
                'detail': 'The Chariot in the present position and Two of Swords in the crossing position show momentum pressing against self-protection.',
                'evidence': {'tarot': {'spread': 'present / crossing', 'cards': [
                    {'card': 'The Chariot', 'position': 'present', 'interpretation': 'momentum wants direction', 'question_link': 'you are closer to action than you admit'},
                    {'card': 'Two of Swords', 'position': 'crossing', 'interpretation': 'indecision is acting like a shield', 'question_link': 'the pause is emotional, not informational'},
                ]}},
            },
            {'id': 'signals_agree', 'headline': 'The overlap is real.', 'detail': 'The pattern is not confusion so much as containment.'},
            {'id': 'what_this_is_asking_of_you', 'headline': 'Stop bargaining with clarity.', 'detail': 'This is asking you to trust the truth you already reached instead of asking for a cleaner emotional moment before acting.'},
            {'id': 'your_next_move', 'headline': 'Move before the window narrows.', 'detail': 'Send the message, make the call, or set the boundary today so the pattern has to become concrete.'},
        ],
        'metadata': {
            'modalities': {'includes_palm': False},
            'question': 'Should I move forward?',
        },
        'snapshot': {'core_theme': 'Choice is active.', 'main_tension': 'Control versus movement.', 'best_next_move': 'Send the message.'},
    }

    result = validate_product_payload('full_reading', payload)

    assert result.passed is False
    assert 'full_reading_missing_astrology_section' in result.issues
