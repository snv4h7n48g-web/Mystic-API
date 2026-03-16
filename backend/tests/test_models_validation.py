import pytest
from pydantic import ValidationError

from models import AuthProvider, UserCreate


def test_user_create_defaults_auth_provider_to_email() -> None:
    payload = UserCreate(email="user@example.com", password="pass123")
    assert payload.auth_provider == AuthProvider.EMAIL


def test_user_create_accepts_apple_provider_without_password() -> None:
    payload = UserCreate(
        email="apple@example.com",
        auth_provider=AuthProvider.APPLE,
        provider_user_id="apple-user-1",
    )
    assert payload.auth_provider == AuthProvider.APPLE
    assert payload.password is None


def test_user_create_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="pass123")
