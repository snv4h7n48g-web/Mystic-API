from __future__ import annotations

import os

os.environ.setdefault("SKIP_DB_INIT", "true")

import main
from pricing import ProductSKU


def test_daily_horoscope_flow_uses_astrology_only() -> None:
    assert main._flow_uses_astrology("daily_horoscope") is True
    assert main._flow_requires_birth_date("daily_horoscope") is True
    assert main._flow_uses_tarot("daily_horoscope") is False


def test_daily_horoscope_flow_maps_to_subscription_product() -> None:
    session = {
        "inputs": {
            "flow_type": "daily_horoscope",
            "selected_tier": "basic",
        },
        "purchased_products": [],
    }

    assert main._required_session_product_id(session) == ProductSKU.DAILY_ASTRO_TAROT
    assert main._session_preview_unlock_contract(session, user=None) == {
        "unlock_amount": 9.99,
        "product_id": ProductSKU.DAILY_ASTRO_TAROT,
        "subscription_active": False,
        "session_unlocked": False,
    }


def test_lunar_flow_uses_lunar_context_without_requiring_birth_date() -> None:
    assert main._flow_uses_astrology("lunar_new_year_solo") is True
    assert main._flow_requires_birth_date("lunar_new_year_solo") is False


def test_tarot_flow_uses_tarot_only() -> None:
    assert main._flow_uses_astrology("tarot_solo") is False
    assert main._flow_requires_birth_date("tarot_solo") is False
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


def test_palm_upload_url_resets_stale_palm_outputs(monkeypatch) -> None:
    updates = {}

    class FakeS3Service:
        def generate_presigned_upload_url(self, *, session_id, content_type):
            assert session_id == "session-1"
            assert content_type == "image/jpeg"
            return {
                "upload_url": "https://upload.example",
                "upload_fields": {"key": "palms/session-1/new.jpg"},
                "object_key": "palms/session-1/new.jpg",
                "expires_in": 300,
            }

    monkeypatch.setattr(main, "db_get_session", lambda session_id: {"id": session_id})
    monkeypatch.setattr(main, "db_get_session_owner_id", lambda session_id: None)
    monkeypatch.setattr(main, "get_s3_service", lambda: FakeS3Service())
    monkeypatch.setattr(main, "db_update_session", lambda session_id, **fields: updates.update(fields))

    response = main.get_palm_upload_url("session-1", content_type="image/jpeg", user=None)

    assert response["upload_url"] == "https://upload.example"
    assert updates == {
        "palm_image_url": "palms/session-1/new.jpg",
        "palm_analysis": None,
        "palm_cost_usd": None,
        "preview": None,
        "reading": None,
        "status": "draft",
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


def test_blessing_flow_maps_to_daruma_unlock_product() -> None:
    session = {
        "inputs": {"flow_type": "blessing_solo"},
        "purchased_products": [],
        "palm_analysis": None,
    }

    assert main._required_session_product_id(session) == ProductSKU.DARUMA_BLESSING
    assert main._session_content_contract(session) == {
        "flow_type": "blessing_solo",
        "include_palm": False,
        "include_lunar_forecast": False,
    }


def test_blessing_flow_preview_contract_unlocks_after_purchase() -> None:
    session = {
        "inputs": {"flow_type": "blessing_solo"},
        "purchased_products": [ProductSKU.DARUMA_BLESSING],
    }

    assert main._session_preview_unlock_contract(session, user=None) == {
        "unlock_amount": 0.0,
        "product_id": ProductSKU.DARUMA_BLESSING,
        "subscription_active": False,
        "session_unlocked": True,
    }
