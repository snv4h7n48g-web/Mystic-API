from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_DB_INIT", "true")

import main
from pricing import ProductSKU


def _auth_user() -> dict:
    return {
        "id": "user-123",
        "email": "user@example.com",
        "role": "user",
        "metadata": {},
    }


def test_session_purchase_rejects_product_that_does_not_match_preview_contract(monkeypatch) -> None:
    user = _auth_user()
    session = {
        "id": "sess-1",
        "user_id": user["id"],
        "purchased_products": [],
        "inputs": {"question_intention": "Help", "birth_date": "1990-01-01"},
        "preview": {
            "product_id": ProductSKU.READING_COMPLETE,
            "unlock_price": {"currency": "USD", "amount": 2.99},
        },
    }

    monkeypatch.setattr(main, "db_get_session", lambda session_id: session)
    monkeypatch.setattr(main, "_assert_session_access", lambda session_id, user: None)
    main.app.dependency_overrides[main.get_current_user_optional] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/sessions/sess-1/purchase",
            json={"product_id": ProductSKU.READING_BASIC, "transaction_id": "tx-1"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Purchase product does not match this preview contract"


def test_session_purchase_rejects_paid_preview_without_product_contract(monkeypatch) -> None:
    user = _auth_user()
    session = {
        "id": "sess-2",
        "user_id": user["id"],
        "purchased_products": [],
        "inputs": {"question_intention": "Help", "birth_date": "1990-01-01"},
        "preview": {
            "product_id": "",
            "unlock_price": {"currency": "USD", "amount": 1.99},
        },
    }

    monkeypatch.setattr(main, "db_get_session", lambda session_id: session)
    monkeypatch.setattr(main, "_assert_session_access", lambda session_id, user: None)
    main.app.dependency_overrides[main.get_current_user_optional] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/sessions/sess-2/purchase",
            json={"product_id": ProductSKU.READING_BASIC, "transaction_id": "tx-2"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Preview contract is invalid for paid unlock"


def test_session_purchase_rejects_subscription_product(monkeypatch) -> None:
    user = _auth_user()
    session = {
        "id": "sess-sub",
        "user_id": user["id"],
        "purchased_products": [],
        "inputs": {"flow_type": "daily_horoscope", "question_intention": "Today?", "birth_date": "1990-01-01"},
        "preview": {
            "product_id": ProductSKU.DAILY_ASTRO_TAROT,
            "unlock_price": {"currency": "USD", "amount": 9.99},
        },
    }

    monkeypatch.setattr(main, "db_get_session", lambda session_id: session)
    monkeypatch.setattr(main, "_assert_session_access", lambda session_id, user: None)
    main.app.dependency_overrides[main.get_current_user_optional] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/sessions/sess-sub/purchase",
            json={"product_id": ProductSKU.DAILY_ASTRO_TAROT, "transaction_id": "tx-sub"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Use /v1/subscription/activate for subscription purchases"


def test_session_purchase_allows_matching_preview_contract(monkeypatch) -> None:
    user = _auth_user()
    session = {
        "id": "sess-3",
        "user_id": user["id"],
        "purchased_products": [],
        "inputs": {"question_intention": "Help", "birth_date": "1990-01-01"},
        "preview": {
            "product_id": ProductSKU.READING_BASIC,
            "unlock_price": {"currency": "USD", "amount": 1.99},
        },
    }
    captured = {}

    class _Verification:
        provider = "apple"
        environment = "production"
        entitlement_active = True
        original_transaction_id = "orig-1"
        transaction_id = "verified-1"
        detail = "ok"
        raw = {"status": 0}

    monkeypatch.setattr(main, "db_get_session", lambda session_id: session)
    monkeypatch.setattr(main, "_assert_session_access", lambda session_id, user: None)
    monkeypatch.setattr(main, "_verified_products_for_user", lambda user: [])
    monkeypatch.setattr(main, "validate_purchase", lambda product_id, existing: True)
    monkeypatch.setattr(main, "_verify_purchase_or_raise", lambda **kwargs: _Verification())
    monkeypatch.setattr(main, "db_update_session", lambda session_id, **kwargs: captured.update(kwargs))
    monkeypatch.setattr(main, "db_record_purchase_transaction", lambda **kwargs: captured.update(recorded=kwargs))

    main.app.dependency_overrides[main.get_current_user_optional] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/sessions/sess-3/purchase",
            json={"product_id": ProductSKU.READING_BASIC, "transaction_id": "tx-3", "receipt_data": "receipt"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "purchased"
    assert payload["product_id"] == ProductSKU.READING_BASIC
    assert ProductSKU.READING_BASIC in captured["purchased_products"]


def test_session_purchase_honors_matching_paid_preview_contract_even_if_catalog_validation_fails(monkeypatch) -> None:
    user = _auth_user()
    session = {
        "id": "sess-4",
        "user_id": user["id"],
        "purchased_products": [],
        "inputs": {"question_intention": "Help"},
        "preview": {
            "product_id": ProductSKU.LUNAR_FORECAST,
            "unlock_price": {"currency": "USD", "amount": 1.00},
        },
    }
    captured = {}

    class _Verification:
        provider = "apple"
        environment = "production"
        entitlement_active = True
        original_transaction_id = "orig-lunar"
        transaction_id = "verified-lunar"
        detail = "ok"
        raw = {"status": 0}

    monkeypatch.setattr(main, "db_get_session", lambda session_id: session)
    monkeypatch.setattr(main, "_assert_session_access", lambda session_id, user: None)
    monkeypatch.setattr(main, "_verified_products_for_user", lambda user: [])
    monkeypatch.setattr(main, "validate_purchase", lambda product_id, existing: False)
    monkeypatch.setattr(main, "_verify_purchase_or_raise", lambda **kwargs: _Verification())
    monkeypatch.setattr(main, "db_update_session", lambda session_id, **kwargs: captured.update(kwargs))
    monkeypatch.setattr(main, "db_record_purchase_transaction", lambda **kwargs: captured.update(recorded=kwargs))

    main.app.dependency_overrides[main.get_current_user_optional] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/sessions/sess-4/purchase",
            json={"product_id": ProductSKU.LUNAR_FORECAST, "transaction_id": "tx-4", "receipt_data": "receipt"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "purchased"
    assert payload["product_id"] == ProductSKU.LUNAR_FORECAST
    assert ProductSKU.LUNAR_FORECAST in captured["purchased_products"]


def test_session_purchase_is_idempotent_when_product_already_on_session(monkeypatch) -> None:
    user = _auth_user()
    session = {
        "id": "sess-5",
        "user_id": user["id"],
        "purchased_products": [ProductSKU.READING_BASIC],
        "inputs": {"question_intention": "Help"},
        "preview": {
            "product_id": ProductSKU.READING_BASIC,
            "unlock_price": {"currency": "USD", "amount": 1.99},
        },
    }

    monkeypatch.setattr(main, "db_get_session", lambda session_id: session)
    monkeypatch.setattr(main, "_assert_session_access", lambda session_id, user: None)
    monkeypatch.setattr(main, "_verified_products_for_user", lambda user: [])

    def _should_not_verify(**kwargs):
        raise AssertionError("Duplicate purchases should not re-run verification")

    monkeypatch.setattr(main, "_verify_purchase_or_raise", _should_not_verify)

    main.app.dependency_overrides[main.get_current_user_optional] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/sessions/sess-5/purchase",
            json={"product_id": ProductSKU.READING_BASIC, "transaction_id": "tx-5", "platform": "android"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "already_purchased"
    assert payload["purchased_products"] == [ProductSKU.READING_BASIC]


def test_session_purchase_android_records_verified_google_purchase(monkeypatch) -> None:
    user = _auth_user()
    session = {
        "id": "sess-6",
        "user_id": user["id"],
        "purchased_products": [],
        "inputs": {"question_intention": "Help"},
        "preview": {
            "product_id": ProductSKU.READING_BASIC,
            "unlock_price": {"currency": "USD", "amount": 1.99},
        },
    }
    captured = {}

    class _Verification:
        provider = "google_play"
        environment = "production"
        entitlement_active = True
        original_transaction_id = "GPA.1-linked"
        transaction_id = "GPA.1-order"
        detail = "Google Play product purchase verified."
        raw = {"orderId": "GPA.1-order"}

    def _verify(**kwargs):
        captured["verification_args"] = kwargs
        return _Verification()

    monkeypatch.setattr(main, "db_get_session", lambda session_id: session)
    monkeypatch.setattr(main, "_assert_session_access", lambda session_id, user: None)
    monkeypatch.setattr(main, "_verified_products_for_user", lambda user: [])
    monkeypatch.setattr(main, "validate_purchase", lambda product_id, existing: True)
    monkeypatch.setattr(main, "_verify_purchase_or_raise", _verify)
    monkeypatch.setattr(main, "db_update_session", lambda session_id, **kwargs: captured.update(updated=kwargs))
    monkeypatch.setattr(main, "db_record_purchase_transaction", lambda **kwargs: captured.update(recorded=kwargs))

    main.app.dependency_overrides[main.get_current_user_optional] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/sessions/sess-6/purchase",
            json={
                "product_id": ProductSKU.READING_BASIC,
                "transaction_id": "client-tx-6",
                "receipt_data": "purchase_token_6",
                "platform": "android",
            },
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "purchased"
    assert payload["verification"]["original_transaction_id"] == "GPA.1-linked"
    assert captured["verification_args"]["platform"] == "android"
    assert captured["verification_args"]["receipt_data"] == "purchase_token_6"
    assert captured["recorded"]["platform"] == "android"
    assert captured["recorded"]["provider"] == "google_play"
    assert captured["recorded"]["transaction_id"] == "GPA.1-order"
