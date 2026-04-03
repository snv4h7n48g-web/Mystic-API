from sit.validators import validate_preview_payload


def test_combined_preview_validator_accepts_minimal_valid_payload() -> None:
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
    }

    result = validate_preview_payload(case_id="combined_preview", product_key="full_reading", payload=payload)

    assert result.status == "passed"
    assert "preview_meta_complete" in result.checks


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
