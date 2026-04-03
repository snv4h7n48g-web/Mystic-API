from sit.reports import write_report_files


def test_report_writer_emits_json_and_markdown(tmp_path) -> None:
    report = {
        "generated_at": "2026-04-03T00:00:00Z",
        "status": "passed",
        "summary": {"cases_run": 1, "passed": 1, "passed_with_warnings": 0, "failed": 0},
        "cases": [
            {
                "case_id": "combined_preview",
                "status": "passed",
                "product_key": "full_reading",
                "surface": "preview",
                "duration_ms": 123.4,
                "generation": {"model_id": "test-model", "persona_id": "premium_mystic", "input_tokens": 10, "output_tokens": 20, "cost_usd": 0.01},
                "validation": {"checks": ["ok"], "warnings": [], "hard_failures": []},
            }
        ],
    }

    json_path, md_path = write_report_files(report=report, output_dir=tmp_path)

    assert json_path.exists()
    assert md_path.exists()
    markdown = md_path.read_text(encoding="utf-8")
    assert "Mystic SIT v2 Report" in markdown
    assert "- Surface: `preview`" in markdown
