#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from deployment_env import llm_configuration_issues
from generation.orchestration import get_generation_orchestrator
from generation.product_routing import resolve_product_key
from generation.validators import validate_product_payload
from sit.fixtures import get_fixture
from sit.validators import validate_preview_payload, validate_reading_payload


def _session_preview(case_id: str = "combined_preview") -> dict:
    fx = get_fixture(case_id)
    return get_generation_orchestrator().build_session_preview_result(
        session=fx["session"],
        user=None,
        astrology_facts=fx["astrology_facts"],
        tarot_payload=fx["tarot_payload"],
        unlock_price=fx["unlock_price"],
        product_id=fx["product_id"],
        entitlements=fx["entitlements"],
    ).payload


def _session_reading(case_id: str) -> dict:
    fx = get_fixture(case_id)
    return get_generation_orchestrator().build_session_reading_result(
        session=fx["session"],
        user=None,
        astrology_facts=fx["astrology_facts"],
        tarot_payload=fx["tarot_payload"],
        palm_features=fx.get("palm_features") or [],
        include_palm=bool(fx.get("include_palm")),
        deep_access=bool(fx.get("deep_access")),
        content_contract=fx.get("content_contract") or {},
    ).payload


def _compat_preview() -> dict:
    fx = get_fixture("compatibility_preview")
    return get_generation_orchestrator().build_compatibility_preview_result(
        compat=fx["compat"],
        user=None,
        person1=fx["person1"],
        person2=fx["person2"],
        chart1=fx["chart1"],
        chart2=fx["chart2"],
        zodiac1=fx["zodiac1"],
        zodiac2=fx["zodiac2"],
        synastry=fx["synastry"],
        zodiac_harmony=fx["zodiac_harmony"],
        entitlements=fx["entitlements"],
    ).payload


def _compat_reading() -> dict:
    fx = get_fixture("compatibility_full_reading")
    return get_generation_orchestrator().build_compatibility_reading_result(
        compat=fx["compat"],
        user=None,
        person1=fx["person1"],
        person2=fx["person2"],
        chart1=fx["chart1"],
        chart2=fx["chart2"],
        synastry=fx["synastry"],
        zodiac_harmony=fx["zodiac_harmony"],
    ).payload


def _feng_preview() -> dict:
    fx = get_fixture("feng_shui_preview")
    return get_generation_orchestrator().build_feng_shui_preview_result(
        analysis=fx["analysis"],
        user=None,
        entitlements=fx["entitlements"],
        product_id=fx["product_id"],
        price_amount=fx["price_amount"],
    ).payload


def _feng_analysis() -> dict:
    fx = get_fixture("feng_shui_preview")
    return get_generation_orchestrator().build_feng_shui_analysis_result(
        analysis=fx["analysis"],
        user=None,
        vision_result={
            "room_summary": "A compact home office with a desk facing a busy shelf, bright side window, and a narrow route to the chair.",
            "visible_supports": ["natural light", "clear desk surface", "plant near window"],
            "visible_blocks": ["crowded shelving", "chair path partly blocked", "mixed paperwork in the south-east corner"],
            "cost_usd": 0.0,
        },
    ).payload


def _validate(case_id: str, payload: dict) -> dict[str, Any]:
    if case_id.endswith("_preview"):
        product_key = {
            "combined_preview": "full_reading",
            "daily_preview": "daily",
            "tarot_solo_preview": "tarot",
            "compatibility_preview": "compatibility",
            "feng_shui_preview": "feng_shui",
        }[case_id]
        return validate_preview_payload(case_id=case_id, product_key=product_key, payload=payload).as_dict()
    if case_id == "feng_shui_analysis":
        validation = validate_product_payload("feng_shui", payload)
        return {
            "status": "failed" if validation.issues else "passed",
            "checks": ["product_validator_passed"] if not validation.issues else [],
            "warnings": [],
            "hard_failures": validation.issues,
            "validator": {
                "product_key": validation.product_key,
                "passed": validation.passed,
                "issues": validation.issues,
                "retry_hint": validation.retry_hint,
            },
        }
    product_key = "compatibility" if case_id == "compatibility_full_reading" else resolve_product_key(
        flow_type="daily_horoscope" if case_id == "daily_full_reading" else "combined",
        object_type="compatibility" if case_id == "compatibility_full_reading" else "session",
    )
    summary = validate_reading_payload(case_id=case_id, product_key=product_key, payload=payload)
    return summary.as_dict()


CASES: dict[str, Callable[[], dict]] = {
    "combined_preview": _session_preview,
    "combined_full_reading": lambda: _session_reading("combined_full_reading"),
    "daily_preview": lambda: _session_preview("daily_preview"),
    "daily_full_reading": lambda: _session_reading("daily_full_reading"),
    "tarot_solo_preview": lambda: _session_preview("tarot_solo_preview"),
    "compatibility_preview": _compat_preview,
    "compatibility_full_reading": _compat_reading,
    "feng_shui_preview": _feng_preview,
    "feng_shui_analysis": _feng_analysis,
}


def _write_reports(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"mystic-llm-uat-{stamp}.json"
    md_path = output_dir / f"mystic-llm-uat-{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Mystic LLM UAT",
        "",
        f"- status: {report['status']}",
        f"- started_at: {report['started_at']}",
        f"- duration_ms: {report['duration_ms']}",
        "",
        "| case | status | model | failures |",
        "| --- | --- | --- | --- |",
    ]
    for result in report["results"]:
        metadata = result.get("payload", {}).get("metadata") or result.get("payload", {}).get("meta") or {}
        failures = ", ".join(result.get("validation", {}).get("hard_failures") or result.get("error", []))
        timing = metadata.get("generation_timing") if isinstance(metadata, dict) else {}
        attempt_models = timing.get("attempt_models") if isinstance(timing, dict) else []
        model = metadata.get("model_id") or metadata.get("model") or (attempt_models[0] if attempt_models else "")
        lines.append(f"| {result['case_id']} | {result['status']} | {model} | {failures} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live-model Mystic LLM UAT cases.")
    parser.add_argument("--case", action="append", choices=sorted(CASES), help="Case to run. Repeat for multiple cases.")
    parser.add_argument("--output-dir", default=str(ROOT / "sit" / "reports"), help="Report output directory.")
    parser.add_argument("--allow-config-warnings", action="store_true", help="Run even if LLM release config checks warn.")
    args = parser.parse_args()

    issues = llm_configuration_issues()
    if issues and not args.allow_config_warnings:
        print("LLM configuration is not release-ready:")
        for issue in issues:
            print(f"- {issue}")
        return 2

    case_ids = args.case or list(CASES)
    started = time.perf_counter()
    report: dict[str, Any] = {
        "status": "passed",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "config_issues": issues,
        "results": [],
    }
    for case_id in case_ids:
        case_started = time.perf_counter()
        try:
            payload = CASES[case_id]()
            validation = _validate(case_id, payload)
            status = "failed" if validation.get("hard_failures") else validation.get("status", "passed")
            report["results"].append(
                {
                    "case_id": case_id,
                    "status": status,
                    "duration_ms": round((time.perf_counter() - case_started) * 1000, 2),
                    "validation": validation,
                    "payload": payload,
                }
            )
            if status == "failed":
                report["status"] = "failed"
            print(f"{case_id}: {status}")
        except Exception as exc:
            report["status"] = "failed"
            report["results"].append(
                {
                    "case_id": case_id,
                    "status": "failed",
                    "duration_ms": round((time.perf_counter() - case_started) * 1000, 2),
                    "error": [f"{type(exc).__name__}: {exc}"],
                }
            )
            print(f"{case_id}: failed ({type(exc).__name__}: {exc})")

    report["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
    _write_reports(report, Path(args.output_dir))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
