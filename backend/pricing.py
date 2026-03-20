"""
Pricing configuration for tiered product offerings.
Defines SKUs, features, and validation logic.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import date


class ProductTier(str, Enum):
    """Product tier enumeration."""
    BASIC = "basic"
    COMPLETE = "complete"


class ProductSKU:
    """Product SKU definitions."""
    
    # Base products
    READING_BASIC = "reading_basic_199"
    READING_COMPLETE = "reading_complete_299"
    
    # Add-ons
    PALM_ADDON = "palm_addon_100"
    DEEP_INSIGHT = "deep_insight_199"
    FOLLOWUP_QUESTION = "followup_question_099"  # Future

    # Subscriptions
    DAILY_ASTRO_TAROT = "subscription_daily_999"

    # Seasonal add-ons
    LUNAR_FORECAST = "lunar_forecast_100"

    # Compatibility
    COMPATIBILITY = "compatibility_399"

    # Blessing offerings
    BLESSING_OFFERING_100 = "blessing_offering_100"
    BLESSING_OFFERING_300 = "blessing_offering_300"
    BLESSING_OFFERING_500 = "blessing_offering_500"

    # Feng Shui
    FENG_SHUI_SINGLE = "feng_shui_single_499"
    FENG_SHUI_FULL = "feng_shui_full_999"
    FENG_SHUI_FLOOR = "feng_shui_floor_299"

    # Bundles
    BUNDLE_NEW_BEGINNINGS = "bundle_new_beginnings_1299"
    BUNDLE_LIFE_HARMONY = "bundle_life_harmony_1999"


# Product catalog
PRODUCTS = {
    ProductSKU.READING_BASIC: {
        "id": ProductSKU.READING_BASIC,
        "name": "Astrology + Tarot Reading",
        "tier": ProductTier.BASIC,
        "price_usd": 1.99,
        "price_after_apple_cut": 1.39,  # 30% to Apple
        "features": ["astrology", "tarot"],
        "description": "Personalized astrology and tarot synthesis"
    },
    ProductSKU.READING_COMPLETE: {
        "id": ProductSKU.READING_COMPLETE,
        "name": "Complete Reading (+ Palm)",
        "tier": ProductTier.COMPLETE,
        "price_usd": 2.99,
        "price_after_apple_cut": 2.09,  # 30% to Apple
        "features": ["astrology", "tarot", "palm"],
        "description": "Complete reading including automated palm interpretation"
    },
    ProductSKU.PALM_ADDON: {
        "id": ProductSKU.PALM_ADDON,
        "name": "Palm Reading Add-on",
        "tier": None,
        "price_usd": 1.00,
        "price_after_apple_cut": 0.70,  # 30% to Apple
        "features": ["palm"],
        "requires": ProductSKU.READING_BASIC,
        "description": "Add palm reading to existing basic reading"
    },
    ProductSKU.DEEP_INSIGHT: {
        "id": ProductSKU.DEEP_INSIGHT,
        "name": "Deep Insight Expansion",
        "tier": None,
        "price_usd": 1.99,
        "price_after_apple_cut": 1.39,
        "features": ["deep"],
        "description": "Extended, in-depth interpretation for each section"
    },
    ProductSKU.DAILY_ASTRO_TAROT: {
        "id": ProductSKU.DAILY_ASTRO_TAROT,
        "name": "Daily Tarot + Astrology",
        "tier": None,
        "price_usd": 9.99,
        "price_after_apple_cut": 6.99,  # 30% to Apple
        "features": [
            "subscription",
            "all_access",
            "astrology",
            "tarot",
            "daily",
            "palm",
            "compatibility",
            "feng_shui",
            "lunar_forecast",
            "deep",
        ],
        "description": "All-access subscription across Mystic services",
        "is_subscription": True,
        "billing_period": "monthly"
    },
    ProductSKU.LUNAR_FORECAST: {
        "id": ProductSKU.LUNAR_FORECAST,
        "name": "Lunar New Year Forecast",
        "tier": None,
        "price_usd": 1.00,
        "price_after_apple_cut": 0.70,
        "features": ["lunar_forecast"],
        "description": "Year-ahead forecast grounded in your Chinese zodiac",
        "is_addon": True,
        "seasonal_start": "01-20",
        "seasonal_end": "02-28"
    },
    ProductSKU.COMPATIBILITY: {
        "id": ProductSKU.COMPATIBILITY,
        "name": "Compatibility Reading",
        "tier": None,
        "price_usd": 3.99,
        "price_after_apple_cut": 2.79,
        "features": ["compatibility"],
        "description": "Two-person compatibility reading",
    },
    ProductSKU.BLESSING_OFFERING_100: {
        "id": ProductSKU.BLESSING_OFFERING_100,
        "name": "Blessing Offering",
        "tier": None,
        "price_usd": 1.00,
        "price_after_apple_cut": 0.70,
        "features": ["blessing_offering"],
        "description": "Small blessing offering"
    },
    ProductSKU.BLESSING_OFFERING_300: {
        "id": ProductSKU.BLESSING_OFFERING_300,
        "name": "Blessing Offering",
        "tier": None,
        "price_usd": 3.00,
        "price_after_apple_cut": 2.10,
        "features": ["blessing_offering"],
        "description": "Generous blessing offering"
    },
    ProductSKU.BLESSING_OFFERING_500: {
        "id": ProductSKU.BLESSING_OFFERING_500,
        "name": "Blessing Offering",
        "tier": None,
        "price_usd": 5.00,
        "price_after_apple_cut": 3.50,
        "features": ["blessing_offering"],
        "description": "Abundant blessing offering"
    },
    ProductSKU.FENG_SHUI_SINGLE: {
        "id": ProductSKU.FENG_SHUI_SINGLE,
        "name": "Feng Shui: Single Room",
        "tier": None,
        "price_usd": 4.99,
        "price_after_apple_cut": 3.49,
        "features": ["feng_shui"],
        "description": "Single room Feng Shui analysis"
    },
    ProductSKU.FENG_SHUI_FULL: {
        "id": ProductSKU.FENG_SHUI_FULL,
        "name": "Feng Shui: Full Home",
        "tier": None,
        "price_usd": 9.99,
        "price_after_apple_cut": 6.99,
        "features": ["feng_shui"],
        "description": "Full home Feng Shui analysis"
    },
    ProductSKU.FENG_SHUI_FLOOR: {
        "id": ProductSKU.FENG_SHUI_FLOOR,
        "name": "Feng Shui: Floor Plan",
        "tier": None,
        "price_usd": 2.99,
        "price_after_apple_cut": 2.09,
        "features": ["feng_shui"],
        "description": "Floor plan Feng Shui analysis"
    },
    ProductSKU.BUNDLE_NEW_BEGINNINGS: {
        "id": ProductSKU.BUNDLE_NEW_BEGINNINGS,
        "name": "New Beginnings Bundle",
        "tier": None,
        "price_usd": 12.99,
        "price_after_apple_cut": 9.09,
        "features": [
            "bundle",
            "astrology",
            "tarot",
            "palm",
            "lunar_forecast",
            "feng_shui",
        ],
        "description": "Complete reading, Lunar New Year forecast, and single-room Feng Shui path",
        "is_bundle": True,
        "bundle_steps": ["core_reading", "lunar_new_year", "feng_shui_single"],
    },
    ProductSKU.BUNDLE_LIFE_HARMONY: {
        "id": ProductSKU.BUNDLE_LIFE_HARMONY,
        "name": "Complete Life Harmony Bundle",
        "tier": None,
        "price_usd": 19.99,
        "price_after_apple_cut": 13.99,
        "features": [
            "bundle",
            "astrology",
            "tarot",
            "palm",
            "compatibility",
            "feng_shui",
        ],
        "description": "Complete reading, compatibility reading, and full-home Feng Shui path",
        "is_bundle": True,
        "bundle_steps": ["core_reading", "compatibility", "feng_shui_full"],
    },
}


def _parse_seasonal_date(month_day: str, year: Optional[int] = None) -> date:
    parts = month_day.split("-")
    if len(parts) != 2:
        raise ValueError("Invalid seasonal date format")
    year = year or date.today().year
    return date(year, int(parts[0]), int(parts[1]))


def _seasonal_available(product: Dict[str, Any], today: Optional[date] = None) -> bool:
    start = product.get("seasonal_start")
    end = product.get("seasonal_end")
    if not start or not end:
        return True
    today = today or date.today()
    start_date = _parse_seasonal_date(start, today.year)
    end_date = _parse_seasonal_date(end, today.year)
    return start_date <= today <= end_date


def get_product(product_id: str) -> Dict[str, Any]:
    """
    Get product details by ID.
    
    Args:
        product_id: Product SKU identifier
        
    Returns:
        Product details dict
    """
    if product_id not in PRODUCTS:
        raise ValueError(f"Unknown product ID: {product_id}")
    
    return PRODUCTS[product_id]


def has_feature(purchased_products: List[str], feature: str) -> bool:
    """
    Check if a feature is included in purchased products.
    
    Args:
        purchased_products: List of product IDs purchased
        feature: Feature name to check (e.g., "palm", "astrology")
        
    Returns:
        True if feature is included
    """
    for product_id in purchased_products:
        if product_id in PRODUCTS:
            product = PRODUCTS[product_id]
            if feature in product.get("features", []):
                return True
    
    return False


def validate_purchase(product_id: str, existing_purchases: List[str]) -> bool:
    """
    Validate if a product can be purchased.
    
    Args:
        product_id: Product being purchased
        existing_purchases: List of already purchased product IDs
        
    Returns:
        True if purchase is valid
    """
    if product_id not in PRODUCTS:
        return False
    
    product = PRODUCTS[product_id]

    # Check seasonal availability
    if not _seasonal_available(product):
        return False
    
    # Check if product requires another product first
    if "requires" in product:
        required = product["requires"]
        if required not in existing_purchases:
            return False
    
    # Check if already purchased
    if product_id in existing_purchases:
        return False
    
    return True


def calculate_revenue(purchased_products: List[str]) -> Dict[str, float]:
    """
    Calculate revenue breakdown for purchased products.
    
    Args:
        purchased_products: List of product IDs purchased
        
    Returns:
        Dict with gross, net (after Apple), and breakdown
    """
    gross_total = 0.0
    net_total = 0.0
    breakdown = []
    
    for product_id in purchased_products:
        if product_id in PRODUCTS:
            product = PRODUCTS[product_id]
            gross = product["price_usd"]
            net = product["price_after_apple_cut"]
            
            gross_total += gross
            net_total += net
            
            breakdown.append({
                "product_id": product_id,
                "name": product["name"],
                "gross": gross,
                "net": net
            })
    
    return {
        "gross_total": round(gross_total, 2),
        "net_total": round(net_total, 2),
        "apple_cut": round(gross_total - net_total, 2),
        "breakdown": breakdown
    }
