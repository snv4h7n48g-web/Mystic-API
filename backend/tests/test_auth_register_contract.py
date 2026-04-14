from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_DB_INIT", "true")

import main


class _FakeUserService:
    def __init__(self) -> None:
        self.stored_tokens: list[tuple[str, str]] = []

    def get_user_by_email(self, email: str):
        return None

    def create_user(self, **kwargs):
        self.created_user = kwargs
        return "user-123"

    def store_auth_token(self, user_id: str, token: str):
        self.stored_tokens.append((user_id, token))


class _FakeAuthService:
    def hash_password(self, password: str) -> str:
        return f"hashed:{password}"

    def create_access_token(self, *, user_id: str, email: str, role: str):
        return {
            "access_token": "token-123",
            "token_type": "bearer",
            "expires_at": "2026-04-14T12:00:00+00:00",
        }


def test_register_returns_access_token_and_user_id(monkeypatch) -> None:
    user_service = _FakeUserService()
    auth_service = _FakeAuthService()

    monkeypatch.setattr(main, "get_user_service", lambda: user_service)
    monkeypatch.setattr(main, "get_auth_service", lambda: auth_service)

    client = TestClient(main.app)
    response = client.post(
        "/v1/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "secret-password",
            "display_name": "New User",
            "auth_provider": "email",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "user-123"
    assert payload["access_token"] == "token-123"
    assert payload["token_type"] == "bearer"
    assert payload["expires_at"] == "2026-04-14T12:00:00+00:00"
    assert user_service.stored_tokens == [("user-123", "token-123")]
