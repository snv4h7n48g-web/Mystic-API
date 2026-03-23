from generation.continuity.builder import build_continuity_context


def test_build_continuity_context_returns_none_without_user_id() -> None:
    assert build_continuity_context(user_id=None, session_id="sess-1") is None


def test_build_continuity_context_is_compact_and_deduplicated(monkeypatch) -> None:
    monkeypatch.setattr(
        "generation.continuity.builder.get_recent_user_generation_metadata",
        lambda user_id, limit=4: [
            {
                "source_id": "s1",
                "source_type": "session_reading",
                "headline": "A very long headline about clarity and boundaries that keeps going well past a compact prompt budget and should be trimmed down before prompt injection happens in production.",
                "persona_id": "ancient_tarot_reader",
                "flow_type": "combined",
                "theme_tags": ["clarity", "boundaries", "clarity"],
            },
            {
                "source_id": "s2",
                "source_type": "compatibility_preview",
                "headline": "A second thing",
                "persona_id": "flirty_cosmic_guide",
                "flow_type": "compatibility",
                "theme_tags": ["chemistry", "boundaries"],
            },
        ],
    )

    payload = build_continuity_context(
        user_id="user-1",
        session_id="sess-1",
        current_flow_type="combined",
        current_object_type="session",
    )

    assert payload is not None
    assert payload["latest_persona_id"] == "ancient_tarot_reader"
    assert payload["recent_theme_tags"] == ["clarity", "boundaries", "chemistry"]
    assert len(payload["recent_persona_ids"]) == 2
    assert len(payload["factual_callbacks"]) == 1
    assert payload["latest_headline"].endswith("…")
    assert payload["current_flow_type"] == "combined"


def test_build_continuity_context_prefers_matching_flow_over_plain_recency(monkeypatch) -> None:
    monkeypatch.setattr(
        "generation.continuity.builder.get_recent_user_generation_metadata",
        lambda user_id, limit=4: [
            {
                "source_id": "recent-preview",
                "source_type": "session_preview",
                "headline": "A generic recent preview",
                "persona_id": "psychic_best_friend",
                "flow_type": "combined",
                "theme_tags": ["clarity"],
            },
            {
                "source_id": "older-compat",
                "source_type": "compatibility_reading",
                "headline": "A strong relationship pattern",
                "persona_id": "flirty_cosmic_guide",
                "flow_type": "compatibility",
                "theme_tags": ["chemistry", "timing"],
            },
        ],
    )

    payload = build_continuity_context(
        user_id="user-1",
        session_id="compat-1",
        current_flow_type="compatibility",
        current_object_type="compatibility",
    )

    assert payload is not None
    assert payload["latest_persona_id"] == "flirty_cosmic_guide"
    assert payload["latest_flow_type"] == "compatibility"
    assert payload["factual_callbacks"][0].startswith("Your latest reading focused on: A strong relationship pattern")
