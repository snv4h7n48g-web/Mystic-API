from geocoding_service import GeocodingService


def test_geocode_is_case_insensitive_for_cached_locations() -> None:
    service = GeocodingService()

    result = service.geocode("Melbourne, Australia")
    assert result == (-37.8136, 144.9631)

    result_upper = service.geocode("MELBOURNE")
    assert result_upper == (-37.8136, 144.9631)


def test_geocode_returns_none_for_unknown_location() -> None:
    service = GeocodingService()
    assert service.geocode("Atlantis") is None


def test_suggest_locations_honors_limit_and_structure() -> None:
    service = GeocodingService()
    suggestions = service.suggest_locations("s", limit=3)

    assert len(suggestions) <= 3
    assert all("label" in s and "normalized" in s and "verified" in s for s in suggestions)
    assert all(s["verified"] is True for s in suggestions)


def test_geocode_with_fallback_returns_default_for_unknown() -> None:
    service = GeocodingService()
    fallback = (1.23, 4.56)

    assert service.geocode_with_fallback("Unknown place", fallback=fallback) == fallback
