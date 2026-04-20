from __future__ import annotations

import os
from dataclasses import dataclass

from .types import GenerationContext


def _env(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value or default


DEFAULT_ANTHROPIC_TEXT_MODEL = _env(
    "BEDROCK_MODEL_CLAUDE_OPUS",
    _env("BEDROCK_FULL_MODEL", "us.amazon.nova-pro-v1:0"),
)
DEFAULT_NOVA_PREVIEW_MODEL = _env("BEDROCK_PREVIEW_MODEL", "us.amazon.nova-lite-v1:0")
DEFAULT_NOVA_FULL_MODEL = _env("BEDROCK_FULL_MODEL", "us.amazon.nova-pro-v1:0")
DEFAULT_VISION_MODEL = _env("PALM_VISION_MODEL", DEFAULT_NOVA_FULL_MODEL)
DEFAULT_FENG_SHUI_VISION_MODEL = _env("FENG_SHUI_VISION_MODEL", DEFAULT_NOVA_FULL_MODEL)


@dataclass(frozen=True)
class ProductRoute:
    product_key: str
    preview_profile_id: str
    full_profile_id: str
    preview_model_id: str
    full_model_id: str
    fallback_model_id: str
    preview_max_tokens: int
    full_max_tokens: int
    persona_hint: str

    def profile_id_for_surface(self, surface: str) -> str:
        return self.preview_profile_id if surface == "preview" else self.full_profile_id

    def model_id_for_surface(self, surface: str) -> str:
        return self.preview_model_id if surface == "preview" else self.full_model_id

    def max_tokens_for_surface(self, surface: str) -> int:
        return self.preview_max_tokens if surface == "preview" else self.full_max_tokens


PRODUCT_ROUTES: dict[str, ProductRoute] = {
    "daily": ProductRoute(
        product_key="daily",
        preview_profile_id="daily_retention",
        full_profile_id="full_premium",
        preview_model_id=_env("MYSTIC_ROUTE_DAILY_PREVIEW_MODEL", DEFAULT_NOVA_PREVIEW_MODEL),
        full_model_id=_env("MYSTIC_ROUTE_DAILY_FULL_MODEL", DEFAULT_ANTHROPIC_TEXT_MODEL),
        fallback_model_id=_env("MYSTIC_ROUTE_DAILY_FALLBACK_MODEL", DEFAULT_NOVA_FULL_MODEL),
        preview_max_tokens=1000,
        full_max_tokens=2600,
        persona_hint="psychic_best_friend",
    ),
    "lunar": ProductRoute(
        product_key="lunar",
        preview_profile_id="preview_mystic",
        full_profile_id="full_premium",
        preview_model_id=_env("MYSTIC_ROUTE_LUNAR_PREVIEW_MODEL", DEFAULT_NOVA_PREVIEW_MODEL),
        full_model_id=_env("MYSTIC_ROUTE_LUNAR_FULL_MODEL", DEFAULT_ANTHROPIC_TEXT_MODEL),
        fallback_model_id=_env("MYSTIC_ROUTE_LUNAR_FALLBACK_MODEL", DEFAULT_NOVA_FULL_MODEL),
        preview_max_tokens=1200,
        full_max_tokens=2600,
        persona_hint="yearkeeper",
    ),
    "tarot": ProductRoute(
        product_key="tarot",
        preview_profile_id="preview_mystic",
        full_profile_id="full_premium",
        preview_model_id=_env("MYSTIC_ROUTE_TAROT_PREVIEW_MODEL", DEFAULT_NOVA_PREVIEW_MODEL),
        full_model_id=_env("MYSTIC_ROUTE_TAROT_FULL_MODEL", DEFAULT_ANTHROPIC_TEXT_MODEL),
        fallback_model_id=_env("MYSTIC_ROUTE_TAROT_FALLBACK_MODEL", DEFAULT_NOVA_FULL_MODEL),
        preview_max_tokens=1000,
        full_max_tokens=2800,
        persona_hint="ancient_tarot_reader",
    ),
    "full_reading": ProductRoute(
        product_key="full_reading",
        preview_profile_id="preview_mystic",
        full_profile_id="full_premium",
        preview_model_id=_env("MYSTIC_ROUTE_FULL_READING_PREVIEW_MODEL", DEFAULT_NOVA_PREVIEW_MODEL),
        full_model_id=_env("MYSTIC_ROUTE_FULL_READING_FULL_MODEL", DEFAULT_ANTHROPIC_TEXT_MODEL),
        fallback_model_id=_env("MYSTIC_ROUTE_FULL_READING_FALLBACK_MODEL", DEFAULT_NOVA_FULL_MODEL),
        preview_max_tokens=1100,
        full_max_tokens=4200,
        persona_hint="flagship_mystic",
    ),
    "palm": ProductRoute(
        product_key="palm",
        preview_profile_id="preview_mystic",
        full_profile_id="full_premium",
        preview_model_id=_env("MYSTIC_ROUTE_PALM_PREVIEW_MODEL", DEFAULT_NOVA_PREVIEW_MODEL),
        full_model_id=_env("MYSTIC_ROUTE_PALM_FULL_MODEL", DEFAULT_ANTHROPIC_TEXT_MODEL),
        fallback_model_id=_env("MYSTIC_ROUTE_PALM_FALLBACK_MODEL", DEFAULT_VISION_MODEL),
        preview_max_tokens=1200,
        full_max_tokens=2600,
        persona_hint="palm_synthesis",
    ),
    "compatibility": ProductRoute(
        product_key="compatibility",
        preview_profile_id="preview_mystic",
        full_profile_id="full_premium",
        preview_model_id=_env("MYSTIC_ROUTE_COMPATIBILITY_PREVIEW_MODEL", DEFAULT_NOVA_PREVIEW_MODEL),
        full_model_id=_env("MYSTIC_ROUTE_COMPATIBILITY_FULL_MODEL", DEFAULT_ANTHROPIC_TEXT_MODEL),
        fallback_model_id=_env("MYSTIC_ROUTE_COMPATIBILITY_FALLBACK_MODEL", DEFAULT_NOVA_FULL_MODEL),
        preview_max_tokens=1100,
        full_max_tokens=2400,
        persona_hint="relationship_reader",
    ),
    "feng_shui": ProductRoute(
        product_key="feng_shui",
        preview_profile_id="grounded_clarity",
        full_profile_id="grounded_clarity",
        preview_model_id=_env("MYSTIC_ROUTE_FENG_SHUI_PREVIEW_MODEL", DEFAULT_NOVA_PREVIEW_MODEL),
        full_model_id=_env("MYSTIC_ROUTE_FENG_SHUI_FULL_MODEL", DEFAULT_ANTHROPIC_TEXT_MODEL),
        fallback_model_id=_env("MYSTIC_ROUTE_FENG_SHUI_FALLBACK_MODEL", DEFAULT_FENG_SHUI_VISION_MODEL),
        preview_max_tokens=1000,
        full_max_tokens=2400,
        persona_hint="practical_astrologer",
    ),
}


FLOW_TO_PRODUCT_KEY = {
    "daily_horoscope": "daily",
    "lunar_new_year_solo": "lunar",
    "tarot_solo": "tarot",
    "palm_solo": "palm",
    "compatibility": "compatibility",
    "feng_shui": "feng_shui",
    "combined": "full_reading",
    "sun_moon_solo": "full_reading",
}


def resolve_product_key(*, flow_type: str, object_type: str | None = None) -> str:
    if flow_type in FLOW_TO_PRODUCT_KEY:
        return FLOW_TO_PRODUCT_KEY[flow_type]
    if object_type == "compatibility":
        return "compatibility"
    if object_type == "feng_shui":
        return "feng_shui"
    return "full_reading"


def get_product_route(*, flow_type: str, surface: str, object_type: str | None = None) -> ProductRoute:
    product_key = resolve_product_key(flow_type=flow_type, object_type=object_type)
    return PRODUCT_ROUTES[product_key]


def get_product_route_for_context(context: GenerationContext) -> ProductRoute:
    return get_product_route(flow_type=context.flow_type, surface=context.surface, object_type=context.object_type)
