from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


TEST_DB_NAME = "mystic_sit_api"
ADMIN_DB_URL = "postgresql+psycopg2://mystic:mysticpass@localhost:5432/postgres"
TEST_DB_URL = f"postgresql+psycopg2://mystic:mysticpass@localhost:5432/{TEST_DB_NAME}"


def _ensure_test_database() -> None:
    admin_engine = create_engine(ADMIN_DB_URL, future=True, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin_engine.dispose()


_ensure_test_database()
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ.setdefault("APP_ENV", "development")
os.environ["MYSTIC_USE_PERSONA_ORCHESTRATION"] = "true"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import main  # noqa: E402
from pricing import ProductSKU  # noqa: E402


class _FakeGeoService:
    def geocode_with_fallback(self, location_text: str) -> tuple[float, float]:
        return (-37.8136, 144.9631)


class _FakeAstrologyEngine:
    def generate_chart(self, **kwargs):
        return {
            "sun_sign": "Aries",
            "moon_sign": "Cancer",
            "rising_sign": "Libra",
            "birth_summary": kwargs.get("birth_date"),
        }

    def calculate_synastry(self, chart1, chart2):
        return {
            "score": 82,
            "summary": "Mutual support with productive tension.",
            "highlights": ["communication", "timing"],
        }

    def calculate_chinese_zodiac(self, birth_year: int):
        return {
            "animal": "Dragon" if birth_year % 2 == 0 else "Rat",
            "element": "Wood",
            "birth_year": birth_year,
        }


class _FakeVerification:
    provider = "apple"
    environment = "sandbox"
    entitlement_active = True
    original_transaction_id = "orig-sit-v3"
    transaction_id = "verified-sit-v3"
    detail = "verified in SIT"
    raw = {"status": 0}


class _FakeOrchestrator:
    def _meta(self, surface: str) -> SimpleNamespace:
        return SimpleNamespace(
            persona_id=f"sit-{surface}-persona",
            llm_profile_id=f"sit-{surface}-profile",
            prompt_version="sit-v3",
            model_id="fake-model-v3",
            theme_tags=[surface, "release-critical"],
            headline=f"SIT {surface} headline",
            continuity_source_session_id=None,
        )

    def build_session_preview_result(self, **kwargs):
        return SimpleNamespace(
            payload={"teaser_text": "A grounded preview teaser for SIT v3."},
            input_tokens=111,
            output_tokens=222,
            cost_usd=0.0123,
            metadata=self._meta("session-preview"),
        )

    def build_session_reading_result(self, **kwargs):
        content_contract = kwargs["content_contract"]
        return SimpleNamespace(
            payload={
                "sections": [
                    {"id": "overview", "title": "Overview", "body": "Your reading opens with a stable core."},
                    {"id": "guidance", "title": "Guidance", "body": "Focus your next move on clarity and pacing."},
                ],
                "full_text": "Overview: stable core. Guidance: clarity and pacing.",
                "metadata": {
                    "flow_type": content_contract.get("flow_type"),
                    "include_palm": content_contract.get("include_palm"),
                    "generated_at": "2026-04-03T06:00:00+00:00",
                },
            },
            input_tokens=333,
            output_tokens=444,
            cost_usd=0.0456,
            metadata=self._meta("session-reading"),
        )

    def build_compatibility_preview_result(self, **kwargs):
        entitlements = kwargs["entitlements"]
        return SimpleNamespace(
            payload={
                "teaser_text": "This connection has strong momentum with useful friction.",
                "person1": {"profile": kwargs["person1"], "chart": kwargs["chart1"], "zodiac": kwargs["zodiac1"]},
                "person2": {"profile": kwargs["person2"], "chart": kwargs["chart2"], "zodiac": kwargs["zodiac2"]},
                "synastry": kwargs["synastry"],
                "unlock_price": {"currency": "USD", "amount": 0.0 if entitlements.get("included") else 3.99},
                "entitlements": entitlements,
            },
            input_tokens=121,
            output_tokens=212,
            cost_usd=0.0212,
            metadata=self._meta("compat-preview"),
        )

    def build_compatibility_reading_result(self, **kwargs):
        return SimpleNamespace(
            payload={
                "sections": [
                    {"id": "bond", "title": "Bond", "body": "The bond is resilient when expectations stay explicit."},
                    {"id": "growth", "title": "Growth", "body": "Shared growth comes from deliberate pacing."},
                ],
                "full_text": "Bond: resilient. Growth: deliberate pacing.",
                "metadata": {"generated_at": "2026-04-03T06:00:00+00:00"},
            },
            input_tokens=515,
            output_tokens=616,
            cost_usd=0.0616,
            metadata=self._meta("compat-reading"),
        )


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(main.app)


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    with main.engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE purchase_transactions, user_sessions, compatibility_readings, sessions, users RESTART IDENTITY CASCADE"))

    main.app.dependency_overrides.clear()
    monkeypatch.setattr(main, "get_geocoding_service", lambda: _FakeGeoService())
    monkeypatch.setattr(main, "get_astrology_engine", lambda: _FakeAstrologyEngine())
    monkeypatch.setattr(main, "get_generation_orchestrator", lambda: _FakeOrchestrator())
    monkeypatch.setattr(main, "draw_tarot", lambda count: [{"name": f"Card {idx+1}", "orientation": "upright"} for idx in range(count)])
    monkeypatch.setattr(main, "_verify_purchase_or_raise", lambda **kwargs: _FakeVerification())
    yield
    main.app.dependency_overrides.clear()



def _create_session(client: TestClient) -> str:
    response = client.post("/v1/sessions", json={})
    assert response.status_code == 200, response.text
    return response.json()["session_id"]



def _update_session(client: TestClient, session_id: str, **inputs) -> None:
    response = client.patch(f"/v1/sessions/{session_id}", json=inputs)
    assert response.status_code == 200, response.text



def _session_row(session_id: str) -> dict:
    row = main.db_get_session(session_id)
    assert row is not None
    return row



def _compat_row(compat_id: str) -> dict:
    row = main.db_get_compatibility(compat_id)
    assert row is not None
    return row



def _compat_people() -> dict:
    return {
        "person1": {
            "name": "Avery",
            "birth_date": "1990-01-02",
            "birth_time": "08:30",
            "birth_location_text": "Melbourne, Australia",
        },
        "person2": {
            "name": "Jordan",
            "birth_date": "1992-03-04",
            "birth_time": "19:45",
            "birth_location_text": "Sydney, Australia",
        },
    }



def test_combined_preview_api_persists_preview_metadata(client: TestClient) -> None:
    session_id = _create_session(client)
    _update_session(
        client,
        session_id,
        question_intention="Help me understand the week ahead",
        birth_date="1990-01-01",
        birth_time="09:15",
        birth_location_text="Melbourne, Australia",
        flow_type="combined",
        selected_tier="complete",
    )

    tarot_response = client.post(f"/v1/sessions/{session_id}/tarot")
    assert tarot_response.status_code == 200, tarot_response.text

    response = client.post(f"/v1/sessions/{session_id}/preview")
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["status"] == "preview_ready"
    assert payload["preview"]["product_id"] == ProductSKU.READING_COMPLETE
    assert payload["preview"]["unlock_price"]["amount"] == 2.99
    assert payload["preview"]["tarot"]["spread"] == "3-card"
    assert payload["preview"]["teaser_text"]

    row = _session_row(session_id)
    assert row["status"] == "preview_ready"
    assert row["preview"]["product_id"] == ProductSKU.READING_COMPLETE
    assert row["preview_persona_id"] == "sit-session-preview-persona"
    assert row["preview_prompt_version"] == "sit-v3"
    assert row["preview_headline"] == "SIT session-preview headline"



def test_combined_full_reading_api_enforces_purchase_then_persists_reading(client: TestClient) -> None:
    session_id = _create_session(client)
    _update_session(
        client,
        session_id,
        question_intention="What should I focus on in this transition?",
        birth_date="1990-01-01",
        birth_time="09:15",
        birth_location_text="Melbourne, Australia",
        flow_type="combined",
        selected_tier="basic",
    )

    client.post(f"/v1/sessions/{session_id}/tarot")
    preview_response = client.post(f"/v1/sessions/{session_id}/preview")
    assert preview_response.status_code == 200, preview_response.text

    blocked = client.post(f"/v1/sessions/{session_id}/reading")
    assert blocked.status_code == 402
    assert blocked.json()["detail"] == "Reading purchase required"

    purchase = client.post(
        f"/v1/sessions/{session_id}/purchase",
        json={"product_id": ProductSKU.READING_BASIC, "transaction_id": f"txn-{uuid.uuid4()}"},
    )
    assert purchase.status_code == 200, purchase.text

    reading_response = client.post(f"/v1/sessions/{session_id}/reading")
    assert reading_response.status_code == 200, reading_response.text
    payload = reading_response.json()

    assert payload["status"] == "complete"
    assert payload["reading"]["sections"][0]["id"] == "overview"
    assert payload["reading"]["metadata"]["flow_type"] == "combined"

    row = _session_row(session_id)
    assert ProductSKU.READING_BASIC in (row["purchased_products"] or [])
    assert row["reading"]["sections"][1]["id"] == "guidance"
    assert row["reading_persona_id"] == "sit-session-reading-persona"
    assert row["reading_prompt_version"] == "sit-v3"



def test_compatibility_preview_api_persists_preview_and_metadata(client: TestClient) -> None:
    create_response = client.post("/v1/compatibility", json=_compat_people())
    assert create_response.status_code == 200, create_response.text
    compat_id = create_response.json()["compatibility_id"]

    response = client.post(f"/v1/compatibility/{compat_id}/preview")
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["status"] == "preview_ready"
    assert payload["preview"]["product_id"] == ProductSKU.COMPATIBILITY
    assert payload["preview"]["unlock_price"]["amount"] == 3.99
    assert payload["preview"]["entitlements"]["included"] is False

    row = _compat_row(compat_id)
    assert row["preview"]["product_id"] == ProductSKU.COMPATIBILITY
    assert row["preview_persona_id"] == "sit-compat-preview-persona"
    assert row["preview_headline"] == "SIT compat-preview headline"



def test_compatibility_full_reading_api_enforces_purchase_then_persists_reading(client: TestClient) -> None:
    create_response = client.post("/v1/compatibility", json=_compat_people())
    assert create_response.status_code == 200, create_response.text
    compat_id = create_response.json()["compatibility_id"]

    blocked = client.post(f"/v1/compatibility/{compat_id}/reading")
    assert blocked.status_code == 402
    assert blocked.json()["detail"] == "Compatibility purchase required"

    purchase = client.post(
        f"/v1/compatibility/{compat_id}/purchase",
        json={"product_id": ProductSKU.COMPATIBILITY, "transaction_id": f"txn-{uuid.uuid4()}"},
    )
    assert purchase.status_code == 200, purchase.text

    response = client.post(f"/v1/compatibility/{compat_id}/reading")
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["status"] == "complete"
    assert payload["reading"]["sections"][0]["id"] == "bond"
    assert payload["reading"]["metadata"]["model"] == "fake-model-v3"

    row = _compat_row(compat_id)
    assert row["purchased"] is True
    assert row["reading"]["sections"][1]["id"] == "growth"
    assert row["reading_persona_id"] == "sit-compat-reading-persona"
    assert row["reading_prompt_version"] == "sit-v3"



def test_daily_preview_api_requires_subscription_and_persists_zero_unlock_preview(client: TestClient) -> None:
    session_id = _create_session(client)
    _update_session(
        client,
        session_id,
        question_intention="What energy should I work with today?",
        birth_date="1990-01-01",
        birth_time="07:00",
        birth_location_text="Melbourne, Australia",
        flow_type="daily_horoscope",
    )

    no_sub_user = {"id": str(uuid.uuid4()), "email": "nosub@example.com", "role": "user", "metadata": {}}
    main.app.dependency_overrides[main.get_current_user_optional] = lambda: no_sub_user
    blocked = client.post(f"/v1/sessions/{session_id}/preview?daily=true")
    assert blocked.status_code == 402
    assert blocked.json()["detail"] == "Active subscription required for daily readings"

    active_user = {
        "id": str(uuid.uuid4()),
        "email": "sub@example.com",
        "role": "user",
        "metadata": {"subscription": {"status": "active"}},
    }
    main.app.dependency_overrides[main.get_current_user_optional] = lambda: active_user
    response = client.post(f"/v1/sessions/{session_id}/preview?daily=true")
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["status"] == "preview_ready"
    assert payload["preview"]["product_id"] == ProductSKU.DAILY_ASTRO_TAROT
    assert payload["preview"]["unlock_price"]["amount"] == 0.0
    assert payload["preview"]["entitlements"]["subscription_active"] is True

    row = _session_row(session_id)
    assert row["preview"]["product_id"] == ProductSKU.DAILY_ASTRO_TAROT
    assert row["preview"]["unlock_price"]["amount"] == 0.0
    assert row["preview_persona_id"] == "sit-session-preview-persona"
