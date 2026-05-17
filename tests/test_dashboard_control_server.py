from __future__ import annotations

import pytest

from scripts import run_dashboard_control_server as control


def test_dashboard_control_runtime_command_is_allowlisted() -> None:
    command = control.build_runtime_command(
        duration="5m",
        output="pt_rt1_5_1_smoke",
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
    assert "reports/paper_runtime/pt_rt1_5_1_smoke" in command
    assert "--decision-log-mode" in command
    assert "compact" in command
    assert "--pt-rt1-5-week1-active" in command
    assert "--fresh-signal-only-after-runtime-start" in command
    assert "--enable-baseline-testnet-transport" in command
    assert "--founder-approved-pt-rt1-5-1-baseline-testnet-orders-25usdc" in command
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
        "--founder-approved-pt-rt1-5-1-baseline-testnet-orders-25usdc",
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
        "pt_rt1_1b_smoke",
        "pt_rt1_1c_24h_dry_run",
        "pt_rt1_4_1_active_week",
        "pt_rt1_5_1_smoke",
        "pt_rt1_5_week1_active",
    ]


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
    monkeypatch.setattr(control, "process_is_running", lambda pid: False)

    status_code, _payload = control.start_runtime({"duration": "5m", "output": "test_output"})

    assert status_code == 200
    log_files = list(control_dir.glob("*.log"))
    assert len(log_files) == 1
    log_text = log_files[0].read_text(encoding="utf-8")
    assert "Starting money-flow" in log_text
    assert "scripts/run_pt_rt1_paper_observation.py" in log_text


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
