from __future__ import annotations

import os
import time

from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_DB_INIT", "true")

import main
from generation.validators import assess_section_safety


def _read_sse_events(response) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    current_event = None
    current_data = None
    for raw_line in response.iter_lines():
        line = raw_line.decode() if isinstance(raw_line, bytes) else raw_line
        if not line:
            if current_event is not None and current_data is not None:
                events.append((current_event, main.json.loads(current_data)))
            current_event = None
            current_data = None
            continue
        if line.startswith("event: "):
            current_event = line.split(": ", 1)[1]
        elif line.startswith("data: "):
            current_data = line.split(": ", 1)[1]
    if current_event is not None and current_data is not None:
        events.append((current_event, main.json.loads(current_data)))
    return events


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


def test_stream_endpoint_emits_started_before_blocking_generation(monkeypatch) -> None:
    def _slow_failure(*args, **kwargs):
        time.sleep(0.05)
        raise RuntimeError("stream generation failed")

    monkeypatch.setattr(main, "_build_session_reading_response", _slow_failure)

    client = TestClient(main.app)
    with client.stream("GET", "/v1/sessions/sess-3/reading/stream") as response:
        assert response.status_code == 200
        events = _read_sse_events(response)

    assert [name for name, _ in events][0] == "reading_started"
    assert [name for name, _ in events][-1] == "reading_failed"
    assert events[-1][1]["detail"] == "stream generation failed"
    assert "timing" in events[-1][1]


def test_reading_route_attaches_route_timing(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "_build_session_reading_response",
        lambda session_id, user, daily=False: {
            "status": "complete",
            "reading": {
                "sections": [{"id": "overview", "text": "The pattern is clear and moving."}],
                "metadata": {"flow_type": "combined"},
            },
        },
    )

    client = TestClient(main.app)
    response = client.post("/v1/sessions/sess-4/reading")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "complete"
    assert set(payload["timing"]) == {
        "total_request_time_ms",
        "queue_time_ms",
        "model_time_ms",
        "time_to_first_output_ms",
    }


def test_preview_route_attaches_route_timing(monkeypatch) -> None:
    session = {
        "id": "sess-5",
        "inputs": {"question_intention": "What should I focus on next?", "birth_date": "1990-01-01"},
        "preview": {
            "astrology_facts": {},
            "tarot": {"spread": "3-card", "cards": []},
            "teaser_text": "A grounded teaser.",
            "unlock_price": {"currency": "USD", "amount": 0.0},
            "product_id": "reading_basic",
            "content_contract": {"flow_type": "combined"},
            "generated_at": "2026-04-14T00:00:00+00:00",
            "seasonal": {"lunar_new_year": False},
            "entitlements": {"subscription_active": False},
            "llm_metadata": {"model": "fake", "input_tokens": 1, "output_tokens": 1},
        },
    }

    monkeypatch.setattr(main, "db_get_session", lambda session_id: session)
    monkeypatch.setattr(main, "_assert_session_access", lambda session_id, user: None)
    monkeypatch.setattr(main, "db_update_session", lambda session_id, **kwargs: None)

    client = TestClient(main.app)
    response = client.post("/v1/sessions/sess-5/preview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "preview_ready"
    assert set(payload["timing"]) == {
        "total_request_time_ms",
        "queue_time_ms",
        "model_time_ms",
        "time_to_first_output_ms",
    }
