from deployment_env import effective_claude_opus_model, effective_persona_profile_models


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
