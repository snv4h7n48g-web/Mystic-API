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

    payload = build_continuity_context(user_id="user-1", session_id="sess-1")

    assert payload is not None
    assert payload["latest_persona_id"] == "ancient_tarot_reader"
    assert payload["recent_theme_tags"] == ["clarity", "boundaries", "chemistry"]
    assert len(payload["recent_persona_ids"]) == 2
    assert len(payload["factual_callbacks"]) == 1
    assert payload["latest_headline"].endswith("…")
