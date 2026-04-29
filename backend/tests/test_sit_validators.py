from sit.validators import validate_preview_payload, validate_reading_payload


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
            {"id": "astrological_foundation", "headline": "The chart gives the choice a backbone", "text": "Your Aries Sun brings the fire to initiate, while the current emphasis on grounded timing asks that impulse to become strategy instead of reaction. The astrology does not remove the risk; it shows where courage needs structure so momentum can hold."},
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
    assert "preview_meta_complete:meta" in result.checks
    assert "product_validator_passed" in result.checks


def test_combined_preview_validator_accepts_generic_preview_envelope_without_full_sections() -> None:
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
            "prompt_version": "mystic-v3",
            "theme_tags": ["clarity"],
            "headline": "A clear pattern is taking shape.",
        },
    }

    result = validate_preview_payload(case_id="combined_preview", product_key="full_reading", payload=payload)

    assert result.status == "passed"
    assert "full_reading_product_validator_skipped_for_generic_preview_envelope" in result.checks
    assert result.validator["issues"] == []


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


def test_daily_preview_validator_accepts_generic_or_specialized_meta_shapes() -> None:
    payload = {
        "flow_type": "daily_horoscope",
        "teaser_text": "Today rewards clear prioritisation.",
        "unlock_price": {"currency": "USD", "amount": 1.99},
        "product_id": "daily_horoscope_unlock",
        "astrology_facts": {"sun_sign": "Virgo"},
        "metadata": {
            "persona_id": "premium_mystic",
            "llm_profile_id": "preview_mystic",
            "prompt_version": "mystic-v1",
            "theme_tags": ["focus"],
            "headline": "Today rewards clear prioritisation.",
        },
        "headline": "Today rewards clear prioritisation.",
        "today_energy": "Keep the day narrow and intentional.",
    }

    result = validate_preview_payload(case_id="daily_preview", product_key="daily", payload=payload)

    assert result.status == "passed"
    assert "preview_meta_complete:metadata" in result.checks
    assert "daily_product_validator_skipped_for_generic_preview_envelope" in result.checks


def test_tarot_preview_validator_accepts_generic_preview_envelope_without_full_tarot_sections() -> None:
    payload = {
        "flow_type": "tarot_solo",
        "teaser_text": "The spread is asking for patience with purpose.",
        "unlock_price": {"currency": "USD", "amount": 2.49},
        "product_id": "tarot_solo_unlock",
        "tarot": {"cards": [{"card": "The Hermit"}]},
        "meta": {
            "persona_id": "premium_mystic",
            "llm_profile_id": "preview_mystic",
            "prompt_version": "mystic-v1",
            "theme_tags": ["patience"],
            "headline": "The spread is asking for patience with purpose.",
        },
    }

    result = validate_preview_payload(case_id="tarot_solo_preview", product_key="tarot", payload=payload)

    assert result.status == "passed"
    assert "tarot_preview_generic_shape_accepted" in result.checks
    assert "tarot_product_validator_skipped_for_generic_preview_envelope" in result.checks
    assert result.validator["issues"] == []


def test_daily_reading_validator_allows_contract_subset_but_rejects_unknown_sections() -> None:
    payload = {
        "sections": [
            {
                "id": "today_theme",
                "headline": "Steady pacing beats reactive overreach.",
                "detail": "Start by narrowing the day to one useful priority instead of letting every message become equally loud. Your Virgo pattern works best when the plan is clean, visible, and small enough to finish before momentum gets diluted.",
                "text": "Steady pacing beats reactive overreach.",
            },
            {
                "id": "today_energy",
                "headline": "Your attention improves when input is reduced.",
                "detail": "The energy favors practical filtering: fewer tabs, fewer side conversations, and fewer half-promises. If you protect one block of uninterrupted time, the day becomes calmer because your nervous system can see what is actually being handled.",
                "text": "Your attention improves when input is reduced.",
            },
            {
                "id": "best_move",
                "headline": "Clear emotional noise with one concrete task.",
                "detail": "Choose the smallest task that removes friction before lunch, even if it is not the most impressive task. Send the clarifying note, tidy the open loop, or make the decision that stops the same thought from circling.",
                "text": "Clear emotional noise with one concrete task.",
            },
            {
                "id": "watch_out_for",
                "headline": "Urgency is not the same as importance.",
                "detail": "When messages pile up, pause before giving the loudest request automatic priority. The trap is reacting quickly to feel responsible, then ending the day with the meaningful work still untouched and quietly resented.",
                "text": "Urgency is not the same as importance.",
            },
            {
                "id": "people_energy",
                "headline": "Keep conversations specific and kind.",
                "detail": "People respond better when you name the actual need rather than implying it through stress. If a conversation starts to sprawl, bring it back to one question, one decision, or one clear next handoff.",
                "text": "Keep conversations specific and kind.",
            },
            {
                "id": "work_focus",
                "headline": "Finish the thing that reduces tomorrow's drag.",
                "detail": "Work flows best when you pick the task that will make the next twenty-four hours easier. Avoid polishing the visible surface while the underlying bottleneck remains untouched, especially if a practical admin step would release pressure.",
                "text": "Finish the thing that reduces tomorrow's drag.",
            },
            {
                "id": "timing",
                "headline": "Use the morning for planning and the afternoon for action.",
                "detail": "Morning favors sorting, prioritising, and deciding what does not deserve your attention today, especially before other people begin shaping the pace. Afternoon is better for sending, submitting, booking, or making the move that turns the plan into something outside your head.",
                "text": "Use the morning for planning and the afternoon for action.",
            },
            {
                "id": "closing_guidance",
                "headline": "Keep the day simple enough to stay embodied.",
                "detail": "Let the closing measure be steadiness, not how many fires you touched. If your body feels less braced tonight because you chose deliberately, the day has done its job even without dramatic progress.",
                "text": "Keep the day simple enough to stay embodied.",
            },
        ],
        "full_text": "Today asks for steady pacing. Keep the day simple enough that your body can stay with your decisions.",
        "metadata": {
            "persona_id": "premium_mystic",
            "llm_profile_id": "full_premium",
            "prompt_version": "mystic-v1",
            "theme_tags": ["focus"],
            "headline": "Today asks for steady pacing.",
            "flow_type": "daily_horoscope",
        },
    }

    result = validate_reading_payload(case_id="daily_full_reading", product_key="daily", payload=payload)

    assert result.status == "passed"
    assert "reading_sections_match_contract_subset" in result.checks


def test_reading_validator_prefers_richer_metadata_container_over_empty_meta() -> None:
    payload = {
        "meta": {},
        "sections": [
            {"id": "opening_hook", "text": "This relationship has chemistry and enough honesty to work with."},
            {"id": "current_pattern", "text": "Between you both, care and defensiveness are arriving in the same breath."},
            {"id": "emotional_truth", "text": "Each of you wants trust, but the bond gets tense when silence does the speaking."},
            {"id": "practical_guidance", "text": "Name the friction directly and keep the conversation grounded in one example at a time."},
            {"id": "next_return_invitation", "text": "Come back when the next layer of the connection is ready to be named."},
        ],
        "full_text": "Compatibility reading text.",
        "metadata": {
            "persona_id": "premium_mystic",
            "llm_profile_id": "full_premium",
            "prompt_version": "mystic-v1",
            "theme_tags": ["relationship"],
            "headline": "A relationship pattern is ready to be named.",
            "flow_type": "compatibility",
        },
    }

    result = validate_reading_payload(case_id="compatibility_full_reading", product_key="compatibility", payload=payload)

    assert result.status == "passed"
    assert "reading_meta_complete:metadata" in result.checks


def test_compatibility_reading_validator_enforces_contract_sections() -> None:
    payload = {
        "sections": [
            {"id": "opening_hook", "text": "This relationship has real chemistry and real friction."},
            {"id": "current_pattern", "text": "Between you both, intensity becomes care one day and control the next."},
            {"id": "emotional_truth", "text": "The bond is strong, but each of you misreads defensiveness as rejection."},
            {"id": "practical_guidance", "text": "Name the tension early and keep the conversation specific."},
        ],
        "full_text": "Compatibility reading text.",
        "metadata": {
            "persona_id": "premium_mystic",
            "llm_profile_id": "full_premium",
            "prompt_version": "mystic-v1",
            "theme_tags": ["relationship"],
            "headline": "A relationship pattern is ready to be named.",
            "flow_type": "compatibility",
        },
    }

    result = validate_reading_payload(case_id="compatibility_full_reading", product_key="compatibility", payload=payload)

    assert result.status == "failed"
    assert any(item.startswith("invalid:sections.expected=") for item in result.hard_failures)
