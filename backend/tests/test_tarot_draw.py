import main


def test_draw_tarot_defaults_to_three_card_spread():
    cards = main.draw_tarot()

    assert len(cards) == 3
    assert [card["position"] for card in cards] == ["Past", "Present", "Guidance"]


def test_draw_tarot_supports_single_card_spread():
    cards = main.draw_tarot(1)

    assert len(cards) == 1
    assert cards[0]["position"] == "Card"
    assert isinstance(cards[0]["card"], str)
