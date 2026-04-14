from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_DB_INIT", "true")

import main
from generation.validators import assess_section_safety


def test_assess_section_safety_rejects_placeholder_and_accepts_real_text() -> None:
    rejected = assess_section_safety({"id": "your_next_move", "text": "TBD"})
    accepted = assess_section_safety(
        {
            "id": "your_next_move",
            "text": "Send the message tonight and make the decision concrete before doubt fills the space again.",
        }
    )

    assert rejected.passed is False
    assert rejected.issues == ["placeholder_text"]
    assert accepted.passed is True
    assert accepted.issues == []


def test_iter_reading_section_events_rejects_unsafe_sections_and_attaches_post_completion_audit() -> None:
    reading = {
        "sections": [
            {"id": "reading_opening", "text": "The pattern is ready to move, and the reading starts where avoidance stops helping you."},
            {"id": "your_next_move", "text": "1."},
        ],
        "metadata": {
            "flow_type": "combined",
            "generated_at": "2026-04-14T00:00:00+00:00",
        },
    }

    events = list(main._iter_reading_section_events(reading=reading, session_id="sess-1"))
    payload = "".join(events)

    assert "event: section_completed" in payload
    assert "event: section_rejected" in payload
    assert '"section_id": "your_next_move"' in payload
    assert '"issues": ["malformed_text"]' in payload
    assert "event: reading_completed" in payload
    assert '"product_key": "full_reading"' in payload


def test_stream_endpoint_fails_coherently_when_all_sections_are_unsafe(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "_build_session_reading_response",
        lambda session_id, user, daily=False: {
            "status": "complete",
            "reading": {
                "sections": [
                    {"id": "reading_opening", "text": "..."},
                    {"id": "your_next_move", "text": "TBD"},
                ],
                "metadata": {"flow_type": "combined"},
            },
        },
    )

    client = TestClient(main.app)
    response = client.get("/v1/sessions/sess-2/reading/stream")

    assert response.status_code == 200
    body = response.text
    assert "event: section_rejected" in body
    assert "event: reading_failed" in body
    assert "No safe sections were available to stream" in body
    assert '"product_key": "full_reading"' in body
