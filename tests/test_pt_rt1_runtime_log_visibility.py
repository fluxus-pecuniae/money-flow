from __future__ import annotations

from pathlib import Path

from scripts import watch_pt_rt1_runtime as watcher


def test_watch_pt_rt1_runtime_reports_status_without_mutating(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    runtime_root = tmp_path / "reports" / "paper_runtime"
    scope_dir = runtime_root / "pt_rt1_6_week2_active"
    scope_dir.mkdir(parents=True)
    (scope_dir / "runtime_audit.jsonl").write_text('{"last_update_utc":"2026-06-08T00:00:00Z"}\n', encoding="utf-8")
    (scope_dir / "trades.jsonl").write_text("", encoding="utf-8")
    control_state = runtime_root / "dashboard_control" / "state.json"
    control_state.parent.mkdir(parents=True)
    control_state.write_text(
        '{"running": true, "output": "pt_rt1_6_week2_active", "message": "paper_runtime_started_with_caffeinate"}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(watcher, "RUNTIME_ROOT", runtime_root)
    monkeypatch.setattr(watcher, "CONTROL_STATE", control_state)
    monkeypatch.setattr(watcher, "runtime_process_lines", lambda: ["123 run_pt_rt1_paper_observation"])

    watcher.print_status("pt_rt1_6_week2_active")

    output = capsys.readouterr().out
    assert "scope: pt_rt1_6_week2_active" in output
    assert "control_state_running: True" in output
    assert "runtime_processes: 1" in output
    assert "tail -n 50 -F" in output
    assert "trades.jsonl can stay empty until a synthetic position closes" in output


def test_watch_pt_rt1_runtime_latest_prints_existing_rows(
    monkeypatch,
    tmp_path,
    capfd,
) -> None:
    runtime_root = tmp_path / "reports" / "paper_runtime"
    scope_dir = runtime_root / "pt_rt1_6_week2_active"
    scope_dir.mkdir(parents=True)
    (scope_dir / "decisions.jsonl").write_text("one\ntwo\nthree\n", encoding="utf-8")

    monkeypatch.setattr(watcher, "RUNTIME_ROOT", runtime_root)

    watcher.print_latest("pt_rt1_6_week2_active", "decisions", 2)

    output = capfd.readouterr().out
    assert "decisions.jsonl" in output
    assert "two" in output
    assert "three" in output
    assert "one" not in output


def test_watch_pt_rt1_runtime_selected_paths_default_scope() -> None:
    paths = watcher.selected_paths(watcher.DEFAULT_SCOPE, "all")

    assert [Path(path).name for path in paths] == [
        "runtime_audit.jsonl",
        "decisions.jsonl",
        "trades.jsonl",
        "testnet_order_lifecycle.jsonl",
    ]
