from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LlmProfile:
    id: str
    model_id: str
    temperature: float
    top_p: float
    max_tokens: int
    timeout_ms: int


def _env(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value or default


DEFAULT_CLAUDE_OPUS = _env("BEDROCK_MODEL_CLAUDE_OPUS", "us.amazon.nova-pro-v1:0")


LLM_PROFILES: dict[str, LlmProfile] = {
    "preview_mystic": LlmProfile(
        id="preview_mystic",
        model_id=_env("MYSTIC_LLM_PROFILE_PREVIEW_MODEL", DEFAULT_CLAUDE_OPUS),
        temperature=0.8,
        top_p=0.9,
        max_tokens=900,
        timeout_ms=25_000,
    ),
    "full_premium": LlmProfile(
        id="full_premium",
        model_id=_env("MYSTIC_LLM_PROFILE_FULL_MODEL", DEFAULT_CLAUDE_OPUS),
        temperature=0.85,
        top_p=0.9,
        max_tokens=1800,
        timeout_ms=35_000,
    ),
    "daily_retention": LlmProfile(
        id="daily_retention",
        model_id=_env("MYSTIC_LLM_PROFILE_DAILY_MODEL", DEFAULT_CLAUDE_OPUS),
        temperature=0.72,
        top_p=0.9,
        max_tokens=700,
        timeout_ms=20_000,
    ),
    "grounded_clarity": LlmProfile(
        id="grounded_clarity",
        model_id=_env("MYSTIC_LLM_PROFILE_GROUNDED_MODEL", DEFAULT_CLAUDE_OPUS),
        temperature=0.6,
        top_p=0.85,
        max_tokens=900,
        timeout_ms=22_000,
    ),
}


def get_llm_profile(profile_id: str) -> LlmProfile:
    try:
        return LLM_PROFILES[profile_id]
    except KeyError as exc:
        raise KeyError(f"Unknown LLM profile: {profile_id}") from exc
