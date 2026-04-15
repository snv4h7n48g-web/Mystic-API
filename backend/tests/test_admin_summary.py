from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_DB_INIT", "true")

import main


class _FakeResult:
    def __init__(self, *, first_row=None, rows=None) -> None:
        self._first_row = first_row
        self._rows = rows or []

    def mappings(self) -> "_FakeResult":
        return self

    def first(self):
        return self._first_row

    def all(self):
        return self._rows


class _FakeConnection:
    def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        if "COUNT(*) as total_users FROM users" in sql:
            return _FakeResult(first_row={"total_users": 10})
        if "COUNT(*) as users_30 FROM users" in sql:
            return _FakeResult(first_row={"users_30": 3})
        if "COUNT(*) as total_sessions FROM sessions" in sql:
            return _FakeResult(first_row={"total_sessions": 20})
        if "COUNT(*) as sessions_today FROM sessions" in sql:
            return _FakeResult(first_row={"sessions_today": 4})
        if "SUM(CASE WHEN status = 'preview_ready'" in sql:
            return _FakeResult(first_row={"previews": 6, "readings": 2})
        if "COUNT(preview_cost_usd) as preview_cost_count" in sql:
            return _FakeResult(
                first_row={
                    "preview_cost": 5.0,
                    "reading_cost": 8.0,
                    "palm_cost": 1.5,
                    "preview_cost_count": 10,
                    "reading_cost_count": 4,
                    "palm_cost_count": 3,
                }
            )
        if "COUNT(cost_usd) as feng_cost_count" in sql:
            return _FakeResult(
                first_row={
                    "feng_total": 5,
                    "feng_purchased": 2,
                    "feng_cost": 4.5,
                    "feng_cost_count": 2,
                }
            )
        if "COUNT(preview_cost_usd) as comp_preview_cost_count" in sql:
            return _FakeResult(
                first_row={
                    "comp_total": 7,
                    "comp_purchased": 3,
                    "comp_preview_cost": 1.2,
                    "comp_reading_cost": 2.4,
                    "comp_preview_cost_count": 3,
                    "comp_reading_cost_count": 2,
                }
            )
        if "COUNT(*) as total_offerings" in sql:
            return _FakeResult(first_row={"total_offerings": 6, "total_amount": 12.0})
        if "SELECT purchased_products FROM sessions" in sql:
            return _FakeResult(
                rows=[
                    {"purchased_products": ["p1", "p2"]},
                    {"purchased_products": ["p3"]},
                ]
            )
        raise AssertionError(f"Unexpected SQL: {sql}")


class _FakeBegin:
    def __enter__(self) -> _FakeConnection:
        return _FakeConnection()

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeEngine:
    def begin(self) -> _FakeBegin:
        return _FakeBegin()


def test_admin_summary_includes_llm_cost_rollups(monkeypatch) -> None:
    monkeypatch.setattr(main, "engine", _FakeEngine())
    monkeypatch.setattr(
        main,
        "calculate_revenue",
        lambda purchased: {
            "gross_total": len(purchased) * 2.0,
            "net_total": len(purchased) * 1.6,
        },
    )

    main.app.dependency_overrides[main.require_admin] = lambda: {"id": "admin-1", "role": "admin"}
    client = TestClient(main.app)
    try:
        response = client.get("/v1/admin/summary")
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()

    assert payload["costs"] == {
        "preview_usd": 5.0,
        "reading_usd": 8.0,
        "palm_usd": 1.5,
        "feng_shui_usd": 4.5,
        "compatibility_preview_usd": 1.2,
        "compatibility_reading_usd": 2.4,
        "sessions_total_usd": 14.5,
        "compatibility_total_usd": 3.6,
        "total_llm_usd": 22.6,
    }
    assert payload["compatibility"] == {
        "total": 7,
        "purchased": 3,
        "preview_cost_usd": 1.2,
        "reading_cost_usd": 2.4,
    }
    assert payload["llm_usage"] == {
        "total_calls": 24,
        "session_preview_calls": 10,
        "session_reading_calls": 4,
        "palm_calls": 3,
        "compatibility_preview_calls": 3,
        "compatibility_reading_calls": 2,
        "feng_shui_calls": 2,
        "average_cost_per_call_usd": 0.941667,
        "average_session_preview_cost_usd": 0.5,
        "average_session_reading_cost_usd": 2.0,
        "average_palm_cost_usd": 0.5,
        "average_compatibility_preview_cost_usd": 0.4,
        "average_compatibility_reading_cost_usd": 1.2,
        "average_feng_shui_cost_usd": 2.25,
    }
    assert payload["revenue"] == {
        "gross_usd": 6.0,
        "net_usd": 4.8,
        "net_after_llm_usd": -17.8,
    }
    assert response.headers["X-Request-ID"]
