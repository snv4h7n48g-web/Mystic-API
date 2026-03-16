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


def test_calculate_revenue_sums_known_products_only() -> None:
    revenue = calculate_revenue(
        [ProductSKU.READING_BASIC, ProductSKU.LUNAR_FORECAST, "missing_product"]
    )

    assert revenue["gross_total"] == 2.99
    assert revenue["net_total"] == 2.09
    assert revenue["apple_cut"] == 0.90
    assert len(revenue["breakdown"]) == 2
