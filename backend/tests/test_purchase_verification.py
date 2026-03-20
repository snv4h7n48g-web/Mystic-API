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
