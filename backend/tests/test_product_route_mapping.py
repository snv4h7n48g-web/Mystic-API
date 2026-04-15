from __future__ import annotations

import os

os.environ.setdefault("SKIP_DB_INIT", "true")

import main
from pricing import ProductSKU


def test_daily_horoscope_flow_uses_astrology_only() -> None:
    assert main._flow_uses_astrology("daily_horoscope") is True
    assert main._flow_requires_birth_date("daily_horoscope") is True
    assert main._flow_uses_tarot("daily_horoscope") is False


def test_lunar_flow_uses_lunar_context_without_requiring_birth_date() -> None:
    assert main._flow_uses_astrology("lunar_new_year_solo") is True
    assert main._flow_requires_birth_date("lunar_new_year_solo") is False


def test_tarot_flow_uses_tarot_only() -> None:
    assert main._flow_uses_astrology("tarot_solo") is False
    assert main._flow_uses_tarot("tarot_solo") is True


def test_palm_flow_content_contract_is_supported() -> None:
    session = {
        "inputs": {"flow_type": "palm_solo"},
        "purchased_products": [],
        "palm_analysis": {"features": [{"feature": "life_line", "value": "deep"}]},
    }

    assert main._session_content_contract(session) == {
        "flow_type": "palm_solo",
        "include_palm": True,
        "include_lunar_forecast": False,
    }



def test_sun_moon_flow_maps_to_basic_unlock_product() -> None:
    session = {
        "inputs": {
            "flow_type": "sun_moon_solo",
            "selected_tier": "basic",
        }
    }

    assert main._required_session_product_id(session) == ProductSKU.READING_BASIC



def test_lunar_flow_maps_to_lunar_forecast_product_and_contract() -> None:
    session = {
        "inputs": {"flow_type": "lunar_new_year_solo"},
        "purchased_products": [],
        "palm_analysis": None,
    }

    assert main._required_session_product_id(session) == ProductSKU.LUNAR_FORECAST
    assert main._session_content_contract(session) == {
        "flow_type": "lunar_new_year_solo",
        "include_palm": False,
        "include_lunar_forecast": True,
    }



def test_combined_complete_flow_keeps_palm_but_not_lunar_without_addon() -> None:
    session = {
        "inputs": {
            "flow_type": "combined",
            "selected_tier": "complete",
        },
        "purchased_products": [],
        "palm_analysis": {"life_line": {"length": "long"}},
    }

    assert main._required_session_product_id(session) == ProductSKU.READING_COMPLETE
    assert main._session_content_contract(session) == {
        "flow_type": "combined",
        "include_palm": True,
        "include_lunar_forecast": False,
    }
