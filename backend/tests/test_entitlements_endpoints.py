from __future__ import annotations

import os
from datetime import datetime, timezone

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


def test_refresh_entitlements_filters_to_active_verified_products(monkeypatch) -> None:
    user = _auth_user()
    now = datetime.now(timezone.utc)

    transactions = [
        {
            "status": "verified",
            "entitlement_active": True,
            "product_id": ProductSKU.BUNDLE_LIFE_HARMONY,
            "transaction_id": "txn_bundle",
            "original_transaction_id": "orig_bundle",
            "resource_type": "compatibility",
            "resource_id": "compat-1",
            "environment": "production",
            "provider": "apple",
            "created_at": now,
            "updated_at": now,
        },
        {
            "status": "verified",
            "entitlement_active": False,
            "product_id": ProductSKU.DAILY_ASTRO_TAROT,
            "transaction_id": "txn_sub_old",
            "original_transaction_id": "orig_sub_old",
            "resource_type": "subscription",
            "resource_id": "sub-1",
            "environment": "production",
            "provider": "apple",
            "created_at": now,
            "updated_at": now,
        },
        {
            "status": "pending",
            "entitlement_active": True,
            "product_id": ProductSKU.FENG_SHUI_SINGLE,
            "transaction_id": "txn_pending",
            "original_transaction_id": "orig_pending",
            "resource_type": "feng_shui",
            "resource_id": "feng-1",
            "environment": "production",
            "provider": "apple",
            "created_at": now,
            "updated_at": now,
        },
    ]

    monkeypatch.setattr(main, "db_get_user_purchase_transactions", lambda user_id: transactions)

    main.app.dependency_overrides[main.get_current_user] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post("/v1/entitlements/refresh")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "refreshed"
    assert payload["subscription_active"] is False
    assert payload["verified_products"] == [ProductSKU.BUNDLE_LIFE_HARMONY]

    feature_entitlements = payload["feature_entitlements"]
    assert feature_entitlements["compatibility"] is True
    assert feature_entitlements["feng_shui_full"] is True
    assert feature_entitlements["feng_shui_single"] is False


def test_compatibility_purchase_short_circuits_when_bundle_entitled(monkeypatch) -> None:
    user = _auth_user()
    now = datetime.now(timezone.utc)

    monkeypatch.setattr(
        main,
        "db_get_compatibility",
        lambda compat_id: {"id": compat_id, "user_id": user["id"], "purchased": False},
    )
    monkeypatch.setattr(
        main,
        "db_get_user_purchase_transactions",
        lambda user_id: [
            {
                "status": "verified",
                "entitlement_active": True,
                "product_id": ProductSKU.BUNDLE_LIFE_HARMONY,
                "created_at": now,
                "updated_at": now,
            }
        ],
    )

    def _should_not_verify(**kwargs):
        raise AssertionError("Purchase verification should not run for included_by_entitlement")

    monkeypatch.setattr(main, "_verify_purchase_or_raise", _should_not_verify)

    main.app.dependency_overrides[main.get_current_user_optional] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/compatibility/compat-123/purchase",
            json={"product_id": ProductSKU.COMPATIBILITY, "transaction_id": "tx_123"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "included_by_entitlement"
    assert payload["product_id"] == ProductSKU.COMPATIBILITY
    assert payload["bundle_active"] is True


def test_restore_entitlement_records_verified_transaction(monkeypatch) -> None:
    user = _auth_user()
    captured = {}

    class _Verification:
        provider = "apple"
        environment = "production"
        entitlement_active = True
        original_transaction_id = "orig_restore_1"
        transaction_id = "txn_restore_1"
        detail = "Apple verifyReceipt accepted."
        raw = {"status": 0}

    monkeypatch.setattr(
        main,
        "_verify_purchase_or_raise",
        lambda **kwargs: _Verification(),
    )

    def _record(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(main, "db_record_purchase_transaction", _record)

    main.app.dependency_overrides[main.get_current_user] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/entitlements/restore",
            json={
                "product_id": ProductSKU.BUNDLE_LIFE_HARMONY,
                "transaction_id": "client_txn_restore_1",
                "receipt_data": "signed-receipt",
                "platform": "ios",
            },
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "restored"
    assert payload["product_id"] == ProductSKU.BUNDLE_LIFE_HARMONY
    assert payload["transaction_id"] == "txn_restore_1"
    assert payload["verification"]["original_transaction_id"] == "orig_restore_1"
    assert captured["user_id"] == user["id"]
    assert captured["resource_type"] == "restore"
    assert captured["resource_id"] == user["id"]
    assert captured["entitlement_active"] is True


def test_feng_shui_purchase_short_circuits_when_bundle_entitled(monkeypatch) -> None:
    user = _auth_user()
    now = datetime.now(timezone.utc)

    monkeypatch.setattr(
        main,
        "db_get_feng_shui",
        lambda analysis_id: {
            "id": analysis_id,
            "user_id": user["id"],
            "analysis_type": "single_room",
            "product_id": ProductSKU.FENG_SHUI_SINGLE,
            "purchased": False,
        },
    )
    monkeypatch.setattr(
        main,
        "db_get_user_purchase_transactions",
        lambda user_id: [
            {
                "status": "verified",
                "entitlement_active": True,
                "product_id": ProductSKU.BUNDLE_NEW_BEGINNINGS,
                "created_at": now,
                "updated_at": now,
            }
        ],
    )

    def _should_not_verify(**kwargs):
        raise AssertionError("Purchase verification should not run for included_by_entitlement")

    monkeypatch.setattr(main, "_verify_purchase_or_raise", _should_not_verify)

    main.app.dependency_overrides[main.get_current_user_optional] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/feng-shui/feng-123/purchase",
            json={"product_id": ProductSKU.FENG_SHUI_SINGLE, "transaction_id": "tx_456"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "included_by_entitlement"
    assert payload["product_id"] == ProductSKU.FENG_SHUI_SINGLE
    assert payload["bundle_active"] is True


def test_activate_subscription_records_android_verification(monkeypatch) -> None:
    user = _auth_user()
    captured = {}

    class _Verification:
        provider = "google_play"
        environment = "sandbox"
        entitlement_active = True
        original_transaction_id = "linked-sub-token-1"
        transaction_id = "GPA.sub-order-1"
        detail = "Google Play subscription purchase verified."
        raw = {"latestOrderId": "GPA.sub-order-1"}

    class _UserService:
        def set_subscription(self, user_id: str, subscription: dict) -> None:
            captured["set_subscription"] = {
                "user_id": user_id,
                "subscription": subscription,
            }

    monkeypatch.setattr(main, "_verify_purchase_or_raise", lambda **kwargs: _Verification())
    monkeypatch.setattr(main, "get_user_service", lambda: _UserService())
    monkeypatch.setattr(main, "db_record_purchase_transaction", lambda **kwargs: captured.update(recorded=kwargs))

    main.app.dependency_overrides[main.get_current_user] = lambda: user
    client = TestClient(main.app)
    try:
        response = client.post(
            "/v1/subscription/activate",
            json={
                "product_id": ProductSKU.DAILY_ASTRO_TAROT,
                "transaction_id": "client-sub-1",
                "receipt_data": "subscription_purchase_token_1",
                "platform": "android",
            },
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "active"
    assert payload["subscription"]["transaction_id"] == "GPA.sub-order-1"
    assert payload["subscription"]["original_transaction_id"] == "linked-sub-token-1"
    assert payload["subscription"]["verification_provider"] == "google_play"
    assert payload["subscription"]["verification_environment"] == "sandbox"
    assert captured["set_subscription"]["user_id"] == user["id"]
    assert captured["recorded"]["platform"] == "android"
    assert captured["recorded"]["provider"] == "google_play"
    assert captured["recorded"]["resource_type"] == "subscription"
