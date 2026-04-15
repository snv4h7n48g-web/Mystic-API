from lunar_knowledge import build_lunar_prompt_context, classify_zodiac_relationship


def test_classify_zodiac_relationship_detects_allied_group():
    relationship = classify_zodiac_relationship("Tiger", "Horse")

    assert relationship["type"] == "allied"
    assert "work with your nature" in relationship["reading"]


def test_classify_zodiac_relationship_detects_opposition():
    relationship = classify_zodiac_relationship("Rat", "Horse")

    assert relationship["type"] == "opposition"
    assert "friction" in relationship["reading"]


def test_build_lunar_prompt_context_includes_birth_year_and_current_year_layers():
    context = build_lunar_prompt_context(
        birth_zodiac={"animal": "Tiger", "element": "Wood", "combined": "Wood Tiger"},
        current_year=2026,
        current_year_zodiac={"animal": "Horse", "element": "Fire", "combined": "Fire Horse"},
    )

    assert context["birth_zodiac"]["combined"] == "Wood Tiger"
    assert context["current_year"]["year_label"] == "2026: Year of the Fire Horse"
    assert context["current_year"]["cycle_marker"] == "February 17, 2026 begins the Year of the Horse."
    assert context["interaction"]["type"] == "allied"
    assert any("Fire Horse" in item for item in context["reading_focus"])


def test_build_lunar_prompt_context_supports_year_only_mode():
    context = build_lunar_prompt_context(
        birth_zodiac=None,
        current_year=2026,
        current_year_zodiac={"animal": "Horse", "element": "Fire", "combined": "Fire Horse"},
    )

    assert "birth_zodiac" not in context
    assert context["current_year"]["year_animal"]["animal"] == "Horse"
    assert len(context["reading_focus"]) >= 3
