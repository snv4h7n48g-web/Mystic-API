from tarot_knowledge import build_tarot_card_prompt, tarot_reference_for_card


def test_tarot_reference_for_card_merges_guidebook_major_arcana() -> None:
    devil = tarot_reference_for_card("The Devil")

    assert devil["guidebook_upright"] == "bondage, materialism, temptation, and addiction"
    assert devil["guidebook_reversed"] == "release, liberation, or overcoming addiction"


def test_build_tarot_card_prompt_uses_guidebook_reversed_meaning() -> None:
    prompt = build_tarot_card_prompt(
        {
            "card": "The Devil",
            "position": "present",
            "orientation": "reversed",
        }
    )

    assert "Reversed emphasis: release, liberation, or overcoming addiction." in prompt
