import json

from generation.parser import parse_normalized_output


def test_parser_allows_missing_next_return_invitation():
    payload = {
        "opening_hook": "Opening",
        "current_pattern": "Pattern",
        "emotional_truth": "Truth",
        "practical_guidance": "Take one clear next step.",
        "continuity_callback": None,
        "theme_tags": ["clarity"],
        "premium_teaser": "Come back to this when the pattern sharpens.",
    }

    parsed = parse_normalized_output(json.dumps(payload))

    assert parsed.next_return_invitation == "Come back to this when the pattern sharpens."


def test_parser_allows_missing_continuity_callback():
    payload = {
        "opening_hook": "Opening",
        "current_pattern": "Pattern",
        "emotional_truth": "Truth",
        "practical_guidance": "Take one clear next step.",
        "theme_tags": ["clarity"],
        "premium_teaser": "Come back to this when the pattern sharpens.",
    }

    parsed = parse_normalized_output(json.dumps(payload))

    assert parsed.continuity_callback is None


def test_parser_allows_missing_theme_tags():
    payload = {
        "opening_hook": "Opening",
        "current_pattern": "Pattern",
        "emotional_truth": "Truth",
        "practical_guidance": "Take one clear next step.",
        "premium_teaser": "Come back to this when the pattern sharpens.",
    }

    parsed = parse_normalized_output(json.dumps(payload))

    assert parsed.theme_tags == []


def test_parser_allows_missing_premium_teaser():
    payload = {
        "opening_hook": "Opening",
        "current_pattern": "Pattern",
        "emotional_truth": "Truth",
        "practical_guidance": "Take one clear next step.",
    }

    parsed = parse_normalized_output(json.dumps(payload))

    assert parsed.premium_teaser is None


def test_parser_derives_legacy_pattern_keys_from_full_reading_fields():
    payload = {
        "opening_hook": "A threshold is here.",
        "reading_opening": "A threshold is here. The reading is already pointing at the choice you keep trying to make theoretical.",
        "astrological_foundation": "Your Virgo Sun and Capricorn Moon make patience look responsible, even after it becomes delay.",
        "tarot_message": "The cards show movement fighting hesitation.",
        "signals_agree": "Every signal says the pattern is less about confusion and more about containment.",
        "what_this_is_asking_of_you": "Stop waiting for perfect emotional conditions before you honour what you already know.",
        "your_next_move": "Start by naming the clearest decision you can make, then take one visible step that turns the reading into action.",
        "theme_tags": ["clarity"],
    }

    parsed = parse_normalized_output(json.dumps(payload))

    assert parsed.current_pattern.startswith("A threshold is here.")
    assert parsed.emotional_truth.startswith("Every signal says")
