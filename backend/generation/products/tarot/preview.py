from __future__ import annotations

from .mapper import map_tarot_preview


def build_tarot_preview_payload(*, normalized, metadata, unlock_price, product_id, entitlements, astrology_facts, tarot_payload):
    mapped = map_tarot_preview(normalized)
    teaser_text = mapped['card_message'] or mapped['guidance_teaser'] or mapped['headline']
    return {
        'teaser_text': teaser_text,
        'headline': mapped['headline'],
        'card_message': mapped['card_message'],
        'guidance_teaser': mapped['guidance_teaser'],
        'deeper_layer_teaser': mapped['deeper_layer_teaser'],
        'unlock_price': unlock_price,
        'product_id': product_id,
        'entitlements': entitlements,
        'astrology_facts': astrology_facts,
        'tarot': tarot_payload,
        'flow_type': 'tarot_solo',
        'metadata': {
            'persona_id': metadata.persona_id,
            'llm_profile_id': metadata.llm_profile_id,
            'prompt_version': metadata.prompt_version,
            'theme_tags': metadata.theme_tags,
            'headline': metadata.headline,
            'model': metadata.model_id,
        },
    }
