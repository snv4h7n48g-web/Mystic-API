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

    assert "east" in mapped["bagua_map"].lower()
    assert "circulation" in mapped["energy_flow"].lower() or "flow" in mapped["energy_flow"].lower()
    assert "clear the path" in mapped["priority_actions"].lower()
    assert "stabilize one focal zone" in mapped["recommendations"].lower()
    assert "revisit the room" in mapped["guidance"].lower()


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
    assert "north" in mapped["bagua_map"].lower()
    assert "1." in mapped["priority_actions"]

