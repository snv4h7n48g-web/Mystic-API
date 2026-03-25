from __future__ import annotations

from .mapper import map_daily_reading


def build_daily_horoscope_reading_payload(*, normalized, metadata):
    mapped = map_daily_reading(normalized)
    sections = [
        {'id': 'today_theme', 'title': "TODAY'S THEME", 'text': mapped['today_theme']},
        {'id': 'today_energy', 'title': "TODAY'S ENERGY", 'text': mapped['today_energy']},
        {'id': 'best_move', 'title': 'BEST MOVE', 'text': mapped['best_move']},
        {'id': 'watch_out_for', 'title': 'WATCH OUT FOR', 'text': mapped['watch_out_for']},
        {'id': 'people_energy', 'title': 'PEOPLE ENERGY', 'text': mapped['people_energy']},
        {'id': 'work_focus', 'title': 'WORK / FOCUS', 'text': mapped['work_focus']},
        {'id': 'timing', 'title': 'TIMING', 'text': mapped['timing']},
        {'id': 'closing_guidance', 'title': 'CLOSING GUIDANCE', 'text': mapped['closing_guidance']},
    ]
    sections = [section for section in sections if section['text'] and section['text'].strip()]
    return {
        'sections': sections,
        'full_text': '\n\n'.join(section['text'] for section in sections),
        'metadata': {
            'persona_id': metadata.persona_id,
            'llm_profile_id': metadata.llm_profile_id,
            'prompt_version': metadata.prompt_version,
            'theme_tags': metadata.theme_tags,
            'headline': metadata.headline,
            'model': metadata.model_id,
            'flow_type': 'daily_horoscope',
        },
    }
