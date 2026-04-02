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
