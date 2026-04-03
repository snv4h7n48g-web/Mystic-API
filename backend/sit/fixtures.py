from __future__ import annotations

from copy import deepcopy


def combined_preview_fixture() -> dict:
    return {
        "session": {
            "id": "11111111-1111-1111-1111-111111111111",
            "locale": "en-AU",
            "timezone": "Australia/Melbourne",
            "style": "grounded",
            "inputs": {
                "flow_type": "combined",
                "question_intention": "Should I stay in my current role or start moving toward my own practice this year?",
            },
        },
        "user": {
            "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "email": "sit@example.com",
            "role": "user",
        },
        "astrology_facts": {
            "sun_sign": "Aries",
            "moon_sign": "Capricorn",
            "rising_sign": "Gemini",
            "dominant_element": "Fire",
            "dominant_planet": "Mars",
            "top_aspects": [
                {"a": "Sun", "type": "trine", "b": "Jupiter"},
                {"a": "Moon", "type": "square", "b": "Saturn"},
            ],
        },
        "tarot_payload": {
            "spread": "Three-card crossroads spread",
            "cards": [
                {
                    "card": "The Fool",
                    "position": "what wants to begin",
                    "meaning": "A clean leap into a less scripted future.",
                    "question_link": "This reflects the pull toward self-directed work.",
                },
                {
                    "card": "Eight of Pentacles",
                    "position": "what needs discipline",
                    "meaning": "Mastery comes from repetitive skill-building, not mood.",
                    "question_link": "This points to training the practical side of the transition.",
                },
                {
                    "card": "Two of Wands",
                    "position": "next horizon",
                    "meaning": "Planning matters more than waiting for total certainty.",
                    "question_link": "This suggests designing the move before announcing it.",
                },
            ],
        },
        "unlock_price": {"currency": "USD", "amount": 2.99},
        "product_id": "reading_complete",
        "entitlements": {"included": False, "subscription_active": False},
    }


def combined_full_reading_fixture() -> dict:
    fixture = combined_preview_fixture()
    fixture.update(
        {
            "palm_features": [
                {
                    "label": "heart_line",
                    "value": "clear and responsive",
                    "relevance": "shows emotional honesty around the career question",
                    "confidence": "high",
                },
                {
                    "label": "head_line",
                    "value": "long and slightly sloping",
                    "relevance": "shows strategic thinking mixed with imagination",
                    "confidence": "medium",
                },
            ],
            "include_palm": True,
            "deep_access": True,
            "content_contract": {
                "requires_snapshot": True,
                "requires_layered_tarot": True,
                "requires_grounded_next_move": True,
            },
        }
    )
    return fixture


def daily_preview_fixture() -> dict:
    return {
        "session": {
            "id": "33333333-3333-3333-3333-333333333333",
            "locale": "en-AU",
            "timezone": "Australia/Melbourne",
            "style": "gentle",
            "inputs": {
                "flow_type": "daily_horoscope",
                "question_intention": "What should I focus on today so I don't scatter my energy?",
            },
        },
        "user": {
            "id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            "email": "sit-daily@example.com",
            "role": "user",
        },
        "astrology_facts": {
            "sun_sign": "Virgo",
            "moon_sign": "Pisces",
            "rising_sign": "Libra",
            "dominant_element": "Earth",
        },
        "tarot_payload": {},
        "unlock_price": {"currency": "USD", "amount": 1.99},
        "product_id": "daily_horoscope_unlock",
        "entitlements": {"included": False, "subscription_active": False},
    }


def daily_full_reading_fixture() -> dict:
    fixture = daily_preview_fixture()
    fixture.update(
        {
            "deep_access": True,
            "content_contract": {
                "day_scope": "today_only",
                "prefer_immediate_timing": True,
            },
        }
    )
    return fixture


def tarot_solo_preview_fixture() -> dict:
    return {
        "session": {
            "id": "44444444-4444-4444-4444-444444444444",
            "locale": "en-AU",
            "timezone": "Australia/Melbourne",
            "style": "direct",
            "inputs": {
                "flow_type": "tarot_solo",
                "question_intention": "What is the real lesson in this period of waiting?",
            },
        },
        "user": {
            "id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
            "email": "sit-tarot@example.com",
            "role": "user",
        },
        "astrology_facts": {},
        "tarot_payload": {
            "spread": "Past / present / guidance",
            "cards": [
                {
                    "card": "The Hermit",
                    "position": "present",
                    "meaning": "Withdrawal is helping discernment, not delay.",
                    "question_link": "This reframes waiting as a filtering process.",
                },
                {
                    "card": "Two of Swords",
                    "position": "block",
                    "meaning": "Mental stalemate protects you from choosing.",
                    "question_link": "This names the cost of staying undecided.",
                },
                {
                    "card": "Ace of Pentacles",
                    "position": "guidance",
                    "meaning": "A practical opening appears when you stop overcomplicating it.",
                    "question_link": "This points toward one tangible first move.",
                },
            ],
        },
        "unlock_price": {"currency": "USD", "amount": 2.49},
        "product_id": "tarot_solo_unlock",
        "entitlements": {"included": False, "subscription_active": False},
    }


def compatibility_preview_fixture() -> dict:
    return {
        "compat": {"id": "22222222-2222-2222-2222-222222222222"},
        "user": {
            "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "email": "sit-compat@example.com",
            "role": "user",
        },
        "person1": {"name": "Ava", "birth_date": "1992-04-14", "birth_place": "Melbourne"},
        "person2": {"name": "Noah", "birth_date": "1989-11-03", "birth_place": "Sydney"},
        "chart1": {"sun_sign": "Aries", "moon_sign": "Leo", "venus_sign": "Taurus"},
        "chart2": {"sun_sign": "Scorpio", "moon_sign": "Cancer", "mars_sign": "Virgo"},
        "zodiac1": {"animal": "Monkey", "element": "Water"},
        "zodiac2": {"animal": "Snake", "element": "Earth"},
        "synastry": {
            "headline": "Strong attraction with control friction",
            "aspects": [
                "Sun trine Moon creates instinctive emotional recognition",
                "Venus opposite Mars creates chemistry and impatience",
            ],
        },
        "zodiac_harmony": {
            "summary": "A strategic pair when both stop testing each other.",
            "rating": "high-potential",
        },
        "entitlements": {"included": False, "subscription_active": False},
    }


def compatibility_full_reading_fixture() -> dict:
    fixture = compatibility_preview_fixture()
    fixture["compat"]["question"] = "How can we stop misreading each other's intensity as rejection?"
    return fixture


def feng_shui_preview_fixture() -> dict:
    return {
        "analysis": {
            "id": "55555555-5555-5555-5555-555555555555",
            "analysis_type": "single_room",
            "room_purpose": "home office",
            "user_goals": "more focus and less visual noise",
            "compass_direction": "south-east",
        },
        "user": {
            "id": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
            "email": "sit-fengshui@example.com",
            "role": "user",
        },
        "entitlements": {"included": False, "subscription_active": False},
        "product_id": "feng_shui_premium",
        "price_amount": 4.99,
    }


def get_fixture(case_id: str) -> dict:
    mapping = {
        "combined_preview": combined_preview_fixture,
        "combined_full_reading": combined_full_reading_fixture,
        "daily_preview": daily_preview_fixture,
        "daily_full_reading": daily_full_reading_fixture,
        "tarot_solo_preview": tarot_solo_preview_fixture,
        "compatibility_preview": compatibility_preview_fixture,
        "compatibility_full_reading": compatibility_full_reading_fixture,
        "feng_shui_preview": feng_shui_preview_fixture,
    }
    if case_id not in mapping:
        raise KeyError(f"Unknown SIT fixture: {case_id}")
    return deepcopy(mapping[case_id]())
