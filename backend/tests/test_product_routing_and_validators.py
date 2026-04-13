from generation.product_routing import get_product_route, resolve_product_key
from generation.validators import validate_product_payload


def test_daily_route_prefers_anthropic_text_lane_by_default() -> None:
    route = get_product_route(flow_type="daily_horoscope", surface="preview")
    assert resolve_product_key(flow_type="daily_horoscope") == "daily"
    assert route.product_key == "daily"
    assert route.persona_hint == "psychic_best_friend"
    assert "anthropic" in route.preview_model_id or route.preview_model_id == "us.amazon.nova-pro-v1:0"
    assert route.fallback_model_id.startswith("us.amazon.nova")


def test_full_reading_route_has_explicit_flagship_persona_hint() -> None:
    route = get_product_route(flow_type="combined", surface="reading")
    assert route.product_key == "full_reading"
    assert route.persona_hint == "flagship_mystic"


def test_lunar_validator_flags_daily_drift_and_duplicates() -> None:
    payload = {
        "sections": [
            {"id": "opening_invocation", "text": "Today's theme is to keep your energy steady."},
            {"id": "lunar_forecast", "text": "Today's theme is to keep your energy steady."},
        ]
    }
    result = validate_product_payload("lunar", payload)
    assert result.valid is False
    assert any(issue.startswith("lunar_daily_drift") for issue in result.issues)
    assert "lunar_duplicate_section_content" in result.issues


def test_daily_validator_flags_year_ahead_drift() -> None:
    payload = {
        "sections": [
            {"id": "today_theme", "text": "This year asks you to slow down and prepare for the months ahead."},
        ]
    }
    result = validate_product_payload("daily", payload)
    assert result.valid is False
    assert any(issue.startswith("daily_drift_detected") for issue in result.issues)


def test_daily_validator_flags_heading_body_repetition() -> None:
    payload = {
        "sections": [
            {"id": "today_theme", "text": "Today theme: today theme is patience and restraint."},
            {"id": "best_move", "text": "Choose the smallest decision that clears backlog before lunch."},
        ]
    }
    result = validate_product_payload("daily", payload)
    assert result.valid is False
    assert "daily_heading_body_repetition:today_theme" in result.issues


def test_daily_validator_flags_repeated_section_stems() -> None:
    payload = {
        "sections": [
            {"id": "today_theme", "text": "Today asks you to slow down before you answer anyone important."},
            {"id": "today_energy", "text": "Today asks you to slow down before you spend energy in the wrong place."},
            {"id": "best_move", "text": "Choose one clear priority and finish it before the afternoon fragments."},
        ]
    }
    result = validate_product_payload("daily", payload)
    assert result.valid is False
    assert any(issue.startswith("daily_repeated_section_stem:") for issue in result.issues)


def test_tarot_validator_requires_card_specific_structure() -> None:
    invalid_payload = {"sections": [{"id": "tarot_narrative", "text": "Trust yourself and stay positive."}]}
    invalid = validate_product_payload("tarot", invalid_payload)
    assert invalid.valid is False
    assert invalid.retry_hint is not None
    assert "tie each claim back to that card/spread evidence" in invalid.retry_hint
    assert "tarot_missing_card_specific_language" in invalid.issues

    valid_payload = {
        "sections": [
            {
                "id": "tarot_narrative",
                "text": "The Hermit in the guidance position sets the tone of the spread and asks for distance from noise before you decide. In interaction with the card-led structure, that retreat becomes discernment rather than avoidance, so the symbolism is doing more than naming solitude. The reading is showing how perspective changes the choice rather than delaying it.",
            },
            {
                "id": "reflective_guidance",
                "text": "Block one quiet hour tonight, write down the decision in plain language, and make one concrete move before tomorrow so the card's quieter instruction becomes action instead of atmosphere.",
            },
        ]
    }
    valid = validate_product_payload("tarot", valid_payload)
    assert valid.valid is True


def test_extended_validators_cover_compatibility_palm_and_feng_shui() -> None:
    compatibility = validate_product_payload(
        "compatibility",
        {"sections": [{"id": "current_pattern", "text": "This is your solo path."}]},
    )
    palm = validate_product_payload(
        "palm",
        {"sections": [{"id": "current_pattern", "text": "A spiritual message is around you."}]},
    )
    feng_shui = validate_product_payload(
        "feng_shui",
        {"sections": [{"id": "current_pattern", "text": "Trust your soul and stay open."}]},
    )

    assert compatibility.valid is False
    assert "compatibility_missing_relationship_framing" in compatibility.issues
    assert palm.valid is False
    assert "palm_missing_feature_led_language" in palm.issues
    assert feng_shui.valid is False
    assert "feng_shui_missing_space_analysis_language" in feng_shui.issues
