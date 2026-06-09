"""Must 2b — Registry consistency guards.

1. Machine Block in CURRENT_TRUTH.md matches current_truth.json (minus provenance keys).
2. Dashboard JS constants match the registry's lane/timeframe order.

Pure file reads only — no runtime, no DB, no network.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRUTH_PATH = REPO_ROOT / "current_truth.json"
DOC_PATH = REPO_ROOT / "CURRENT_TRUTH.md"
JS_PATH = REPO_ROOT / "apps" / "dashboard" / "evidence-dashboard.js"

_PROVENANCE_KEYS = frozenset(
    {"_anchors", "_enforcing_tests", "_generated_by", "_do_not_hand_edit", "_generated_at_utc"}
)


def _load_registry() -> dict:  # type: ignore[type-arg]
    assert TRUTH_PATH.exists(), (
        f"{TRUTH_PATH} missing — run: python scripts/export_current_truth.py"
    )
    data = json.loads(TRUTH_PATH.read_text(encoding="utf-8"))
    data.pop("_generated_at_utc", None)
    return data


def _registry_substantive(registry: dict) -> dict:  # type: ignore[type-arg]
    return {k: v for k, v in registry.items() if k not in _PROVENANCE_KEYS}


def _extract_machine_block() -> dict:  # type: ignore[type-arg]
    doc = DOC_PATH.read_text(encoding="utf-8")
    pattern = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
    matches = list(pattern.finditer(doc))
    assert matches, f"No ```json block found in {DOC_PATH}"
    return json.loads(matches[-1].group(1))


def _extract_js_list(js: str, const_name: str) -> list:  # type: ignore[type-arg]
    """Extract a JS const array declaration like: const NAME = ["a", "b"];"""
    pattern = re.compile(
        rf"const\s+{re.escape(const_name)}\s*=\s*\[(.*?)\];",
        re.DOTALL,
    )
    m = pattern.search(js)
    assert m, f"{const_name} not found in evidence-dashboard.js"
    raw = m.group(1)
    items = re.findall(r'"([^"]+)"', raw)
    return items


# ---------------------------------------------------------------------------
# 1. Machine Block matches registry
# ---------------------------------------------------------------------------


def test_machine_block_matches_registry_substantive_fields() -> None:
    registry = _load_registry()
    substantive = _registry_substantive(registry)
    machine_block = _extract_machine_block()
    assert machine_block == substantive, (
        "CURRENT_TRUTH.md Machine Block is out of sync with current_truth.json. "
        "Run: python scripts/export_current_truth.py"
    )


def test_machine_block_has_no_provenance_keys() -> None:
    machine_block = _extract_machine_block()
    for key in _PROVENANCE_KEYS:
        assert key not in machine_block, (
            f"Provenance key '{key}' must not appear in the Machine Block"
        )


# ---------------------------------------------------------------------------
# 2. Dashboard constants match registry
# ---------------------------------------------------------------------------


def test_dashboard_active_lane_ids_match_registry() -> None:
    registry = _load_registry()
    expected = [lane["lane_id"] for lane in registry["active_lanes"]]
    js = JS_PATH.read_text(encoding="utf-8")
    actual = _extract_js_list(js, "PAPER_OBSERVATION_WEEK2_ACTIVE_LANE_IDS")
    assert actual == expected, (
        f"PAPER_OBSERVATION_WEEK2_ACTIVE_LANE_IDS in JS ({actual}) "
        f"does not match registry active_lanes ({expected}). "
        "Do NOT auto-edit the dashboard in this phase — fix the registry or open a follow-up."
    )


def test_dashboard_archived_lane_ids_match_registry() -> None:
    registry = _load_registry()
    expected = [lane["lane_id"] for lane in registry["archived_lanes"]]
    js = JS_PATH.read_text(encoding="utf-8")
    actual = _extract_js_list(js, "PAPER_OBSERVATION_WEEK2_ARCHIVED_LANE_IDS")
    assert actual == expected, (
        f"PAPER_OBSERVATION_WEEK2_ARCHIVED_LANE_IDS in JS ({actual}) "
        f"does not match registry archived_lanes ({expected})."
    )


def test_dashboard_active_timeframes_match_registry() -> None:
    registry = _load_registry()
    expected = registry["active_timeframes"]
    js = JS_PATH.read_text(encoding="utf-8")
    actual = _extract_js_list(js, "PAPER_OBSERVATION_ACTIVE_TIMEFRAMES")
    assert actual == expected, (
        f"PAPER_OBSERVATION_ACTIVE_TIMEFRAMES in JS ({actual}) "
        f"does not match registry active_timeframes ({expected})."
    )


def test_dashboard_disabled_timeframes_match_registry() -> None:
    registry = _load_registry()
    expected = registry["paused_timeframes"]
    js = JS_PATH.read_text(encoding="utf-8")
    actual = _extract_js_list(js, "PAPER_OBSERVATION_DISABLED_TIMEFRAMES")
    assert actual == expected, (
        f"PAPER_OBSERVATION_DISABLED_TIMEFRAMES in JS ({actual}) "
        f"does not match registry paused_timeframes ({expected})."
    )
