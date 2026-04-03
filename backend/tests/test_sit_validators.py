from sit.validators import validate_preview_payload


def test_combined_preview_validator_accepts_valid_full_reading_payload() -> None:
    payload = {
        "flow_type": "combined",
        "astrology_facts": {"sun_sign": "Aries"},
        "tarot": {"cards": [{"card": "The Fool"}]},
        "teaser_text": "A clear pattern is taking shape.",
        "unlock_price": {"currency": "USD", "amount": 2.99},
        "product_id": "reading_complete",
        "meta": {
            "persona_id": "premium_mystic",
            "llm_profile_id": "preview_mystic",
            "prompt_version": "mystic-v1",
            "theme_tags": ["clarity"],
            "headline": "A clear pattern is taking shape.",
        },
        "sections": [
            {"id": "reading_opening", "headline": "A threshold you can no longer dodge", "text": "The pattern around this question is becoming impossible to ignore, and it is asking you to stop treating your intuition like background noise while you decide what matters most."},
            {"id": "palm_revelation", "headline": "What your palm is echoing", "text": "Your palm shows a steady head line and a responsive heart line, which suggests you are balancing caution with feeling instead of acting purely on impulse.", "evidence": {"palm": {"signals": [{"display_name": "Heart line", "observation": "clear and responsive", "relevance": "shows emotional honesty around this question"}]}}},
            {"id": "tarot_message", "headline": "How the cards frame the choice", "text": "The Fool appears in the first position of the spread, and the card's symbolism points to a deliberate leap that still needs conscious grounding before you move.", "evidence": {"tarot": {"cards": [{"card": "The Fool", "interpretation": "This card invites a fresh start with awareness instead of denial.", "question_link": "It reflects the choice you already know you need to make."}], "combined_interpretation": "The Fool in this spread asks for courageous but conscious movement."}}},
            {"id": "signals_agree", "headline": "Where the evidence converges", "text": "Both the palm evidence and the tarot spread point to the same truth: you are ready for movement, but only if you stop outsourcing your certainty to timing or permission."},
            {"id": "what_this_is_asking_of_you", "headline": "The inner requirement", "text": "This is asking you to trust the insight you have already earned and to stop hiding inside endless preparation just because action feels emotionally expensive."},
            {"id": "your_next_move", "headline": "A move that changes the pattern", "text": "Choose one concrete action today that proves you are moving with intention: send the message, make the plan, or name the boundary instead of rehearsing it privately."},
        ],
        "metadata": {
            "includes_palm": True,
            "modalities": {"includes_palm": True},
        },
        "snapshot": {
            "core_theme": "A threshold is already here.",
            "main_tension": "You want certainty before movement.",
            "best_next_move": "Name one irreversible next step.",
        },
    }

    result = validate_preview_payload(case_id="combined_preview", product_key="full_reading", payload=payload)

    assert result.status == "passed"
    assert "preview_meta_complete" in result.checks
    assert "product_validator_passed" in result.checks


def test_combined_preview_validator_fails_on_structural_product_issues() -> None:
    payload = {
        "flow_type": "combined",
        "astrology_facts": {"sun_sign": "Aries"},
        "tarot": {"cards": [{"card": "The Fool"}]},
        "teaser_text": "A clear pattern is taking shape.",
        "unlock_price": {"currency": "USD", "amount": 2.99},
        "product_id": "reading_complete",
        "meta": {
            "persona_id": "premium_mystic",
            "llm_profile_id": "preview_mystic",
            "prompt_version": "mystic-v1",
            "theme_tags": ["clarity"],
            "headline": "A clear pattern is taking shape.",
        },
        "sections": [
            {"id": "reading_opening", "text": "A pattern is gathering."},
            {"id": "tarot_message", "text": "Trust the moment."},
            {"id": "signals_agree", "text": "Everything points the same way."},
            {"id": "what_this_is_asking_of_you", "text": "Be open."},
            {"id": "your_next_move", "text": "Wait."},
        ],
        "metadata": {
            "includes_palm": True,
            "modalities": {"includes_palm": True},
        },
        "snapshot": {
            "core_theme": "A pattern is gathering.",
            "main_tension": "Everything points the same way.",
            "best_next_move": "Wait.",
        },
    }

    result = validate_preview_payload(case_id="combined_preview", product_key="full_reading", payload=payload)

    assert result.status == "failed"
    assert "full_reading_missing_palm_section" in result.hard_failures
    assert "full_reading_vague_asking_section" in result.hard_failures
    assert "full_reading_vague_next_move_section" in result.hard_failures
    assert result.validator["passed"] is False


def test_compatibility_validator_downgrades_soft_issues_to_warnings() -> None:
    payload = {
        "teaser_text": "There is chemistry in this bond.",
        "unlock_price": {"currency": "USD", "amount": 3.99},
        "product_id": "compatibility",
        "meta": {
            "persona_id": "premium_mystic",
            "llm_profile_id": "preview_mystic",
            "prompt_version": "mystic-v1",
            "theme_tags": ["chemistry"],
            "headline": "There is chemistry in this bond.",
        },
        "sections": [
            {"id": "opening_hook", "text": "A relationship pattern is emerging."},
            {"id": "current_pattern", "text": "There is relationship chemistry here."},
            {"id": "emotional_truth", "text": "Trust is present."},
            {"id": "practical_guidance", "text": "Go slowly."},
            {"id": "next_return_invitation", "text": "Check back soon."},
        ],
    }

    result = validate_preview_payload(case_id="compatibility_preview", product_key="compatibility", payload=payload)

    assert result.status == "passed_with_warnings"
    assert "compatibility_missing_two_person_structure" in result.warnings
    assert not result.hard_failures
