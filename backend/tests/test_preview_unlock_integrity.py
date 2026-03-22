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
