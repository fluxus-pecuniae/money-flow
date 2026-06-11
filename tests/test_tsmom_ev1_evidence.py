"""TSMOM-EV1 — deterministic, offline tests (no network, no DB, no runtime).

Asserts the phase's documented guarantees:
  - routing: ``time_series_momentum`` is its own strategy type with its own
    buy-and-hold risk-adjusted gate; cross-application of gates raises;
  - vol targeting equalizes per-asset risk contribution (the ZEC-class fix);
  - no-lookahead: the signal and realized vol at t use only data <= t (a
    deliberately leaky scorer is caught);
  - friction is applied (frictionless run strictly better) at the traded
    notional;
  - the gate compares to buy-and-hold on Sharpe AND max drawdown, OOS, and
    carries non-failing honesty qualifiers when the absolute OOS result is
    negative (a relative pass in a falling market must not read as profit);
  - leave-one-out runs for every liquid-universe symbol;
  - a synthetic always-up series trends long while a zero-drift chop series
    accumulates NO exposure;
  - the committed evidence summary reconciles (per-symbol PnL sums to net —
    the K-019 lesson) and the authored Research Log outcome stays honest
    (mixed, never green) despite the relative gate pass.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from services.execution_quality.exec_ev1 import scenario_by_id
from services.strategy_validation import strategy_types
from services.strategy_validation import tsmom_ev1 as tsmom
from services.strategy_validation.goal_strat1 import Candle, Dataset
from services.strategy_validation.sel_ev1 import SelectionUniverse

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = REPO_ROOT / "docs" / "tsmom_ev1_vol_targeted_momentum_evidence_summary.json"
CONSERVATIVE = scenario_by_id("exec_ev1_conservative")


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


def smoke_config(**overrides) -> tsmom.TsmomConfig:
    base = dict(
        config_id="tsmom_ev1_test",
        strategy_type=tsmom.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
        lookback_days=30,
        portfolio_vol_target=Decimal("0.20"),
        mode="long_only",
    )
    base.update(overrides)
    return tsmom.TsmomConfig(**base)


# ---------------------------------------------------------------------------
# Routing seam
# ---------------------------------------------------------------------------


def test_tsmom_routing_is_its_own_type_with_its_own_gate() -> None:
    assert (
        strategy_types.strategy_type_for("tsmom_ev1_lb30_vt20_long_only_1d")
        == strategy_types.STRATEGY_TYPE_TIME_SERIES_MOMENTUM
    )
    route = strategy_types.route_for(strategy_types.STRATEGY_TYPE_TIME_SERIES_MOMENTUM)
    assert route.gate_id == strategy_types.TSMOM_GATE_ID
    assert "tsmom_ev1" in route.simulator_ref
    # The TSMOM gate refuses other strategy types...
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        strategy_types.ensure_gate_applies("per_symbol", strategy_types.TSMOM_GATE_ID)
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        strategy_types.ensure_gate_applies(
            "cross_sectional_selection", strategy_types.TSMOM_GATE_ID
        )
    # ...and other gates refuse TSMOM strategies.
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        strategy_types.ensure_gate_applies(
            strategy_types.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
            strategy_types.SELECTION_GATE_ID,
        )
    # Existing routings unchanged.
    assert strategy_types.strategy_type_for("sel_ev1_x") == "cross_sectional_selection"
    assert strategy_types.strategy_type_for("money_flow_v1_2_baseline") == "per_symbol"


# ---------------------------------------------------------------------------
# Vol targeting + risk parity (the core fix)
# ---------------------------------------------------------------------------


def test_vol_targeting_equalizes_per_asset_risk_contribution() -> None:
    """In the uncapped regime, weight * realized_vol == the per-asset risk
    budget for every asset — equal risk contribution regardless of vol."""
    config = smoke_config()
    vols = {"CALM": Decimal("0.40"), "WILD": Decimal("0.80"), "MID": Decimal("0.55")}
    weights = tsmom.target_weights(
        signals={s: 1 for s in vols}, vols=vols, config=config
    )
    budget = config.portfolio_vol_target / Decimal(len(vols))
    for symbol, vol in vols.items():
        contribution = weights[symbol] * vol
        assert abs(contribution - budget) < Decimal("1e-12"), symbol
    # The wild asset gets HALF the weight of the calm one (inverse vol).
    assert weights["WILD"] < weights["CALM"]
    assert abs(weights["CALM"] / weights["WILD"] - Decimal("2")) < Decimal("1e-9")


def test_weight_caps_and_leverage_cap_apply() -> None:
    config = smoke_config()
    # Tiny vol would demand a huge weight -> capped at MAX_SINGLE_ASSET_WEIGHT.
    weights = tsmom.target_weights(
        signals={"A": 1}, vols={"A": Decimal("0.01")}, config=config
    )
    assert weights["A"] == tsmom.MAX_SINGLE_ASSET_WEIGHT
    # Gross leverage never exceeds the documented cap.
    many = {f"S{i}": 1 for i in range(20)}
    vols = {s: Decimal("0.02") for s in many}
    config_high = smoke_config(portfolio_vol_target=Decimal("0.40"))
    weights = tsmom.target_weights(signals=many, vols=vols, config=config_high)
    gross = sum(abs(w) for w in weights.values())
    assert gross <= tsmom.MAX_GROSS_LEVERAGE + Decimal("1e-9")
    # long_only zeroes negative signals; long_short shorts them.
    weights_lo = tsmom.target_weights(
        signals={"A": -1}, vols={"A": Decimal("0.5")}, config=config
    )
    assert weights_lo["A"] == 0
    weights_ls = tsmom.target_weights(
        signals={"A": -1},
        vols={"A": Decimal("0.5")},
        config=smoke_config(mode="long_short"),
    )
    assert weights_ls["A"] < 0


# ---------------------------------------------------------------------------
# No-lookahead
# ---------------------------------------------------------------------------


def test_signal_and_vol_are_point_in_time_and_leaky_scorer_is_caught() -> None:
    prices = [100 * (1.003**i) * (1 + 0.02 * math.sin(i / 3)) for i in range(160)]
    candles = make_dataset("BTC", prices).candles
    sample = [40, 80, 120, 150]

    def signal_fn(cs, idx):
        return tsmom.tsmom_signal([c.close for c in cs], idx, 30)

    def vol_fn(cs, idx):
        return tsmom.realized_vol_annual([c.close for c in cs], idx, 30)

    assert tsmom.verify_point_in_time_scores(signal_fn, candles, sample)
    assert tsmom.verify_point_in_time_scores(vol_fn, candles, sample)

    def leaky_fn(cs, idx):  # reads the LAST close — future data
        return cs[-1].close - cs[idx - 30].close

    assert not tsmom.verify_point_in_time_scores(leaky_fn, candles, sample)


# ---------------------------------------------------------------------------
# Simulator behavior: trend vs chop, friction
# ---------------------------------------------------------------------------


def _trend_chop_universe() -> SelectionUniverse:
    up = [100 * (1.005**i) for i in range(200)]
    chop = [100 if i % 2 == 0 else 101 for i in range(200)]  # zero drift
    return SelectionUniverse([make_dataset("UP", up), make_dataset("CHOP", chop)])


def test_always_up_trends_long_and_zero_drift_chop_stays_flat() -> None:
    universe = _trend_chop_universe()
    result = tsmom.simulate_tsmom_portfolio(universe, smoke_config(), CONSERVATIVE)
    # The chop symbol's 30d trailing return is exactly zero -> flat forever.
    assert result["per_symbol_net_pnl"]["CHOP"] == 0
    assert all(symbol == "UP" for _, symbol, *_ in result["trade_events"])
    # The trending symbol is held long and contributes positively.
    assert result["per_symbol_net_pnl"]["UP"] > 0
    assert result["avg_gross_exposure"] > 0
    assert result["avg_net_exposure"] > 0  # long, not short


def test_friction_is_applied_and_only_subtracts() -> None:
    universe = _trend_chop_universe()
    config = smoke_config()
    with_friction = tsmom.simulate_tsmom_portfolio(universe, config, CONSERVATIVE)
    zero = replace(
        CONSERVATIVE,
        scenario_id="zero_friction_test",
        fee_bps=Decimal("0"),
        slippage_bps=Decimal("0"),
        adverse_gap_penalty_bps=Decimal("0"),
        spread_tier_multiplier=Decimal("0"),
        impact_coefficient_bps=Decimal("0"),
        fill_probability=Decimal("1"),
        chase_penalty_bps=Decimal("0"),
    )
    frictionless = tsmom.simulate_tsmom_portfolio(universe, config, zero)
    assert with_friction["avg_friction_bps"] > 0
    assert with_friction["friction_paid_quote"] > 0
    assert with_friction["net_pnl"] < frictionless["net_pnl"]


def test_per_symbol_pnl_reconciles_to_net_pnl() -> None:
    """The K-019 lesson: results are not trusted until PnL reconciles."""
    universe = _trend_chop_universe()
    result = tsmom.simulate_tsmom_portfolio(universe, smoke_config(), CONSERVATIVE)
    total = sum(result["per_symbol_net_pnl"].values(), Decimal("0"))
    assert abs(total - result["net_pnl"]) < Decimal("0.5")
    # And the equity curve ends where cash ended (forced close realizes all).
    assert result["equity_curve"][-1][1] == result["ending_equity"]


# ---------------------------------------------------------------------------
# The gate: Sharpe + drawdown vs buy-and-hold, with honesty qualifiers
# ---------------------------------------------------------------------------


def _stats(sharpe, dd, days=200, ret=Decimal("10")) -> dict:
    return {
        "days": days,
        "sharpe_annual": sharpe,
        "max_drawdown_pct": dd,
        "total_return_pct": ret,
        "vol_annual": Decimal("0.2"),
    }


def test_gate_requires_sharpe_and_drawdown_vs_buy_hold() -> None:
    kwargs = dict(
        strategy_type=tsmom.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
        walk_forward_sharpe_edges=[Decimal("0.5"), Decimal("0.3")],
        leave_one_out_edges={"BTC": Decimal("0.2"), "ETH": Decimal("0.1")},
        oos_trade_count=40,
    )
    passing = tsmom.evaluate_tsmom_gate(
        oos_strategy_stats=_stats(Decimal("1.2"), Decimal("15")),
        oos_buy_hold_stats=_stats(Decimal("0.6"), Decimal("40")),
        **kwargs,
    )
    assert passing["passed"] and passing["status"] == tsmom.VERDICT_BEATS_BUY_HOLD
    assert passing["qualifiers"] == []

    worse_sharpe = tsmom.evaluate_tsmom_gate(
        oos_strategy_stats=_stats(Decimal("0.4"), Decimal("15")),
        oos_buy_hold_stats=_stats(Decimal("0.6"), Decimal("40")),
        **kwargs,
    )
    assert not worse_sharpe["passed"]
    assert "oos_sharpe_does_not_beat_buy_hold" in worse_sharpe["reason_codes"]

    worse_dd = tsmom.evaluate_tsmom_gate(
        oos_strategy_stats=_stats(Decimal("1.2"), Decimal("50")),
        oos_buy_hold_stats=_stats(Decimal("0.6"), Decimal("40")),
        **kwargs,
    )
    assert not worse_dd["passed"]
    assert "oos_drawdown_worse_than_buy_hold" in worse_dd["reason_codes"]

    broken_loo = tsmom.evaluate_tsmom_gate(
        oos_strategy_stats=_stats(Decimal("1.2"), Decimal("15")),
        oos_buy_hold_stats=_stats(Decimal("0.6"), Decimal("40")),
        strategy_type=tsmom.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
        walk_forward_sharpe_edges=[Decimal("0.5"), Decimal("0.3")],
        leave_one_out_edges={"BTC": Decimal("0.2"), "ETH": Decimal("-0.1")},
        oos_trade_count=40,
    )
    assert not broken_loo["passed"]
    assert "leave_one_out_breaks_risk_adjusted_edge" in broken_loo["reason_codes"]


def test_relative_pass_with_negative_absolute_oos_carries_qualifiers() -> None:
    """Pinned: beating a collapsing benchmark while losing money must be
    impossible to read as profit."""
    gate = tsmom.evaluate_tsmom_gate(
        strategy_type=tsmom.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
        oos_strategy_stats=_stats(Decimal("-1.4"), Decimal("16"), ret=Decimal("-12")),
        oos_buy_hold_stats=_stats(Decimal("-1.8"), Decimal("65"), ret=Decimal("-61")),
        walk_forward_sharpe_edges=[Decimal("1.1"), Decimal("0.4")],
        leave_one_out_edges={"BTC": Decimal("0.3")},
        oos_trade_count=100,
    )
    assert gate["passed"]  # the relative bar IS met...
    assert "oos_absolute_sharpe_not_positive_relative_edge_only" in gate["qualifiers"]
    assert "oos_absolute_return_negative_defensive_value_only" in gate["qualifiers"]


# ---------------------------------------------------------------------------
# Committed evidence summary (CI-safe: reads the committed doc only)
# ---------------------------------------------------------------------------


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def test_committed_summary_has_leave_one_out_for_every_liquid_symbol() -> None:
    summary = _summary()
    assert set(summary["leave_one_out"]) == set(tsmom.LIQUID_UNIVERSE)
    assert summary["universe"]["excluded_thin_symbols"] == ["HYPE"]
    for row in summary["leave_one_out"].values():
        assert row["oos_sharpe_edge_vs_buy_hold"] is not None


def test_committed_summary_gate_and_qualifiers_are_honest() -> None:
    summary = _summary()
    gate = summary["selection_gate"]
    assert gate["gate_id"] == "tsmom_buy_hold_risk_adjusted_gate"
    assert summary["verdict"] == gate["status"]
    strategy_oos = summary["headline_comparison"]["strategy_oos"]
    if Decimal(str(strategy_oos["sharpe_annual"])) <= 0:
        # A relative pass with negative absolute OOS Sharpe MUST carry the
        # defensive-value qualifiers (this is the current data's regime).
        assert "oos_absolute_sharpe_not_positive_relative_edge_only" in gate["qualifiers"]
    assert summary["boundaries"]["research_only"] is True
    assert summary["boundaries"]["perp_funding_not_modeled"] is True
    assert summary["design"]["perp_funding_modeled"] is False
    assert summary["no_lookahead_verification"]["signal_point_in_time_ok"] is True
    assert summary["no_lookahead_verification"]["vol_point_in_time_ok"] is True


def test_committed_summary_per_symbol_pnl_reconciles() -> None:
    summary = _summary()
    for row in summary["per_config_results"]["exec_ev1_conservative"]:
        total = sum(Decimal(v) for v in row["per_symbol_net_pnl"].values())
        assert abs(total - Decimal(row["net_pnl"])) < Decimal("1"), row["config_id"]


def test_research_log_outcome_for_tsmom_stays_honest_not_green() -> None:
    """Pinned: the Research Log entry is authored `mixed` — a relative gate
    pass with negative absolute OOS performance must never render green."""
    payload = json.loads(
        (REPO_ROOT / "docs" / "research_log.json").read_text(encoding="utf-8")
    )
    by_phase = {entry["phase"]: entry for entry in payload["entries"]}
    entry = by_phase.get("TSMOM-EV1")
    assert entry is not None, "TSMOM-EV1 research_log block missing"
    assert entry["outcome"] == "mixed"
    assert payload["standing"]["passed_gate"] == sum(
        1 for e in payload["entries"] if e["outcome"] == "pass"
    )
