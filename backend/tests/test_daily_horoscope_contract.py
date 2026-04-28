from generation.parser import parse_normalized_output
from generation.products.daily_horoscope.preview import (
    build_daily_horoscope_preview_payload,
)
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


def test_daily_reading_payload_enriches_thin_sections_with_astrology_facts() -> None:
    normalized = parse_normalized_output(
        """
        {
          "opening_hook": "Today asks for a cleaner rhythm.",
          "current_pattern": "You are sharper when the day has fewer open loops.",
          "emotional_truth": "Irritation spikes when avoidable mess keeps stealing attention.",
          "practical_guidance": "Choose one priority and finish it before lunch.",
          "next_return_invitation": "Reset tonight and check back tomorrow.",
          "theme_tags": ["daily"],
          "daily_sections": {
            "today_theme": {
              "headline": "Today rewards precision.",
              "detail": "Stay practical and keep the lane clean."
            },
            "today_energy": {
              "headline": "Your energy is clearer with fewer inputs.",
              "detail": "Reduce noise before you decide."
            },
            "best_move": {
              "headline": "Clear the bottleneck.",
              "detail": "Do the task that makes everything else easier."
            },
            "watch_out_for": {
              "headline": "Do not over-correct.",
              "detail": "Watch the urge to fix what only needs patience."
            },
            "people_energy": {
              "headline": "Clear signals land.",
              "detail": "Ask directly."
            },
            "work_focus": {
              "headline": "Practical progress wins.",
              "detail": "Close loops."
            },
            "timing": {
              "headline": "Use the morning well.",
              "detail": "Plan before lunch."
            },
            "closing_guidance": {
              "headline": "End lighter.",
              "detail": "Close one loop tonight."
            }
          }
        }
        """
    )

    payload = build_daily_horoscope_reading_payload(
        normalized=normalized,
        metadata=_metadata(),
        astrology_facts={
            "sun_sign": "Virgo",
            "moon_sign": "Capricorn",
            "ascendant": "Leo",
        },
    )

    sections = {section["id"]: section for section in payload["sections"]}
    assert "Your Virgo Sun wants precision today." in sections["today_theme"]["detail"]
    assert "Capricorn Moon" in sections["closing_guidance"]["detail"]
    assert validate_product_payload("daily", payload).passed is True


def test_daily_preview_payload_exposes_structured_preview_fields() -> None:
    normalized = parse_normalized_output(
        """
        {
          "opening_hook": "Today works best when you keep your energy clean and intentional.",
          "current_pattern": "The day is steadier than it first looks.",
          "emotional_truth": "Irritation grows when you let too many small demands pile up.",
          "practical_guidance": "Do the task that removes the hidden bottleneck first.",
          "next_return_invitation": "Close one loop tonight and check back tomorrow.",
          "theme_tags": ["daily"],
          "daily_sections": {
            "today_theme": {
              "headline": "Today rewards clean execution over drama.",
              "detail": "A little discipline will carry more weight than trying to do everything at once."
            },
            "today_energy": {
              "headline": "Mental clarity improves once the noise drops.",
              "detail": "The day gets better when you reduce inputs and stop reacting to every interruption."
            },
            "best_move": {
              "headline": "Clear the one thing that frees the rest of the day.",
              "detail": "You do not need a perfect plan before you begin, but you do need one useful first move."
            },
            "watch_out_for": {
              "headline": "Do not let competence become irritation.",
              "detail": "If the day turns brittle, pause before you start correcting everyone around you."
            },
            "closing_guidance": {
              "headline": "End lighter than you started.",
              "detail": "Leave tonight with one loop closed so tomorrow begins cleaner."
            }
          }
        }
        """
    )

    payload = build_daily_horoscope_preview_payload(
        normalized=normalized,
        metadata=_metadata(),
        unlock_price={"currency": "USD", "amount": 0.0},
        product_id="subscription_daily_999",
        entitlements={"subscription_active": True},
        astrology_facts={"sun_sign": "Virgo", "moon_sign": "Capricorn"},
        tarot_payload={"spread": "", "cards": []},
    )

    assert payload["headline"] == "Today rewards clean execution over drama."
    assert payload["teaser_text"].startswith("A little discipline")
    assert payload["today_energy"].startswith("Mental clarity improves")
    assert payload["best_move_teaser"].startswith("Clear the one thing")
    assert payload["watch_out_teaser"].startswith("Do not let competence")
    assert payload["deeper_layer_teaser"].startswith("Inside the full read")


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


def test_daily_validator_flags_cta_leak_short_sections_and_vague_timing() -> None:
    payload = {
        "sections": [
            {
                "id": "today_theme",
                "headline": "Today works best with a cleaner lane.",
                "detail": "For a deeper dive, consider exploring a personalized reading.",
                "text": "For a deeper dive, consider exploring a personalized reading.",
            },
            {
                "id": "today_energy",
                "headline": "Clarity improves once the noise drops.",
                "detail": "Keep it simple and direct today.",
                "text": "Keep it simple and direct today.",
            },
            {
                "id": "best_move",
                "headline": "Clear the bottleneck.",
                "detail": "Do the task that makes the rest easier.",
                "text": "Do the task that makes the rest easier.",
            },
            {
                "id": "watch_out_for",
                "headline": "Watch irritation.",
                "detail": "You can turn sharp quickly if you carry too much.",
                "text": "You can turn sharp quickly if you carry too much.",
            },
            {
                "id": "people_energy",
                "headline": "People respond to clarity.",
                "detail": "Ask directly for what you need.",
                "text": "Ask directly for what you need.",
            },
            {
                "id": "work_focus",
                "headline": "Administrative cleanup helps.",
                "detail": "Finish practical tasks before you brainstorm.",
                "text": "Finish practical tasks before you brainstorm.",
            },
            {
                "id": "timing",
                "headline": "The pace matters.",
                "detail": "Pick the cleaner window and use it well.",
                "text": "Pick the cleaner window and use it well.",
            },
            {
                "id": "closing_guidance",
                "headline": "End lighter than you started.",
                "detail": "Close one loop tonight before you stop.",
                "text": "Close one loop tonight before you stop.",
            },
        ]
    }

    result = validate_product_payload("daily", payload)

    assert result.valid is False
    assert any(issue.startswith("daily_cta_leak:today_theme") for issue in result.issues)
    assert "daily_section_too_short:today_energy" in result.issues
    assert "daily_section_needs_more_depth:today_energy" in result.issues
    assert "daily_timing_not_concrete" in result.issues
