from generation.products.feng_shui.mapper import map_feng_shui_analysis
from generation.types import NormalizedMysticOutput


def test_feng_shui_mapper_creates_product_specific_sections_with_actionable_guidance() -> None:
    normalized = NormalizedMysticOutput(
        opening_hook="The lounge is ready to support growth, but only if the layout stops splitting the eye in three directions.",
        current_pattern="Facing east, this room should build momentum, yet the current arrangement keeps the room visually busy instead of focused.",
        emotional_truth="The room is carrying low-grade friction because circulation and focal points are competing with one another.",
        practical_guidance="Clear the path between the entry and the main seating zone, then remove one object that is visually crowding the eastern side of the room.",
        what_this_is_asking_of_you="Treat the room like a working support system: stabilize one focal zone first, then let every object justify its place.",
        your_next_move="Start with the fastest visible shift: anchor the main seating area and stop the eye from bouncing between too many surfaces.",
        next_return_invitation="Revisit the room after the first round of changes and notice whether the body relaxes more quickly on entry.",
        premium_teaser="Once the room stops leaking attention, the wealth goal has a better structure to land in.",
        theme_tags=["feng_shui"],
        reading_opening="This room is less blocked than diluted: the support is there, but it needs clearer structure.",
    )

    mapped = map_feng_shui_analysis(
        normalized,
        analysis={
            "analysis_type": "single_room",
            "room_purpose": "lounge",
            "user_goals": "wealth and steadier momentum",
            "compass_direction": "east",
        },
    )

    assert "east" in mapped["what_helps"].lower()
    assert "circulation" in mapped["what_blocks"].lower() or "flow" in mapped["what_blocks"].lower()
    assert "clear the path" in mapped["practical_fixes"].lower()
    assert "revisit the room" in mapped["action_plan"].lower()


def test_feng_shui_mapper_prefers_explicit_action_led_sections() -> None:
    normalized = NormalizedMysticOutput(
        opening_hook="Generic opening.",
        current_pattern="Generic pattern.",
        emotional_truth="Generic block.",
        practical_guidance="Generic guidance.",
        next_return_invitation="Generic return.",
        theme_tags=["feng_shui"],
        feng_shui_sections={
            "overview": "The office is not failing; it is over-signalling. The desk, doorway, and storage all compete to tell the room what it is for.",
            "what_helps": "The window side already gives the room useful lift and should stay visually clear because it is the part of the office that restores attention fastest.",
            "what_blocks": "The blocked path behind the chair and crowded shelf create a pressure point that makes the room feel unfinished before work even begins.",
            "practical_fixes": "Move the spare chair away from the doorway, clear the shelf nearest the desk, place one plant near the window, and anchor the work zone with one lamp.",
            "action_plan": "Start with the doorway path, then reset the desk surface, then observe whether sitting down feels less braced after a full work session.",
        },
    )

    mapped = map_feng_shui_analysis(
        normalized,
        analysis={
            "analysis_type": "single_room",
            "room_purpose": "office",
            "user_goals": "focus",
            "compass_direction": "east",
        },
    )

    assert mapped["overview"].startswith("The office is not failing")
    assert "window side" in mapped["what_helps"]
    assert "blocked path" in mapped["what_blocks"]
    assert "spare chair" in mapped["practical_fixes"]
    assert "doorway path" in mapped["action_plan"]


def test_feng_shui_mapper_backfills_missing_practical_guidance_from_room_context() -> None:
    normalized = NormalizedMysticOutput(
        opening_hook="",
        current_pattern="",
        emotional_truth="",
        practical_guidance="",
        next_return_invitation="",
        premium_teaser="",
        theme_tags=["feng_shui"],
    )

    mapped = map_feng_shui_analysis(
        normalized,
        analysis={
            "analysis_type": "single_room",
            "room_purpose": "bedroom",
            "user_goals": "rest and emotional steadiness",
            "compass_direction": "north",
        },
    )

    assert "bedroom" in mapped["overview"].lower()
    assert "north" in mapped["what_helps"].lower()
    assert "1." in mapped["practical_fixes"]
    assert "24 hours" in mapped["action_plan"]
