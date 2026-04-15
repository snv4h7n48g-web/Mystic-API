from __future__ import annotations

from .mapper import map_lunar_preview


def build_lunar_preview_payload(*, normalized, metadata, unlock_price, product_id, entitlements, astrology_facts, lunar_context=None):
    mapped = map_lunar_preview(normalized, lunar_context=lunar_context or {})
    return {
        'teaser_text': mapped['headline'] or mapped['year_symbolism_teaser'] or mapped['movement_guidance_teaser'],
        'headline': mapped['headline'],
        'cycle_theme_teaser': mapped['cycle_theme_teaser'],
        'year_symbolism_teaser': mapped['year_symbolism_teaser'],
        'welcome_release_teaser': mapped['welcome_release_teaser'],
        'movement_guidance_teaser': mapped['movement_guidance_teaser'],
        'unlock_price': unlock_price,
        'product_id': product_id,
        'entitlements': entitlements,
        'astrology_facts': astrology_facts,
        'tarot': {'spread': 'none', 'cards': []},
        'flow_type': 'lunar_new_year_solo',
        'seasonal': {'lunar_new_year': True},
        'metadata': {
            'persona_id': metadata.persona_id,
            'llm_profile_id': metadata.llm_profile_id,
            'prompt_version': metadata.prompt_version,
            'theme_tags': metadata.theme_tags,
            'headline': metadata.headline,
            'model': metadata.model_id,
            'lunar_context': lunar_context or {},
        },
    }
