from datetime import datetime, timedelta, timezone

from purchase_verification import (
    APPLE_PRODUCTION_VERIFY_RECEIPT_URL,
    APPLE_SANDBOX_VERIFY_RECEIPT_URL,
    PurchaseVerificationService,
)


class _FakeResponse:
    def __init__(self, body):
        self._body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self._body


def test_dev_bypass_verifies_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("ALLOW_DEV_PURCHASE_BYPASS", "true")
    service = PurchaseVerificationService()

    result = service.verify_purchase(
        product_id="reading_basic_199",
        transaction_id="dev_123",
        receipt_data="dev_mode",
    )

    assert result.verified is True
    assert result.environment == "dev_bypass"
    assert result.entitlement_active is True
    assert result.original_transaction_id == "dev_123"


def test_missing_receipt_is_rejected_without_bypass(monkeypatch) -> None:
    monkeypatch.delenv("ALLOW_DEV_PURCHASE_BYPASS", raising=False)
    service = PurchaseVerificationService()

    try:
        service.verify_purchase(
            product_id="reading_basic_199",
            transaction_id="txn_123",
            receipt_data=None,
        )
    except ValueError as exc:
        assert "receipt_data is required" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_ios_verification_readiness_detects_app_store_config(monkeypatch) -> None:
    monkeypatch.setenv("APP_STORE_SERVER_API_KEY", "test-key")
    service = PurchaseVerificationService()

    assert service.verification_ready("ios") is True
    assert service.verification_ready("android") is False


def test_android_verification_readiness_detects_google_play_config(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_PLAY_PACKAGE_NAME", "com.example.mystic")
    monkeypatch.setenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        '{"client_email":"svc@example.iam.gserviceaccount.com","private_key":"-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n"}',
    )
    service = PurchaseVerificationService()

    assert service.verification_ready("android") is True
    assert service.verification_ready("ios") is False


def test_ios_receipt_verification_extracts_subscription_transaction(monkeypatch) -> None:
    monkeypatch.setenv("APPLE_SHARED_SECRET", "shared-secret")
    service = PurchaseVerificationService()
    future_ms = int((datetime.now(timezone.utc) + timedelta(days=10)).timestamp() * 1000)

    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return _FakeResponse(
            {
                "status": 0,
                "environment": "Production",
                "latest_receipt_info": [
                    {
                        "product_id": "subscription_daily_999",
                        "transaction_id": "txn_live_2",
                        "original_transaction_id": "orig_sub_1",
                        "expires_date_ms": str(future_ms),
                    },
                    {
                        "product_id": "subscription_daily_999",
                        "transaction_id": "txn_live_1",
                        "original_transaction_id": "orig_sub_1",
                        "expires_date_ms": str(future_ms - 1000),
                    },
                ],
            }
        )

    monkeypatch.setattr("purchase_verification.requests.post", fake_post)

    result = service.verify_purchase(
        product_id="subscription_daily_999",
        transaction_id="orig_sub_1",
        receipt_data="signed-receipt",
        is_subscription=True,
    )

    assert len(calls) == 1
    assert calls[0][0] == APPLE_PRODUCTION_VERIFY_RECEIPT_URL
    assert result.verified is True
    assert result.provider == "apple"
    assert result.environment == "production"
    assert result.transaction_id == "txn_live_2"
    assert result.original_transaction_id == "orig_sub_1"
    assert result.entitlement_active is True


def test_ios_receipt_verification_retries_in_sandbox(monkeypatch) -> None:
    monkeypatch.setenv("APPLE_SHARED_SECRET", "shared-secret")
    service = PurchaseVerificationService()
    calls = []

    def fake_post(url, json, timeout):
        calls.append(url)
        if url == APPLE_PRODUCTION_VERIFY_RECEIPT_URL:
            return _FakeResponse({"status": 21007})
        return _FakeResponse(
            {
                "status": 0,
                "environment": "Sandbox",
                "receipt": {
                    "in_app": [
                        {
                            "product_id": "reading_basic_199",
                            "transaction_id": "txn_sandbox_1",
                            "original_transaction_id": "txn_sandbox_1",
                        }
                    ]
                },
            }
        )

    monkeypatch.setattr("purchase_verification.requests.post", fake_post)

    result = service.verify_purchase(
        product_id="reading_basic_199",
        transaction_id="txn_sandbox_1",
        receipt_data="signed-receipt",
    )

    assert calls == [
        APPLE_PRODUCTION_VERIFY_RECEIPT_URL,
        APPLE_SANDBOX_VERIFY_RECEIPT_URL,
    ]
    assert result.environment == "sandbox"
    assert result.transaction_id == "txn_sandbox_1"
    assert result.entitlement_active is True


def test_android_product_purchase_verifies_successfully(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_PLAY_PACKAGE_NAME", "com.example.mystic")
    monkeypatch.setenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        '{"client_email":"svc@example.iam.gserviceaccount.com","private_key":"-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n"}',
    )
    service = PurchaseVerificationService()
    service._get_google_access_token = lambda: "google-access-token"

    calls = []

    def fake_get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return _FakeResponse(
            {
                "productId": "reading_basic_199",
                "orderId": "GPA.1234-5678-9012-34567",
                "purchaseState": 0,
                "acknowledgementState": 1,
            }
        )

    monkeypatch.setattr("purchase_verification.requests.get", fake_get)

    result = service.verify_purchase(
        product_id="reading_basic_199",
        transaction_id="client_txn_1",
        receipt_data="purchase_token_123",
        platform="android",
    )

    assert len(calls) == 1
    assert "/applications/com.example.mystic/purchases/products/reading_basic_199/tokens/purchase_token_123" in calls[0][0]
    assert calls[0][1]["Authorization"] == "Bearer google-access-token"
    assert result.verified is True
    assert result.provider == "google_play"
    assert result.environment == "production"
    assert result.transaction_id == "GPA.1234-5678-9012-34567"
    assert result.original_transaction_id == "GPA.1234-5678-9012-34567"
    assert result.entitlement_active is True


def test_android_product_purchase_rejects_pending_state(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_PLAY_PACKAGE_NAME", "com.example.mystic")
    monkeypatch.setenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        '{"client_email":"svc@example.iam.gserviceaccount.com","private_key":"-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n"}',
    )
    service = PurchaseVerificationService()
    service._get_google_access_token = lambda: "google-access-token"

    def fake_get(url, headers, timeout):
        return _FakeResponse(
            {
                "productId": "reading_basic_199",
                "purchaseState": 2,
            }
        )

    monkeypatch.setattr("purchase_verification.requests.get", fake_get)

    try:
        service.verify_purchase(
            product_id="reading_basic_199",
            transaction_id="client_txn_2",
            receipt_data="purchase_token_456",
            platform="android",
        )
    except ValueError as exc:
        assert "pending" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_inactive_subscription_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("APPLE_SHARED_SECRET", "shared-secret")
    service = PurchaseVerificationService()
    past_ms = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp() * 1000)

    def fake_post(url, json, timeout):
        return _FakeResponse(
            {
                "status": 0,
                "latest_receipt_info": [
                    {
                        "product_id": "subscription_daily_999",
                        "transaction_id": "txn_expired_1",
                        "original_transaction_id": "orig_expired_1",
                        "expires_date_ms": str(past_ms),
                    }
                ],
            }
        )

    monkeypatch.setattr("purchase_verification.requests.post", fake_post)

    try:
        service.verify_purchase(
            product_id="subscription_daily_999",
            transaction_id="txn_expired_1",
            receipt_data="signed-receipt",
            is_subscription=True,
        )
    except ValueError as exc:
        assert "not currently active" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_android_subscription_verifies_active_state(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_PLAY_PACKAGE_NAME", "com.example.mystic")
    monkeypatch.setenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        '{"client_email":"svc@example.iam.gserviceaccount.com","private_key":"-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n"}',
    )
    service = PurchaseVerificationService()
    service._get_google_access_token = lambda: "google-access-token"
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat().replace("+00:00", "Z")

    def fake_get(url, headers, timeout):
        return _FakeResponse(
            {
                "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
                "latestOrderId": "GPA.subs-order-1",
                "linkedPurchaseToken": "linked_purchase_token_1",
                "lineItems": [
                    {
                        "productId": "subscription_daily_999",
                        "expiryTime": future_expiry,
                        "autoRenewingPlan": {"autoRenewEnabled": True},
                    }
                ],
            }
        )

    monkeypatch.setattr("purchase_verification.requests.get", fake_get)

    result = service.verify_purchase(
        product_id="subscription_daily_999",
        transaction_id="client_sub_txn",
        receipt_data="subscription_token_123",
        platform="android",
        is_subscription=True,
    )

    assert result.verified is True
    assert result.provider == "google_play"
    assert result.transaction_id == "GPA.subs-order-1"
    assert result.original_transaction_id == "linked_purchase_token_1"
    assert result.entitlement_active is True


def test_android_subscription_rejects_inactive_state(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_PLAY_PACKAGE_NAME", "com.example.mystic")
    monkeypatch.setenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        '{"client_email":"svc@example.iam.gserviceaccount.com","private_key":"-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n"}',
    )
    service = PurchaseVerificationService()
    service._get_google_access_token = lambda: "google-access-token"
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat().replace("+00:00", "Z")

    def fake_get(url, headers, timeout):
        return _FakeResponse(
            {
                "subscriptionState": "SUBSCRIPTION_STATE_ON_HOLD",
                "latestOrderId": "GPA.subs-order-2",
                "lineItems": [
                    {
                        "productId": "subscription_daily_999",
                        "expiryTime": future_expiry,
                    }
                ],
            }
        )

    monkeypatch.setattr("purchase_verification.requests.get", fake_get)

    try:
        service.verify_purchase(
            product_id="subscription_daily_999",
            transaction_id="client_sub_txn_2",
            receipt_data="subscription_token_456",
            platform="android",
            is_subscription=True,
        )
    except ValueError as exc:
        assert "not currently active" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_production_rejects_dev_bypass_flag(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOW_DEV_PURCHASE_BYPASS", "true")

    try:
        PurchaseVerificationService()
    except RuntimeError as exc:
        assert "cannot be enabled" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


def test_subscription_cancelled_transaction_is_not_active(monkeypatch) -> None:
    monkeypatch.setenv("APPLE_SHARED_SECRET", "shared-secret")
    service = PurchaseVerificationService()
    future_ms = int((datetime.now(timezone.utc) + timedelta(days=10)).timestamp() * 1000)

    def fake_post(url, json, timeout):
        return _FakeResponse(
            {
                "status": 0,
                "latest_receipt_info": [
                    {
                        "product_id": "subscription_daily_999",
                        "transaction_id": "txn_cancelled",
                        "original_transaction_id": "orig_cancelled",
                        "expires_date_ms": str(future_ms),
                        "cancellation_date": "2026-03-01T00:00:00Z",
                    }
                ],
            }
        )

    monkeypatch.setattr("purchase_verification.requests.post", fake_post)

    try:
        service.verify_purchase(
            product_id="subscription_daily_999",
            transaction_id="txn_cancelled",
            receipt_data="signed-receipt",
            is_subscription=True,
        )
    except ValueError as exc:
        assert "not currently active" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_transaction_matching_prefers_active_candidate(monkeypatch) -> None:
    monkeypatch.setenv("APPLE_SHARED_SECRET", "shared-secret")
    service = PurchaseVerificationService()
    future_ms = int((datetime.now(timezone.utc) + timedelta(days=2)).timestamp() * 1000)
    past_ms = int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp() * 1000)

    def fake_post(url, json, timeout):
        return _FakeResponse(
            {
                "status": 0,
                "latest_receipt_info": [
                    {
                        "product_id": "subscription_daily_999",
                        "transaction_id": "txn_old",
                        "original_transaction_id": "orig_123",
                        "expires_date_ms": str(past_ms),
                    },
                    {
                        "product_id": "subscription_daily_999",
                        "transaction_id": "txn_new",
                        "original_transaction_id": "orig_123",
                        "expires_date_ms": str(future_ms),
                    },
                ],
            }
        )

    monkeypatch.setattr("purchase_verification.requests.post", fake_post)
    result = service.verify_purchase(
        product_id="subscription_daily_999",
        transaction_id="orig_123",
        receipt_data="signed-receipt",
        is_subscription=True,
    )

    assert result.transaction_id == "txn_new"
    assert result.entitlement_active is True


def test_no_matching_product_or_transaction_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("APPLE_SHARED_SECRET", "shared-secret")
    service = PurchaseVerificationService()

    def fake_post(url, json, timeout):
        return _FakeResponse(
            {
                "status": 0,
                "receipt": {
                    "in_app": [
                        {
                            "product_id": "different_product",
                            "transaction_id": "txn_1",
                        }
                    ]
                },
            }
        )

    monkeypatch.setattr("purchase_verification.requests.post", fake_post)

    try:
        service.verify_purchase(
            product_id="reading_basic_199",
            transaction_id="txn_expected",
            receipt_data="signed-receipt",
        )
    except ValueError as exc:
        assert "does not contain" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
