"""Export canonical current-truth registry to current_truth.json and render CURRENT_TRUTH.md.

Read-only: imports Python anchors, writes JSON and Machine Block. No runtime, no network, no orders.

Usage:
    python scripts/export_current_truth.py            # write json + render Machine Block in CURRENT_TRUTH.md
    python scripts/export_current_truth.py --check    # exit non-zero if on-disk json differs
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from core.config.settings import RuntimeSafetyPolicy
from services.paper_runtime.pt_rt1 import (
    PT_RT1_4_DISABLED_TIMEFRAMES,
    PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC,
    PT_RT1_6_ACTIVE_STRATEGY_LANES,
    PT_RT1_6_ACTIVE_TIMEFRAMES,
    PT_RT1_6_ARCHIVED_STRATEGY_LANES,
    PT_RT1_6_RUNTIME_SCOPE,
    SUPPORTED_CANONICAL_SYMBOLS,
    pt_rt1_6_lane_testnet_eligible,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "current_truth.json"
DOC_PATH = REPO_ROOT / "CURRENT_TRUTH.md"

# Provenance keys excluded from the Machine Block (present in json, not in the doc block)
_PROVENANCE_KEYS = frozenset(
    {"_anchors", "_enforcing_tests", "_generated_by", "_do_not_hand_edit", "_generated_at_utc"}
)

# Markers bounding the Machine Block region in CURRENT_TRUTH.md
_BLOCK_START = "```json"
_BLOCK_END = "```"

# Human-readable role labels keyed by LaneRole value
_ROLE_LABELS: dict[str, str] = {
    "control_lane": "Control / Baseline",
    "evidence_only_candidate_lane": "Diagnostic Comparator",
    "mf_orig_evidence_only_reference_lane": "MF-ORIG Source-Faithful Candidate",
    "wildcard_expert_observation_lane": "Wildcard Expert Observation",
}


def _lane_entry(lane) -> dict:  # type: ignore[no-untyped-def]
    role_val = str(lane.role)
    return {
        "lane_id": lane.lane_id,
        "display_name": lane.display_name,
        "role": role_val,
        "role_label": _ROLE_LABELS.get(role_val, role_val),
        "testnet_eligible": pt_rt1_6_lane_testnet_eligible(lane.lane_id),
        "production_approved": False,
        "live_approved": False,
        "pnl_source": "Synthetic Ledger",
        "signal_truth": "Public Mainnet Candles",
    }


def build_truth() -> dict:  # type: ignore[type-arg]
    """Build the current-truth dict from canonical Python anchors.

    Deterministic ordering. No side effects.
    """
    policy = RuntimeSafetyPolicy()

    active_lanes = [_lane_entry(lane) for lane in PT_RT1_6_ACTIVE_STRATEGY_LANES]
    archived_lanes = [_lane_entry(lane) for lane in PT_RT1_6_ARCHIVED_STRATEGY_LANES]

    testnet_eligible_lanes = [lane["lane_id"] for lane in active_lanes if lane["testnet_eligible"]]

    return {
        "scope": PT_RT1_6_RUNTIME_SCOPE,
        "active_surface": "PT-RT1.6 Week 2 Paper Observation",
        "strategy_truth": "Public Hyperliquid mainnet fully closed candles and derived indicators",
        "pnl_truth": "Independent synthetic 10,000 USDC paper ledgers per lane",
        "production_approved": False,
        "live_trading_approved": False,
        "active_lanes": active_lanes,
        "archived_lanes": archived_lanes,
        "active_timeframes": list(PT_RT1_6_ACTIVE_TIMEFRAMES),
        "paused_timeframes": list(PT_RT1_4_DISABLED_TIMEFRAMES),
        "configured_symbols": list(SUPPORTED_CANONICAL_SYMBOLS),
        "testnet_eligible_lanes": testnet_eligible_lanes,
        "testnet_fixed_notional_usdc": int(PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC),
        "testnet_fills_update_synthetic_pnl": False,
        "runtime_safety_policy": {
            "live_trading_enabled": policy.live_trading_enabled,
            "exchange_order_submission_enabled": policy.exchange_order_submission_enabled,
            "private_exchange_endpoints_enabled": policy.private_exchange_endpoints_enabled,
            "sandbox_mode_required": policy.sandbox_mode_required,
        },
        "_anchors": {
            "scope": "pt_rt1.py::PT_RT1_6_RUNTIME_SCOPE",
            "active_lanes": (
                "pt_rt1.py::PT_RT1_6_ACTIVE_STRATEGY_LANE_IDS + PT_RT1_6_ACTIVE_STRATEGY_LANES"
            ),
            "archived_lanes": (
                "pt_rt1.py::PT_RT1_6_ARCHIVED_STRATEGY_LANE_IDS + PT_RT1_6_ARCHIVED_STRATEGY_LANES"
            ),
            "active_timeframes": "pt_rt1.py::PT_RT1_6_ACTIVE_TIMEFRAMES",
            "paused_timeframes": "pt_rt1.py::PT_RT1_4_DISABLED_TIMEFRAMES",
            "configured_symbols": "pt_rt1.py::SUPPORTED_CANONICAL_SYMBOLS",
            "testnet_eligible_lanes": "pt_rt1.py::pt_rt1_6_lane_testnet_eligible()",
            "testnet_fixed_notional_usdc": "pt_rt1.py::PT_RT1_5_TESTNET_ORDER_NOTIONAL_USDC",
            "runtime_safety_policy": "settings.py::RuntimeSafetyPolicy (defaults)",
        },
        "_enforcing_tests": [
            "tests/test_pt_rt1_6_week2_slate.py",
            "tests/test_current_truth_registry.py",
            "tests/test_current_truth_consistency.py",
        ],
        "_generated_by": "scripts/export_current_truth.py",
        "_do_not_hand_edit": True,
    }


def _serialize(truth: dict) -> str:  # type: ignore[type-arg]
    return json.dumps(truth, indent=2, ensure_ascii=False) + "\n"


def _machine_block_json(truth: dict) -> str:  # type: ignore[type-arg]
    """Serialize only the substantive fields (no provenance keys) for the Machine Block."""
    substantive = {k: v for k, v in truth.items() if k not in _PROVENANCE_KEYS}
    return json.dumps(substantive, indent=2, ensure_ascii=False)


def render_machine_block(truth: dict, doc_path: Path = DOC_PATH) -> None:  # type: ignore[type-arg]
    """Replace the fenced ```json block in CURRENT_TRUTH.md with freshly generated content."""
    if not doc_path.exists():
        return
    doc = doc_path.read_text(encoding="utf-8")
    new_block = _machine_block_json(truth)
    # Replace the content between the LAST ```json ... ``` fences
    pattern = re.compile(r"(```json\n)(.*?)(\n```)", re.DOTALL)
    matches = list(pattern.finditer(doc))
    if not matches:
        return
    last = matches[-1]
    updated = doc[: last.start()] + "```json\n" + new_block + "\n```" + doc[last.end() :]
    doc_path.write_text(updated, encoding="utf-8")


def extract_machine_block(doc_path: Path = DOC_PATH) -> dict:  # type: ignore[type-arg]
    """Extract and parse the fenced ```json block from CURRENT_TRUTH.md."""
    doc = doc_path.read_text(encoding="utf-8")
    pattern = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
    matches = list(pattern.finditer(doc))
    if not matches:
        raise ValueError(f"No ```json block found in {doc_path}")
    return json.loads(matches[-1].group(1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if on-disk current_truth.json differs from a fresh export.",
    )
    args = parser.parse_args()

    truth = build_truth()
    fresh = _serialize(truth)

    if args.check:
        if not OUTPUT_PATH.exists():
            print(f"FAIL: {OUTPUT_PATH} does not exist. Run without --check to generate.")
            sys.exit(1)
        on_disk = OUTPUT_PATH.read_text(encoding="utf-8")
        on_disk_data = json.loads(on_disk)
        fresh_data = json.loads(fresh)
        on_disk_data.pop("_generated_at_utc", None)
        fresh_data.pop("_generated_at_utc", None)
        if on_disk_data == fresh_data:
            print("OK: current_truth.json matches fresh export (ignoring timestamp).")
            sys.exit(0)
        print("FAIL: current_truth.json is out of sync with anchors.")
        print("Run: python scripts/export_current_truth.py")
        sys.exit(1)

    truth["_generated_at_utc"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUTPUT_PATH.write_text(_serialize(truth), encoding="utf-8")
    print(f"Written: {OUTPUT_PATH}")
    render_machine_block(truth)
    print(f"Machine Block rendered: {DOC_PATH}")


if __name__ == "__main__":
    main()
