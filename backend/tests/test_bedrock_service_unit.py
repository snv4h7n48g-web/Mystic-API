from bedrock_service import BedrockService


def _service_without_client() -> BedrockService:
    service = BedrockService.__new__(BedrockService)
    service.preview_model = "us.amazon.nova-lite-v1:0"
    service.full_model = "us.amazon.nova-pro-v1:0"
    service.costs = {
        "us.amazon.nova-lite-v1:0": {"input": 0.00006, "output": 0.00024},
        "us.amazon.nova-pro-v1:0": {"input": 0.0008, "output": 0.0032},
    }
    return service


def test_flow_schema_combined_and_blessing_shapes() -> None:
    service = _service_without_client()

    combined = service._flow_reading_schema("combined")
    blessing = service._flow_reading_schema("blessing_solo")

    assert len(combined) == 7
    assert combined[0]["id"] == "opening_invocation"
    assert combined[-1]["id"] == "closing_prompt"

    assert len(blessing) == 3
    assert [item["id"] for item in blessing] == [
        "opening_invocation",
        "reflective_guidance",
        "closing_prompt",
    ]


def test_flow_schema_covers_all_supported_flows() -> None:
    service = _service_without_client()
    expected_lengths = {
        "combined": 7,
        "tarot_solo": 5,
        "palm_solo": 5,
        "sun_moon_solo": 5,
        "daily_horoscope": 4,
        "lunar_new_year_solo": 5,
        "blessing_solo": 3,
    }

    for flow, expected_length in expected_lengths.items():
        schema = service._flow_reading_schema(flow)
        assert len(schema) == expected_length
        assert schema[0]["id"] == "opening_invocation"
        assert schema[-1]["id"] == "closing_prompt"


def test_parse_sections_by_schema_extracts_deep_insight() -> None:
    service = _service_without_client()
    schema = service._flow_reading_schema("tarot_solo")
    text = """---OPENING---
Start here.
DEEP_INSIGHT: Extra detail one.
---TAROT_FOUNDATION---
Card thread.
DEEP_INSIGHT: Extra detail two.
---PATTERN_SYNTHESIS---
Synthesis line.
---GUIDANCE---
Practical guidance.
---CLOSING---
One question."""

    parsed = service._parse_sections_by_schema(text, schema)

    assert len(parsed) == 5
    assert parsed[0]["id"] == "opening_invocation"
    assert parsed[0]["text"] == "Start here."
    assert parsed[0]["deep_text"] == "Extra detail one."
    assert parsed[1]["id"] == "tarot_narrative"
    assert parsed[1]["deep_text"] == "Extra detail two."
    assert parsed[-1]["id"] == "closing_prompt"


def test_build_anchor_list_collects_astro_tarot_and_palm() -> None:
    service = _service_without_client()
    astrology = {
        "sun_sign": "Virgo",
        "moon_sign": "Capricorn",
        "rising_sign": "Leo",
        "dominant_element": "Earth",
        "dominant_planet": "Mercury",
        "top_aspects": [{"a": "Sun", "type": "Square", "b": "Moon"}],
    }
    tarot = [{"card": "Strength", "position": "past"}]
    palm = [{"feature": "life_line", "value": "long"}]

    anchors = service._build_anchor_list(astrology, tarot, palm)

    assert "Sun sign: Virgo" in anchors
    assert "Moon sign: Capricorn" in anchors
    assert "Rising sign: Leo" in anchors
    assert "Aspect: Sun Square Moon" in anchors
    assert "Tarot: Strength (past)" in anchors
    assert "Palm: life_line = long" in anchors


def test_build_anchor_list_marks_reversed_tarot_cards() -> None:
    service = _service_without_client()

    anchors = service._build_anchor_list(
        {},
        [{"card": "The Hanged Man", "position": "guidance", "orientation": "reversed"}],
        [],
    )

    assert "Tarot: The Hanged Man (guidance, reversed)" in anchors


def test_calculate_cost_uses_per_model_rates() -> None:
    service = _service_without_client()

    lite_cost = service._calculate_cost("us.amazon.nova-lite-v1:0", 1000, 1000)
    pro_cost = service._calculate_cost("us.amazon.nova-pro-v1:0", 1000, 1000)
    unknown = service._calculate_cost("missing", 1000, 1000)

    assert lite_cost == 0.0003
    assert pro_cost == 0.004
    assert unknown == 0.0
