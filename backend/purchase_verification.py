from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote

import jwt
import requests


APPLE_PRODUCTION_VERIFY_RECEIPT_URL = "https://buy.itunes.apple.com/verifyReceipt"
APPLE_SANDBOX_VERIFY_RECEIPT_URL = "https://sandbox.itunes.apple.com/verifyReceipt"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_ANDROID_PUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher"


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
        self._google_service_account_info_cache: Optional[Dict[str, Any]] = None
        self._google_access_token_cache: Optional[str] = None
        self._google_access_token_expires_at: float = 0.0

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
        if platform == "android":
            return self._verify_google_purchase(
                product_id=product_id,
                transaction_id=transaction_id,
                purchase_token=receipt,
                is_subscription=is_subscription,
            )

        raise NotImplementedError(f"{platform.upper()} purchase verification is not supported")

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

    def _verify_google_purchase(
        self,
        *,
        product_id: str,
        transaction_id: str,
        purchase_token: str,
        is_subscription: bool,
    ) -> PurchaseVerificationResult:
        if is_subscription:
            return self._verify_google_subscription_purchase(
                product_id=product_id,
                transaction_id=transaction_id,
                purchase_token=purchase_token,
            )
        return self._verify_google_product_purchase(
            product_id=product_id,
            transaction_id=transaction_id,
            purchase_token=purchase_token,
        )

    def _verify_google_product_purchase(
        self,
        *,
        product_id: str,
        transaction_id: str,
        purchase_token: str,
    ) -> PurchaseVerificationResult:
        package_name = quote(self.google_play_package_name, safe="")
        encoded_product_id = quote(product_id, safe="")
        encoded_token = quote(purchase_token, safe="")
        response = self._get_google_json(
            f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
            f"{package_name}/purchases/products/{encoded_product_id}/tokens/{encoded_token}"
        )

        verified_product_id = str(response.get("productId") or product_id)
        if verified_product_id != product_id:
            raise ValueError("Google Play purchase token does not match the expected product")

        purchase_state = self._coerce_int(response.get("purchaseState"))
        if purchase_state != 0:
            raise ValueError(
                self._google_product_purchase_state_message(purchase_state)
            )

        resolved_transaction_id = str(response.get("orderId") or transaction_id)
        environment = self._google_environment(response)
        detail = "Google Play product purchase verified."

        return PurchaseVerificationResult(
            verified=True,
            environment=environment,
            provider="google_play",
            product_id=verified_product_id,
            transaction_id=resolved_transaction_id,
            original_transaction_id=resolved_transaction_id,
            entitlement_active=True,
            detail=detail,
            raw=response,
        )

    def _verify_google_subscription_purchase(
        self,
        *,
        product_id: str,
        transaction_id: str,
        purchase_token: str,
    ) -> PurchaseVerificationResult:
        package_name = quote(self.google_play_package_name, safe="")
        encoded_token = quote(purchase_token, safe="")
        response = self._get_google_json(
            f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
            f"{package_name}/purchases/subscriptionsv2/tokens/{encoded_token}"
        )

        line_item = self._find_matching_google_subscription_line_item(response, product_id)
        if line_item is None:
            raise ValueError("Google Play subscription token does not contain the expected product")

        entitlement_active = self._google_subscription_entitlement_active(response, line_item)
        if not entitlement_active:
            raise ValueError("Google Play subscription is verified but not currently active")

        resolved_transaction_id = str(response.get("latestOrderId") or transaction_id)
        original_transaction_id = str(
            response.get("linkedPurchaseToken") or purchase_token or resolved_transaction_id
        )
        environment = self._google_environment(response)

        return PurchaseVerificationResult(
            verified=True,
            environment=environment,
            provider="google_play",
            product_id=str(line_item.get("productId") or product_id),
            transaction_id=resolved_transaction_id,
            original_transaction_id=original_transaction_id,
            entitlement_active=True,
            detail="Google Play subscription purchase verified.",
            raw=response,
        )

    def _get_google_json(self, url: str) -> Dict[str, Any]:
        access_token = self._get_google_access_token()
        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=self.request_timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError("Google Play verification response was not a JSON object")
            return body
        except requests.RequestException as exc:
            raise RuntimeError(f"Google Play verification request failed: {exc}") from exc

    def _get_google_access_token(self) -> str:
        now = time.time()
        if self._google_access_token_cache and now < self._google_access_token_expires_at - 60:
            return self._google_access_token_cache

        service_account = self._google_service_account_info()
        token_uri = str(service_account.get("token_uri") or GOOGLE_OAUTH_TOKEN_URL)
        issued_at = int(now)
        payload = {
            "iss": service_account["client_email"],
            "scope": GOOGLE_ANDROID_PUBLISHER_SCOPE,
            "aud": token_uri,
            "iat": issued_at,
            "exp": issued_at + 3600,
        }
        headers = {}
        private_key_id = str(service_account.get("private_key_id") or "").strip()
        if private_key_id:
            headers["kid"] = private_key_id

        try:
            assertion = jwt.encode(
                payload,
                service_account["private_key"],
                algorithm="RS256",
                headers=headers or None,
            )
        except Exception as exc:
            raise RuntimeError(
                "Unable to sign Google service account assertion. "
                "Ensure the GOOGLE_SERVICE_ACCOUNT_JSON credential is valid and cryptography is installed."
            ) from exc

        try:
            response = requests.post(
                token_uri,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
                timeout=self.request_timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError("Google OAuth token response was not a JSON object")
            access_token = str(body.get("access_token") or "").strip()
            if not access_token:
                raise ValueError("Google OAuth token response did not include access_token")
            expires_in = self._coerce_int(body.get("expires_in")) or 3600
            self._google_access_token_cache = access_token
            self._google_access_token_expires_at = now + expires_in
            return access_token
        except requests.RequestException as exc:
            raise RuntimeError(f"Google OAuth token request failed: {exc}") from exc

    def _google_service_account_info(self) -> Dict[str, Any]:
        if self._google_service_account_info_cache is not None:
            return self._google_service_account_info_cache

        raw = self.google_service_account_json
        if not raw:
            raise RuntimeError("Android purchase verification requires GOOGLE_SERVICE_ACCOUNT_JSON")

        payload = raw
        if not raw.lstrip().startswith("{") and os.path.exists(raw):
            with open(raw, "r", encoding="utf-8") as handle:
                payload = handle.read()

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON or a readable JSON file path") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON must decode to a JSON object")

        client_email = str(parsed.get("client_email") or "").strip()
        private_key = str(parsed.get("private_key") or "").replace("\\n", "\n").strip()
        if not client_email or not private_key:
            raise RuntimeError(
                "GOOGLE_SERVICE_ACCOUNT_JSON must include client_email and private_key"
            )

        parsed["client_email"] = client_email
        parsed["private_key"] = private_key
        self._google_service_account_info_cache = parsed
        return parsed

    def _find_matching_google_subscription_line_item(
        self,
        response: Dict[str, Any],
        product_id: str,
    ) -> Optional[Dict[str, Any]]:
        line_items = self._dict_items(response.get("lineItems"))
        exact = [
            item for item in line_items
            if str(item.get("productId") or "") == product_id
        ]
        if exact:
            return self._pick_best_google_subscription_line_item(exact)
        return None

    def _pick_best_google_subscription_line_item(
        self,
        line_items: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        def sort_key(item: Dict[str, Any]):
            expiry = self._parse_google_rfc3339(item.get("expiryTime"))
            expiry_ts = expiry.timestamp() if expiry else -1
            auto_renew = 1 if isinstance(item.get("autoRenewingPlan"), dict) else 0
            return (expiry_ts, auto_renew)

        return sorted(line_items, key=sort_key, reverse=True)[0]

    def _google_subscription_entitlement_active(
        self,
        response: Dict[str, Any],
        line_item: Dict[str, Any],
    ) -> bool:
        state = str(response.get("subscriptionState") or "").strip().upper()
        expiry = self._parse_google_rfc3339(line_item.get("expiryTime"))
        if expiry is None:
            return False
        now = datetime.now(timezone.utc)
        if expiry <= now:
            return False
        return state in {
            "SUBSCRIPTION_STATE_ACTIVE",
            "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
            "SUBSCRIPTION_STATE_CANCELED",
        }

    def _google_environment(self, response: Dict[str, Any]) -> str:
        purchase_type = self._coerce_int(response.get("purchaseType"))
        if purchase_type == 0 or isinstance(response.get("testPurchase"), dict):
            return "sandbox"
        return "production"

    @staticmethod
    def _google_product_purchase_state_message(purchase_state: Optional[int]) -> str:
        if purchase_state == 1:
            return "Google Play purchase was canceled"
        if purchase_state == 2:
            return "Google Play purchase is pending and not yet completed"
        return "Google Play purchase is not in a completed state"

    @staticmethod
    def _parse_google_rfc3339(value: Any) -> Optional[datetime]:
        if not value:
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return None

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
