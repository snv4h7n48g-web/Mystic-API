from generation.validators import validate_product_payload


def test_feng_shui_validator_rejects_generic_scaffold_sections() -> None:
    payload = {
        "sections": [
            {"id": "opening_hook", "text": "Welcome to your space."},
            {"id": "current_pattern", "text": "Trust your soul and stay open."},
        ]
    }

    result = validate_product_payload("feng_shui", payload)

    assert result.valid is False
    assert "feng_shui_missing_product_sections" in result.issues
    assert "feng_shui_generic_section_ids_leaked" in result.issues
    assert "feng_shui_missing_priority_actions" in result.issues


def test_feng_shui_validator_accepts_actionable_space_analysis() -> None:
    payload = {
        "sections": [
            {"id": "overview", "text": "This lounge is asking for a stronger focal point before it can support calmer conversation."},
            {"id": "bagua_map", "text": "The east side carries growth energy, so what sits there should feel deliberate rather than crowded."},
            {"id": "energy_flow", "text": "Flow is being slowed by clutter near the main circulation path and by too many competing visual anchors."},
            {"id": "priority_actions", "text": "Clear the path from the door to the sofa, remove one oversized decorative item, and shift the lamp so the entry feels open."},
            {"id": "recommendations", "text": "Place the strongest anchor piece on the east wall, keep surfaces lighter, and add only one supportive object instead of several small ones."},
            {"id": "guidance", "text": "Return to the room after these changes and notice whether your body settles faster when you walk in."},
        ]
    }

    result = validate_product_payload("feng_shui", payload)

    assert result.valid is True
