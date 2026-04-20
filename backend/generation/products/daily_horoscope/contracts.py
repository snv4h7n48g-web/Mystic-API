from __future__ import annotations

PRODUCT_KEY = "daily"
PROMPT_IDS = {
    "preview": "daily_horoscope_preview",
    "reading": "daily_horoscope_reading",
}
EXPECTED_SECTION_IDS = [
    "today_theme",
    "today_energy",
    "best_move",
    "watch_out_for",
    "people_energy",
    "work_focus",
    "timing",
    "closing_guidance",
]
CONTRACT_INSTRUCTION = """DAILY HOROSCOPE CONTRACT:
- This is a true daily reading about today only.
- Do not drift into year-ahead framing, Lunar New Year framing, or seasonal annual guidance.
- Keep the reading shape recognisably daily: today's theme, today's energy, best move, watch out for, people energy, work/focus, timing, closing guidance.
- Timing language should stay immediate: today, this morning, this afternoon, tonight, the next few hours.
- For the full reading, all eight daily sections should be present and materially developed.
- Each daily section must contain distinct content. Do not repeat the same sentence across theme, energy, best move, watch out for, people energy, work/focus, timing, or closing guidance.
- In daily_sections, headline should be one crisp sentence; detail should be 2-4 fresh sentences that deepen the section instead of paraphrasing the headline.
- Translate astrology into practical day-language. The user should understand what to notice, do, avoid, or prioritise today.
"""
