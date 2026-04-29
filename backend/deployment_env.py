from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote_plus

DEFAULT_PREMIUM_BEDROCK_TEXT_MODEL = "global.anthropic.claude-opus-4-5-20251101-v1:0"
PREMIUM_BEDROCK_MODEL_PREFIXES = (
    "anthropic.claude-opus",
    "us.anthropic.claude-opus",
    "global.anthropic.claude-opus",
)


def env(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    return value or default


def app_env() -> str:
    return env("APP_ENV", "development").lower() or "development"


def is_production() -> bool:
    return app_env() == "production"


def is_release_like() -> bool:
    return app_env() in {"uat", "staging", "production"}


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

    if is_release_like():
        raise RuntimeError(
            "Static AWS credentials are not allowed when APP_ENV is uat, staging, or production. Use IAM task roles instead."
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
    return env(
        "BEDROCK_MODEL_CLAUDE_OPUS",
        env("MYSTIC_PREMIUM_TEXT_MODEL", DEFAULT_PREMIUM_BEDROCK_TEXT_MODEL),
    )


def effective_persona_profile_models() -> dict[str, str]:
    fallback = effective_claude_opus_model()
    return {
        "preview_mystic": env("MYSTIC_LLM_PROFILE_PREVIEW_MODEL", fallback),
        "full_premium": env("MYSTIC_LLM_PROFILE_FULL_MODEL", fallback),
        "daily_retention": env("MYSTIC_LLM_PROFILE_DAILY_MODEL", fallback),
        "grounded_clarity": env("MYSTIC_LLM_PROFILE_GROUNDED_MODEL", fallback),
    }


def is_premium_text_model(model_id: str) -> bool:
    normalized = (model_id or "").strip()
    return normalized.startswith(PREMIUM_BEDROCK_MODEL_PREFIXES)


def llm_configuration_issues() -> list[str]:
    issues: list[str] = []
    persona_enabled = env("MYSTIC_USE_PERSONA_ORCHESTRATION", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not persona_enabled:
        issues.append("persona_orchestration_disabled")

    profile_models = effective_persona_profile_models()
    for profile_id, model_id in profile_models.items():
        if not is_premium_text_model(model_id):
            issues.append(f"profile_not_premium:{profile_id}:{model_id}")

    if is_release_like():
        hard_fail = env("MYSTIC_HARD_FAIL_QUALITY_GATES", "true").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not hard_fail:
            issues.append("quality_gates_not_hard_fail")
        if env("AWS_ACCESS_KEY_ID") or env("AWS_SECRET_ACCESS_KEY") or env("AWS_SESSION_TOKEN"):
            issues.append("static_aws_credentials_configured")
        jwt_secret = env("JWT_SECRET_KEY")
        if not jwt_secret or jwt_secret.startswith("your_") or len(jwt_secret) < 32:
            issues.append("jwt_secret_not_release_ready")
        dev_purchase_bypass = env("ALLOW_DEV_PURCHASE_BYPASS", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if dev_purchase_bypass:
            issues.append("dev_purchase_bypass_enabled")

    return issues
