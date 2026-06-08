#!/usr/bin/env python3
"""Read-only PT-RT1 runtime log watcher for operators."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = "pt_rt1_6_week2_active"
RUNTIME_ROOT = REPO_ROOT / "reports" / "paper_runtime"
CONTROL_STATE = RUNTIME_ROOT / "dashboard_control" / "state.json"
LOG_SPECS = {
    "audit": ("runtime_audit.jsonl", "heartbeat / public-mainnet connection"),
    "decisions": ("decisions.jsonl", "paper decisions / signal checks"),
    "trades": ("trades.jsonl", "closed synthetic trades only"),
    "testnet": ("testnet_order_lifecycle.jsonl", "separate Hyperliquid testnet lifecycle"),
    "health": ("data_health.json", "latest data-health snapshot"),
    "summary": ("summary.json", "latest runtime summary"),
}
TAIL_GROUPS = {
    "all": ["audit", "decisions", "trades", "testnet"],
    **{key: [key] for key in LOG_SPECS},
}


def runtime_dir(scope: str) -> Path:
    return RUNTIME_ROOT / scope


def log_path(scope: str, key: str) -> Path:
    return runtime_dir(scope) / LOG_SPECS[key][0]


def file_status(path: Path) -> dict[str, object]:
    exists = path.exists()
    stat = path.stat() if exists else None
    return {
        "path": str(path),
        "exists": exists,
        "size_bytes": stat.st_size if stat else 0,
        "modified_epoch": stat.st_mtime if stat else None,
    }


def read_control_state() -> dict[str, object]:
    try:
        return json.loads(CONTROL_STATE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {"status": "control_state_invalid"}


def runtime_process_lines() -> list[str]:
    result = subprocess.run(
        ["pgrep", "-fl", "run_pt_rt1_paper_observation"],
        check=False,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def selected_paths(scope: str, target: str) -> list[Path]:
    return [log_path(scope, key) for key in TAIL_GROUPS[target]]


def print_status(scope: str) -> None:
    control = read_control_state()
    print(f"scope: {scope}")
    print(f"output_dir: {runtime_dir(scope)}")
    print(f"control_state_running: {control.get('running', 'unknown')}")
    print(f"control_state_output: {control.get('output', 'unknown')}")
    print(f"control_state_message: {control.get('message', 'unknown')}")
    processes = runtime_process_lines()
    print(f"runtime_processes: {len(processes)}")
    for line in processes:
        print(f"  {line}")
    print()
    for key, (_filename, role) in LOG_SPECS.items():
        status = file_status(log_path(scope, key))
        size = status["size_bytes"]
        modified = status["modified_epoch"]
        print(f"{key}: {role}")
        print(f"  path: {status['path']}")
        print(f"  exists: {status['exists']}")
        print(f"  size_bytes: {size}")
        print(f"  modified_epoch: {modified}")
        print(f"  tail: tail -n 50 -F {log_path(scope, key)}")
        if key == "trades":
            print("  note: trades.jsonl can stay empty until a synthetic position closes.")


def print_latest(scope: str, target: str, lines: int) -> None:
    for path in selected_paths(scope, target):
        print(f"==> {path} <==")
        if not path.exists():
            print("missing")
            continue
        if path.stat().st_size == 0:
            print("empty")
            continue
        result = subprocess.run(
            ["tail", "-n", str(lines), str(path)],
            check=False,
            text=True,
        )
        if result.returncode != 0:
            raise SystemExit(result.returncode)


def tail(scope: str, target: str, lines: int) -> None:
    paths = selected_paths(scope, target)
    missing = [path for path in paths if not path.exists()]
    for path in missing:
        print(f"warning: missing file: {path}", file=sys.stderr)
    existing = [path for path in paths if path.exists()]
    if not existing:
        raise SystemExit("no selected runtime log files exist")
    command = ["tail", "-n", str(lines), "-F", *[str(path) for path in existing]]
    raise SystemExit(subprocess.call(command))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect or tail PT-RT1 runtime logs without changing runtime state.")
    parser.add_argument("--scope", default=DEFAULT_SCOPE, help="Runtime output scope under reports/paper_runtime/.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--status", action="store_true", help="Print process, control-state, file, and tail-command status.")
    mode.add_argument("--latest", choices=sorted(TAIL_GROUPS), help="Print latest rows immediately from one log group.")
    mode.add_argument("--tail", choices=sorted(TAIL_GROUPS), help="Follow one log group with tail -F.")
    parser.add_argument("--lines", type=int, default=50, help="Rows to show before following or in latest mode.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.lines <= 0:
        raise SystemExit("--lines must be positive")
    if args.latest:
        print_latest(args.scope, args.latest, args.lines)
        return 0
    if args.tail:
        tail(args.scope, args.tail, args.lines)
        return 0
    print_status(args.scope)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
