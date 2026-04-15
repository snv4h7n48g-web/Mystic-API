from generation.products.lunar.validator import validate_lunar_payload


def test_lunar_validator_flags_missing_sections_and_thin_content():
    payload = {
        "sections": [
            {"id": "opening_invocation", "text": "A year is opening."},
            {"id": "lunar_forecast", "text": "Too thin."},
            {"id": "reflective_guidance", "text": "Move carefully."},
        ]
    }

    issues = validate_lunar_payload(payload)

    assert "lunar_missing_sections" in issues
    assert "lunar_missing_required_section:integrated_synthesis" in issues
    assert "lunar_section_too_thin:lunar_forecast" in issues
    assert "lunar_section_too_thin:reflective_guidance" in issues


def test_lunar_validator_accepts_complete_distinct_payload():
    payload = {
        "sections": [
            {"id": "opening_invocation", "text": "2026 opens as a Fire Horse year that rewards visible courage, cleaner momentum, and a more honest appetite for change."},
            {"id": "lunar_forecast", "text": "The year symbolism is all movement and heat: progress comes when you back what is alive, but restlessness becomes expensive if you keep leaping without direction or discipline."},
            {"id": "integrated_synthesis", "text": "Welcome the part of you that is ready to move, create, and choose with conviction. Release the reflex to call every surge of motion alignment when some of it is only escape velocity."},
            {"id": "reflective_guidance", "text": "Protect one priority, commit to the path with real energy, and trim the distractions that make momentum feel exciting while quietly draining your year."},
        ]
    }

    assert validate_lunar_payload(payload) == []
