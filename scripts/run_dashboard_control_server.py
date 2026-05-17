#!/usr/bin/env python3
"""Local-only dashboard control server for PT-RT1 paper observation.

The server intentionally exposes only a tiny localhost API. It can start or
stop the PT-RT1 paper-observation runtime through `caffeinate` so a Mac stays
awake while synthetic paper observation runs. PT-RT1.5.1 uses candle-close
signal evaluation, warm-start fresh-signal gating, and baseline-only
Hyperliquid testnet lifecycle transport capped at a fixed 25 USDC; testnet
fills do not update synthetic paper PnL.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTROL_DIR = REPO_ROOT / "reports" / "paper_runtime" / "dashboard_control"
STATE_PATH = CONTROL_DIR / "state.json"
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
SAFE_FLAGS = [
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
DURATION_OPTIONS = {
    "5m": ("--duration-minutes", "5", "5 minutes"),
    "1h": ("--duration-hours", "1", "1 hour"),
    "6h": ("--duration-hours", "6", "6 hours"),
    "24h": ("--duration-hours", "24", "24 hours"),
}
OUTPUT_OPTIONS = {
    "pt_rt1_5_2_week1_active": REPO_ROOT / "reports" / "paper_runtime" / "pt_rt1_5_2_week1_active",
    "pt_rt1_5_2_transport_smoke": REPO_ROOT / "reports" / "paper_runtime" / "pt_rt1_5_2_transport_smoke",
    "pt_rt1_5_1_smoke": REPO_ROOT / "reports" / "paper_runtime" / "pt_rt1_5_1_smoke",
    "pt_rt1_5_week1_active": REPO_ROOT / "reports" / "paper_runtime" / "pt_rt1_5_week1_active",
    "pt_rt1_4_1_active_week": REPO_ROOT / "reports" / "paper_runtime" / "pt_rt1_4_1_active_week",
    "pt_rt1_1c_24h_dry_run": REPO_ROOT / "reports" / "paper_runtime" / "pt_rt1_1c_24h_dry_run",
    "pt_rt1_1b_smoke": REPO_ROOT / "reports" / "paper_runtime" / "pt_rt1_1b_smoke",
}
SUPPRESSED_STATIC_LOG_PREFIXES = (
    "/reports/strategy_validation/money_flow_sv2_1",
    "/reports/strategy_validation/money_flow_sv2_0_2",
)
STARTING_LOG_LINE = "Starting money-flow"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def should_suppress_access_log(method: str, request_path: str) -> bool:
    if method.upper() != "GET":
        return False
    parsed = urlparse(request_path)
    return any(parsed.path.startswith(prefix) for prefix in SUPPRESSED_STATIC_LOG_PREFIXES)


def read_state() -> dict[str, Any]:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {"status": "state_file_invalid", "running": False}


def write_state(payload: dict[str, Any]) -> None:
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_local_host(host: str) -> str:
    normalized = (host or "").strip().lower()
    if normalized not in LOCAL_HOSTS:
        raise ValueError("dashboard_control_server_must_bind_localhost")
    return normalized


def validate_duration(value: str) -> tuple[str, str, str]:
    try:
        return DURATION_OPTIONS[value]
    except KeyError as exc:
        raise ValueError("invalid_duration_option") from exc


def validate_output(value: str) -> Path:
    try:
        output = OUTPUT_OPTIONS[value]
    except KeyError as exc:
        raise ValueError("invalid_output_option") from exc
    output_resolved = output.resolve()
    allowed_root = (REPO_ROOT / "reports" / "paper_runtime").resolve()
    if allowed_root not in output_resolved.parents and output_resolved != allowed_root:
        raise ValueError("output_dir_outside_paper_runtime")
    return output


def find_caffeinate() -> str:
    candidate = shutil.which("caffeinate") or "/usr/bin/caffeinate"
    if candidate and Path(candidate).exists():
        return candidate
    raise RuntimeError("caffeinate_not_available")


def build_runtime_command(
    *,
    duration: str,
    output: str,
    python_executable: str | None = None,
    caffeinate_path: str | None = None,
) -> list[str]:
    duration_flag, duration_value, _duration_label = validate_duration(duration)
    output_dir = validate_output(output)
    caffeinate = caffeinate_path or find_caffeinate()
    python_bin = python_executable or sys.executable
    phase_flags = list(SAFE_FLAGS)
    if output == "pt_rt1_5_2_transport_smoke":
        phase_flags.extend(
            [
                "--founder-approved-pt-rt1-5-2-testnet-transport-smoke",
                "--max-testnet-orders-this-phase",
                "1",
            ]
        )
    return [
        caffeinate,
        "-dimsu",
        python_bin,
        "scripts/run_pt_rt1_paper_observation.py",
        duration_flag,
        duration_value,
        "--output-dir",
        str(output_dir.relative_to(REPO_ROOT)),
        "--decision-log-mode",
        "compact",
        *phase_flags,
    ]


def process_is_running(pid: Any) -> bool:
    try:
        numeric_pid = int(pid)
    except (TypeError, ValueError):
        return False
    if numeric_pid <= 0:
        return False
    try:
        os.kill(numeric_pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def current_status() -> dict[str, Any]:
    state = read_state()
    running = process_is_running(state.get("pid"))
    if state and state.get("running") and not running:
        state = {
            **state,
            "running": False,
            "status": "stopped_or_exited",
            "updated_at_utc": utc_now(),
        }
        write_state(state)
    return {
        "control_server_available": True,
        "running": running,
        "status": state.get("status") or ("running" if running else "idle"),
        "pid": state.get("pid") if running else None,
        "duration": state.get("duration"),
        "duration_label": state.get("duration_label"),
        "output": state.get("output"),
        "output_dir": state.get("output_dir"),
        "started_at_utc": state.get("started_at_utc"),
        "updated_at_utc": state.get("updated_at_utc"),
        "log_path": state.get("log_path"),
        "safe_flags": SAFE_FLAGS,
        "message": state.get("message") or "local_control_server_ready",
    }


def start_runtime(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    status = current_status()
    if status["running"]:
        return HTTPStatus.CONFLICT, {**status, "message": "paper_runtime_already_running"}

    duration = str(payload.get("duration") or "24h")
    output = str(payload.get("output") or "pt_rt1_5_2_week1_active")
    _duration_flag, _duration_value, duration_label = validate_duration(duration)
    output_dir = validate_output(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)

    command = build_runtime_command(duration=duration, output=output)
    log_path = CONTROL_DIR / f"{run_id()}_{duration}_{output}.log"
    log_handle = log_path.open("a", encoding="utf-8")
    log_handle.write(f"{utc_now()} {STARTING_LOG_LINE}\n")
    log_handle.write(f"{utc_now()} starting {' '.join(command)}\n")
    log_handle.flush()
    try:
        process = subprocess.Popen(  # noqa: S603 - command is fully allowlisted above.
            command,
            cwd=REPO_ROOT,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        log_handle.close()
    state = {
        "running": True,
        "status": "running",
        "pid": process.pid,
        "duration": duration,
        "duration_label": duration_label,
        "output": output,
        "output_dir": str(output_dir.relative_to(REPO_ROOT)),
        "started_at_utc": utc_now(),
        "updated_at_utc": utc_now(),
        "log_path": str(log_path.relative_to(REPO_ROOT)),
        "command": command,
        "safe_flags": SAFE_FLAGS,
        "message": "paper_runtime_started_with_caffeinate",
    }
    write_state(state)
    return HTTPStatus.OK, current_status()


def stop_runtime() -> tuple[int, dict[str, Any]]:
    state = read_state()
    pid = state.get("pid")
    if not process_is_running(pid):
        state = {
            **state,
            "running": False,
            "status": "stopped",
            "updated_at_utc": utc_now(),
            "message": "paper_runtime_not_running",
        }
        write_state(state)
        return HTTPStatus.OK, current_status()

    numeric_pid = int(pid)
    try:
        os.killpg(numeric_pid, signal.SIGTERM)
        message = "paper_runtime_stop_signal_sent"
    except ProcessLookupError:
        message = "paper_runtime_already_exited"
    except PermissionError:
        return HTTPStatus.FORBIDDEN, {**current_status(), "message": "permission_denied_stopping_runtime"}

    state = {
        **state,
        "running": False,
        "status": "stopping",
        "updated_at_utc": utc_now(),
        "message": message,
    }
    write_state(state)
    return HTTPStatus.OK, current_status()


class DashboardControlHandler(SimpleHTTPRequestHandler):
    server_version = "MoneyFlowDashboardControl/1.0"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(REPO_ROOT), **kwargs)

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("invalid_json_body") from exc
        if not isinstance(payload, dict):
            raise ValueError("json_body_must_be_object")
        return payload

    def log_message(self, format: str, *args: Any) -> None:
        if should_suppress_access_log(self.command, self.path):
            return
        super().log_message(format, *args)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler method name.
        parsed = urlparse(self.path)
        if parsed.path == "/api/paper-runtime/status":
            self._send_json(HTTPStatus.OK, current_status())
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler method name.
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/paper-runtime/start":
                status_code, payload = start_runtime(self._read_json())
                self._send_json(status_code, payload)
                return
            if parsed.path == "/api/paper-runtime/stop":
                status_code, payload = stop_runtime()
                self._send_json(status_code, payload)
                return
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"control_server_available": True, "message": str(exc)})
            return
        except RuntimeError as exc:
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"control_server_available": True, "message": str(exc)})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"control_server_available": True, "message": "api_route_not_found"})


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the Money Flow dashboard with local PT-RT1 runtime controls.")
    parser.add_argument("--host", default="127.0.0.1", help="Local bind host. Only 127.0.0.1 or localhost are allowed.")
    parser.add_argument("--port", type=int, default=8767, help="Local bind port.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    host = validate_local_host(args.host)
    if args.port <= 0 or args.port > 65535:
        raise SystemExit("invalid_port")

    server = ThreadingHTTPServer((host, args.port), DashboardControlHandler)
    print(f"Serving Money Flow dashboard with local controls at http://{host}:{args.port}/apps/dashboard/index.html")
    print(
        "Paper runtime start always uses caffeinate, PT-RT1.5 candle-close mode, "
        "baseline-only fixed 25 USDC testnet lifecycle gates, and --public-mainnet-only."
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard control server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
