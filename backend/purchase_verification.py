from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests


APPLE_PRODUCTION_VERIFY_RECEIPT_URL = "https://buy.itunes.apple.com/verifyReceipt"
APPLE_SANDBOX_VERIFY_RECEIPT_URL = "https://sandbox.itunes.apple.com/verifyReceipt"


@dataclass
class PurchaseVerificationResult:
    verified: bool
    environment: str
    provider: str
    product_id: str
    transaction_id: str
    original_transaction_id: Optional[str] = None
    entitlement_active: bool = False
    detail: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


class PurchaseVerificationService:
    """Central seam for store purchase verification."""

    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development").strip().lower() or "development"
        self.allow_dev_bypass = self._bool_env("ALLOW_DEV_PURCHASE_BYPASS", False)
        if self.app_env == "production" and self.allow_dev_bypass:
            raise RuntimeError("ALLOW_DEV_PURCHASE_BYPASS cannot be enabled when APP_ENV=production")
        self.apple_shared_secret = os.getenv("APPLE_SHARED_SECRET", "").strip()
        self.app_store_server_api_key = os.getenv("APP_STORE_SERVER_API_KEY", "").strip()
        self.google_play_package_name = os.getenv("GOOGLE_PLAY_PACKAGE_NAME", "").strip()
        self.google_service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
        self.request_timeout_seconds = float(os.getenv("PURCHASE_VERIFICATION_TIMEOUT_SECONDS", "15"))

    def verification_ready(self, platform: str = "ios") -> bool:
        platform = (platform or "ios").strip().lower()
        if platform == "android":
            return bool(self.google_play_package_name and self.google_service_account_json)
        return bool(self.apple_shared_secret or self.app_store_server_api_key)

    def verify_purchase(
        self,
        *,
        product_id: str,
        transaction_id: str,
        receipt_data: Optional[str],
        platform: str = "ios",
        is_subscription: bool = False,
    ) -> PurchaseVerificationResult:
        platform = (platform or "ios").strip().lower()
        receipt = (receipt_data or "").strip()

        if self.allow_dev_bypass and receipt.lower() == "dev_mode":
            return PurchaseVerificationResult(
                verified=True,
                environment="dev_bypass",
                provider=platform,
                product_id=product_id,
                transaction_id=transaction_id,
                original_transaction_id=transaction_id,
                entitlement_active=True,
                detail="Development purchase bypass accepted.",
                raw={"mode": "dev_bypass"},
            )

        if not receipt:
            raise ValueError("receipt_data is required for purchase verification")

        if not self.verification_ready(platform):
            raise RuntimeError(
                f"{platform.upper()} purchase verification is not configured"
            )

        if platform == "ios":
            return self._verify_apple_purchase(
                product_id=product_id,
                transaction_id=transaction_id,
                receipt_data=receipt,
                is_subscription=is_subscription,
            )

        raise NotImplementedError(
            f"{platform.upper()} purchase verification is configured but not implemented yet"
        )

    def _verify_apple_purchase(
        self,
        *,
        product_id: str,
        transaction_id: str,
        receipt_data: str,
        is_subscription: bool,
    ) -> PurchaseVerificationResult:
        if not self.apple_shared_secret:
            raise RuntimeError(
                "IOS purchase verification requires APPLE_SHARED_SECRET for verifyReceipt"
            )

        response = self._post_apple_receipt(receipt_data, use_sandbox=False)
        environment = "production"
        status = self._coerce_int(response.get("status"))

        if status == 21007:
            response = self._post_apple_receipt(receipt_data, use_sandbox=True)
            environment = "sandbox"
            status = self._coerce_int(response.get("status"))

        if status != 0:
            raise ValueError(f"Apple receipt verification failed with status {status}")

        transaction = self._find_matching_apple_transaction(
            response=response,
            product_id=product_id,
            transaction_id=transaction_id,
            is_subscription=is_subscription,
        )
        if transaction is None:
            raise ValueError("Verified Apple receipt does not contain the expected product/transaction")

        verified_transaction_id = str(
            transaction.get("transaction_id")
            or transaction.get("web_order_line_item_id")
            or transaction_id
        )
        original_transaction_id = transaction.get("original_transaction_id")
        entitlement_active = self._apple_entitlement_active(transaction, is_subscription=is_subscription)

        if is_subscription and not entitlement_active:
            raise ValueError("Apple subscription receipt is verified but not currently active")

        return PurchaseVerificationResult(
            verified=True,
            environment=environment,
            provider="apple",
            product_id=str(transaction.get("product_id") or product_id),
            transaction_id=verified_transaction_id,
            original_transaction_id=str(original_transaction_id) if original_transaction_id else verified_transaction_id,
            entitlement_active=entitlement_active,
            detail="Apple verifyReceipt accepted.",
            raw={
                "status": status,
                "environment": response.get("environment") or environment,
                "transaction": transaction,
                "pending_renewal_info": response.get("pending_renewal_info") or [],
            },
        )

    def _post_apple_receipt(self, receipt_data: str, *, use_sandbox: bool) -> Dict[str, Any]:
        url = APPLE_SANDBOX_VERIFY_RECEIPT_URL if use_sandbox else APPLE_PRODUCTION_VERIFY_RECEIPT_URL
        payload = {
            "receipt-data": receipt_data,
            "password": self.apple_shared_secret,
            "exclude-old-transactions": False,
        }
        try:
            response = requests.post(url, json=payload, timeout=self.request_timeout_seconds)
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError("Apple receipt verification response was not a JSON object")
            return body
        except requests.RequestException as exc:
            raise RuntimeError(f"Apple receipt verification request failed: {exc}") from exc

    def _find_matching_apple_transaction(
        self,
        *,
        response: Dict[str, Any],
        product_id: str,
        transaction_id: str,
        is_subscription: bool,
    ) -> Optional[Dict[str, Any]]:
        requested_txn = str(transaction_id)
        candidates = self._apple_transaction_candidates(response)

        exact = [
            item for item in candidates
            if str(item.get("product_id") or "") == product_id
            and str(item.get("transaction_id") or "") == requested_txn
        ]
        if exact:
            return self._pick_best_apple_transaction(exact, is_subscription=is_subscription)

        original_matches = [
            item for item in candidates
            if str(item.get("product_id") or "") == product_id
            and str(item.get("original_transaction_id") or "") == requested_txn
        ]
        if original_matches:
            return self._pick_best_apple_transaction(original_matches, is_subscription=is_subscription)

        product_matches = [
            item for item in candidates if str(item.get("product_id") or "") == product_id
        ]
        if product_matches:
            return self._pick_best_apple_transaction(product_matches, is_subscription=is_subscription)

        return None

    def _apple_transaction_candidates(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for key in ("latest_receipt_info",):
            candidates.extend(self._dict_items(response.get(key)))

        receipt = response.get("receipt")
        if isinstance(receipt, dict):
            candidates.extend(self._dict_items(receipt.get("in_app")))

        return candidates

    def _pick_best_apple_transaction(
        self,
        transactions: Iterable[Dict[str, Any]],
        *,
        is_subscription: bool,
    ) -> Dict[str, Any]:
        def sort_key(item: Dict[str, Any]):
            expiry = self._coerce_int(item.get("expires_date_ms")) or -1
            purchase = self._coerce_int(item.get("purchase_date_ms")) or -1
            active_bias = 1 if self._apple_entitlement_active(item, is_subscription=is_subscription) else 0
            return (active_bias, expiry, purchase)

        return sorted(transactions, key=sort_key, reverse=True)[0]

    def _apple_entitlement_active(self, transaction: Dict[str, Any], *, is_subscription: bool) -> bool:
        if str(transaction.get("cancellation_date") or "").strip():
            return False
        if not is_subscription:
            return True
        expires_ms = self._coerce_int(transaction.get("expires_date_ms"))
        if expires_ms is None:
            return False
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        return expires_ms > now_ms

    @staticmethod
    def _dict_items(value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _coerce_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _bool_env(name: str, default: bool = False) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}


_service: Optional[PurchaseVerificationService] = None


def get_purchase_verification_service() -> PurchaseVerificationService:
    global _service
    if _service is None:
        _service = PurchaseVerificationService()
    return _service
