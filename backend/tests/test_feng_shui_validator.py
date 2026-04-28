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
    assert "feng_shui_missing_section:practical_fixes" in result.issues


def test_feng_shui_validator_accepts_actionable_space_analysis() -> None:
    payload = {
        "sections": [
            {"id": "overview", "text": "This lounge is asking for a stronger focal point before it can support calmer conversation, because the room currently splits attention between the doorway, seating zone, and decorative surfaces instead of offering one settled visual anchor."},
            {"id": "what_helps", "text": "The east side already carries useful growth energy through its light and openness, so the pieces placed there should stay deliberate, visible, and easy to maintain rather than crowded by decorative extras."},
            {"id": "what_blocks", "text": "Flow is being slowed by clutter near the main circulation path and by too many competing visual anchors, which makes the room ask for attention before it can offer calm."},
            {"id": "practical_fixes", "text": "Clear the path from the door to the sofa, remove one oversized decorative item, shift the lamp so the entry feels open, and place one healthier plant near the east wall to support growth without adding noise."},
            {"id": "action_plan", "text": "Start with the circulation path first because that will change the room fastest. Next, settle the focal point and remove the extra object creating visual static. After one evening in the room, observe whether your body relaxes sooner when you enter."},
        ]
    }

    result = validate_product_payload("feng_shui", payload)

    assert result.valid is True


def test_feng_shui_validator_rejects_thin_practical_plan() -> None:
    payload = {
        "sections": [
            {"id": "overview", "text": "This lounge has a room layout issue."},
            {"id": "what_helps", "text": "The room has some useful support."},
            {"id": "what_blocks", "text": "The room has some blockages."},
            {"id": "practical_fixes", "text": "Make it nicer."},
            {"id": "action_plan", "text": "Try improving the room soon."},
        ]
    }

    result = validate_product_payload("feng_shui", payload)

    assert result.valid is False
    assert "feng_shui_practical_fixes_not_actionable" in result.issues
    assert "feng_shui_action_plan_too_thin" in result.issues
