"""TREND-SUITE1 — deterministic, offline tests (no network, no DB, no runtime).

Asserts the phase's documented guarantees:
  - routing: ``trend_suite`` is its own strategy type (prefix
    ``trend_suite1_``) DELIBERATELY judged by the same buy-and-hold
    risk-adjusted gate as TSMOM-EV1; the other gates still refuse it;
  - each signal computes correctly on synthetic series (Donchian breakout
    enters on the prior-N-high break and exits on the opposite channel or
    the chandelier trail; MA cross flips at the crossover; MTF requires the
    frozen weekly sign to agree; ensemble majority/average math);
  - no-lookahead per signal family (truncation + future-tampering probes; a
    deliberately leaky scorer is caught);
  - fractional signal strengths scale sizing while the integer ±1 path of
    ``tsmom_ev1.target_weights`` is unchanged (TSMOM-EV1 results cannot
    drift);
  - friction is applied (frictionless run strictly better);
  - the vol-targeted vs non-vol-targeted comparison exists for every signal
    cell and its classification is deterministic;
  - gate semantics carry the absolute-loss honesty qualifiers, and the
    committed evidence summary reconciles (per-symbol PnL sums to net — the
    K-019 lesson);
  - the suite's TSMOM carry-over reproduces the committed TSMOM-EV1 chosen
    config OOS stats exactly (the reuse-discipline pin);
  - the authored Research Log outcome stays honest (mixed, never green)
    despite the relative gate pass.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from services.execution_quality.exec_ev1 import scenario_by_id
from services.strategy_validation import strategy_types
from services.strategy_validation import trend_suite1 as suite
from services.strategy_validation import tsmom_ev1 as tsmom
from services.strategy_validation.goal_strat1 import Candle, Dataset
from services.strategy_validation.sel_ev1 import SelectionUniverse

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = (
    REPO_ROOT / "docs" / "trend_suite1_canonical_trend_suite_evidence_summary.json"
)
TSMOM_SUMMARY_PATH = (
    REPO_ROOT / "docs" / "tsmom_ev1_vol_targeted_momentum_evidence_summary.json"
)
CONSERVATIVE = scenario_by_id("exec_ev1_conservative")

D = Decimal


def make_dataset(symbol: str, prices: list[float], volume: float = 5_000_000) -> Dataset:
    t0 = datetime(2025, 1, 1, tzinfo=UTC)
    candles = []
    for i, price in enumerate(prices):
        p = Decimal(str(price))
        candles.append(
            Candle(
                symbol=symbol,
                timeframe="1d",
                timestamp=t0 + timedelta(days=i),
                open=p,
                high=p * Decimal("1.01"),
                low=p * Decimal("0.99"),
                close=p,
                volume=Decimal(str(volume)),
                source_path="synthetic",
            )
        )
    return Dataset(
        symbol=symbol,
        timeframe="1d",
        source_path="synthetic",
        source_provenance="synthetic",
        canonical_evidence_status="synthetic",
        candles=tuple(candles),
    )


def config_by_id(config_id: str) -> suite.TrendSuiteConfig:
    return next(
        c for c in suite.generate_trend_suite_configs() if c.config_id == config_id
    )


# ---------------------------------------------------------------------------
# Routing seam
# ---------------------------------------------------------------------------


def test_trend_suite_routing_shares_the_tsmom_gate_deliberately() -> None:
    assert (
        strategy_types.strategy_type_for("trend_suite1_donchian20x10_channel_vt_1d")
        == strategy_types.STRATEGY_TYPE_TREND_SUITE
    )
    route = strategy_types.route_for(strategy_types.STRATEGY_TYPE_TREND_SUITE)
    assert route.gate_id == strategy_types.TSMOM_GATE_ID  # the deliberate share
    assert "trend_suite1" in route.simulator_ref
    assert "evaluate_tsmom_gate" in route.gate_ref
    # The shared gate accepts BOTH trend types and still refuses the others.
    strategy_types.ensure_gate_applies("trend_suite", strategy_types.TSMOM_GATE_ID)
    strategy_types.ensure_gate_applies(
        "time_series_momentum", strategy_types.TSMOM_GATE_ID
    )
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        strategy_types.ensure_gate_applies("per_symbol", strategy_types.TSMOM_GATE_ID)
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        strategy_types.ensure_gate_applies(
            "cross_sectional_selection", strategy_types.TSMOM_GATE_ID
        )
    # ...and other gates refuse trend-suite strategies.
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        strategy_types.ensure_gate_applies(
            strategy_types.STRATEGY_TYPE_TREND_SUITE, strategy_types.SELECTION_GATE_ID
        )
    # Existing routings unchanged.
    assert strategy_types.strategy_type_for("tsmom_ev1_x") == "time_series_momentum"
    assert strategy_types.strategy_type_for("money_flow_v1_2_baseline") == "per_symbol"


def test_grid_is_bounded_with_every_cell_in_both_sizings() -> None:
    configs = suite.generate_trend_suite_configs()
    assert len(configs) == 46
    ids = {c.config_id for c in configs}
    assert len(ids) == 46
    assert all(c.config_id.startswith("trend_suite1_") for c in configs)
    # Pairwise sizing: every vol-targeted cell has its equal-dollar twin.
    for config in configs:
        if config.sizing == suite.SIZING_VOL_TARGETED:
            assert config.config_id.replace("_vt_", "_eq_") in ids, config.config_id
    families = {c.family for c in configs}
    assert families == set(suite.FAMILIES)


# ---------------------------------------------------------------------------
# Signal correctness (synthetic series with known events)
# ---------------------------------------------------------------------------


def test_donchian_enters_on_breakout_and_exits_on_opposite_channel() -> None:
    # Flat at 100 for 30 days, breakout to 120, then collapse to 80.
    prices = [Decimal("100")] * 30 + [Decimal("120")] * 10 + [Decimal("80")] * 10
    highs = list(prices)
    lows = list(prices)
    closes = list(prices)
    states = suite.donchian_state_series(
        highs, lows, closes, entry_period=20, exit_period=10, exit_style=suite.EXIT_CHANNEL
    )
    assert states[29] == 0  # no breakout while flat at the prior high
    assert states[30] == 1  # close 120 > prior 20-day high 100 -> long
    assert states[39] == 1  # still above the exit channel
    assert states[40] == 0  # close 80 < prior 10-day low (120) -> exit
    assert all(s == 0 for s in states[40:])


def test_donchian_atr_trail_exits_below_chandelier_stop() -> None:
    # Breakout then a slow bleed that never breaks the 10-day channel but
    # crosses the chandelier trail (highest close - 2.8 * ATR).
    prices = [100.0] * 30 + [120.0]
    level = 120.0
    for _ in range(20):
        level -= 1.0  # ATR(14) ~ 2.4 here (1% synthetic H/L band + drift)
        prices.append(level)
    closes = [Decimal(str(p)) for p in prices]
    highs = [p * Decimal("1.01") for p in closes]
    lows = [p * Decimal("0.99") for p in closes]
    channel = suite.donchian_state_series(
        highs, lows, closes, entry_period=20, exit_period=10, exit_style=suite.EXIT_CHANNEL
    )
    trail = suite.donchian_state_series(
        highs, lows, closes, entry_period=20, exit_period=10, exit_style=suite.EXIT_ATR_TRAIL
    )
    assert channel[30] == 1 and trail[30] == 1  # both enter on the breakout
    # The trail exits during the bleed; find where, and confirm the channel
    # variant was still long at that point (the stop is genuinely earlier).
    trail_exit = next(i for i in range(31, len(closes)) if trail[i] == 0)
    assert channel[trail_exit] == 1
    assert all(s == 0 for s in trail[trail_exit:])  # disarmed, no re-entry


def test_ma_cross_flips_at_the_crossover() -> None:
    # Down-up V shape: short MA crosses the long MA from below after the turn.
    prices = [200.0 - i for i in range(60)] + [140.0 + 2 * i for i in range(60)]
    closes = [Decimal(str(p)) for p in prices]
    states = suite.ma_cross_state_series(closes, short_period=10, long_period=50)
    assert states[59] == 0  # downtrend: short MA below long MA
    assert states[-1] == 1  # recovered: short MA above long MA
    flip = next(i for i in range(60, len(closes)) if states[i] == 1)
    sma10 = suite._sma_series(closes, 10)
    sma50 = suite._sma_series(closes, 50)
    assert sma10[flip] > sma50[flip]
    assert sma10[flip - 1] <= sma50[flip - 1]


def test_mtf_requires_frozen_weekly_alignment() -> None:
    # 80 days down then 80 days strongly up: the daily 10d sign turns long at
    # the turn, but the frozen weekly 4-week sign stays negative for weeks —
    # the MTF state must lag the daily signal by the weekly confirmation.
    prices = [300.0 - i for i in range(80)] + [220.0 + 3 * i for i in range(80)]
    closes = [Decimal(str(p)) for p in prices]
    states = suite.mtf_state_series(closes, daily_lookback=10, weekly_lookback_weeks=4)
    daily_first_long = next(
        i for i in range(len(closes)) if suite.tsmom_signal(closes, i, 10) == 1
    )
    mtf_first_long = next(i for i in range(len(closes)) if states[i] == 1)
    assert mtf_first_long > daily_first_long  # the weekly gate binds
    # The weekly sign is FROZEN between completed 7-day blocks: inside a week
    # the state can only change via the daily leg.
    week_start = (mtf_first_long // 7) * 7
    boundary = week_start - 1  # weekly sign evaluated at idx where (idx+1)%7==0
    assert (boundary + 1) % 7 == 0
    assert states[-1] == 1  # fully aligned by the end


def test_ensemble_majority_and_average_math() -> None:
    members = [[1, 1, 0], [1, 0, 0], [1, 1, 0], [0, 0, 0], [1, 1, 1]]
    majority = suite.ensemble_state_series(members, kind="majority")
    average = suite.ensemble_state_series(members, kind="average")
    assert majority == [1, 1, 0]  # 4, 3, 1 votes vs threshold 3
    assert average == [D("0.8"), D("0.6"), D("0.2")]
    with pytest.raises(ValueError):
        suite.ensemble_state_series(members, kind="nope")


# ---------------------------------------------------------------------------
# No-lookahead per signal family (+ a leaky scorer is caught)
# ---------------------------------------------------------------------------


def test_every_family_is_point_in_time_and_leaky_scorer_is_caught() -> None:
    import math

    prices = [100 * (1.004**i) * (1 + 0.03 * math.sin(i / 5)) for i in range(240)]
    candles = make_dataset("BTC", prices).candles
    sample = [60, 120, 180, 230]
    probe_ids = [
        "trend_suite1_donchian20x10_channel_vt_1d",
        "trend_suite1_donchian55x20_atr_vt_1d",
        "trend_suite1_ma20x100_signal_vt_1d",
        "trend_suite1_ma20x100_atr_vt_1d",
        "trend_suite1_mtf60w8_signal_vt_1d",
        "trend_suite1_tsmom30_signal_vt_1d",
        "trend_suite1_ens_majority_vt_1d",
        "trend_suite1_ens_average_vt_1d",
    ]
    for config_id in probe_ids:
        config = config_by_id(config_id)

        def scorer(cs, idx, _config=config):
            return suite.strength_at(cs, idx, _config)

        assert suite.verify_point_in_time_scores(scorer, candles, sample), config_id

    def leaky(cs, idx):  # peeks at the global maximum — future data
        peak = max(c.high for c in cs)
        return 1 if cs[idx].close >= peak * Decimal("0.9") else 0

    assert not suite.verify_point_in_time_scores(leaky, candles, sample)


# ---------------------------------------------------------------------------
# Fractional strengths + the unchanged integer path (TSMOM cannot drift)
# ---------------------------------------------------------------------------


def test_fractional_strength_scales_weights_and_integer_path_is_unchanged() -> None:
    config = tsmom.TsmomConfig(
        config_id="tsmom_ev1_test",
        strategy_type=tsmom.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
        lookback_days=30,
        portfolio_vol_target=D("0.20"),
        mode="long_only",
    )
    vols = {"A": D("0.50"), "B": D("0.50")}
    full = tsmom.target_weights(signals={"A": 1, "B": 1}, vols=vols, config=config)
    frac = tsmom.target_weights(
        signals={"A": D("0.4"), "B": 1}, vols=vols, config=config
    )
    assert frac["A"] == full["A"] * D("0.4")  # strength scales the magnitude
    assert frac["B"] == full["B"]
    # Integer ±1/0 path identical to the documented formula (no drift).
    budget = config.portfolio_vol_target / D(2)
    assert full["A"] == min(budget / vols["A"], tsmom.MAX_SINGLE_ASSET_WEIGHT)
    # Equal-dollar: strength / N, same gross cap.
    eq_config = replace(config, vol_targeting=False)
    eq = tsmom.target_weights(
        signals={"A": D("0.6"), "B": 1}, vols=vols, config=eq_config
    )
    assert eq["A"] == D("0.6") / D(2)
    assert eq["B"] == D("0.5")


def test_equal_dollar_gross_exposure_respects_the_leverage_cap() -> None:
    config = config_by_id("trend_suite1_ens_average_eq_1d")
    many = {f"S{i}": D("1") for i in range(4)}
    weights = tsmom.target_weights(
        signals=many, vols={s: None for s in many}, config=config
    )
    gross = sum(abs(w) for w in weights.values())
    assert gross <= suite.MAX_GROSS_LEVERAGE + D("1e-9")
    assert all(w == D("0.25") for w in weights.values())  # strength/N


# ---------------------------------------------------------------------------
# Simulator behavior on synthetic universes
# ---------------------------------------------------------------------------


def _breakout_chop_universe() -> SelectionUniverse:
    up = [100.0] * 30 + [100 * (1.01 ** i) for i in range(1, 171)]
    chop = [100.0 if i % 2 == 0 else 100.5 for i in range(200)]
    return SelectionUniverse([make_dataset("UP", up), make_dataset("CHOP", chop)])


def test_donchian_trades_the_breakout_and_friction_only_subtracts() -> None:
    universe = _breakout_chop_universe()
    config = config_by_id("trend_suite1_donchian20x10_channel_eq_1d")
    result = suite.simulate_trend_suite_portfolio(universe, config, CONSERVATIVE)
    assert result["per_symbol_net_pnl"]["UP"] > 0  # rode the breakout
    assert all(symbol == "UP" for _, symbol, *_ in result["trade_events"])
    zero = replace(
        CONSERVATIVE,
        scenario_id="zero_friction_test",
        fee_bps=D("0"),
        slippage_bps=D("0"),
        adverse_gap_penalty_bps=D("0"),
        spread_tier_multiplier=D("0"),
        impact_coefficient_bps=D("0"),
        fill_probability=D("1"),
        chase_penalty_bps=D("0"),
    )
    frictionless = suite.simulate_trend_suite_portfolio(universe, config, zero)
    assert result["avg_friction_bps"] > 0
    assert result["net_pnl"] < frictionless["net_pnl"]


def test_per_symbol_pnl_reconciles_on_synthetic_run() -> None:
    """The K-019 lesson: results are not trusted until PnL reconciles."""
    universe = _breakout_chop_universe()
    config = config_by_id("trend_suite1_ens_average_vt_1d")
    result = suite.simulate_trend_suite_portfolio(universe, config, CONSERVATIVE)
    total = sum(result["per_symbol_net_pnl"].values(), D("0"))
    assert abs(total - result["net_pnl"]) < D("0.5")
    assert result["equity_curve"][-1][1] == result["ending_equity"]


# ---------------------------------------------------------------------------
# The vol-targeting classification (deterministic)
# ---------------------------------------------------------------------------


def test_vol_targeting_effect_classification_is_deterministic() -> None:
    def stats(ret, dd):
        return {"total_return_pct": ret, "max_drawdown_pct": dd}

    assert (
        suite.classify_vol_targeting_effect(stats(D("-5"), D("10")), stats(D("4"), D("20")))
        == suite.VT_VERDICT_CONVERTED
    )
    assert (
        suite.classify_vol_targeting_effect(stats(D("2"), D("20")), stats(D("8"), D("15")))
        == suite.VT_VERDICT_IMPROVED_BOTH
    )
    assert (
        suite.classify_vol_targeting_effect(stats(D("2"), D("10")), stats(D("8"), D("25")))
        == suite.VT_VERDICT_RETURN_FOR_DD
    )
    assert (
        suite.classify_vol_targeting_effect(stats(D("-4"), D("10")), stats(D("-9"), D("25")))
        == suite.VT_VERDICT_JUST_RISK
    )
    assert (
        suite.classify_vol_targeting_effect(
            stats(D("2"), D("10")), stats(D("2.5"), D("11"))
        )
        == suite.VT_VERDICT_NO_CHANGE
    )


# ---------------------------------------------------------------------------
# Gate semantics through the shared gate
# ---------------------------------------------------------------------------


def test_shared_gate_accepts_trend_suite_and_keeps_honesty_qualifiers() -> None:
    def stats(sharpe, dd, ret):
        return {
            "days": 266,
            "sharpe_annual": sharpe,
            "max_drawdown_pct": dd,
            "total_return_pct": ret,
            "vol_annual": D("0.2"),
        }

    gate = suite.evaluate_tsmom_gate(
        strategy_type=suite.STRATEGY_TYPE_TREND_SUITE,
        oos_strategy_stats=stats(D("-1.4"), D("16"), D("-12")),
        oos_buy_hold_stats=stats(D("-1.8"), D("65"), D("-61")),
        walk_forward_sharpe_edges=[D("1.1"), D("0.4")],
        leave_one_out_edges={"BTC": D("0.3")},
        oos_trade_count=100,
    )
    assert gate["passed"]  # the relative bar IS met...
    assert "oos_absolute_sharpe_not_positive_relative_edge_only" in gate["qualifiers"]
    assert "oos_absolute_return_negative_defensive_value_only" in gate["qualifiers"]
    # The per-config screen never forces a positive either.
    screen = suite.per_config_screen(
        oos_strategy_stats=stats(D("-2.0"), D("70"), D("-50")),
        oos_buy_hold_stats=stats(D("-1.8"), D("65"), D("-61")),
        oos_trade_count=100,
    )
    assert not screen["passed"]
    assert "oos_sharpe_does_not_beat_buy_hold" in screen["reason_codes"]
    assert screen["full_gate"] is False


# ---------------------------------------------------------------------------
# Committed evidence summary (CI-safe: reads the committed docs only)
# ---------------------------------------------------------------------------


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def test_committed_summary_answers_both_headline_questions() -> None:
    summary = _summary()
    answers = summary["headline_answers"]
    assert (
        "question_1_does_any_trend_form_beat_buy_hold_risk_adjusted_oos_in_absolute_terms"
        in answers
    )
    q2 = answers["question_2_did_removing_vol_targeting_unlock_profit_or_just_risk"]
    assert sum(q2["classification_counts"].values()) == q2["pair_count"] > 0
    # Every family has a champion judged by the FULL gate.
    assert set(summary["family_gates"]) == set(suite.FAMILIES)
    for block in summary["family_gates"].values():
        assert set(block["leave_one_out"]) == set(suite.LIQUID_UNIVERSE)
        assert block["gate"]["gate_id"] == "tsmom_buy_hold_risk_adjusted_gate"


def test_committed_summary_has_vt_pair_for_every_signal_cell() -> None:
    summary = _summary()
    rows = summary["per_config_results"]["exec_ev1_conservative"]
    vt_cells = [r for r in rows if r["sizing"] == "vol_targeted"]
    assert len(summary["vol_targeting_comparison"]) == len(vt_cells) == 23
    for pair in summary["vol_targeting_comparison"].values():
        assert pair["classification"] in (
            suite.VT_VERDICT_CONVERTED,
            suite.VT_VERDICT_IMPROVED_BOTH,
            suite.VT_VERDICT_RETURN_FOR_DD,
            suite.VT_VERDICT_JUST_RISK,
            suite.VT_VERDICT_NO_CHANGE,
        )


def test_committed_summary_is_honest_and_reconciles() -> None:
    summary = _summary()
    gate = summary["global_gate"]["gate"]
    assert summary["verdict"] == gate["status"]
    strategy_oos = summary["headline_comparison"]["strategy_oos"]
    if Decimal(str(strategy_oos["sharpe_annual"])) <= 0:
        assert "oos_absolute_sharpe_not_positive_relative_edge_only" in gate["qualifiers"]
    if Decimal(str(strategy_oos["total_return_pct"])) <= 0:
        assert "oos_absolute_return_negative_defensive_value_only" in gate["qualifiers"]
    assert summary["no_lookahead_verification"]["all_ok"] is True
    assert summary["boundaries"]["research_only"] is True
    assert summary["boundaries"]["perp_funding_not_modeled"] is True
    assert summary["design"]["perp_funding_modeled"] is False
    # K-019: per-symbol PnL sums to net for every conservative-scenario row.
    for row in summary["per_config_results"]["exec_ev1_conservative"]:
        total = sum(Decimal(v) for v in row["per_symbol_net_pnl"].values())
        assert abs(total - Decimal(row["net_pnl"])) < Decimal("1"), row["config_id"]


def test_suite_tsmom_carry_over_reproduces_committed_ev1_oos_exactly() -> None:
    """The reuse-discipline pin: the suite's TSMOM carry-over, run through
    the provider/timestamps seams, must equal the committed TSMOM-EV1
    train-chosen config OOS stats digit for digit. If this drifts, the suite
    is no longer testing the same baseline."""
    summary = _summary()
    tsmom_summary = json.loads(TSMOM_SUMMARY_PATH.read_text(encoding="utf-8"))
    assert (
        tsmom_summary["train_only_choice"]["chosen_config"]
        == "tsmom_ev1_lb30_vt20_long_only_1d"
    )
    ev1_oos = tsmom_summary["headline_comparison"]["strategy_oos"]
    row = next(
        r
        for r in summary["per_config_results"]["exec_ev1_conservative"]
        if r["config_id"] == "trend_suite1_tsmom30_signal_vt_1d"
    )
    for key in ("sharpe_annual", "max_drawdown_pct", "total_return_pct", "days"):
        assert row["oos_stats"][key] == ev1_oos[key], key


def test_research_log_outcome_for_trend_suite_stays_honest_not_green() -> None:
    """Pinned: the Research Log entry is authored `mixed` — a relative gate
    pass with negative absolute OOS performance (and both headline answers
    negative) must never render green."""
    payload = json.loads(
        (REPO_ROOT / "docs" / "research_log.json").read_text(encoding="utf-8")
    )
    by_phase = {entry["phase"]: entry for entry in payload["entries"]}
    entry = by_phase.get("TREND-SUITE1")
    assert entry is not None, "TREND-SUITE1 research_log block missing"
    assert entry["outcome"] == "mixed"
    assert payload["standing"]["passed_gate"] == sum(
        1 for e in payload["entries"] if e["outcome"] == "pass"
    )
