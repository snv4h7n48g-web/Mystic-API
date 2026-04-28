from __future__ import annotations

PRODUCT_KEY = "feng_shui"
PROMPT_IDS = {
    "preview": "feng_shui_preview",
    "reading": "feng_shui_analysis",
}
EXPECTED_SECTION_IDS = [
    "overview",
    "what_helps",
    "what_blocks",
    "practical_fixes",
    "action_plan",
]
CONTRACT_INSTRUCTION = """FENG SHUI CONTRACT:
- This is a Feng Shui analysis of a space, room, or placement situation.
- Ground the reading in rooms, layout, placement, flow, clutter, direction, or environmental features.
- The payload must resolve into product sections that feel like a real space analysis: overview, what helps, what blocks, practical fixes, and action plan.
- For full analysis JSON, include these additional keys with distinct content: "overview", "what_helps", "what_blocks", "practical_fixes", and "action_plan".
- Overview explains the room's main energetic diagnosis in plain language.
- What helps names the existing strengths, supportive placement, useful element cues, or layout choices that should be protected.
- What blocks names friction points: clutter, blocked circulation, harsh sightlines, competing focal points, imbalance, missing support, or direction/goal mismatch.
- Practical fixes must give at least 4 specific room changes using action verbs such as move, clear, place, add, remove, shift, soften, anchor, or open. Include why each change matters.
- Action plan must prioritise what to do first, what to do next, and what to observe afterward so the user can act without guessing.
- Do not repeat the same sentence across sections. The headline/summary can be short, but section detail must add new material.
- Keep the tone as environmental analysis rather than a personal tarot or astrology reading.
"""
