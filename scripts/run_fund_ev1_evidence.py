#!/usr/bin/env python3
"""Build FUND-EV1 delta-neutral funding-carry evidence.

FUND-EV1 is research/evidence only. It tests the structural, non-predictive
edge: harvest Hyperliquid perp funding while hedged delta-neutral on the SAME
venue (short HL perp + long HL spot, equal notional; BTC/ETH/SOL/HYPE — the
HL-spot-supported liquid names), judged on net funding AFTER ALL COSTS
staying positive out-of-sample (chronological 70/30 + anchored walk-forward
thirds), NOT bull-only, surviving leave-one-out, and keeping tail drawdown
inside documented limits (OOS <= 5%, stressed <= 8%). Parameters are chosen
on the train split only. The gate never forces a positive verdict.

Inputs (all public read-only provenance, no fetching here):
  - SV2.2 perp raw candle artifacts (local, via the committed SV2.2 summary);
  - the committed FUND-EV1 funding snapshot summary (daily funding-rate sums
    aggregated from public ``fundingHistory``);
  - FUND-EV1 HL spot raw candle artifacts (local, fetched once by
    scripts/fetch_fund_ev1_funding_snapshot.py).

No network I/O, no runtime mutation, no orders, no private/signed/testnet/
live endpoints, no production or live approval. Deterministic.

Run locally:
    .venv/bin/python scripts/run_fund_ev1_evidence.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


def _load_module(relative: str, alias: str):
    module_path = Path(__file__).resolve().parents[1] / relative
    spec = importlib.util.spec_from_file_location(alias, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fund = _load_module("services/strategy_validation/fund_ev1.py", "fund_ev1_runner_module")

from services.execution_quality.exec_ev1 import scenario_by_id  # noqa: E402

PHASE = "FUND-EV1"
REPORT_NAME = "fund_ev1_delta_neutral_carry_evidence"
DEFAULT_SV22_SUMMARY_INPUT = Path("docs/sv2_2_hyperliquid_research_refresh_summary.json")
DEFAULT_FUNDING_SNAPSHOT_INPUT = Path("docs/fund_ev1_funding_data_snapshot_summary.json")
DEFAULT_SPOT_RAW_DIR = Path("/tmp/money-flow-fund-ev1/raw_spot_candles")
DEFAULT_SUMMARY_OUTPUT = Path("docs/fund_ev1_delta_neutral_carry_evidence_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/fund_ev1_delta_neutral_carry_evidence.md")
GATE_SCENARIO_ID = "exec_ev1_conservative"
REFERENCE_SCENARIO_IDS = ("exec_ev1_base", "exec_ev1_conservative", "exec_ev1_stress")
CHRONOLOGICAL_TRAIN_RATIO = Decimal("0.70")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sv22-summary", type=Path, default=DEFAULT_SV22_SUMMARY_INPUT)
    parser.add_argument(
        "--funding-snapshot", type=Path, default=DEFAULT_FUNDING_SNAPSHOT_INPUT
    )
    parser.add_argument("--spot-raw-dir", type=Path, default=DEFAULT_SPOT_RAW_DIR)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--run-timestamp", default=None)
    return parser


def load_universe(
    sv22_summary_path: Path, funding_snapshot_path: Path, spot_raw_dir: Path
) -> tuple[dict[str, Any], dict[str, Any], Any]:
    sv22 = json.loads(sv22_summary_path.read_text(encoding="utf-8"))
    if sv22.get("phase") != "SV2.2":
        raise ValueError("fund_ev1_requires_sv2_2_summary_input")
    snapshot = json.loads(funding_snapshot_path.read_text(encoding="utf-8"))
    if snapshot.get("phase") != "FUND-EV1":
        raise ValueError("fund_ev1_requires_fund_ev1_funding_snapshot")
    perp_paths: dict[str, str] = {}
    for row in sv22.get("datasets", []):
        if (
            row.get("status") == "refreshed"
            and row.get("timeframe") == fund.CARRY_TIMEFRAME
            and row.get("symbol") in fund.CARRY_UNIVERSE
        ):
            perp_paths[row["symbol"]] = row["raw_path"]
    assets = []
    for symbol in fund.CARRY_UNIVERSE:
        perp_path = perp_paths.get(symbol)
        if not perp_path or not Path(perp_path).exists():
            raise FileNotFoundError(f"sv2_2_perp_candles_missing:{symbol}:{perp_path}")
        perp_payload = json.loads(Path(perp_path).read_text(encoding="utf-8"))
        perp = fund.dataset_from_sv22_payload(perp_payload, source_path=str(perp_path))
        spot_path = spot_raw_dir / f"hyperliquid_public_spot_{symbol.lower()}_1d_fund_ev1.json"
        if not spot_path.exists():
            raise FileNotFoundError(
                f"fund_ev1_spot_candles_missing:{symbol}:{spot_path} "
                "(run scripts/fetch_fund_ev1_funding_snapshot.py)"
            )
        spot_payload = json.loads(spot_path.read_text(encoding="utf-8"))
        spot = fund.dataset_from_sv22_payload(spot_payload, source_path=str(spot_path))
        funding_by_close, hours_by_close = fund.funding_maps_from_snapshot(
            snapshot["funding"][symbol]
        )
        assets.append(
            fund.CarryAsset(
                symbol=symbol,
                perp=perp,
                spot=spot,
                funding_by_close=funding_by_close,
                funding_hours_by_close=hours_by_close,
            )
        )
    return sv22, snapshot, fund.CarryUniverse(assets)


def _stats_str(stats: dict[str, Any]) -> dict[str, Any]:
    return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in stats.items()}


def _s(value: Any) -> Any:
    return str(value) if isinstance(value, Decimal) else value


def oos_trade_count(result: dict[str, Any], split: datetime) -> int:
    return sum(1 for t, *_ in result["trade_events"] if t > split)


def config_row(config: Any, result: dict[str, Any], split: datetime) -> dict[str, Any]:
    full = fund.curve_stats(result["equity_curve"])
    train = fund.curve_stats(result["equity_curve"], up_to=split)
    oos = fund.curve_stats(result["equity_curve"], after=split)
    return {
        "config_id": config.config_id,
        "strategy_type": config.strategy_type,
        "mode": config.mode,
        "rebalance_interval_days": config.rebalance_interval_days,
        "top_k": config.top_k,
        "funding_lookback_days": config.funding_lookback_days,
        "net_pnl": _s(result["net_pnl"]),
        "ending_equity": _s(result["ending_equity"]),
        "funding_collected_total": _s(result["funding_collected_total"]),
        "fees_total": _s(result["fees_total"]),
        "friction_quote_by_leg": {k: _s(v) for k, v in result["friction_quote_by_leg"].items()},
        "avg_friction_bps": _s(result["avg_friction_bps"]),
        "trade_count": result["trade_count"],
        "rebalance_count": result["rebalance_count"],
        "traded_notional_total": _s(result["traded_notional_total"]),
        "max_residual_delta_fraction": _s(result["max_residual_delta_fraction"]),
        "avg_residual_delta_fraction": _s(result["avg_residual_delta_fraction"]),
        "full_stats": _stats_str(full),
        "train_stats": _stats_str(train),
        "oos_stats": _stats_str(oos),
        "oos_net_pnl": _s(fund.window_net_pnl(result["equity_curve"], after=split)),
        "oos_trade_count": oos_trade_count(result, split),
        "per_symbol_net_pnl": {k: _s(v) for k, v in result["per_symbol_net_pnl"].items()},
        "funding_by_symbol": {k: _s(v) for k, v in result["funding_by_symbol"].items()},
    }


def verify_no_lookahead(universe: Any) -> dict[str, Any]:
    """Probe the causal trailing-funding signal on the real series
    (truncation + tampering), and confirm a leaky variant is caught."""
    results: dict[str, Any] = {}
    timeline = universe.timeline
    sample = [timeline[40], timeline[len(timeline) // 2], timeline[-30]]
    for symbol in universe.symbols:
        results[symbol] = fund.verify_funding_signal_point_in_time(
            universe.funding_times[symbol],
            universe.assets[symbol].funding_by_close,
            sample,
            fund.FUNDING_LOOKBACK_DAYS,
        )

    # A deliberately leaky "signal" (reads the LAST slot regardless of t)
    # must fail the tamper probe: tampering future slots changes its output.
    symbol = universe.symbols[0]
    times = universe.funding_times[symbol]
    fmap = universe.assets[symbol].funding_by_close
    t = sample[0]
    tampered = dict(fmap)
    for ts in times:
        if ts > t:
            tampered[ts] = fmap[ts] * Decimal("-7") + Decimal("1")

    def leaky(series: dict) -> Decimal:
        return series[times[-1]]

    leaky_caught = leaky(tampered) != leaky(fmap)
    return {
        "trailing_funding_signal_point_in_time_ok_by_symbol": results,
        "leaky_probe_would_be_caught": leaky_caught,
        "sampled_times": [str(t) for t in sample],
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_timestamp = args.run_timestamp or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    sv22, snapshot, universe = load_universe(
        args.sv22_summary, args.funding_snapshot, args.spot_raw_dir
    )
    gate_scenario = scenario_by_id(GATE_SCENARIO_ID)
    configs = fund.generate_funding_carry_configs()
    config_by_id = {c.config_id: c for c in configs}
    split = fund.timeline_split_time(universe, CHRONOLOGICAL_TRAIN_RATIO)
    timeline = universe.timeline
    t1 = timeline[len(timeline) // 3]
    t2 = timeline[(2 * len(timeline)) // 3]

    # --- full grid under every scenario (gate uses conservative) -----------
    per_scenario_rows: dict[str, list[dict[str, Any]]] = {}
    results_by_config: dict[str, dict[str, Any]] = {}
    for scenario_id in REFERENCE_SCENARIO_IDS:
        scenario = scenario_by_id(scenario_id)
        rows = []
        for config in configs:
            result = fund.simulate_funding_carry_portfolio(universe, config, scenario)
            rows.append(config_row(config, result, split))
            if scenario_id == GATE_SCENARIO_ID:
                results_by_config[config.config_id] = result
        per_scenario_rows[scenario_id] = rows

    # --- train-only choice + OOS headline -----------------------------------
    chosen_id = fund.select_best_config_id(results_by_config, train_up_to=split)
    chosen_config = config_by_id[chosen_id]
    chosen_result = results_by_config[chosen_id]
    oos_strategy_stats = fund.curve_stats(chosen_result["equity_curve"], after=split)
    train_strategy_stats = fund.curve_stats(chosen_result["equity_curve"], up_to=split)
    oos_net = fund.window_net_pnl(chosen_result["equity_curve"], after=split)

    # --- benchmarks ----------------------------------------------------------
    # 1) Gross-carry bound: the SAME chosen config with every cost zeroed.
    zero_scenario = fund.zero_cost_scenario(gate_scenario)
    gross_result = fund.simulate_funding_carry_portfolio(
        universe, chosen_config, zero_scenario
    )
    costs_total = fund._money(gross_result["net_pnl"] - chosen_result["net_pnl"])
    # 2) Always-on carry (no tilt): all four names, collect side, never flat.
    always_on_config = replace(
        chosen_config,
        config_id="fund_ev1_benchmark_always_on_top4",
        mode="collect_only",
        top_k=len(universe.symbols),
    )
    always_on_result = fund.simulate_funding_carry_portfolio(
        universe, always_on_config, gate_scenario, signal_provider=fund.always_on_provider
    )
    # 3) Cash: holding 10,000 USDC flat (0% return, 0 drawdown) — documented.

    # --- anchored walk-forward thirds (train-only choice per fold) ----------
    fold_b_choice = fund.select_best_config_id(results_by_config, train_up_to=t1)
    fold_b_net = fund.window_net_pnl(
        results_by_config[fold_b_choice]["equity_curve"], after=t1, up_to=t2
    )
    fold_c_choice = fund.select_best_config_id(results_by_config, train_up_to=t2)
    fold_c_net = fund.window_net_pnl(
        results_by_config[fold_c_choice]["equity_curve"], after=t2
    )
    walk_forward = {
        "fold_b": {
            "chosen_config": fold_b_choice,
            "window": [str(t1), str(t2)],
            "net_carry": _s(fold_b_net),
        },
        "fold_c": {
            "chosen_config": fold_c_choice,
            "window": [str(t2), "end"],
            "net_carry": _s(fold_c_net),
        },
    }

    # --- leave-one-out (drop each asset; same chosen config) ----------------
    leave_one_out: dict[str, Any] = {}
    loo_oos_net: dict[str, Decimal | None] = {}
    for drop in universe.symbols:
        sub_assets = [universe.assets[s] for s in universe.symbols if s != drop]
        sub_universe = fund.CarryUniverse(sub_assets)
        sub_split = fund.timeline_split_time(sub_universe, CHRONOLOGICAL_TRAIN_RATIO)
        sub_result = fund.simulate_funding_carry_portfolio(
            sub_universe, chosen_config, gate_scenario
        )
        sub_oos_net = fund.window_net_pnl(sub_result["equity_curve"], after=sub_split)
        sub_stats = fund.curve_stats(sub_result["equity_curve"], after=sub_split)
        loo_oos_net[drop] = sub_oos_net
        leave_one_out[drop] = {
            "oos_net_carry": _s(sub_oos_net),
            "oos_sharpe": _s(sub_stats["sharpe_annual"]),
            "oos_max_drawdown_pct": _s(sub_stats["max_drawdown_pct"]),
        }

    # --- tail stress (Must 2) ------------------------------------------------
    regimes = fund.classify_regimes(universe)
    regime_pnls = fund.pnl_by_regime(chosen_result["equity_curve"], regimes)
    stress_scenario = scenario_by_id("exec_ev1_stress")
    stressed_config = replace(
        chosen_config, config_id=f"{chosen_id}_stressed_leglag1", spot_leg_lag_days=1
    )
    stressed_result = fund.simulate_funding_carry_portfolio(
        universe, stressed_config, stress_scenario
    )
    stressed_stats = fund.curve_stats(stressed_result["equity_curve"])
    leglag_result = fund.simulate_funding_carry_portfolio(
        universe,
        replace(chosen_config, config_id=f"{chosen_id}_leglag1", spot_leg_lag_days=1),
        gate_scenario,
    )
    leglag_stats = fund.curve_stats(leglag_result["equity_curve"])
    worst_day_move = max(
        (
            abs(
                universe.assets[s].perp.candles[universe.perp_index[s][t]].close
                / universe.assets[s].perp.candles[universe.perp_index[s][t]].open
                - Decimal("1")
            )
            for s in universe.symbols
            for t in universe.timeline
        ),
    )
    tail_stress = {
        "worst_days_chosen_config": [
            [str(t), _s(v)] for t, v in chosen_result["worst_days"]
        ],
        "max_residual_delta_fraction": _s(chosen_result["max_residual_delta_fraction"]),
        "avg_residual_delta_fraction": _s(chosen_result["avg_residual_delta_fraction"]),
        "worst_single_candle_move_pct_in_window": _s(
            fund._money(worst_day_move * Decimal("100"))
        ),
        "modeled_gap_loss_at_max_residual_pct_of_equity": _s(
            fund._money(
                chosen_result["max_residual_delta_fraction"] * worst_day_move * Decimal("100")
            )
        ),
        "stressed_run": {
            "config": stressed_config.config_id,
            "scenario": stress_scenario.scenario_id,
            "spot_leg_lag_days": 1,
            "net_pnl": _s(stressed_result["net_pnl"]),
            "max_drawdown_pct": _s(stressed_stats["max_drawdown_pct"]),
            "sharpe_annual": _s(stressed_stats["sharpe_annual"]),
        },
        "leg_lag_only_run": {
            "scenario": GATE_SCENARIO_ID,
            "spot_leg_lag_days": 1,
            "net_pnl": _s(leglag_result["net_pnl"]),
            "net_pnl_delta_vs_chosen": _s(
                fund._money(leglag_result["net_pnl"] - chosen_result["net_pnl"])
            ),
            "max_drawdown_pct": _s(leglag_stats["max_drawdown_pct"]),
            "max_residual_delta_fraction": _s(
                leglag_result["max_residual_delta_fraction"]
            ),
            "modeled_gap_loss_at_leg_lag_residual_pct_of_equity": _s(
                fund._money(
                    leglag_result["max_residual_delta_fraction"]
                    * worst_day_move
                    * Decimal("100")
                )
            ),
            "note": (
                "the positive net delta is fill-price PATH LUCK in this window, not "
                "an edge: a one-day-legged book held up to the residual fraction "
                "above UNHEDGED for a day — against the worst candle in this window "
                "that is the modeled gap loss, the real steamroller"
            ),
        },
        "funding_inversion": {
            "funding_paid_on_negative_days_by_symbol": {
                k: _s(v)
                for k, v in chosen_result["funding_paid_on_negative_days_by_symbol"].items()
            },
            "negative_funding_exposure_days_by_symbol": chosen_result[
                "negative_funding_exposure_days_by_symbol"
            ],
            "note": (
                "collect_only goes flat after the trailing signal turns; the bleed above "
                "is the funding paid during signal lag while still positioned"
            ),
        },
        "liquidation_note": (
            "perp margin basis ~1x effective leverage (leg notional = half equity, "
            "unencumbered other half); liquidation mechanics not modeled — at 1x a "
            "short perp liquidates only near +100% adverse move, far outside the "
            "observed worst candle above"
        ),
    }

    # --- the gate -------------------------------------------------------------
    gate = fund.evaluate_funding_carry_gate(
        strategy_type=chosen_config.strategy_type,
        oos_strategy_stats=oos_strategy_stats,
        oos_net_pnl=oos_net,
        walk_forward_net_pnls=[fold_b_net, fold_c_net],
        regime_pnls=regime_pnls,
        leave_one_out_oos_net=loo_oos_net,
        stressed_max_drawdown_pct=stressed_stats["max_drawdown_pct"],
    )

    def bench_block(result: dict[str, Any]) -> dict[str, Any]:
        return {
            "config_id": result["config_id"],
            "scenario_id": result["scenario_id"],
            "net_pnl": _s(result["net_pnl"]),
            "funding_collected_total": _s(result["funding_collected_total"]),
            "fees_total": _s(result["fees_total"]),
            "trade_count": result["trade_count"],
            "full_stats": _stats_str(fund.curve_stats(result["equity_curve"])),
            "oos_stats": _stats_str(fund.curve_stats(result["equity_curve"], after=split)),
            "oos_net_pnl": _s(fund.window_net_pnl(result["equity_curve"], after=split)),
            "per_symbol_net_pnl": {k: _s(v) for k, v in result["per_symbol_net_pnl"].items()},
        }

    def gate_json(g: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in g.items():
            if isinstance(v, Decimal):
                out[k] = str(v)
            elif isinstance(v, dict):
                out[k] = {
                    ks: (
                        str(vs)
                        if isinstance(vs, Decimal)
                        else (
                            {k2: _s(v2) for k2, v2 in vs.items()}
                            if isinstance(vs, dict)
                            else vs
                        )
                    )
                    for ks, vs in v.items()
                }
            elif isinstance(v, list):
                out[k] = [_s(x) for x in v]
            else:
                out[k] = v
        return out

    summary = {
        "phase": PHASE,
        "report": REPORT_NAME,
        "run_timestamp_utc": run_timestamp,
        "status": "funding_carry_evidence_complete",
        "verdict": gate["status"],
        "account_size_usdc": str(fund.STARTING_EQUITY),
        "universe": {
            "carry_universe": list(fund.CARRY_UNIVERSE),
            "spot_pairs": dict(fund.SPOT_PAIR_BY_SYMBOL),
            "rationale": (
                "BTC/ETH/SOL via Unit spot + HYPE native spot — the liquid HL-spot-"
                "supported names; aligned window limited by the youngest spot listing "
                "(USOL 2025-05-10); UFART/UPUMP-tier listings excluded as thin"
            ),
            "timeframe": fund.CARRY_TIMEFRAME,
            "aligned_days": len(universe.timeline),
            "window": [str(universe.timeline[0]), str(universe.timeline[-1])],
        },
        "design": {
            "construction": (
                "single-venue Hyperliquid delta-neutral: SHORT perp + LONG spot equal "
                "notional per asset (collect side); flip_sides variant mirrors the book "
                "when trailing funding is negative (spot borrow ASSUMED, cost NOT "
                "modeled — upper bound)"
            ),
            "selection_tilt": (
                f"trailing {fund.FUNDING_LOOKBACK_DAYS}d mean funding (causal), rank by "
                "|funding|, hold up to top_k names on the collectable side"
            ),
            "sizing": (
                f"leg notional = {fund.LEG_NOTIONAL_FRACTION} * equity / top_k per "
                "selected asset; perp margin basis ~1x effective leverage"
            ),
            "funding_accrual": (
                "daily slot sum of hourly public funding rates, accrued on the perp "
                "leg at the daily close mark (documented approximation); positive "
                "funding pays the short perp"
            ),
            "costs": (
                "EXEC-EV1 depth-aware friction on EVERY fill of BOTH legs (perp at its "
                "tier; spot always at the widest mid-alt tier), scenario fee_bps on "
                "both legs, rebalance band, forced final close"
            ),
            "config_grid_size": len(configs),
            "modes": list(fund.CARRY_MODES),
            "rebalance_cadences_days": list(fund.REBALANCE_CADENCES_DAYS),
            "top_k_choices": list(fund.TOP_K_CHOICES),
        },
        "no_lookahead_verification": verify_no_lookahead(universe),
        "chronological_split": {
            "train_ratio": str(CHRONOLOGICAL_TRAIN_RATIO),
            "split_time": str(split),
        },
        "train_only_choice": {
            "criterion": "best train-window Sharpe under conservative friction",
            "chosen_config": chosen_id,
        },
        "headline": {
            "gate_scenario": GATE_SCENARIO_ID,
            "strategy_oos": _stats_str(oos_strategy_stats),
            "strategy_train": _stats_str(train_strategy_stats),
            "oos_net_carry": _s(oos_net),
            "full_net_pnl": _s(chosen_result["net_pnl"]),
            "full_funding_collected": _s(chosen_result["funding_collected_total"]),
            "gross_carry_zero_cost_net": _s(gross_result["net_pnl"]),
            "costs_total_vs_zero_cost": _s(costs_total),
            "cost_share_of_gross_pct": _s(
                fund._money(
                    costs_total / gross_result["net_pnl"] * Decimal("100")
                )
                if gross_result["net_pnl"] > 0
                else None
            ),
        },
        "benchmarks": {
            "gross_funding_zero_cost_same_positions": bench_block(gross_result),
            "always_on_carry_top4": bench_block(always_on_result),
            "cash": {
                "config_id": "hold_10000_usdc",
                "net_pnl": "0",
                "max_drawdown_pct": "0",
                "note": "the do-nothing benchmark: carry must beat cash after costs to matter",
            },
        },
        "per_config_results": per_scenario_rows,
        "walk_forward": walk_forward,
        "leave_one_out": leave_one_out,
        "regimes": {
            "classification": (
                f"BTC perp trailing {fund.REGIME_TRAILING_DAYS}d return, point-in-time; "
                f"bear < -{fund.REGIME_BAND}, bull > +{fund.REGIME_BAND}"
            ),
            "day_counts": {
                label: sum(1 for r in regimes.values() if r == label)
                for label in ("bull", "neutral", "bear")
            },
            "chosen_config_pnl_by_regime": {
                label: {"days": row["days"], "net_pnl": _s(row["net_pnl"])}
                for label, row in regime_pnls.items()
            },
        },
        "tail_stress": tail_stress,
        "funding_carry_gate": gate_json(gate),
        "routing": {
            "strategy_type": fund.STRATEGY_TYPE_FUNDING_CARRY,
            "gate_id": fund.FUNDING_CARRY_GATE_ID,
            "never_judged_by": [
                "per_symbol_breadth_friction_gate",
                "selection_random_benchmark_gate",
                "tsmom_buy_hold_risk_adjusted_gate",
            ],
        },
        "data_provenance": {
            "perp_candles": {
                "source": "hyperliquid_public_mainnet_candles_sv2_2_refresh",
                "summary": str(args.sv22_summary),
            },
            "funding": {
                "source": "hyperliquid_public_mainnet_fundingHistory",
                "snapshot_summary": str(args.funding_snapshot),
                "fetched_at_utc": snapshot.get("fetched_at_utc"),
                "daily_sums_committed": True,
            },
            "spot_candles": {
                "source": "hyperliquid_public_mainnet_candleSnapshot_spot",
                "raw_dir": str(args.spot_raw_dir),
                "sha256": {
                    s: snapshot["spot_candles"][s]["raw_sha256"]
                    for s in fund.CARRY_UNIVERSE
                },
            },
            "access": "public_read_only_no_keys_no_private_no_signed_no_orders",
        },
        "boundaries": {k: v for k, v in fund.boundary_flags().items()},
    }

    args.summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_report(args.report_output, summary)
    print(f"Wrote {args.summary_output}")
    print(f"Wrote {args.report_output}")
    print(f"verdict: {gate['status']}")
    print(f"reasons: {gate['reason_codes']}")
    return 0


def write_report(path: Path, summary: dict[str, Any]) -> None:
    h = summary["headline"]
    gate = summary["funding_carry_gate"]
    tail = summary["tail_stress"]
    gross = summary["benchmarks"]["gross_funding_zero_cost_same_positions"]
    always = summary["benchmarks"]["always_on_carry_top4"]
    wf = summary["walk_forward"]
    lines = [
        "# FUND-EV1 — Delta-Neutral Funding Carry Evidence",
        "",
        "Research/evidence only. No runtime, strategy-rule, order, testnet, live,",
        "or production-approval change follows from this report. Funding is modeled",
        "from public hourly history (daily-close accrual approximation); depth is",
        "modeled (EXEC-EV1), not real; flip-side rows assume unmodeled spot borrow.",
        "Account basis: 10,000 USDC.",
        "",
        f"## Verdict: `{summary['verdict']}`",
        "",
        f"Gate reasons: `{gate['reason_codes']}`",
        f"Qualifiers: `{gate['qualifiers']}`",
        "",
        "## The honest question",
        "",
        "Short the Hyperliquid perp, hold the same notional in HL spot, collect the",
        "funding stream with ~zero price exposure. Does the net stream survive BOTH",
        "legs' costs out-of-sample — and the tail (crash days, funding inversions,",
        "legged fills) — or is it pennies in front of a steamroller?",
        "",
        "## Headline (chronological 70/30 OOS, conservative friction)",
        "",
        f"- Train-only choice: `{summary['train_only_choice']['chosen_config']}`",
        f"- OOS net carry (after all costs): **{h['oos_net_carry']}** USDC",
        f"- OOS Sharpe {h['strategy_oos'].get('sharpe_annual')}, OOS max drawdown {h['strategy_oos'].get('max_drawdown_pct')}%, OOS days {h['strategy_oos'].get('days')}",
        f"- Full-window net {h['full_net_pnl']} vs gross zero-cost {h['gross_carry_zero_cost_net']} — costs ate {h['costs_total_vs_zero_cost']} ({h['cost_share_of_gross_pct']}% of gross)",
        f"- Funding collected (full window): {h['full_funding_collected']}",
        "",
        "## Benchmarks",
        "",
        "| Benchmark | Net PnL | OOS net | Full Sharpe | Max DD % |",
        "| --- | --- | --- | --- | --- |",
        (
            f"| Gross carry (zero cost, same positions) | {gross['net_pnl']} | {gross['oos_net_pnl']} "
            f"| {gross['full_stats'].get('sharpe_annual')} | {gross['full_stats'].get('max_drawdown_pct')} |"
        ),
        (
            f"| Always-on carry, all 4 names | {always['net_pnl']} | {always['oos_net_pnl']} "
            f"| {always['full_stats'].get('sharpe_annual')} | {always['full_stats'].get('max_drawdown_pct')} |"
        ),
        "| Cash (hold 10,000 USDC) | 0 | 0 | — | 0 |",
        "",
        "## Walk-forward (anchored thirds, train-only choice per fold)",
        "",
        f"- Fold B (`{wf['fold_b']['chosen_config']}`): net carry {wf['fold_b']['net_carry']}",
        f"- Fold C (`{wf['fold_c']['chosen_config']}`): net carry {wf['fold_c']['net_carry']}",
        "",
        "## Regimes (not bull-only check)",
        "",
        f"- {summary['regimes']['classification']}",
    ]
    for label, row in summary["regimes"]["chosen_config_pnl_by_regime"].items():
        lines.append(f"- {label}: {row['days']} days, net {row['net_pnl']}")
    lines += [
        f"- Gate non-bull net carry: {gate['non_bull_net_pnl']}",
        "",
        "## Leave-one-out (drop each asset)",
        "",
        "| Dropped | OOS net carry | OOS Sharpe | OOS max DD % |",
        "| --- | --- | --- | --- |",
    ]
    for symbol, row in summary["leave_one_out"].items():
        lines.append(
            f"| {symbol} | {row['oos_net_carry']} | {row['oos_sharpe']} | {row['oos_max_drawdown_pct']} |"
        )
    lines += [
        "",
        "## Tail stress (the gate that matters most)",
        "",
        f"- Worst days (chosen config): {tail['worst_days_chosen_config']}",
        f"- Residual delta: max {tail['max_residual_delta_fraction']}, avg {tail['avg_residual_delta_fraction']} of equity",
        f"- Worst single candle move in window: {tail['worst_single_candle_move_pct_in_window']}%",
        f"- Modeled gap loss at max residual: {tail['modeled_gap_loss_at_max_residual_pct_of_equity']}% of equity",
        (
            f"- Stressed run (stress friction + spot leg lag 1): net {tail['stressed_run']['net_pnl']}, "
            f"max DD {tail['stressed_run']['max_drawdown_pct']}% (limit {gate['max_stressed_drawdown_pct_limit']}%)"
        ),
        (
            f"- Leg-lag-only run (conservative): net delta {tail['leg_lag_only_run']['net_pnl_delta_vs_chosen']} "
            f"(fill-price path luck, not edge), max DD {tail['leg_lag_only_run']['max_drawdown_pct']}%, "
            f"**max one-leg exposure {tail['leg_lag_only_run']['max_residual_delta_fraction']} of equity** -> "
            f"modeled gap loss {tail['leg_lag_only_run']['modeled_gap_loss_at_leg_lag_residual_pct_of_equity']}% "
            "of equity against the window's worst candle — the real steamroller"
        ),
        f"- Funding paid on negative days: {tail['funding_inversion']['funding_paid_on_negative_days_by_symbol']}",
        f"- {tail['liquidation_note']}",
        "",
        "## Universe + window",
        "",
        f"- {', '.join(summary['universe']['carry_universe'])} (spot: {summary['universe']['spot_pairs']})",
        f"- Window: {summary['universe']['window'][0]} -> {summary['universe']['window'][1]} ({summary['universe']['aligned_days']} aligned days)",
        f"- {summary['universe']['rationale']}",
        "",
        "## Boundaries",
        "",
        "Research/evidence only; no order, testnet, live, production, or approval",
        "surface. Public read-only data; modeled depth; daily funding accrual",
        "approximation; spot borrow unmodeled (flip rows are upper bounds);",
        "liquidation mechanics unmodeled. The verdict above is the gate's output",
        "and was not forced positive.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
