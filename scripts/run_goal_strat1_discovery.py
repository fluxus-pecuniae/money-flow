"""Run GOAL-STRAT1 research-only autonomous strategy discovery."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "services" / "strategy_validation" / "goal_strat1.py"
    spec = importlib.util.spec_from_file_location("goal_strat1_research_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load GOAL-STRAT1 module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_GOAL_STRAT1 = _load_module()
DEFAULT_SELECTED_REPLAY_GLOBS = _GOAL_STRAT1.DEFAULT_SELECTED_REPLAY_GLOBS
build_goal_strat1_report = _GOAL_STRAT1.build_goal_strat1_report
write_goal_strat1_outputs = _GOAL_STRAT1.write_goal_strat1_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run GOAL-STRAT1 research-only strategy discovery over local public-mainnet evidence JSON.",
    )
    parser.add_argument("--markdown-output", default="docs/goal_strat1_strategy_discovery.md")
    parser.add_argument("--json-output", default="docs/goal_strat1_strategy_discovery_summary.json")
    parser.add_argument(
        "--selected-replay-glob",
        action="append",
        default=[],
        help="Optional selected-replay glob. Repeat to add sources. Defaults to SV2.0.2/SV2.1 Money Flow baseline replays.",
    )
    parser.add_argument("--max-total-candidate-runs", type=int, default=121)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_goal_strat1_report(
        selected_replay_globs=tuple(args.selected_replay_glob or DEFAULT_SELECTED_REPLAY_GLOBS),
        max_total_candidate_runs=args.max_total_candidate_runs,
        generated_at=datetime.now(UTC),
    )
    write_goal_strat1_outputs(report, args.markdown_output, args.json_output)
    print(f"wrote {args.markdown_output}")
    print(f"wrote {args.json_output}")
    print(f"conclusion {report['conclusion']}")
    print(f"candidate_runs {report['search_budget_used']['candidate_runs']}")
    print(f"passing_candidates {len(report.get('passing_candidates', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
