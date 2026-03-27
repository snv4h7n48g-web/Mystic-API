from generation.product_routing import get_product_route, resolve_product_key
from generation.validators import validate_product_payload


def test_daily_route_prefers_anthropic_text_lane_by_default() -> None:
    route = get_product_route(flow_type="daily_horoscope", surface="preview")
    assert resolve_product_key(flow_type="daily_horoscope") == "daily"
    assert route.product_key == "daily"
    assert "anthropic" in route.preview_model_id or route.preview_model_id == "us.amazon.nova-pro-v1:0"
    assert route.fallback_model_id.startswith("us.amazon.nova")


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


def test_tarot_validator_requires_card_specific_structure() -> None:
    invalid_payload = {"sections": [{"id": "tarot_narrative", "text": "Trust yourself and stay positive."}]}
    invalid = validate_product_payload("tarot", invalid_payload)
    assert invalid.valid is False
    assert "tarot_missing_card_specific_language" in invalid.issues

    valid_payload = {
        "sections": [
            {
                "id": "tarot_narrative",
                "text": "The Hermit in the guidance position sets the tone of the spread. This card's symbolism points to retreat, discernment, and a slower answer.",
            }
        ]
    }
    valid = validate_product_payload("tarot", valid_payload)
    assert valid.valid is True
