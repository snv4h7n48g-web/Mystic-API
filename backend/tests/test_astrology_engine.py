from astrology_engine import AstrologyEngine


def test_calculate_chinese_zodiac_2025() -> None:
    engine = AstrologyEngine()
    result = engine.calculate_chinese_zodiac(2025)

    assert result["animal"] == "Snake"
    assert result["element"] == "Wood"
    assert result["combined"] == "Wood Snake"


def test_generate_chart_without_birth_time() -> None:
    engine = AstrologyEngine()
    chart = engine.generate_chart("1990-12-31", birth_time=None, birth_time_unknown=True)

    assert chart["sun_sign"] == "Capricorn"
    assert chart["moon_sign"] is None
    assert chart["rising_sign"] is None
    assert chart["has_time"] is False


def test_generate_chart_with_birth_time_populates_time_based_fields() -> None:
    engine = AstrologyEngine()
    chart = engine.generate_chart("1990-12-31", birth_time="08:30", birth_time_unknown=False)

    assert chart["sun_sign"] == "Capricorn"
    assert chart["moon_sign"] is not None
    assert chart["rising_sign"] is not None
    assert chart["has_time"] is True


def test_calculate_synastry_returns_structured_aspects() -> None:
    engine = AstrologyEngine()
    person1 = {"sun_sign": "Aries", "moon_sign": "Leo", "rising_sign": "Gemini"}
    person2 = {"sun_sign": "Sagittarius", "moon_sign": "Aries", "rising_sign": "Libra"}

    result = engine.calculate_synastry(person1, person2)

    assert "aspects" in result
    assert isinstance(result["aspects"], list)
    assert all("a" in x and "b" in x and "type" in x for x in result["aspects"])


def test_generate_chart_includes_dominant_modality() -> None:
    engine = AstrologyEngine()
    chart = engine.generate_chart("1990-12-31", birth_time="08:30", birth_time_unknown=False)

    assert chart["dominant_modality"] in {"Cardinal", "Fixed", "Mutable"}


def test_generate_persistent_profile_returns_premium_themes() -> None:
    engine = AstrologyEngine()
    chart = engine.generate_chart("1990-12-31", birth_time="08:30", birth_time_unknown=False)
    profile = engine.generate_persistent_profile(chart, birth_location="Melbourne, Australia")

    assert profile["dominant_element"] == chart["dominant_element"]
    assert profile["dominant_modality"] == chart["dominant_modality"]
    assert len(profile["signature"]) == 3
    theme_ids = {theme["id"] for theme in profile["themes"]}
    assert {"relationships", "work", "parent-child", "growth-edge"}.issubset(theme_ids)
