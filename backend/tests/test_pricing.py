from datetime import date

from pricing import (
    PRODUCTS,
    ProductSKU,
    _seasonal_available,
    calculate_revenue,
    validate_purchase,
)


def test_validate_purchase_rejects_unknown_product() -> None:
    assert validate_purchase("unknown", []) is False


def test_validate_purchase_blocks_duplicate_purchase() -> None:
    existing = [ProductSKU.READING_BASIC]
    assert validate_purchase(ProductSKU.READING_BASIC, existing) is False


def test_validate_purchase_requires_prerequisite_for_addon() -> None:
    assert validate_purchase(ProductSKU.PALM_ADDON, []) is False
    assert validate_purchase(ProductSKU.PALM_ADDON, [ProductSKU.READING_BASIC]) is True


def test_lunar_forecast_seasonal_window() -> None:
    product = PRODUCTS[ProductSKU.LUNAR_FORECAST]

    assert _seasonal_available(product, today=date(2026, 1, 20)) is True
    assert _seasonal_available(product, today=date(2026, 2, 28)) is True
    assert _seasonal_available(product, today=date(2026, 1, 19)) is False
    assert _seasonal_available(product, today=date(2026, 3, 1)) is False


def test_new_beginnings_bundle_declares_lunar_step() -> None:
    product = PRODUCTS[ProductSKU.BUNDLE_NEW_BEGINNINGS]

    assert product["is_bundle"] is True
    assert "lunar_forecast" in product["features"]
    assert "feng_shui" in product["features"]
    assert product["bundle_steps"] == [
        "core_reading",
        "lunar_new_year",
        "feng_shui_single",
    ]


def test_life_harmony_bundle_keeps_cross_surface_sequence() -> None:
    product = PRODUCTS[ProductSKU.BUNDLE_LIFE_HARMONY]

    assert product["is_bundle"] is True
    assert "compatibility" in product["features"]
    assert "feng_shui" in product["features"]
    assert product["bundle_steps"] == [
        "core_reading",
        "compatibility",
        "feng_shui_full",
    ]


def test_subscription_includes_cross_surface_features() -> None:
    product = PRODUCTS[ProductSKU.DAILY_ASTRO_TAROT]

    assert product["is_subscription"] is True
    for feature in ["compatibility", "feng_shui", "palm", "deep", "lunar_forecast"]:
        assert feature in product["features"]


def test_complete_reading_copy_avoids_hard_ai_claim_language() -> None:
    product = PRODUCTS[ProductSKU.READING_COMPLETE]

    assert 'AI palm analysis' not in product['description']
    assert 'automated palm interpretation' in product['description']


def test_calculate_revenue_sums_known_products_only() -> None:
    revenue = calculate_revenue(
        [ProductSKU.READING_BASIC, ProductSKU.LUNAR_FORECAST, "missing_product"]
    )

    assert revenue["gross_total"] == 2.99
    assert revenue["net_total"] == 2.09
    assert revenue["apple_cut"] == 0.90
    assert len(revenue["breakdown"]) == 2
