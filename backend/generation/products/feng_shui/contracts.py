from __future__ import annotations

PRODUCT_KEY = "feng_shui"
PROMPT_IDS = {
    "preview": "feng_shui_preview",
    "reading": "feng_shui_analysis",
}
EXPECTED_SECTION_IDS = [
    "overview",
    "bagua_map",
    "energy_flow",
    "priority_actions",
    "recommendations",
    "guidance",
]
CONTRACT_INSTRUCTION = """FENG SHUI CONTRACT:
- This is a Feng Shui analysis of a space, room, or placement situation.
- Ground the reading in rooms, layout, placement, flow, clutter, direction, or environmental features.
- The payload must resolve into product sections that feel like a real space analysis: overview, bagua map, energy flow, priority actions, recommendations, and guidance.
- Priority actions and recommendations must be specific, practical, and immediately actionable, not generic reassurance.
- Keep the tone as environmental analysis rather than a personal tarot or astrology reading.
"""
