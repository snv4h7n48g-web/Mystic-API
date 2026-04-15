from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote_plus


def env(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    return value or default


def app_env() -> str:
    return env("APP_ENV", "development").lower() or "development"


def is_production() -> bool:
    return app_env() == "production"


def aws_region() -> str:
    return env("AWS_REGION", "us-east-1")


def aws_client_kwargs(service_name: str) -> dict[str, Any]:
    access_key = env("AWS_ACCESS_KEY_ID")
    secret_key = env("AWS_SECRET_ACCESS_KEY")
    session_token = env("AWS_SESSION_TOKEN")

    kwargs: dict[str, Any] = {
        "service_name": service_name,
        "region_name": aws_region(),
    }

    has_any_static = any([access_key, secret_key, session_token])
    if not has_any_static:
        return kwargs

    if not access_key or not secret_key:
        raise RuntimeError(
            "Explicit AWS credentials require both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
        )

    if is_production():
        raise RuntimeError(
            "Static AWS credentials are not allowed when APP_ENV=production. Use IAM task roles instead."
        )

    kwargs["aws_access_key_id"] = access_key
    kwargs["aws_secret_access_key"] = secret_key
    if session_token:
        kwargs["aws_session_token"] = session_token
    return kwargs


def database_url(
    default_local: str = "postgresql+psycopg2://mystic:mysticpass@localhost:5432/mystic",
) -> str:
    configured = env("DATABASE_URL")
    if configured:
        return configured

    host = env("DB_HOST")
    port = env("DB_PORT", "5432")
    name = env("DB_NAME")
    user = env("DB_USER")
    password = env("DB_PASSWORD")

    discrete_values = {
        "DB_HOST": host,
        "DB_NAME": name,
        "DB_USER": user,
        "DB_PASSWORD": password,
    }
    if any(discrete_values.values()):
        missing = [key for key, value in discrete_values.items() if not value]
        if missing:
            raise RuntimeError(
                "Discrete database configuration is incomplete. Missing: " + ", ".join(missing)
            )
        return (
            "postgresql+psycopg2://"
            f"{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{quote_plus(name)}"
        )

    if is_production():
        raise RuntimeError(
            "DATABASE_URL must be set when APP_ENV=production, or provide DB_HOST, DB_NAME, DB_USER, and DB_PASSWORD"
        )

    return default_local


def effective_claude_opus_model() -> str:
    return env("BEDROCK_MODEL_CLAUDE_OPUS", env("BEDROCK_FULL_MODEL", "us.amazon.nova-pro-v1:0"))


def effective_persona_profile_models() -> dict[str, str]:
    fallback = effective_claude_opus_model()
    return {
        "preview_mystic": env("MYSTIC_LLM_PROFILE_PREVIEW_MODEL", fallback),
        "full_premium": env("MYSTIC_LLM_PROFILE_FULL_MODEL", fallback),
        "daily_retention": env("MYSTIC_LLM_PROFILE_DAILY_MODEL", fallback),
        "grounded_clarity": env("MYSTIC_LLM_PROFILE_GROUNDED_MODEL", fallback),
    }
