"""RLOG1 Research Log — deterministic, offline tests.

No network, no runtime, no DB. Asserts the phase's documented guarantees:
  - the aggregator parses the Decision-Log research_log blocks, joins the
    committed evidence summaries, and is reproducible (--check passes against
    the committed docs/research_log.json);
  - the honest outcome taxonomy comes ONLY from the authored Decision-Log
    field — a phase whose summary status says "ready_for_founder_review" (or
    any other upbeat status string) must keep its authored mixed/context/fail
    outcome and must never map to `pass`/green (pinned regression);
  - docs/research_log.json carries an entry per backfilled phase with all six
    post-mortem facets;
  - the joined analytics are real (EXEC-EV1 ZEC concentration, SEL-EV1 random
    benchmark) and derived from the committed summaries;
  - the dashboard renderer colors badges from the authored outcome only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_research_log  # noqa: E402

OUTCOMES = {"fail", "mixed", "context", "pass"}
BACKFILLED_PHASES = {
    "SEL-EV1",
    "EXEC-EV1",
    "SV2.3",
    "SV2.2",
    "GOAL-STRAT1",
    "GOAL-STRAT2",
    "SOR-EV1",
    "SOR-EV2",
    "SOR-EV3",
    "MF-ORIG-EV1.1",
    "MF-ORIG-EV2",
    "EV-AUDIT1",
}


def _committed() -> dict:
    return json.loads((REPO_ROOT / "docs" / "research_log.json").read_text(encoding="utf-8"))


def _entries_by_phase(payload: dict) -> dict:
    return {entry["phase"]: entry for entry in payload["entries"]}


def test_aggregator_is_reproducible_and_committed_file_matches() -> None:
    fresh_one = build_research_log.render_json(build_research_log.build())
    fresh_two = build_research_log.render_json(build_research_log.build())
    assert fresh_one == fresh_two, "aggregator must be deterministic"
    committed = (REPO_ROOT / "docs" / "research_log.json").read_text(encoding="utf-8")
    assert committed == fresh_one, (
        "docs/research_log.json drifts from the Decision Log blocks — run "
        "scripts/build_research_log.py"
    )
    assert build_research_log.main(["--check"]) == 0


def test_every_backfilled_phase_has_an_entry_with_facets() -> None:
    payload = _committed()
    by_phase = _entries_by_phase(payload)
    missing = BACKFILLED_PHASES - set(by_phase)
    assert not missing, f"missing research_log entries: {sorted(missing)}"
    assert payload["entry_count"] >= len(BACKFILLED_PHASES)
    for phase in BACKFILLED_PHASES:
        entry = by_phase[phase]
        facets = entry["facets"]
        assert entry["title"] and entry["finding"], phase
        for facet in ("why", "worked", "didnt", "lesson", "changed"):
            assert str(facets.get(facet) or "").strip(), f"{phase}: empty facet {facet}"
        # our_error is text or null — and null carries an explanatory note or is allowed bare.
        assert "our_error" in facets, phase
        assert entry["evidence_summary"], phase
        assert entry["evidence_summary_found"] is True, f"{phase}: evidence summary missing on disk"


def test_outcome_taxonomy_is_authored_never_inferred() -> None:
    """Pinned regression: upbeat raw status strings must not become green."""
    payload = _committed()
    by_phase = _entries_by_phase(payload)
    for entry in payload["entries"]:
        assert entry["outcome"] in OUTCOMES, entry["phase"]

    # These summaries carry upbeat status/verdict strings ("...ready_for_founder_review",
    # "...complete") but their authored outcomes are non-positive — they must
    # render amber/red/blue, never green.
    upbeat_but_not_pass = {
        "SOR-EV2": "mixed",      # verdict: true_forward_replay_ready_for_founder_review
        "SOR-EV3": "mixed",      # verdict: ...ready_for_founder_review
        "MF-ORIG-EV1.1": "mixed",  # verdict: ...ready_for_founder_review
        "MF-ORIG-EV2": "mixed",  # verdict: ...ready_for_founder_review
        "EXEC-EV1": "fail",      # status: execution_quality_evidence_complete
        "SV2.3": "fail",         # status: realistic_backtest_complete
        "SV2.2": "context",      # status: latest_replay_complete
    }
    for phase, expected in upbeat_but_not_pass.items():
        entry = by_phase[phase]
        summary = json.loads((REPO_ROOT / entry["evidence_summary"]).read_text(encoding="utf-8"))
        raw_status = " ".join(
            str(summary.get(key, "")) for key in ("verdict", "status", "conclusion", "audit_verdict")
        ).lower()
        assert "ready" in raw_status or "complete" in raw_status, (
            f"{phase}: fixture drifted — expected an upbeat raw status string"
        )
        assert entry["outcome"] == expected, f"{phase}: authored outcome drifted"
        assert entry["outcome"] != "pass", f"{phase}: upbeat status must never render green"

    # Nothing passed: the standing strip and the entries agree.
    assert payload["standing"]["passed_gate"] == sum(
        1 for entry in payload["entries"] if entry["outcome"] == "pass"
    )


def test_outcome_validation_rejects_non_taxonomy_values() -> None:
    blocks = "```yaml\nresearch_log:\n  phase: X-TEST\n  outcome: ready_for_review\n```\n"
    try:
        build_research_log.parse_research_log_blocks(blocks)
    except ValueError as error:
        assert "taxonomy" in str(error)
    else:
        raise AssertionError("non-taxonomy outcome must be rejected")


def test_joined_analytics_are_real() -> None:
    payload = _committed()
    by_phase = _entries_by_phase(payload)

    exec_blocks = by_phase["EXEC-EV1"]["analytics"]
    assert exec_blocks, "EXEC-EV1 must surface the concentration analytics"
    kvs = {kv["label"]: kv["value"] for block in exec_blocks for kv in block.get("kvs", [])}
    assert kvs["ZEC share of PnL"] == "132%"
    assert kvs["Negative symbols"] == "15 / 23"
    assert any(block.get("table", {}).get("rows") for block in exec_blocks), (
        "EXEC-EV1 per-symbol concentration table missing"
    )

    sel_blocks = by_phase["SEL-EV1"]["analytics"]
    kvs = {kv["label"]: kv["value"] for block in sel_blocks for kv in block.get("kvs", [])}
    assert kvs["Random seeds beaten"] == "2 / 50"
    assert kvs["OOS net (post-friction)"].startswith("−")
    assert any(block.get("table", {}).get("rows") for block in sel_blocks), (
        "SEL-EV1 near-miss config table missing"
    )

    # Lessons rail is derived from authored hardened_gate fields.
    gates = {(row["phase"], row["gate"]) for row in payload["lessons_hardened_gates"]}
    assert ("EXEC-EV1", "leave-one-out concentration gate") in gates
    assert ("SEL-EV1", "beat random OOS, or it's nothing") in gates
    assert ("MF-ORIG-EV1.1", "PnL must reconcile to equity") in gates

    # Active lanes are auto-joined from current_truth.json.
    truth = json.loads((REPO_ROOT / "current_truth.json").read_text(encoding="utf-8"))
    assert [lane["lane_id"] for lane in payload["active_lanes"]] == [
        lane["lane_id"] for lane in truth["active_lanes"]
    ]


def test_renderer_uses_authored_outcome_only() -> None:
    js = (REPO_ROOT / "apps" / "dashboard" / "evidence-dashboard.js").read_text(encoding="utf-8")
    assert "RESEARCH_LOG_OUTCOME_CLASSES" in js
    assert "researchLogOutcomeClass" in js
    # The old naive fallback chain must not return.
    assert "researchLogVerdict(" not in js
    assert "payload?.verdict || payload?.conclusion" not in js
    assert "audit_verdict ||" not in js
    # Badge classes map 1:1 from the taxonomy.
    for tone in ("fail", "mixed", "context", "pass"):
        assert tone in js
    css = (REPO_ROOT / "apps" / "dashboard" / "evidence-dashboard.css").read_text(encoding="utf-8")
    for selector in (".rlog-badge.fail", ".rlog-badge.mixed", ".rlog-badge.context", ".rlog-badge.pass"):
        assert selector in css
    # Facet labels rendered for the six post-mortem dimensions.
    for label in ("Why it failed", "What worked", "What didn't", "Lesson", "Our error", "What it changed"):
        assert label in js
