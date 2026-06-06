#!/usr/bin/env python3
"""Run GOAL-STRAT2 research-only non-existing strategy selection."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _load_goal_strat2():
    module_path = Path(__file__).resolve().parents[1] / "services" / "strategy_validation" / "goal_strat2.py"
    spec = importlib.util.spec_from_file_location("goal_strat2", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description="Select two non-existing research-only strategies worth testing.")
    parser.add_argument("--source-summary", default="docs/goal_strat1_strategy_discovery_summary.json")
    parser.add_argument("--report", default="docs/goal_strat2_two_non_existing_strategies.md")
    parser.add_argument("--summary", default="docs/goal_strat2_two_non_existing_strategies_summary.json")
    args = parser.parse_args()

    goal_strat2 = _load_goal_strat2()
    report = goal_strat2.build_goal_strat2_report(Path(args.source_summary))
    goal_strat2.write_goal_strat2_outputs(report, Path(args.report), Path(args.summary))
    print(report["decision"])
    for candidate in report["selected_candidates"]:
        print(candidate["strategy_id"])
    return 0 if len(report["selected_candidates"]) == 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
