import pytest

from deployment_env import (
    aws_client_kwargs,
    effective_claude_opus_model,
    effective_persona_profile_models,
)


def test_effective_claude_opus_model_falls_back_to_legacy_full(monkeypatch) -> None:
    monkeypatch.delenv("BEDROCK_MODEL_CLAUDE_OPUS", raising=False)
    monkeypatch.setenv("BEDROCK_FULL_MODEL", "legacy-full")

    assert effective_claude_opus_model() == "legacy-full"


def test_effective_persona_profile_models_use_claude_fallback(monkeypatch) -> None:
    monkeypatch.setenv("BEDROCK_MODEL_CLAUDE_OPUS", "claude-opus-id")
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_PREVIEW_MODEL", raising=False)
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_FULL_MODEL", raising=False)
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_DAILY_MODEL", raising=False)
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_GROUNDED_MODEL", raising=False)

    models = effective_persona_profile_models()

    assert models["preview_mystic"] == "claude-opus-id"
    assert models["full_premium"] == "claude-opus-id"
    assert models["daily_retention"] == "claude-opus-id"
    assert models["grounded_clarity"] == "claude-opus-id"


def test_aws_client_kwargs_uses_region_and_explicit_creds_in_development(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AWS_REGION", "ap-southeast-2")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-access")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "test-session")

    kwargs = aws_client_kwargs("s3")

    assert kwargs["service_name"] == "s3"
    assert kwargs["region_name"] == "ap-southeast-2"
    assert kwargs["aws_access_key_id"] == "test-access"
    assert kwargs["aws_secret_access_key"] == "test-secret"
    assert kwargs["aws_session_token"] == "test-session"


def test_aws_client_kwargs_uses_default_chain_when_no_explicit_creds(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)

    kwargs = aws_client_kwargs("bedrock-runtime")

    assert kwargs == {
        "service_name": "bedrock-runtime",
        "region_name": "us-east-1",
    }


def test_aws_client_kwargs_rejects_partial_static_credentials(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "only-access")
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="require both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"):
        aws_client_kwargs("s3")


def test_aws_client_kwargs_rejects_static_credentials_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "prod-access")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "prod-secret")

    with pytest.raises(RuntimeError, match="Static AWS credentials are not allowed"):
        aws_client_kwargs("bedrock-runtime")
