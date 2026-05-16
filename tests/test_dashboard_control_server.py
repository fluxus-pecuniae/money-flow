from __future__ import annotations

import pytest

from scripts import run_dashboard_control_server as control


def test_dashboard_control_runtime_command_is_allowlisted() -> None:
    command = control.build_runtime_command(
        duration="5m",
        output="pt_rt1_1c_24h_dry_run",
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
    assert "reports/paper_runtime/pt_rt1_1c_24h_dry_run" in command
    assert "--decision-log-mode" in command
    assert "compact" in command
    assert "--disable-testnet-probes" in command
    assert "--public-mainnet-only" in command
    assert "--enable-testnet-probes" not in command
    assert "order" not in " ".join(command).lower()


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
    assert control.SAFE_FLAGS == ["--disable-testnet-probes", "--public-mainnet-only"]
    assert sorted(control.DURATION_OPTIONS) == ["1h", "24h", "5m", "6h"]
    assert sorted(control.OUTPUT_OPTIONS) == ["pt_rt1_1b_smoke", "pt_rt1_1c_24h_dry_run"]
