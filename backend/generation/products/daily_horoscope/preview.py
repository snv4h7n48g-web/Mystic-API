from __future__ import annotations

from .mapper import map_daily_preview


def build_daily_horoscope_preview_payload(*, normalized, metadata, unlock_price, product_id, entitlements, astrology_facts):
    mapped = map_daily_preview(normalized)
    return {
        'teaser_text': mapped['headline'],
        'headline': mapped['headline'],
        'today_energy': mapped['today_energy'],
        'best_move_teaser': mapped['best_move_teaser'],
        'watch_out_teaser': mapped['watch_out_teaser'],
        'deeper_layer_teaser': mapped['deeper_layer_teaser'],
        'unlock_price': unlock_price,
        'product_id': product_id,
        'entitlements': entitlements,
        'astrology_facts': astrology_facts,
        'flow_type': 'daily_horoscope',
        'metadata': {
            'persona_id': metadata.persona_id,
            'llm_profile_id': metadata.llm_profile_id,
            'prompt_version': metadata.prompt_version,
            'theme_tags': metadata.theme_tags,
            'headline': metadata.headline,
            'model': metadata.model_id,
        },
    }
