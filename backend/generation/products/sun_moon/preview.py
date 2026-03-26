from __future__ import annotations

from .mapper import map_sun_moon_preview


def build_sun_moon_preview_payload(*, normalized, metadata, unlock_price, product_id, entitlements, astrology_facts):
    mapped = map_sun_moon_preview(normalized)
    return {
        'teaser_text': mapped['headline'] or mapped['foundation_teaser'] or mapped['guidance_teaser'],
        'headline': mapped['headline'],
        'foundation_teaser': mapped['foundation_teaser'],
        'synthesis_teaser': mapped['synthesis_teaser'],
        'guidance_teaser': mapped['guidance_teaser'],
        'unlock_price': unlock_price,
        'product_id': product_id,
        'entitlements': entitlements,
        'astrology_facts': astrology_facts,
        'tarot': {'spread': 'none', 'cards': []},
        'flow_type': 'sun_moon_solo',
        'metadata': {
            'persona_id': metadata.persona_id,
            'llm_profile_id': metadata.llm_profile_id,
            'prompt_version': metadata.prompt_version,
            'theme_tags': metadata.theme_tags,
            'headline': metadata.headline,
            'model': metadata.model_id,
        },
    }
