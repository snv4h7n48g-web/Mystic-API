from __future__ import annotations

import os


def env(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    return value or default


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
