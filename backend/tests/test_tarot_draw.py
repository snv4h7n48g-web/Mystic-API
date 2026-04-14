import main


def test_draw_tarot_defaults_to_three_card_spread():
    cards = main.draw_tarot()

    assert len(cards) == 3
    assert [card["position"] for card in cards] == ["Past", "Present", "Guidance"]
    assert all(card["orientation"] in {"upright", "reversed"} for card in cards)


def test_draw_tarot_supports_single_card_spread():
    cards = main.draw_tarot(1)

    assert len(cards) == 1
    assert cards[0]["position"] == "Card"
    assert isinstance(cards[0]["card"], str)
    assert cards[0]["orientation"] in {"upright", "reversed"}


def test_tarot_matcher_respects_flow_card_count():
    assert main._tarot_matches_flow({"tarot": {"cards": [{"card": "A", "position": "Card"}]}}, "tarot_solo") is True
    assert main._tarot_matches_flow({"tarot": {"cards": [{"card": "A", "position": "Card"}]}}, "combined") is False
    assert main._tarot_matches_flow({"tarot": {"cards": [{"card": "A", "position": "Past"}, {"card": "B", "position": "Present"}, {"card": "C", "position": "Guidance"}]}}, "combined") is True
