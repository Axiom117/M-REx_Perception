"""CLI tests (M3): end-to-end headless run + JSON report."""

from __future__ import annotations

import json
from pathlib import Path

from mrex_perception.cli import main


def test_run_prints_summary_and_writes_json_report(tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "out.json"

    exit_code = main(
        ["run", "--seed", "42", "--count", "6", "--steps", "10", "--report", str(report_path)]
    )

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "----- Simulation Summary -----" in stdout
    assert "[report]" in stdout

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["finish_reason"] == "completed"
    summary = payload["summary"]
    assert summary["total"] == 6
    accounted = (
        summary["moved"] + summary["failed"] + summary["free"] + summary["selected"]
        + summary["grasped"]
    )
    assert accounted == 6
    assert summary["num_motion_samples"] > 0


def test_run_reports_config_errors(capsys) -> None:
    exit_code = main(["run", "--config", "does-not-exist"])

    assert exit_code == 1
    assert "[error]" in capsys.readouterr().err


def test_run_reports_tool_head_config_errors(capsys) -> None:
    exit_code = main(["run", "--tool", "does-not-exist"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "[error]" in err
    assert "Tool head config" in err
