import jwt

from auth_service import AuthService


def _auth_service() -> AuthService:
    service = AuthService()
    service.jwt_secret = "unit-test-secret-abcdefghijklmnopqrstuvwxyz"
    return service


def test_password_hash_and_verify() -> None:
    service = _auth_service()

    password = "testpass123"
    password_hash = service.hash_password(password)

    assert password_hash != password
    assert service.verify_password(password, password_hash) is True
    assert service.verify_password("wrong", password_hash) is False


def test_create_and_verify_access_token() -> None:
    service = _auth_service()

    token_payload = service.create_access_token(
        user_id="user-1",
        email="user@example.com",
        role="admin",
    )
    decoded = service.verify_token(token_payload["access_token"])

    assert decoded is not None
    assert decoded["user_id"] == "user-1"
    assert decoded["email"] == "user@example.com"
    assert decoded["role"] == "admin"
    assert "jti" in decoded


def test_verify_apple_identity_token_validation(monkeypatch) -> None:
    service = _auth_service()

    valid_token = jwt.encode(
        {"iss": "https://appleid.apple.com", "exp": 4102444800, "sub": "apple-user-1"},  # year 2100
        key="apple-test-signing-key-abcdefghijklmnopqrstuvwxyz",
        algorithm="HS256",
    )
    invalid_issuer = jwt.encode(
        {"iss": "https://example.com", "exp": 4102444800},
        key="apple-test-signing-key-abcdefghijklmnopqrstuvwxyz",
        algorithm="HS256",
    )

    monkeypatch.delenv("ALLOW_INSECURE_APPLE_SIGN_IN", raising=False)
    monkeypatch.setenv("APPLE_SIGN_IN_AUDIENCES", "com.mystic.app")
    monkeypatch.setattr(
        service,
        "_decode_verified_apple_identity_token",
        lambda token: {"iss": "https://appleid.apple.com", "exp": 4102444800, "sub": "apple-user-1", "aud": "com.mystic.app"}
        if token == valid_token else {"iss": "https://example.com", "exp": 4102444800},
    )
    assert service.verify_apple_identity_token(valid_token) is not None
    assert service.verify_apple_identity_token(invalid_issuer) is None

    monkeypatch.setenv("ALLOW_INSECURE_APPLE_SIGN_IN", "true")
    assert service.verify_apple_identity_token(valid_token) is not None
    assert service.verify_apple_identity_token(invalid_issuer) is None


def test_apple_identity_token_requires_explicit_user_identifier_by_default(monkeypatch) -> None:
    monkeypatch.delenv("ALLOW_INSECURE_APPLE_SIGN_IN", raising=False)

    token = jwt.encode(
        {"iss": "https://appleid.apple.com", "sub": "apple-user-123", "exp": 4102444800},
        key="apple-test-signing-key-abcdefghijklmnopqrstuvwxyz",
        algorithm="HS256",
    )

    from models import AppleSignIn

    try:
        AppleSignIn(identity_token=token, authorization_code="code-123")
    except Exception as exc:
        assert "user_identifier is required" in str(exc)
    else:
        raise AssertionError("Expected validation error")


def test_production_requires_configured_apple_audience_for_verified_sign_in(monkeypatch) -> None:
    monkeypatch.delenv("ALLOW_INSECURE_APPLE_SIGN_IN", raising=False)
    monkeypatch.delenv("APPLE_SIGN_IN_AUDIENCES", raising=False)
    monkeypatch.delenv("APPLE_SERVICE_ID", raising=False)
    monkeypatch.delenv("APPLE_BUNDLE_ID", raising=False)
    monkeypatch.delenv("APPLE_CLIENT_ID", raising=False)
    monkeypatch.setattr("auth_service.APP_ENV", "production")

    service = _auth_service()
    try:
        service._decode_verified_apple_identity_token("not-a-token")
    except RuntimeError as exc:
        assert "APPLE_SIGN_IN_AUDIENCES must be set" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


def test_hash_token_is_stable_and_non_plaintext() -> None:
    service = _auth_service()
    token = "abc123"

    first = service.hash_token(token)
    second = service.hash_token(token)

    assert first == second
    assert first != token
    assert len(first) == 64
