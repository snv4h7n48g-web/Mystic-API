from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_DB_INIT", "true")

import main
from deployment_env import database_url


def test_database_url_builds_from_discrete_env(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DB_HOST", "db.internal")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "mystic")
    monkeypatch.setenv("DB_USER", "mystic_user")
    monkeypatch.setenv("DB_PASSWORD", "secret-pass")

    assert database_url() == "postgresql+psycopg2://mystic_user:secret-pass@db.internal:5432/mystic"


def test_database_url_rejects_partial_discrete_config(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DB_HOST", "db.internal")
    monkeypatch.setenv("DB_NAME", "mystic")
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.setenv("DB_PASSWORD", "secret-pass")

    try:
        database_url()
    except RuntimeError as exc:
        assert "Missing: DB_USER" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


def test_readiness_returns_200_when_database_ping_succeeds(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setattr(main, "_database_ping", lambda: True)

    client = TestClient(main.app)
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["ready"] is True
    assert response.headers["X-Request-ID"]


def test_readiness_returns_503_when_database_ping_fails(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setattr(main, "_database_ping", lambda: False)

    client = TestClient(main.app)
    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["ready"] is False
    assert response.headers["X-Request-ID"]


def test_request_id_header_respects_incoming_header(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setattr(main, "_database_ping", lambda: True)

    client = TestClient(main.app)
    response = client.get("/health", headers={"X-Request-ID": "req-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"


def test_release_readiness_rejects_non_premium_llm_config(monkeypatch) -> None:
    monkeypatch.setattr(main, "_database_ping", lambda: True)
    monkeypatch.setenv("APP_ENV", "uat")
    monkeypatch.setenv("MYSTIC_USE_PERSONA_ORCHESTRATION", "true")
    monkeypatch.setenv("BEDROCK_MODEL_CLAUDE_OPUS", "us.amazon.nova-pro-v1:0")
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 48)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_PREVIEW_MODEL", raising=False)
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_FULL_MODEL", raising=False)
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_DAILY_MODEL", raising=False)
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_GROUNDED_MODEL", raising=False)

    client = TestClient(main.app)
    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["llm"] == "misconfigured"


def test_release_readiness_accepts_premium_llm_config(monkeypatch) -> None:
    premium = "global.anthropic.claude-opus-4-5-20251101-v1:0"
    monkeypatch.setattr(main, "_database_ping", lambda: True)
    monkeypatch.setenv("APP_ENV", "uat")
    monkeypatch.setenv("MYSTIC_USE_PERSONA_ORCHESTRATION", "true")
    monkeypatch.setenv("MYSTIC_HARD_FAIL_QUALITY_GATES", "true")
    monkeypatch.setenv("BEDROCK_MODEL_CLAUDE_OPUS", premium)
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 48)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)
    monkeypatch.setenv("ALLOW_DEV_PURCHASE_BYPASS", "false")
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_PREVIEW_MODEL", raising=False)
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_FULL_MODEL", raising=False)
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_DAILY_MODEL", raising=False)
    monkeypatch.delenv("MYSTIC_LLM_PROFILE_GROUNDED_MODEL", raising=False)

    client = TestClient(main.app)
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["llm"] == "ready"
