from __future__ import annotations

import pytest

from scripts import run_dashboard_control_server as control


def test_dashboard_control_runtime_command_is_allowlisted() -> None:
    command = control.build_runtime_command(
        duration="5m",
        output="pt_rt1_6_week2_active",
        python_executable=".venv/bin/python",
        caffeinate_path="/usr/bin/caffeinate",
    )

    assert command[:4] == [
        "/usr/bin/caffeinate",
        "-dimsu",
        ".venv/bin/python",
        "scripts/run_pt_rt1_paper_observation.py",
    ]
    assert "--duration-minutes" in command
    assert "5" in command
    assert "--output-dir" in command
    assert "reports/paper_runtime/pt_rt1_6_week2_active" in command
    assert "--decision-log-mode" in command
    assert "compact" in command
    assert "--pt-rt1-5-week1-active" in command
    assert "--fresh-signal-only-after-runtime-start" in command
    assert "--enable-baseline-testnet-transport" in command
    assert "--founder-approved-pt-rt1-5-2-baseline-testnet-orders-25usdc" in command
    assert "--pt-rt1-5-testnet-order-notional-usdc" in command
    assert "25" in command
    assert "--signal-evaluation-mode" in command
    assert "candle_close_only" in command
    assert "--public-mainnet-only" in command
    assert "--disable-legacy-testnet-probes" in command
    assert "exchange" not in " ".join(command).lower()


def test_dashboard_control_rejects_unapproved_duration_and_output() -> None:
    with pytest.raises(ValueError, match="invalid_duration_option"):
        control.build_runtime_command(
            duration="30d",
            output="pt_rt1_1c_24h_dry_run",
            python_executable=".venv/bin/python",
            caffeinate_path="/usr/bin/caffeinate",
        )

    with pytest.raises(ValueError, match="invalid_output_option"):
        control.build_runtime_command(
            duration="24h",
            output="../../tmp/not_allowed",
            python_executable=".venv/bin/python",
            caffeinate_path="/usr/bin/caffeinate",
        )


def test_dashboard_control_server_is_localhost_only() -> None:
    assert control.validate_local_host("127.0.0.1") == "127.0.0.1"
    assert control.validate_local_host("localhost") == "localhost"
    with pytest.raises(ValueError, match="dashboard_control_server_must_bind_localhost"):
        control.validate_local_host("0.0.0.0")


def test_dashboard_control_status_contract_exposes_safety_flags() -> None:
    assert control.SAFE_FLAGS == [
        "--pt-rt1-5-week1-active",
        "--fresh-signal-only-after-runtime-start",
        "--enable-baseline-testnet-transport",
        "--founder-approved-pt-rt1-5-2-baseline-testnet-orders-25usdc",
        "--pt-rt1-5-testnet-order-notional-usdc",
        "25",
        "--pt-rt1-5-testnet-daily-order-cap",
        "25",
        "--pt-rt1-5-testnet-per-symbol-daily-cap",
        "3",
        "--signal-evaluation-mode",
        "candle_close_only",
        "--disable-legacy-testnet-probes",
        "--public-mainnet-only",
    ]
    assert sorted(control.DURATION_OPTIONS) == ["1h", "24h", "5m", "6h"]
    assert sorted(control.OUTPUT_OPTIONS) == [
        "pt_rt1_5_2_week1_active",
        "pt_rt1_5_3_transport_smoke",
        "pt_rt1_6_week2_active",
    ]
    assert control.DEFAULT_OUTPUT == "pt_rt1_6_week2_active"


def test_dashboard_control_status_contract_exposes_runtime_log_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    reports_root = tmp_path / "reports" / "paper_runtime"
    control_dir = reports_root / "dashboard_control"
    output_dir = reports_root / "pt_rt1_6_week2_active"
    output_dir.mkdir(parents=True)
    (output_dir / "runtime_audit.jsonl").write_text('{"last_update_utc":"2026-06-08T00:00:00Z"}\n', encoding="utf-8")
    (output_dir / "trades.jsonl").write_text("", encoding="utf-8")

    monkeypatch.setattr(control, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(control, "CONTROL_DIR", control_dir)
    monkeypatch.setattr(control, "STATE_PATH", control_dir / "state.json")
    monkeypatch.setattr(control, "OUTPUT_OPTIONS", {"pt_rt1_6_week2_active": output_dir})
    monkeypatch.setattr(control, "DEFAULT_OUTPUT", "pt_rt1_6_week2_active")
    monkeypatch.setattr(control, "process_is_managed_runtime", lambda pid, state=None: False)

    status = control.current_status()

    files = {item["key"]: item for item in status["runtime_log_files"]}
    assert files["runtime_audit"]["exists"] is True
    assert files["runtime_audit"]["size_bytes"] > 0
    assert files["runtime_audit"]["role"] == "heartbeat and public-mainnet connection rows"
    assert files["runtime_audit"]["tail_command"].startswith("tail -n 50 -F ")
    assert files["trades"]["exists"] is True
    assert files["trades"]["size_bytes"] == 0
    assert files["trades"]["empty_hint"] == "Can stay empty until an open synthetic position closes."
    assert files["testnet_lifecycle"]["role"] == "separate Hyperliquid testnet plumbing lifecycle"


def test_dashboard_control_transport_smoke_adds_single_smoke_flag() -> None:
    command = control.build_runtime_command(
        duration="5m",
        output="pt_rt1_5_3_transport_smoke",
        python_executable=".venv/bin/python",
        caffeinate_path="/usr/bin/caffeinate",
    )

    assert "reports/paper_runtime/pt_rt1_5_3_transport_smoke" in command
    assert "--founder-approved-pt-rt1-5-3-testnet-size-hotfix-smoke" in command
    assert "--max-testnet-orders-this-phase" in command
    assert "1" in command
    assert "--max-cycles" in command
    assert "--poll-seconds" in command
    assert "--max-candle-symbols" in command


def test_dashboard_control_runtime_log_announces_money_flow_start(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    reports_root = tmp_path / "reports" / "paper_runtime"
    control_dir = reports_root / "dashboard_control"
    output_dir = reports_root / "test_output"

    class FakeProcess:
        pid = 999999

    def fake_popen(*args, **kwargs):  # noqa: ANN001, ANN202 - subprocess test double.
        return FakeProcess()

    monkeypatch.setattr(control, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(control, "CONTROL_DIR", control_dir)
    monkeypatch.setattr(control, "STATE_PATH", control_dir / "state.json")
    monkeypatch.setattr(control, "OUTPUT_OPTIONS", {"test_output": output_dir})
    monkeypatch.setattr(control, "find_caffeinate", lambda: "/usr/bin/caffeinate")
    monkeypatch.setattr(control.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(control, "process_is_managed_runtime", lambda pid, state=None: False)

    status_code, _payload = control.start_runtime({"duration": "5m", "output": "test_output"})

    assert status_code == 200
    log_files = list(control_dir.glob("*.log"))
    assert len(log_files) == 1
    log_text = log_files[0].read_text(encoding="utf-8")
    assert "Starting money-flow" in log_text
    assert "scripts/run_pt_rt1_paper_observation.py" in log_text


def test_dashboard_control_access_log_appends_control_message() -> None:
    calls: list[str] = []
    handler = control.DashboardControlHandler.__new__(control.DashboardControlHandler)
    handler.command = "POST"
    handler.path = "/api/paper-runtime/start"
    handler.requestline = 'POST /api/paper-runtime/start HTTP/1.1'
    handler._control_server_message = "{paper_runtime_started_with_caffeinate}"
    handler.log_message = lambda fmt, *args: calls.append(fmt % args)  # type: ignore[method-assign]

    handler.log_request(200, "-")

    assert calls == ['"POST /api/paper-runtime/start HTTP/1.1" 200 - {paper_runtime_started_with_caffeinate}']


def test_dashboard_control_access_log_message_is_sanitized() -> None:
    assert control.control_access_log_message("paper_runtime_started_with_caffeinate") == "{paper_runtime_started_with_caffeinate}"
    assert control.control_access_log_message("bad\nmessage") == "{bad message}"
    assert control.control_access_log_message(None) == "{control_message_unavailable}"


def test_dashboard_control_reconciles_stale_reused_pid(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    reports_root = tmp_path / "reports" / "paper_runtime"
    control_dir = reports_root / "dashboard_control"
    output_dir = reports_root / "pt_rt1_5_2_week1_active"
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(control, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(control, "CONTROL_DIR", control_dir)
    monkeypatch.setattr(control, "STATE_PATH", control_dir / "state.json")
    monkeypatch.setattr(control, "OUTPUT_OPTIONS", {"pt_rt1_5_2_week1_active": output_dir})
    monkeypatch.setattr(control, "DEFAULT_OUTPUT", "pt_rt1_5_2_week1_active")
    monkeypatch.setattr(control, "process_is_managed_runtime", lambda pid, state=None: False)
    control.write_state(
        {
            "running": True,
            "status": "running",
            "pid": 76218,
            "duration": "24h",
            "output": "pt_rt1_5_2_week1_active",
            "output_dir": "reports/paper_runtime/pt_rt1_5_2_week1_active",
            "started_at_utc": "2026-05-17T18:53:29Z",
            "log_path": "reports/paper_runtime/dashboard_control/stale.log",
            "message": "paper_runtime_started_with_caffeinate",
        }
    )

    status = control.current_status()

    assert status["running"] is False
    assert status["pid"] is None
    assert status["status"] == "idle"
    assert status["message"] == "paper_runtime_state_reconciled_not_running"
    assert status["started_at_utc"] is None
    assert status["log_path"] is None
    persisted = control.read_state()
    assert persisted["status"] == "stale_state_reconciled"
    assert persisted["message"] == "paper_runtime_state_reconciled_not_running"


def test_dashboard_control_stop_reconciles_stale_pid_without_forbidden(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    reports_root = tmp_path / "reports" / "paper_runtime"
    control_dir = reports_root / "dashboard_control"
    output_dir = reports_root / "pt_rt1_5_2_week1_active"
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(control, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(control, "CONTROL_DIR", control_dir)
    monkeypatch.setattr(control, "STATE_PATH", control_dir / "state.json")
    monkeypatch.setattr(control, "OUTPUT_OPTIONS", {"pt_rt1_5_2_week1_active": output_dir})
    monkeypatch.setattr(control, "DEFAULT_OUTPUT", "pt_rt1_5_2_week1_active")
    monkeypatch.setattr(control, "process_is_managed_runtime", lambda pid, state=None: False)
    control.write_state(
        {
            "running": True,
            "status": "running",
            "pid": 76218,
            "duration": "24h",
            "output": "pt_rt1_5_2_week1_active",
            "output_dir": "reports/paper_runtime/pt_rt1_5_2_week1_active",
            "message": "paper_runtime_started_with_caffeinate",
        }
    )

    status_code, payload = control.stop_runtime()

    assert status_code == 200
    assert payload["running"] is False
    assert payload["pid"] is None
    assert payload["message"] == "paper_runtime_not_running"


def test_dashboard_control_allowlisted_command_requires_runtime_output() -> None:
    control_command = (
        "/usr/bin/caffeinate -dimsu .venv/bin/python "
        "scripts/run_pt_rt1_paper_observation.py --duration-hours 24 "
        "--output-dir reports/paper_runtime/pt_rt1_5_2_week1_active --public-mainnet-only"
    )
    wrong_output_command = control_command.replace("pt_rt1_5_2_week1_active", "other_runtime")
    unrelated_command = "/usr/bin/python scripts/unrelated.py --output-dir reports/paper_runtime/pt_rt1_5_2_week1_active"

    state = {"output_dir": "reports/paper_runtime/pt_rt1_5_2_week1_active"}

    assert control.command_is_allowlisted_runtime(control_command, state)
    assert not control.command_is_allowlisted_runtime(wrong_output_command, state)
    assert not control.command_is_allowlisted_runtime(unrelated_command, state)


def test_dashboard_control_suppresses_noisy_static_evidence_get_logs() -> None:
    assert control.should_suppress_access_log(
        "GET",
        "/reports/strategy_validation/money_flow_sv2_1_example/summary.json",
    )
    assert control.should_suppress_access_log(
        "GET",
        "/reports/strategy_validation/money_flow_sv2_0_2_example/summary.json?cache=1",
    )
    assert not control.should_suppress_access_log("GET", "/api/paper-runtime/status")
    assert not control.should_suppress_access_log(
        "POST",
        "/reports/strategy_validation/money_flow_sv2_1_example/summary.json",
    )
