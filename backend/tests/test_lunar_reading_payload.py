from generation.products.lunar.preview import build_lunar_preview_payload
from generation.products.lunar.reading import build_lunar_reading_payload
from generation.types import GenerationMetadata, NormalizedMysticOutput


def _metadata() -> GenerationMetadata:
    return GenerationMetadata(
        persona_id="yearkeeper",
        llm_profile_id="full_premium",
        prompt_version="mystic-v3",
        model_id="test-model",
        theme_tags=["lunar"],
        headline="A threshold year is opening.",
    )


def test_lunar_reading_payload_emits_deep_text_for_expanded_sections():
    normalized = NormalizedMysticOutput(
        opening_hook="A threshold year is opening.",
        current_pattern="The year rewards disciplined movement over reactive motion.",
        emotional_truth="Carry only what still belongs in this next cycle.",
        practical_guidance="Protect your time, back the steady path, and leave old noise behind.",
        your_next_move="Choose one decisive move and give it sustained energy.",
        what_this_is_asking_of_you="Stop mistaking motion for alignment.",
        next_return_invitation="Return when the pattern sharpens.",
        premium_teaser="The year wants cleaner momentum.",
        reading_opening="This new cycle will test whether your urgency serves liberation or simply feeds old restlessness.",
        theme_tags=["lunar"],
    )
    payload = build_lunar_reading_payload(
        normalized=normalized,
        metadata=_metadata(),
        lunar_context={
            "current_year": {
                "year_label": "2026: Year of the Fire Horse",
                "year_animal": {
                    "combined": "Fire Horse",
                    "headline": "a year that rewards motion, courage, and visible aliveness",
                    "symbolism": "The Horse year asks whether your momentum is truly liberating you or merely keeping you busy.",
                    "opportunity": "Fresh starts and bold pivots are amplified.",
                    "caution": "Restlessness and scattered effort can cost more than expected.",
                },
                "year_element": {
                    "element": "Fire",
                    "gift": "confidence, magnetism, and the power to energize a stagnant situation",
                    "move_well": "let passion light the path, but keep enough discipline to sustain what begins",
                },
            },
            "interaction": {
                "reading": "This year presses for visible movement instead of private hesitation.",
            },
        },
    )

    sections = {section["id"]: section for section in payload["sections"]}

    assert sections["opening_invocation"]["deep_text"]
    assert sections["opening_invocation"]["deep_text"] != sections["opening_invocation"]["text"]
    assert sections["lunar_forecast"]["deep_text"]
    assert "The Fire element brings confidence, magnetism, and the power to energize a stagnant situation" in sections["lunar_forecast"]["deep_text"]


def test_lunar_preview_payload_keeps_teaser_distinct_from_headline():
    normalized = NormalizedMysticOutput(
        opening_hook="A threshold year is opening.",
        current_pattern="The Fire Horse cycle rewards motion, courage, and visible aliveness.",
        emotional_truth="Welcome brave movement, but release the habit of chasing every spark.",
        practical_guidance="Move well by choosing one bold priority and giving it enough discipline to last.",
        next_return_invitation="Return when the year begins to show its first pattern.",
        theme_tags=["lunar"],
    )

    payload = build_lunar_preview_payload(
        normalized=normalized,
        metadata=_metadata(),
        unlock_price={"currency": "USD", "amount": 1.0},
        product_id="lunar_forecast_100",
        entitlements={},
        astrology_facts={},
        lunar_context={},
    )

    assert payload["headline"] == "A threshold year is opening."
    assert payload["teaser_text"] == "The Fire Horse cycle rewards motion, courage, and visible aliveness."
    assert payload["teaser_text"] != payload["headline"]
    assert payload["welcome_release_teaser"].startswith("Welcome brave movement")
