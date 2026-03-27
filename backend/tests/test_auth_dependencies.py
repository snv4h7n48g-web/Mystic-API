from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

import auth_dependencies


class _FakeUserService:
    def __init__(self, user_id: str | None = None, user: dict | None = None):
        self._user_id = user_id
        self._user = user

    def verify_and_refresh_token(self, token: str):
        return self._user_id

    def get_user_by_id(self, user_id: str):
        return self._user


def test_get_current_user_requires_authorization_header() -> None:
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth_dependencies.get_current_user(None))
    assert exc.value.status_code == 401
    assert "Not authenticated" in str(exc.value.detail)


def test_get_current_user_rejects_malformed_header() -> None:
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth_dependencies.get_current_user("Token abc"))
    assert exc.value.status_code == 401
    assert "Invalid authorization header" in str(exc.value.detail)


def test_get_current_user_rejects_invalid_or_expired_token(monkeypatch) -> None:
    monkeypatch.setattr(auth_dependencies, "get_auth_service", lambda: object())
    monkeypatch.setattr(auth_dependencies, "get_user_service", lambda: _FakeUserService(user_id=None))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth_dependencies.get_current_user("Bearer token-123"))

    assert exc.value.status_code == 401
    assert "Invalid or expired token" in str(exc.value.detail)


def test_get_current_user_rejects_missing_user(monkeypatch) -> None:
    monkeypatch.setattr(auth_dependencies, "get_auth_service", lambda: object())
    monkeypatch.setattr(
        auth_dependencies,
        "get_user_service",
        lambda: _FakeUserService(user_id="user-1", user=None),
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth_dependencies.get_current_user("Bearer token-123"))

    assert exc.value.status_code == 401
    assert "User not found" in str(exc.value.detail)


def test_get_current_user_returns_user_when_token_valid(monkeypatch) -> None:
    expected = {"id": "user-1", "email": "u@example.com", "role": "user"}
    monkeypatch.setattr(auth_dependencies, "get_auth_service", lambda: object())
    monkeypatch.setattr(
        auth_dependencies,
        "get_user_service",
        lambda: _FakeUserService(user_id="user-1", user=expected),
    )

    result = asyncio.run(auth_dependencies.get_current_user("Bearer token-123"))
    assert result == expected


def test_get_current_user_optional_returns_none_on_auth_failure(monkeypatch) -> None:
    async def _raise_http_exception(_: str):
        raise HTTPException(401, "nope")

    monkeypatch.setattr(auth_dependencies, "get_current_user", _raise_http_exception)

    result = asyncio.run(auth_dependencies.get_current_user_optional("Bearer token-123"))
    assert result is None


def test_require_admin_blocks_non_admin() -> None:
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth_dependencies.require_admin({"id": "u1", "role": "user"}))
    assert exc.value.status_code == 403


def test_require_admin_allows_admin() -> None:
    admin = {"id": "a1", "role": "admin"}
    result = asyncio.run(auth_dependencies.require_admin(admin))
    assert result == admin
