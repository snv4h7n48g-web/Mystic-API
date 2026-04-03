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


def get_fixture(case_id: str) -> dict:
    mapping = {
        "combined_preview": combined_preview_fixture,
        "compatibility_preview": compatibility_preview_fixture,
    }
    if case_id not in mapping:
        raise KeyError(f"Unknown SIT fixture: {case_id}")
    return deepcopy(mapping[case_id]())
