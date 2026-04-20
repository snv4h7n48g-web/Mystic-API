from generation.parser import parse_normalized_output
from generation.products.daily_horoscope.reading import (
    build_daily_horoscope_reading_payload,
)
from generation.types import GenerationMetadata
from generation.validators import validate_product_payload


def _metadata() -> GenerationMetadata:
    return GenerationMetadata(
        persona_id="psychic_best_friend",
        llm_profile_id="full_premium",
        prompt_version="mystic-v3",
        model_id="test-model",
        theme_tags=["daily"],
        headline="Today asks for a cleaner rhythm.",
    )


def test_parse_normalized_output_accepts_daily_sections() -> None:
    normalized = parse_normalized_output(
        """
        {
          "opening_hook": "Today asks for a cleaner rhythm.",
          "current_pattern": "You are sharper than the noise around you.",
          "emotional_truth": "Irritation spikes when you let small inefficiencies pile up.",
          "practical_guidance": "Choose one priority and finish it before lunch.",
          "next_return_invitation": "Reset tonight and check back tomorrow.",
          "theme_tags": ["daily"],
          "daily_sections": {
            "timing": {
              "headline": "Your cleanest decision window lands before lunch.",
              "detail": "Use the first half of the day for anything that needs precision, sign-off, or clear thinking. By late afternoon, other people's urgency is more likely to muddy the signal."
            }
          }
        }
        """
    )

    assert normalized.daily_sections["timing"]["headline"].startswith(
        "Your cleanest decision window"
    )


def test_daily_reading_payload_prefers_layered_daily_sections() -> None:
    normalized = parse_normalized_output(
        """
        {
          "opening_hook": "Today asks for a cleaner rhythm.",
          "current_pattern": "You are sharper than the noise around you.",
          "emotional_truth": "Irritation spikes when you let small inefficiencies pile up.",
          "practical_guidance": "Choose one priority and finish it before lunch.",
          "next_return_invitation": "Reset tonight and check back tomorrow.",
          "theme_tags": ["daily"],
          "daily_sections": {
            "today_theme": {
              "headline": "Today rewards clean execution over dramatic effort.",
              "detail": "The win is not speed for its own sake. It is the kind of discipline that keeps small tasks from multiplying into a low-grade drain by mid-afternoon."
            },
            "today_energy": {
              "headline": "Mental clarity is high when you keep the environment simple.",
              "detail": "The astrology is pushing toward practical discrimination rather than inspiration-chasing. Reduce inputs, tighten the list, and you will feel the day open up."
            },
            "best_move": {
              "headline": "Finish the one thing that removes friction for everything else.",
              "detail": "Do the task that clears backlog, answers the key message, or makes the next decision easier. Momentum will build once the hidden bottleneck is gone."
            },
            "watch_out_for": {
              "headline": "Do not let competence slide into micro-irritation.",
              "detail": "The day can turn brittle if you start silently judging every delay around you. Name the standard, make the correction, and move on."
            },
            "people_energy": {
              "headline": "People respond best to calm precision today.",
              "detail": "You do not need extra charm to get traction. A short, direct ask will land better than over-explaining or softening the point."
            },
            "work_focus": {
              "headline": "Administrative cleanup has unusually high leverage.",
              "detail": "The less glamorous tasks are exactly what give the day its strength. Sorting, closing loops, and clarifying the next action are more powerful than brainstorming."
            },
            "timing": {
              "headline": "Your sharpest window lands before lunch.",
              "detail": "Use the early stretch for precision, planning, and anything that needs a clean head. Leave looser collaboration or catch-up work for later in the day."
            },
            "closing_guidance": {
              "headline": "End the day lighter than you started it.",
              "detail": "Before tonight, close one loop that has been quietly taxing your attention. That small reset matters more than squeezing in one more half-focused task."
            }
          }
        }
        """
    )

    payload = build_daily_horoscope_reading_payload(
        normalized=normalized,
        metadata=_metadata(),
    )

    sections = {section["id"]: section for section in payload["sections"]}
    assert sections["timing"]["headline"] == "Your sharpest window lands before lunch."
    assert "clean head" in sections["timing"]["detail"]
    assert len(payload["sections"]) == 8


def test_daily_validator_flags_missing_sections_and_missing_detail() -> None:
    payload = {
        "sections": [
            {
                "id": "today_theme",
                "headline": "Today rewards clean execution over dramatic effort.",
                "detail": "",
                "text": "Today rewards clean execution over dramatic effort.",
            },
            {
                "id": "today_energy",
                "headline": "Mental clarity is high when you keep the environment simple.",
                "detail": "Mental clarity is high when you keep the environment simple.",
                "text": "Mental clarity is high when you keep the environment simple.",
            },
        ]
    }

    result = validate_product_payload("daily", payload)

    assert result.valid is False
    assert "daily_missing_section:timing" in result.issues
    assert "daily_missing_section_detail:today_theme" in result.issues
    assert "daily_headline_detail_repetition:today_energy" in result.issues
