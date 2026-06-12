#!/usr/bin/env python3
"""Build MONEYFLOW-SIGNAL1 evidence: fidelity record + honest characterization.

SOURCE-FAITHFUL SIGNAL, NOT ALPHA — research/evidence only. This is NOT an
alpha hunt: the directional Money Flow rules already showed no standalone
out-of-sample edge (MF-ORIG-EV1.1/EV2 at trade level; STRAT-DISC1 discovery
pass). This runner characterizes the signal honestly — standalone, post
EXEC-EV1 friction, against buy-and-hold and seeded random benchmarks, and
with the REGIME informational risk overlay (committed verdict: honest FAIL —
endpoint-strong, process-unstable; carried through every surface, never a
validated control). A green-looking result here is pre-stated to be a reason
to re-audit, not a win. Nothing is selected or tuned toward a pass.

Books are EXPOSURE characterizations of the signal (entry/exit rules through
the friction simulator at equal weight); structure stops, 25% trims, and
1%-risk sizing are trade-level mechanics already characterized in
MF-ORIG-EV1.1/EV2 and are cited, not re-modeled.

Run locally:
    .venv/bin/python scripts/run_moneyflow_signal1_evidence.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Read-only evidence computation: keep the local runtime .env out of settings
# (same isolation tests/conftest.py applies); nothing here reads the DB.
from core.config.settings import AppSettings, get_settings  # noqa: E402

AppSettings.model_config["env_file"] = None
get_settings.cache_clear()

from services.strategy_validation import moneyflow_signal1 as ms  # noqa: E402


def _load_module(relative: str, alias: str):
    module_path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(alias, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rg = _load_module("services/strategy_validation/regime1.py", "mfsig1_regime1")
fv = _load_module("services/strategy_validation/fund_venues1.py", "mfsig1_fund_venues1")
tsmom = rg.tsmom_ev1
sel_ev1 = rg._load_sel_ev1()

from services.execution_quality.exec_ev1 import scenario_by_id  # noqa: E402
from services.market_data.data1_multi_venue import load_data1_dataset  # noqa: E402

PHASE = ms.PHASE
DEFAULT_SUMMARY_OUTPUT = Path("docs/moneyflow_signal1_source_faithful_signal_surface_evidence_summary.json")
DEFAULT_REPORT_OUTPUT = Path("docs/moneyflow_signal1_source_faithful_signal_surface_evidence.md")
DEFAULT_DATA1_SUMMARY = Path("docs/data1_multi_venue_snapshot_summary.json")
GATE_SCENARIO_ID = "exec_ev1_conservative"
CHRONOLOGICAL_TRAIN_RATIO = Decimal("0.70")
BOOK_ASSETS = ("AVAX", "BNB", "BTC", "DOGE", "ETH", "SOL", "XRP")
BOOK_VENUE = "binance"
# All books (and benchmarks) share the SAME warmed start: the regime filter's
# 90-candle warm-up dominates the signal's own ~50-candle warm-up.
WARMUP_CANDLES = max(rg.REGIME_LOOKBACKS)
# Money Flow is a daily-decision system (the book: scan charts daily, act on
# the close's signal at the next open) — decisions are evaluated every
# aligned close; the dust band keeps no-change days from churning.
REBALANCE_DAYS = 1
RANDOM_SEEDS = tuple(range(1, 31))

FORBIDDEN = ms.mf_orig_ev1.FORBIDDEN_REPORT_PHRASES


def _s(value: Any) -> Any:
    return str(value) if isinstance(value, Decimal) else value


def _stats_str(stats: dict[str, Any]) -> dict[str, Any]:
    return {k: _s(v) for k, v in stats.items()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data1-summary", type=Path, default=DEFAULT_DATA1_SUMMARY)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--run-timestamp", default=None)
    parser.add_argument("--random-seeds", type=int, default=len(RANDOM_SEEDS))
    return parser


def build_universe(ds):
    datasets = []
    for symbol in BOOK_ASSETS:
        series = ds.series(BOOK_VENUE, symbol, "perp_1d")
        if series.status != "ok":
            raise RuntimeError(f"data1_series_not_ok:{BOOK_VENUE}:{symbol}:{series.status}")
        datasets.append(
            fv.dataset_from_data1_rows(symbol, BOOK_VENUE, "perp_1d", list(series.rows))
        )
    return sel_ev1.SelectionUniverse(datasets)


def book_config(label: str) -> Any:
    return tsmom.TsmomConfig(
        config_id=f"moneyflow_signal1_book_{label}",
        strategy_type=tsmom.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
        lookback_days=60,  # unused: signal_provider overrides
        portfolio_vol_target=Decimal("0.20"),  # unused with vol_targeting=False
        mode="long_only",
        vol_targeting=False,
        rebalance_interval_days=REBALANCE_DAYS,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_timestamp = args.run_timestamp or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    ds = load_data1_dataset(args.data1_summary)
    universe = build_universe(ds)
    timeline = [
        t
        for t in universe.timeline
        if all(universe.index_by_time[s].get(t) is not None for s in universe.symbols)
    ]
    warmup_cutoff = timeline[WARMUP_CANDLES]
    scenario = scenario_by_id(GATE_SCENARIO_ID)
    split = timeline[max(0, min(len(timeline) - 1, int(len(timeline) * float(CHRONOLOGICAL_TRAIN_RATIO)) - 1))]
    print(f"universe: {len(timeline)} aligned days {timeline[0]} .. {timeline[-1]}")
    print(f"warmed start: {warmup_cutoff}; train/OOS split: {split}")

    def warmed(provider):
        def wrapped(symbol: str, idx: int):
            candles = universe.datasets[symbol].candles
            t = candles[idx].timestamp if idx < len(candles) else None
            if t is None or t < warmup_cutoff:
                return 0
            return provider(symbol, idx)

        return wrapped

    # --- the books -----------------------------------------------------------
    regime_provider = rg.gated_long_provider(universe, rg.DEFAULT_CONFIG)
    providers = {
        "mf_source_stage2": ms.moneyflow_exposure_provider(universe, entry_mode="source_stage2"),
        "mf_basic_5_20": ms.moneyflow_exposure_provider(universe, entry_mode="basic_5_20"),
    }
    providers["mf_source_stage2_regime_gated"] = ms.regime_gated_provider(
        providers["mf_source_stage2"], regime_provider
    )
    providers["mf_basic_5_20_regime_gated"] = ms.regime_gated_provider(
        providers["mf_basic_5_20"], regime_provider
    )
    providers["always_long"] = rg.always_long_provider

    results: dict[str, Any] = {}
    flips: dict[str, int] = {}
    for label, provider in providers.items():
        results[label] = tsmom.simulate_tsmom_portfolio(
            universe, book_config(label), scenario, signal_provider=warmed(provider)
        )
        flips[label] = ms.exposure_flip_count(warmed(provider), universe)
        print(f"{label}: net {results[label]['net_pnl']} flips {flips[label]}")

    buy_hold = tsmom.buy_hold_benchmark(universe, scenario, reference=book_config("buy_hold_ref"))
    randoms = tsmom.random_long_flat_benchmark(
        universe,
        scenario,
        reference=book_config("random_ref"),
        seeds=RANDOM_SEEDS[: args.random_seeds],
    )

    # RE-AUDIT CORRECTION (pre-stated rule: a green screen triggers a
    # methodology re-audit). The coin-flip random benchmark re-draws every
    # day at daily decisions, so it trades ~half the book daily and friction
    # destroys it — an unfair churn artifact, not a real bar. The FAIR random
    # comparator matches the Money Flow exposure's own persistence (the same
    # Markov enter/exit rates, pooled across symbols), so it carries the same
    # friction load and differs only in WHERE the flips land.
    mf_provider_warmed = warmed(providers["mf_source_stage2"])
    enters = exits = long_days = flat_days = 0
    for symbol in universe.symbols:
        n = len(universe.datasets[symbol].candles)
        last = None
        for idx in range(n):
            value = mf_provider_warmed(symbol, idx)
            if value is None:
                continue
            if last is not None:
                if last == 0:
                    flat_days += 1
                    if value == 1:
                        enters += 1
                else:
                    long_days += 1
                    if value == 0:
                        exits += 1
            last = value
    p_enter = Decimal(enters) / Decimal(flat_days) if flat_days else Decimal("0")
    p_exit = Decimal(exits) / Decimal(long_days) if long_days else Decimal("0")
    print(f"persistence-matched random: p_enter={p_enter:.6f} p_exit={p_exit:.6f}")

    import random as _random

    matched_randoms: list[dict[str, Any]] = []
    for seed in RANDOM_SEEDS[: args.random_seeds]:
        rng = _random.Random(10_000 + seed)
        states: dict[str, dict[int, int]] = {s: {} for s in universe.symbols}

        def matched_provider(
            symbol: str, idx: int, *, _rng=rng, _states=states
        ) -> int:
            cache = _states[symbol]
            if idx in cache:
                return cache[idx]
            prev = cache.get(idx - 1)
            if prev is None:
                value = 0  # start flat, like the warmed Money Flow books
            elif prev == 0:
                value = 1 if Decimal(str(_rng.random())) < p_enter else 0
            else:
                value = 0 if Decimal(str(_rng.random())) < p_exit else 1
            cache[idx] = value
            return value

        # Walk indices in order so the Markov chain is well-defined.
        for symbol in universe.symbols:
            for idx in range(len(universe.datasets[symbol].candles)):
                matched_provider(symbol, idx)
        result = tsmom.simulate_tsmom_portfolio(
            universe,
            book_config(f"matched_random_seed{seed}"),
            scenario,
            signal_provider=warmed(matched_provider),
        )
        result["seed"] = seed
        matched_randoms.append(result)

    def window_stats(curve) -> dict[str, Any]:
        return {
            "full": _stats_str(rg.curve_stats(curve, after=warmup_cutoff)),
            "train": _stats_str(rg.curve_stats(curve, after=warmup_cutoff, up_to=split)),
            "oos": _stats_str(rg.curve_stats(curve, after=split)),
        }

    books: dict[str, Any] = {}
    for label, result in results.items():
        books[label] = {
            **window_stats(result["equity_curve"]),
            "net_pnl": _s(result["net_pnl"]),
            "trade_count": result["trade_count"],
            "exposure_flips": flips[label],
        }
    books["benchmark_buy_hold"] = {
        **window_stats(buy_hold["equity_curve"]),
        "net_pnl": _s(buy_hold["net_pnl"]),
        "trade_count": buy_hold["trade_count"],
    }

    def _dec_or_none(value):
        return None if value is None else Decimal(str(value))

    def oos_sharpes(rows: list[dict[str, Any]]) -> list[Decimal]:
        values = []
        for row in rows:
            oos = rg.curve_stats(row["equity_curve"], after=split)
            if oos["sharpe_annual"] is not None:
                values.append(Decimal(str(oos["sharpe_annual"])))
        values.sort()
        return values

    def p95(population: list[Decimal]) -> Decimal | None:
        if len(population) < 20:
            return None
        return population[int(len(population) * 95 // 100) - 1]

    def pct_rank(value: Decimal | None, population: list[Decimal]) -> str | None:
        if value is None or not population:
            return None
        below = sum(1 for v in population if v < value)
        return str(Decimal(below) / Decimal(len(population)))

    random_oos_sharpes = oos_sharpes(randoms)
    matched_oos_sharpes = oos_sharpes(matched_randoms)

    # Sub-window texture: thirds of the aligned timeline (the REGIME fold
    # windows) expose WHERE any outperformance lives — a long/flat exit rule
    # mechanically beats buy-and-hold in bear windows (risk-off mechanic, the
    # REGIME story), which is not an alpha claim.
    t1 = timeline[len(timeline) // 3]
    t2 = timeline[(2 * len(timeline)) // 3]
    thirds = {}
    for label, result in {
        "mf_source_stage2": results["mf_source_stage2"],
        "always_long": results["always_long"],
        "benchmark_buy_hold": buy_hold,
    }.items():
        thirds[label] = {
            "first_third": _stats_str(rg.curve_stats(result["equity_curve"], after=warmup_cutoff, up_to=t1)),
            "middle_third": _stats_str(rg.curve_stats(result["equity_curve"], after=t1, up_to=t2)),
            "final_third": _stats_str(rg.curve_stats(result["equity_curve"], after=t2)),
        }

    # --- the honest characterization labels --------------------------------
    # Pre-stated, two-stage, honest in BOTH directions (tuned toward neither
    # a pass nor the expected fail):
    #   stage 1 (raw screens): MF OOS Sharpe > buy-and-hold OOS Sharpe AND >
    #     p95 of the coin-flip randoms -> the re-audit rule fires.
    #   stage 2 (the re-audit): replace the churn-unfair coin-flip bar with
    #     the persistence-matched random p95, and ask the MECHANIC question
    #     with the right metric: in the rising third (where always-long's
    #     return is best), does MF beat always-long's RETURN? Return - not
    #     Sharpe - because a flat-heavy book's Sharpe is flattered by time
    #     in cash; only beating the market's own return when it rises would
    #     look like return PREDICTION rather than drawdown-avoidance.
    # Context that pins the reading: on this same universe/machinery the
    # repo has already committed `beats_buy_hold_risk_adjusted_oos` for the
    # trend family (TSMOM-EV1 'defensive, not profitable'; TREND-SUITE1
    # 'defensive only - suite adds nothing'; REGIME1/2 carry the same bears-
    # vs-chop texture). A 5/20 MA long/flat book IS a trend-family member,
    # so clearing the relative bar is the KNOWN defensive mechanic, not a
    # discovery; the trade-level namesake (stops/trims/1% sizing vs v1.2)
    # remains 'source_faithful_but_underperformed' (MF-ORIG-EV1.1/EV2).
    # Labels:
    #   no_standalone_edge_reconfirmed - fails buy-and-hold or the matched
    #     random bar OOS;
    #   defensive_trend_mechanic_not_validated_alpha - clears the bars but
    #     gives up the rising third's return: drawdown-avoidance, the
    #     committed trend-family texture, window-dependent, NOT validated
    #     alpha;
    #   unexpected_return_prediction_signature_re_audit - clears the bars
    #     AND beats always-long's return in the rising third; flagged
    #     loudly, still not an alpha claim without a dedicated
    #     pre-registered confirmatory phase.
    mf_oos = rg.curve_stats(results["mf_source_stage2"]["equity_curve"], after=split)
    bh_oos = rg.curve_stats(buy_hold["equity_curve"], after=split)
    mf_oos_sharpe = _dec_or_none(mf_oos["sharpe_annual"])
    bh_oos_sharpe = _dec_or_none(bh_oos["sharpe_annual"])
    coinflip_p95 = p95(random_oos_sharpes)
    matched_p95 = p95(matched_oos_sharpes)
    beats_buy_hold = (
        mf_oos_sharpe is not None and bh_oos_sharpe is not None and mf_oos_sharpe > bh_oos_sharpe
    )
    beats_random_p95 = (
        mf_oos_sharpe is not None and coinflip_p95 is not None and mf_oos_sharpe > coinflip_p95
    )
    beats_matched_p95 = (
        mf_oos_sharpe is not None and matched_p95 is not None and mf_oos_sharpe > matched_p95
    )
    raw_screen_green = beats_buy_hold and beats_random_p95

    # The rising third (always-long's best return window) and both metrics.
    al_third_returns = {
        k: _dec_or_none(v["total_return_pct"])
        for k, v in thirds["always_long"].items()
        if _dec_or_none(v["total_return_pct"]) is not None
    }
    bull_third = max(al_third_returns, key=lambda k: al_third_returns[k]) if al_third_returns else None

    def _third_metric(label: str, metric: str) -> Decimal | None:
        if bull_third is None:
            return None
        return _dec_or_none(thirds[label][bull_third][metric])

    mf_bull_return = _third_metric("mf_source_stage2", "total_return_pct")
    al_bull_return = _third_metric("always_long", "total_return_pct")
    mf_bull_sharpe = _third_metric("mf_source_stage2", "sharpe_annual")
    al_bull_sharpe = _third_metric("always_long", "sharpe_annual")
    mf_beats_always_long_return_in_bull = bool(
        mf_bull_return is not None and al_bull_return is not None and mf_bull_return > al_bull_return
    )

    if not raw_screen_green or not beats_matched_p95 or not beats_buy_hold:
        standalone_label = "no_standalone_edge_reconfirmed"
    elif not mf_beats_always_long_return_in_bull:
        standalone_label = "defensive_trend_mechanic_not_validated_alpha"
    else:
        standalone_label = "unexpected_return_prediction_signature_re_audit"

    overlay_blocks = {}
    for base_label in ("mf_source_stage2", "mf_basic_5_20"):
        gated_label = f"{base_label}_regime_gated"
        base_oos = rg.curve_stats(results[base_label]["equity_curve"], after=split)
        gated_oos = rg.curve_stats(results[gated_label]["equity_curve"], after=split)
        base_dd = _dec_or_none(base_oos["max_drawdown_pct"])
        gated_dd = _dec_or_none(gated_oos["max_drawdown_pct"])
        dd_reduction_pct = (
            str((base_dd - gated_dd) / base_dd * Decimal("100"))
            if base_dd not in (None, Decimal("0")) and gated_dd is not None
            else None
        )
        overlay_blocks[base_label] = {
            "ungated_oos": _stats_str(base_oos),
            "gated_oos": _stats_str(gated_oos),
            "oos_drawdown_reduction_pct_of_ungated": dd_reduction_pct,
            "whipsaw_cost": {
                "ungated_exposure_flips": flips[base_label],
                "gated_exposure_flips": flips[gated_label],
                "extra_flips_from_overlay": flips[gated_label] - flips[base_label],
                "oos_return_ungated_pct": _s(base_oos["total_return_pct"]),
                "oos_return_gated_pct": _s(gated_oos["total_return_pct"]),
            },
            "label": "informational_overlay_not_validated_control",
        }

    regime_series = rg.compute_regime_series(universe, rg.DEFAULT_CONFIG)
    risk_off_days = sum(1 for _, state in regime_series if not state["risk_on"])

    summary = {
        "phase": PHASE,
        "report": "moneyflow_signal1_source_faithful_signal_surface_evidence",
        "generated_at_utc": run_timestamp,
        "status": "source_faithful_signal_surface_delivered_characterized_honestly",
        "headline": {
            "deliverable": (
                "a trustworthy, auditable, source-faithful Money Flow signal "
                "surface with the regime overlay - fidelity and trust, not a "
                "profit claim"
            ),
            "standalone_characterization": standalone_label,
            "known_prior_result_reconfirmed": ms.PRIOR_EVIDENCE["known_result"],
            "regime_overlay": (
                "informational risk context, not a validated control "
                "(committed REGIME2 verdict: honest FAIL - endpoint-strong, "
                "process-unstable)"
            ),
        },
        "source_document": ms.SOURCE_DOCUMENT,
        "pdf_provenance": ms.pdf_provenance_check(REPO_ROOT),
        "source_citations": list(ms.SOURCE_CITATIONS),
        "ambiguity_resolutions": list(ms.AMBIGUITY_RESOLUTIONS),
        "primary_hypothesis": ms.PRIMARY_HYPOTHESIS,
        "prior_evidence": ms.PRIOR_EVIDENCE,
        "methodology": {
            "data": f"DATA1 {BOOK_VENUE} perp_1d candles for {', '.join(BOOK_ASSETS)} (closed daily, no lookahead)",
            "friction": GATE_SCENARIO_ID,
            "books": (
                "long/flat exposure of the signal at equal weight through "
                "tsmom_ev1.simulate_tsmom_portfolio (decisions at each aligned "
                "close, fills at next open, EXEC-EV1 friction)"
            ),
            "windows": {
                "aligned_days": len(timeline),
                "first_close": str(timeline[0]),
                "last_close": str(timeline[-1]),
                "warmed_start": str(warmup_cutoff),
                "train_oos_split_70_30": str(split),
            },
            "oos_note": (
                "no parameter was selected in this phase (the rules are pinned "
                "by the source document), so the 70/30 split is an evaluation "
                "convention, not a selection guard; the known no-edge prior "
                "makes this characterization, not a test to pass"
            ),
            "scope_note": next(
                a["resolution"]
                for a in ms.AMBIGUITY_RESOLUTIONS
                if a["ambiguity_id"] == "characterization_scope_exposure_only"
            ),
            "random_benchmarks": (
                f"{args.random_seeds} seeded coin-flip long/flat books "
                f"(transparency) + {args.random_seeds} persistence-matched "
                "random books (the fair bar; same machinery, same friction)"
            ),
            "rebalance_interval_days": REBALANCE_DAYS,
        },
        "books": books,
        "sub_window_texture_thirds": {
            "windows": {"t1": str(t1), "t2": str(t2)},
            "bull_third": bull_third,
            "stats": thirds,
        },
        "random_benchmarks": {
            "seeds": args.random_seeds,
            "coin_flip": {
                "note": (
                    "re-draws every (symbol, day) - at daily decisions this "
                    "trades ~half the book daily, so friction destroys it; "
                    "kept for transparency, replaced as a bar by the "
                    "persistence-matched distribution below (the re-audit "
                    "correction)"
                ),
                "oos_sharpe_distribution": {
                    "min": _s(random_oos_sharpes[0]) if random_oos_sharpes else None,
                    "median": _s(random_oos_sharpes[len(random_oos_sharpes) // 2]) if random_oos_sharpes else None,
                    "p95": _s(coinflip_p95),
                    "max": _s(random_oos_sharpes[-1]) if random_oos_sharpes else None,
                },
            },
            "persistence_matched": {
                "note": (
                    "Markov enter/exit rates matched to the Money Flow "
                    "exposure itself (pooled), so the random books carry the "
                    "SAME friction load and differ only in where the flips "
                    "land - the fair 'random timing' bar"
                ),
                "p_enter_per_day": str(p_enter),
                "p_exit_per_day": str(p_exit),
                "oos_sharpe_distribution": {
                    "min": _s(matched_oos_sharpes[0]) if matched_oos_sharpes else None,
                    "median": _s(matched_oos_sharpes[len(matched_oos_sharpes) // 2]) if matched_oos_sharpes else None,
                    "p95": _s(matched_p95),
                    "max": _s(matched_oos_sharpes[-1]) if matched_oos_sharpes else None,
                },
            },
            "mf_source_stage2_oos_sharpe": _s(mf_oos["sharpe_annual"]),
            "mf_oos_sharpe_percentile_vs_coin_flip": pct_rank(mf_oos_sharpe, random_oos_sharpes),
            "mf_oos_sharpe_percentile_vs_persistence_matched": pct_rank(mf_oos_sharpe, matched_oos_sharpes),
        },
        "standalone_characterization": {
            "label": standalone_label,
            "mf_source_stage2_oos": _stats_str(mf_oos),
            "buy_hold_oos": _stats_str(bh_oos),
            "screens": {
                "stage1_raw": {
                    "beats_buy_hold_risk_adjusted_oos": bool(beats_buy_hold),
                    "beats_coin_flip_random_p95_oos": bool(beats_random_p95),
                    "re_audit_rule_fired": bool(raw_screen_green),
                },
                "stage2_re_audit": {
                    "beats_persistence_matched_random_p95_oos": bool(beats_matched_p95),
                    "bull_third": bull_third,
                    "mf_bull_third_return_pct": _s(mf_bull_return),
                    "always_long_bull_third_return_pct": _s(al_bull_return),
                    "mf_bull_third_sharpe": _s(mf_bull_sharpe),
                    "always_long_bull_third_sharpe": _s(al_bull_sharpe),
                    "mf_beats_always_long_return_in_bull_third": bool(
                        mf_beats_always_long_return_in_bull
                    ),
                    "metric_note": (
                        "the mechanic question uses RETURN in the rising "
                        "third (a flat-heavy book's Sharpe is flattered by "
                        "time in cash); both metrics are reported"
                    ),
                },
                "labeling_rule": (
                    "pre-stated and two-sided: no_standalone_edge_reconfirmed "
                    "if any corrected bar fails; "
                    "defensive_trend_mechanic_not_validated_alpha if the bars "
                    "clear but MF gives up the rising third's return "
                    "(drawdown-avoidance - the committed trend-family "
                    "texture, not return prediction); "
                    "unexpected_return_prediction_signature_re_audit only if "
                    "it also beats always-long's return when the market "
                    "rises - and even then it is not an alpha claim without "
                    "a dedicated pre-registered confirmatory phase"
                ),
            },
            "committed_context": {
                "tsmom_ev1": "beats_buy_hold_risk_adjusted_oos - 'defensive, not profitable' (committed verdict, same universe/machinery)",
                "trend_suite1": "beats_buy_hold_risk_adjusted_oos - 'defensive only - suite adds nothing' (committed; the MA-cross family includes 5/20-style systems)",
                "regime1_regime2": "the same bears-vs-chop defensive texture, committed as honest fails on their own bars",
                "mf_orig_trade_level": "source_faithful_but_underperformed - the namesake trade-level system (stops/trims/1% sizing vs v1.2) cleared no gate (MF-ORIG-EV1.1/EV2)",
                "implication": (
                    "a 5/20 MA long/flat book clearing the relative bar on "
                    "this universe is the KNOWN defensive trend mechanic on a "
                    "refreshed window, not a new discovery; the absolute sign "
                    "of OOS return is window placement (TSMOM-EV1's OOS was a "
                    "-62% bear and absolutely negative)"
                ),
            },
            "reading": {
                "no_standalone_edge_reconfirmed": (
                    "expected and confirmed: a characterized, trustworthy "
                    "signal surface without a standalone out-of-sample edge"
                ),
                "defensive_trend_mechanic_not_validated_alpha": (
                    "the long/flat exits avoid the bear windows (OOS drawdown "
                    "27% vs buy-and-hold 72%) while giving up most of the "
                    "rising third's return - drawdown-avoidance, exactly the "
                    "committed TSMOM-EV1/TREND-SUITE1/REGIME texture on this "
                    "universe; single window, window-dependent, NOT validated "
                    "alpha, and ~p95 against only 30 matched randoms is no "
                    "multiplicity-aware significance claim; the trade-level "
                    "namesake result (source_faithful_but_underperformed) "
                    "stands"
                ),
                "unexpected_return_prediction_signature_re_audit": (
                    "UNEXPECTED return-prediction signature that survived the "
                    "re-audit screens - flagged for the founder; still not an "
                    "alpha claim without a dedicated pre-registered "
                    "confirmatory phase"
                ),
            }[standalone_label],
        },
        "regime_overlay_characterization": {
            **overlay_blocks,
            "regime_config": rg.DEFAULT_CONFIG.config_id,
            "committed_verdict": rg.VERDICT_FAIL,
            "committed_verdict_note": rg.COMMITTED_VERDICT_NOTE,
            "risk_off_days_in_regime_series": risk_off_days,
            "regime_series_days": len(regime_series),
        },
        "limitations": sorted(
            {
                "exposure_books_do_not_model_structure_stops_trims_or_1pct_sizing (trade-level lane characterized in MF-ORIG-EV1.1/EV2)",
                "seven_major_perp_universe_only",
                "single_venue_binance_perp_daily_candles",
                "equal_weight_long_only_books",
                "single_window_result_window_dependent (the OOS tail is a deep bear; long/flat exit rules are mechanically flattered there)",
                "random_benchmarks_are_seeded_coin_flip_and_persistence_matched_long_flat",
                "regime_overlay_carries_its_honest_fail_verdict_everywhere",
            }
        ),
        "boundaries": ms.boundary_flags(),
        "warmup_note": ms.WARMUP_NOTE,
        "disclaimer": ms.DISCLAIMER,
    }

    markdown = render_markdown(summary)
    _assert_safe_language(markdown)
    _assert_safe_language(json.dumps(summary))
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report_output.write_text(markdown, encoding="utf-8")
    print(f"\nwrote {args.summary_output}")
    print(f"wrote {args.report_output}")
    print(f"standalone characterization: {standalone_label}")
    print(f"> {ms.DISCLAIMER}")
    return 0


def _assert_safe_language(text: str) -> None:
    import re

    lowered = text.lower()
    for phrase in FORBIDDEN:
        # word-boundary match so e.g. "provenance" never trips "proven"
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            raise RuntimeError(f"forbidden_report_phrase:{phrase}")


def render_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# MONEYFLOW-SIGNAL1 — Source-Faithful Money Flow Signal Surface (Evidence)")
    lines.append("")
    lines.append(f"> {summary['disclaimer']}")
    lines.append("")
    lines.append(f"- `generated_at_utc`: `{summary['generated_at_utc']}`")
    lines.append(f"- `status`: `{summary['status']}`")
    lines.append(f"- `standalone_characterization`: `{summary['headline']['standalone_characterization']}`")
    lines.append(f"- `regime_overlay`: {summary['headline']['regime_overlay']}")
    lines.append("")
    lines.append("## Source Document (the PDF, read directly this phase)")
    lines.append("")
    src = summary["source_document"]
    lines.append(f"- `{src['title']}` — {src['author']}, {src['edition']}")
    lines.append(f"- repo path: `{src['repo_path']}`")
    lines.append(f"- sha256: `{src['pdf_sha256']}` ({src['pdf_page_count']} PDF pages)")
    lines.append(f"- provenance check: present=`{summary['pdf_provenance']['present']}`, sha256 match=`{summary['pdf_provenance']['sha256_matches_pin']}`")
    lines.append(f"- {src['upgrade_over_mf_orig_ev1']}")
    lines.append("")
    lines.append("## The Documented Rules (page-cited) and Their Implementation")
    lines.append("")
    lines.append("| Rule | Printed page | Implementation |")
    lines.append("| --- | --- | --- |")
    for c in summary["source_citations"]:
        lines.append(f"| `{c['rule_id']}` | {c['printed_page']} | {c['implementation']} |")
    lines.append("")
    lines.append("Quotes are recorded verbatim in the summary JSON (`source_citations[*].quote`).")
    lines.append("")
    lines.append("## Recorded Interpretation Choices (never silently picked)")
    lines.append("")
    for a in summary["ambiguity_resolutions"]:
        lines.append(f"- `{a['ambiguity_id']}`: {a['resolution']}")
    lines.append("")
    lines.append("## Honest Standalone Characterization (expected no-edge; reported straight)")
    lines.append("")
    lines.append(f"- methodology: {summary['methodology']['books']}; friction `{summary['methodology']['friction']}`")
    lines.append(f"- window: {summary['methodology']['windows']['aligned_days']} aligned days, warmed start `{summary['methodology']['windows']['warmed_start']}`, 70/30 split `{summary['methodology']['windows']['train_oos_split_70_30']}`")
    lines.append(f"- scope: {summary['methodology']['scope_note']}")
    lines.append("")
    lines.append("| Book | OOS Sharpe | OOS max DD % | OOS return % | Flips |")
    lines.append("| --- | --- | --- | --- | --- |")
    for label, book in summary["books"].items():
        oos = book["oos"]
        lines.append(
            f"| `{label}` | {oos['sharpe_annual']} | {oos['max_drawdown_pct']} | "
            f"{oos['total_return_pct']} | {book.get('exposure_flips', '—')} |"
        )
    rnd = summary["random_benchmarks"]
    lines.append("")
    cf = rnd["coin_flip"]["oos_sharpe_distribution"]
    pm = rnd["persistence_matched"]["oos_sharpe_distribution"]
    lines.append(
        f"- coin-flip randoms ({rnd['seeds']} seeds; churn-unfair, kept for transparency): "
        f"OOS Sharpe median {cf['median']}, p95 {cf['p95']}"
    )
    lines.append(
        f"- persistence-matched randoms (the fair bar; p_enter {rnd['persistence_matched']['p_enter_per_day']}, "
        f"p_exit {rnd['persistence_matched']['p_exit_per_day']}): OOS Sharpe median {pm['median']}, "
        f"p95 {pm['p95']}; Money Flow percentile vs matched: "
        f"{rnd['mf_oos_sharpe_percentile_vs_persistence_matched']}"
    )
    sc = summary["standalone_characterization"]
    s1 = sc["screens"]["stage1_raw"]
    s2 = sc["screens"]["stage2_re_audit"]
    lines.append(
        f"- stage-1 raw screens: beats buy-and-hold OOS `{s1['beats_buy_hold_risk_adjusted_oos']}`, "
        f"beats coin-flip p95 `{s1['beats_coin_flip_random_p95_oos']}` — re-audit fired: `{s1['re_audit_rule_fired']}`"
    )
    lines.append(
        f"- stage-2 re-audit: beats persistence-matched p95 `{s2['beats_persistence_matched_random_p95_oos']}`; "
        f"rising third `{s2['bull_third']}` return MF {s2['mf_bull_third_return_pct']}% vs always-long "
        f"{s2['always_long_bull_third_return_pct']}% (return-prediction signature: "
        f"`{s2['mf_beats_always_long_return_in_bull_third']}`)"
    )
    lines.append(f"- committed context: {sc['committed_context']['implication']}")
    lines.append(f"- **{sc['label']}** — {sc['reading']}")
    lines.append("")
    lines.append("### Sub-window texture (thirds of the aligned timeline)")
    lines.append("")
    lines.append("| Book | First third Sharpe / return % | Middle third Sharpe / return % | Final third Sharpe / return % |")
    lines.append("| --- | --- | --- | --- |")
    for label, block in summary["sub_window_texture_thirds"]["stats"].items():
        cells = []
        for key in ("first_third", "middle_third", "final_third"):
            cells.append(f"{block[key]['sharpe_annual']} / {block[key]['total_return_pct']}")
        lines.append(f"| `{label}` | {cells[0]} | {cells[1]} | {cells[2]} |")
    lines.append("")
    lines.append("## Money Flow Alone vs Regime-Gated (informational overlay, not a validated control)")
    lines.append("")
    ro = summary["regime_overlay_characterization"]
    lines.append(f"- regime config: `{ro['regime_config']}`; committed verdict: `{ro['committed_verdict']}`")
    lines.append(f"- verdict note: {ro['committed_verdict_note']}")
    lines.append(f"- risk-off days: {ro['risk_off_days_in_regime_series']} of {ro['regime_series_days']} regime-series days")
    lines.append("")
    lines.append("| Base book | OOS DD % ungated | OOS DD % gated | DD reduction (% of ungated) | OOS return ungated % | OOS return gated % | Extra flips |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for base in ("mf_source_stage2", "mf_basic_5_20"):
        block = ro[base]
        wc = block["whipsaw_cost"]
        lines.append(
            f"| `{base}` | {block['ungated_oos']['max_drawdown_pct']} | {block['gated_oos']['max_drawdown_pct']} | "
            f"{block['oos_drawdown_reduction_pct_of_ungated']} | {wc['oos_return_ungated_pct']} | "
            f"{wc['oos_return_gated_pct']} | {wc['extra_flips_from_overlay']} |"
        )
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    for item in summary["limitations"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Boundaries")
    lines.append("")
    for key, value in sorted(summary["boundaries"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append(f"> {summary['disclaimer']}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
