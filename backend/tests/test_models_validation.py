import pytest
from pydantic import ValidationError

from models import AppleSignIn, AuthProvider, UserCreate


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


def test_apple_sign_in_builds_full_name_from_given_and_family_names():
    payload = AppleSignIn(
        identity_token='header.payload.signature',
        authorization_code='auth-code',
        user_identifier='apple-user-123',
        given_name='Taylor',
        family_name='Smith',
    )

    assert payload.full_name == 'Taylor Smith'


def test_apple_sign_in_requires_user_identifier_when_token_cannot_supply_one():
    with pytest.raises(ValidationError):
        AppleSignIn(
            identity_token='not-a-jwt',
            authorization_code='auth-code',
        )
