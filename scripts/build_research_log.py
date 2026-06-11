#!/usr/bin/env python3
"""RLOG1 — build the Research Log dataset (docs/research_log.json).

READ-ONLY aggregator over committed records, deterministic and offline:

  - Parses the fenced ```yaml `research_log:` post-mortem blocks from
    money-flow/03_Decision_Log.md (the authored source of truth — additive
    backfill, the factual record is never altered).
  - Joins each phase to its committed `evidence_summary` docs/*_summary.json
    and resolves the block's `analytics` references (dotted-path values or
    named computed views such as the EXEC-EV1 per-symbol concentration table
    and the SEL-EV1 random-benchmark headline).
  - Joins the active paper lanes from current_truth.json.
  - Emits docs/research_log.json (entries newest-first).

The honest outcome taxonomy (`fail` / `mixed` / `context` / `pass`) comes ONLY
from the authored Decision-Log field — it is never inferred from a summary's
raw status/verdict string ("ready_for_founder_review" must never render
green).

Usage:
    .venv/bin/python scripts/build_research_log.py            # write
    .venv/bin/python scripts/build_research_log.py --check    # drift guard

No network, no runtime, no DB. Display/docs tooling only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DECISION_LOG = REPO_ROOT / "money-flow" / "03_Decision_Log.md"
CURRENT_TRUTH = REPO_ROOT / "current_truth.json"
OUTPUT = REPO_ROOT / "docs" / "research_log.json"

OUTCOMES = ("fail", "mixed", "context", "pass")

# Authored standing context (documented sources; not inferred from statuses):
# hypotheses tested ~130+ = GOAL-STRAT1 121 bounded configs + STRAT-DISC1 12
# curated hypotheses + SEL-EV1 16 selection configs + SOR/MF-ORIG variants;
# 7 strategy families per the GOAL-STRAT1 search budget.
STANDING = {
    "hypotheses_tested": "130+",
    "strategy_families": 7,
    "production_approved": "NONE",
    "live_trading": "NOT APPROVED",
    "standing_verdict": "no price-rule edge",
}
VERDICT_BANNER = {
    "headline": "No demonstrable price-rule edge to date.",
    "sub": (
        "Two hypothesis classes — per-symbol universal rules and cross-sectional "
        "selection — comprehensively tested under realistic friction. Neither beats "
        "baseline; selection does not beat random. Apparent positives traced to "
        "single-symbol (ZEC) concentration."
    ),
    "tone": "fail",
}
AT_A_GLANCE = [
    {"label": "per-symbol rules", "result": "no edge"},
    {"label": "selection", "result": "no skill"},
    {"label": "variants", "result": "none promoted"},
    {"label": "original MF", "result": "underperformed"},
    {"label": "friction", "result": "kills thin-alt pockets"},
]
UNTESTED_FRONTIER = (
    "Untested frontier: cross-venue microstructure (CoinRoutes) — pending "
    "data-use clearance."
)
BOUNDARIES = (
    "Every row is research/evidence only — no order, testnet, live, or production "
    "approval follows from anything here. Modeled friction is an assumption layer, "
    "not real historical depth. Synthetic paper PnL is not live PnL. Live trading "
    "is not approved."
)


def _dec(value: Any) -> Decimal:
    return Decimal(str(value))


def _fmt_money(value: Decimal) -> str:
    sign = "−" if value < 0 else "+" if value > 0 else ""
    magnitude = abs(value)
    if magnitude >= 1000:
        return f"{sign}{magnitude / 1000:,.0f}k"
    return f"{sign}{magnitude:,.0f}"


def parse_research_log_blocks(text: str) -> list[dict[str, Any]]:
    blocks = re.findall(r"```yaml\n(research_log:.*?)```", text, re.S)
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in blocks:
        data = yaml.safe_load(raw)["research_log"]
        phase = str(data.get("phase") or "")
        if not phase:
            raise ValueError("research_log block missing phase")
        if phase in seen:
            raise ValueError(f"duplicate research_log block for phase {phase}")
        seen.add(phase)
        outcome = data.get("outcome")
        if outcome not in OUTCOMES:
            raise ValueError(
                f"{phase}: outcome must be one of {OUTCOMES} (authored taxonomy), got {outcome!r}"
            )
        entries.append(data)
    return entries


def load_summary(entry: dict[str, Any]) -> dict[str, Any] | None:
    rel = entry.get("evidence_summary")
    if not rel:
        return None
    path = REPO_ROOT / rel
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def dotted(summary: dict[str, Any], path: str) -> Any:
    node: Any = summary
    for part in path.split("."):
        if isinstance(node, dict):
            node = node.get(part)
        else:
            return None
    return node


# ---------------------------------------------------------------------------
# Named computed analytics (deterministic views over the committed summaries)
# ---------------------------------------------------------------------------


def sel_ev1_random_benchmark(summary: dict[str, Any]) -> dict[str, Any]:
    headline = summary["headline_comparison"]
    gate = summary["selection_gate"]
    dist = gate["random_oos_distribution"]
    return {
        "kvs": [
            {"label": "OOS net (post-friction)", "value": _fmt_money(_dec(headline["strategy_oos_net_pnl"])), "tone": "neg"},
            {"label": "Random median OOS", "value": _fmt_money(_dec(dist["median"]))},
            {"label": "Random seeds beaten", "value": f"{gate['random_seeds_beaten']} / {dist['count']}", "tone": "neg"},
            {"label": "Rotation diversity", "value": f"{gate['diversity']['distinct_symbols_held']} names"},
        ]
    }


def sel_ev1_top_oos_configs(summary: dict[str, Any]) -> dict[str, Any]:
    rows = sorted(
        summary["per_config_results"],
        key=lambda row: _dec(row["oos_net_pnl"]),
        reverse=True,
    )[:3]
    return {
        "table": {
            "columns": ["Config", "Train net", "OOS net"],
            "rows": [
                [row["config_id"], _fmt_money(_dec(row["train_net_pnl"])), _fmt_money(_dec(row["oos_net_pnl"]))]
                for row in rows
            ],
        },
        "note": "Hindsight-best OOS configs; the train-only choice picked none of them — that gap is the overfit.",
    }


def exec_ev1_symbol_concentration(summary: dict[str, Any]) -> dict[str, Any]:
    by_symbol: dict[str, Decimal] = defaultdict(Decimal)
    for row in summary["results"]:
        if (
            row["strategy_id"] == "mf_orig_1d_stage2_breakout_resistance_full_equity"
            and row["execution_scenario"] == "exec_ev1_base"
        ):
            by_symbol[row["symbol"]] += _dec(row["net_pnl"])
    total = sum(by_symbol.values(), Decimal("0"))
    zec = by_symbol.get("ZEC", Decimal("0"))
    negative = sum(1 for value in by_symbol.values() if value < 0)
    top = sorted(by_symbol.items(), key=lambda item: item[1], reverse=True)[:5]
    zec_share = (zec / total * 100) if total else Decimal("0")
    return {
        "kvs": [
            {"label": "mf_orig base", "value": _fmt_money(total)},
            {"label": "ZEC share of PnL", "value": f"{zec_share:.0f}%", "tone": "neg"},
            {"label": "ex-ZEC", "value": _fmt_money(total - zec), "tone": "neg"},
            {"label": "Negative symbols", "value": f"{negative} / {len(by_symbol)}", "tone": "neg"},
        ],
        "table": {
            "columns": ["Symbol", "Net PnL", "Share of total"],
            "rows": [
                [symbol, _fmt_money(value), f"{(value / total * 100):.0f}%" if total else "n/a"]
                for symbol, value in top
            ],
        },
        "note": "Per-symbol net PnL, mf_orig lane, base scenario — the whole edge is one thin alt.",
    }


def sv23_aggregate_net(summary: dict[str, Any]) -> dict[str, Any]:
    aggregates = summary.get("aggregate_results", [])
    total = sum(_dec(row.get("total_net_pnl", 0)) for row in aggregates)
    survivors = [row for row in aggregates if str(row.get("verdict", "")).startswith("survives")]
    return {
        "kvs": [
            {"label": "Result rows", "value": str(summary.get("result_count", len(summary.get("results", []))))},
            {"label": "Aggregate net (all lanes/scenarios)", "value": _fmt_money(total), "tone": "neg"},
            {"label": "Lane/scenario survivors", "value": str(len(survivors)), "tone": "neg"},
        ]
    }


def sv22_refresh_stats(summary: dict[str, Any]) -> dict[str, Any]:
    datasets = [row for row in summary.get("datasets", []) if row.get("status") == "refreshed"]
    timeframes = sorted({row.get("timeframe") for row in datasets if row.get("timeframe")})
    symbols = sorted({row.get("symbol") for row in datasets if row.get("symbol")})
    return {
        "kvs": [
            {"label": "Symbols refreshed", "value": str(len(symbols))},
            {"label": "Timeframes", "value": " / ".join(timeframes) or "n/a"},
            {"label": "Datasets", "value": str(len(datasets))},
        ]
    }


def goal_strat1_stats(summary: dict[str, Any]) -> dict[str, Any]:
    used = summary.get("search_budget_used", {})
    return {
        "kvs": [
            {"label": "Configs tested", "value": str(used.get("candidate_runs", "n/a"))},
            {"label": "Families", "value": str(used.get("strategy_families", "n/a"))},
            {"label": "Passed gate", "value": str(len(summary.get("passing_candidates", []))), "tone": "neg"},
            {"label": "Datasets accepted", "value": str(used.get("datasets_accepted", "n/a"))},
        ]
    }


def tsmom_ev1_risk_adjusted_headline(summary: dict[str, Any]) -> dict[str, Any]:
    h = summary["headline_comparison"]
    s, b = h["strategy_oos"], h["buy_hold_oos"]

    def fmt(value: Any, suffix: str = "") -> str:
        return f"{Decimal(str(value)):.2f}{suffix}" if value is not None else "n/a"

    return {
        "kvs": [
            {"label": "OOS Sharpe (strategy vs hold)", "value": f"{fmt(s['sharpe_annual'])} vs {fmt(b['sharpe_annual'])}", "tone": "neg"},
            {"label": "OOS max drawdown", "value": f"{fmt(s['max_drawdown_pct'], '%')} vs {fmt(b['max_drawdown_pct'], '%')}"},
            {"label": "OOS return", "value": f"{fmt(s['total_return_pct'], '%')} vs {fmt(b['total_return_pct'], '%')}", "tone": "neg"},
            {"label": "Sharpe edge vs buy-hold", "value": fmt(h["oos_sharpe_edge_vs_buy_hold"])},
        ],
        "note": "Relative bar passed with qualifiers: absolute OOS Sharpe negative - defensive value in a bear, not profit.",
    }


def tsmom_ev1_leave_one_out(summary: dict[str, Any]) -> dict[str, Any]:
    rows = [
        [symbol, str(row["oos_strategy_sharpe"]), str(row["oos_buy_hold_sharpe"]), str(row["oos_sharpe_edge_vs_buy_hold"])]
        for symbol, row in sorted(summary["leave_one_out"].items())
    ]
    return {
        "table": {"columns": ["Dropped", "Strategy Sharpe", "Buy-hold Sharpe", "Edge"], "rows": rows},
        "note": "Dropping any single asset (from book AND benchmark) keeps the risk-adjusted edge - not a one-name artifact.",
    }


COMPUTED = {
    "sel_ev1_random_benchmark": sel_ev1_random_benchmark,
    "sel_ev1_top_oos_configs": sel_ev1_top_oos_configs,
    "exec_ev1_symbol_concentration": exec_ev1_symbol_concentration,
    "sv23_aggregate_net": sv23_aggregate_net,
    "sv22_refresh_stats": sv22_refresh_stats,
    "goal_strat1_stats": goal_strat1_stats,
    "tsmom_ev1_risk_adjusted_headline": tsmom_ev1_risk_adjusted_headline,
    "tsmom_ev1_leave_one_out": tsmom_ev1_leave_one_out,
}


def resolve_analytics(entry: dict[str, Any], summary: dict[str, Any] | None) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for spec in entry.get("analytics") or []:
        kind = spec.get("kind")
        label = spec.get("label", "")
        source = spec.get("source", "")
        if summary is None:
            continue
        if kind == "computed":
            fn = COMPUTED.get(source)
            if fn is None:
                raise ValueError(f"{entry['phase']}: unknown computed analytics {source!r}")
            payload = fn(summary)
        elif kind == "value":
            payload = {"kvs": [{"label": label, "value": str(dotted(summary, source))}]}
        elif kind == "table":
            node = dotted(summary, source)
            payload = {"table": node if isinstance(node, dict) else {"columns": [], "rows": []}}
        else:
            raise ValueError(f"{entry['phase']}: unknown analytics kind {kind!r}")
        resolved.append({"label": label, "kind": kind, "source": source, **payload})
    return resolved


def active_lanes() -> list[dict[str, Any]]:
    truth = json.loads(CURRENT_TRUTH.read_text(encoding="utf-8"))
    return [
        {"lane_id": lane.get("lane_id"), "role": lane.get("role", "")}
        for lane in truth.get("active_lanes", [])
    ]


def build() -> dict[str, Any]:
    entries = parse_research_log_blocks(DECISION_LOG.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for entry in entries:
        summary = load_summary(entry)
        gates = entry.get("hardened_gate")
        if isinstance(gates, str):
            gates = [gates]
        rows.append(
            {
                "phase": entry["phase"],
                "date": str(entry.get("date", "")),
                "class": entry.get("class", ""),
                "outcome": entry["outcome"],  # authored taxonomy ONLY
                "badge": entry.get("badge", entry["outcome"]),
                "title": entry.get("title", entry["phase"]),
                "finding": entry.get("finding", ""),
                "facets": {
                    "why": entry.get("why", ""),
                    "worked": entry.get("worked", ""),
                    "didnt": entry.get("didnt", ""),
                    "lesson": entry.get("lesson", ""),
                    "our_error": entry.get("our_error"),
                    "our_error_note": entry.get("our_error_note", ""),
                    "changed": entry.get("changed", ""),
                },
                "hardened_gates": gates or [],
                "evidence_summary": entry.get("evidence_summary", ""),
                "evidence_doc": entry.get("evidence_doc", ""),
                "evidence_summary_found": summary is not None,
                "analytics": resolve_analytics(entry, summary),
            }
        )
    rows.sort(key=lambda row: (row["date"], row["phase"]), reverse=True)
    standing = dict(STANDING)
    standing["passed_gate"] = sum(1 for row in rows if row["outcome"] == "pass")
    lessons = [
        {"phase": row["phase"], "gate": gate}
        for row in sorted(rows, key=lambda r: (r["date"], r["phase"]))
        for gate in row["hardened_gates"]
    ]
    return {
        "report": "research_log",
        "source": {
            "decision_log": "money-flow/03_Decision_Log.md",
            "outcome_taxonomy": "authored in the Decision Log research_log blocks; never inferred from summary status strings",
        },
        "standing": standing,
        "verdict_banner": VERDICT_BANNER,
        "at_a_glance": AT_A_GLANCE,
        "untested_frontier": UNTESTED_FRONTIER,
        "boundaries": BOUNDARIES,
        "active_lanes": active_lanes(),
        "lessons_hardened_gates": lessons,
        "entry_count": len(rows),
        "entries": rows,
    }


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit non-zero if docs/research_log.json drifts from a fresh build")
    args = parser.parse_args(argv)
    fresh = render_json(build())
    if args.check:
        if not OUTPUT.exists():
            print("research_log_check_failed: docs/research_log.json missing")
            return 2
        if OUTPUT.read_text(encoding="utf-8") != fresh:
            print("research_log_check_failed: docs/research_log.json drifts from the Decision Log blocks — run scripts/build_research_log.py")
            return 1
        print("research_log_check_ok")
        return 0
    OUTPUT.write_text(fresh, encoding="utf-8")
    payload = json.loads(fresh)
    print(f"Wrote {OUTPUT} ({payload['entry_count']} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
