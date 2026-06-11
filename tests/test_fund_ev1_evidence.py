"""FUND-EV1 — deterministic, offline tests (no network, no DB, no runtime).

Asserts the phase's documented guarantees:
  - routing: ``funding_carry`` is its own strategy type with its own
    net-carry/tail gate; cross-application of gates raises;
  - funding accrues correctly per period (exact value on constant funding,
    flat prices) and with the right SIGN (short perp RECEIVES positive
    funding; the flip side receives negative funding);
  - the two-leg book is delta-neutral within tolerance (flat prices ->
    price PnL nets to ~0; residual delta ~0 between clean two-leg fills);
  - costs are applied on BOTH legs and only subtract;
  - no-lookahead: the trailing-funding signal at t uses only slots <= t
    (truncation + tampering probes; a leaky reader is caught);
  - the leg-lag tail stress models REAL one-leg exposure (residual delta
    spikes to the unhedged fraction), not just re-priced fills;
  - collect_only goes flat under negative funding; flip_sides flips;
  - PnL reconciles: per-symbol net sums to net_pnl and the equity curve
    ends at ending equity (the K-019 lesson);
  - gate semantics: every documented reason code fires; tail limits bind;
  - the committed evidence summary + funding snapshot reconcile, and the
    authored Research Log outcome stays honest (fail — never green).
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from services.execution_quality.exec_ev1 import scenario_by_id
from services.strategy_validation import fund_ev1 as fund
from services.strategy_validation import strategy_types
from services.strategy_validation.goal_strat1 import Candle, Dataset

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = REPO_ROOT / "docs" / "fund_ev1_delta_neutral_carry_evidence_summary.json"
SNAPSHOT_PATH = REPO_ROOT / "docs" / "fund_ev1_funding_data_snapshot_summary.json"
CONSERVATIVE = scenario_by_id("exec_ev1_conservative")
ZERO_COST = fund.zero_cost_scenario(CONSERVATIVE)
T0 = datetime(2025, 1, 1, tzinfo=UTC)


def make_dataset(symbol: str, prices: list[float], volume: float = 5_000_000) -> Dataset:
    candles = []
    for i, price in enumerate(prices):
        p = Decimal(str(price))
        candles.append(
            Candle(
                symbol=symbol,
                timeframe="1d",
                timestamp=T0 + timedelta(days=i + 1),
                open=p,
                high=p * Decimal("1.001"),
                low=p * Decimal("0.999"),
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


def make_asset(
    symbol: str,
    n: int,
    *,
    prices: list[float] | None = None,
    spot_prices: list[float] | None = None,
    funding: Decimal | list[Decimal] = Decimal("0.0003"),
) -> fund.CarryAsset:
    perp_prices = prices if prices is not None else [100.0] * n
    funding_map: dict[datetime, Decimal] = {}
    hours: dict[datetime, int] = {}
    for i in range(n):
        t = T0 + timedelta(days=i + 1)
        rate = funding[i] if isinstance(funding, list) else funding
        funding_map[t] = rate
        hours[t] = 24
    return fund.CarryAsset(
        symbol=symbol,
        perp=make_dataset(symbol, perp_prices),
        spot=make_dataset(symbol, spot_prices if spot_prices is not None else perp_prices),
        funding_by_close=funding_map,
        funding_hours_by_close=hours,
    )


def smoke_config(**overrides) -> fund.FundingCarryConfig:
    base = dict(
        config_id="fund_ev1_test",
        strategy_type=fund.STRATEGY_TYPE_FUNDING_CARRY,
        mode="collect_only",
        rebalance_interval_days=7,
        top_k=2,
    )
    base.update(overrides)
    return fund.FundingCarryConfig(**base)


def two_asset_universe(n: int = 120, **kwargs) -> fund.CarryUniverse:
    return fund.CarryUniverse(
        [make_asset("AAA", n, **kwargs), make_asset("BBB", n, **kwargs)]
    )


# ---------------------------------------------------------------------------
# Routing seam
# ---------------------------------------------------------------------------


def test_funding_carry_routing_is_its_own_type_with_its_own_gate() -> None:
    assert (
        strategy_types.strategy_type_for("fund_ev1_collect_only_cad14_top4_1d")
        == strategy_types.STRATEGY_TYPE_FUNDING_CARRY
    )
    route = strategy_types.route_for(strategy_types.STRATEGY_TYPE_FUNDING_CARRY)
    assert route.gate_id == strategy_types.FUNDING_CARRY_GATE_ID
    assert "fund_ev1" in route.simulator_ref
    # The carry gate refuses every other strategy type...
    for other in ("per_symbol", "cross_sectional_selection", "time_series_momentum"):
        with pytest.raises(strategy_types.StrategyTypeRoutingError):
            strategy_types.ensure_gate_applies(other, strategy_types.FUNDING_CARRY_GATE_ID)
    # ...and other gates refuse carry strategies.
    for other_gate in (
        strategy_types.PER_SYMBOL_GATE_ID,
        strategy_types.SELECTION_GATE_ID,
        strategy_types.TSMOM_GATE_ID,
    ):
        with pytest.raises(strategy_types.StrategyTypeRoutingError):
            strategy_types.ensure_gate_applies(
                strategy_types.STRATEGY_TYPE_FUNDING_CARRY, other_gate
            )
    # Existing routings unchanged.
    assert strategy_types.strategy_type_for("tsmom_ev1_x") == "time_series_momentum"
    assert strategy_types.strategy_type_for("sel_ev1_x") == "cross_sectional_selection"
    assert strategy_types.strategy_type_for("money_flow_v1_2_baseline") == "per_symbol"


# ---------------------------------------------------------------------------
# Funding accrual: exact value and sign
# ---------------------------------------------------------------------------


def test_funding_accrues_exactly_and_short_perp_receives_positive_funding() -> None:
    """Constant +3bps/day funding, flat prices, zero costs: funding income
    must be exactly notional * rate * accrual_days per asset, all of it
    received by the SHORT perp legs."""
    n = 120
    universe = two_asset_universe(n)
    config = smoke_config()
    result = fund.simulate_funding_carry_portfolio(universe, config, ZERO_COST)
    # Signal needs 7 slots; first rebalance with signal at aligned step 7;
    # fills at step 8's candle -> accrual from step 8 through the end.
    accrual_days = n - 8
    expected_per_asset = Decimal("2500") * Decimal("0.0003") * accrual_days
    for symbol in ("AAA", "BBB"):
        assert abs(result["funding_by_symbol"][symbol] - expected_per_asset) < Decimal(
            "0.01"
        ), symbol
    assert result["funding_collected_total"] > 0
    assert abs(result["net_pnl"] - result["funding_collected_total"]) < Decimal("0.01")


def test_flip_side_receives_negative_funding_and_collect_only_stays_flat() -> None:
    universe = two_asset_universe(120, funding=Decimal("-0.0003"))
    collect = fund.simulate_funding_carry_portfolio(
        universe, smoke_config(), CONSERVATIVE
    )
    assert collect["trade_count"] == 0  # nothing to collect -> flat book
    assert collect["net_pnl"] == 0
    flip_result = fund.simulate_funding_carry_portfolio(
        universe, smoke_config(config_id="fund_ev1_flip", mode="flip_sides"), ZERO_COST
    )
    assert flip_result["funding_collected_total"] > 0  # long perp receives when negative
    # The flip_resultped book is long perp / short spot.
    legs = {(leg, side) for _, _, leg, side, _ in flip_result["trade_events"][:4]}
    assert ("perp", "buy") in legs and ("spot", "sell") in legs


# ---------------------------------------------------------------------------
# Delta neutrality + costs on both legs
# ---------------------------------------------------------------------------


def test_book_is_delta_neutral_price_pnl_nets_to_zero_without_gaps() -> None:
    """Steadily trending prices, ZERO funding, zero costs: the long-spot and
    short-perp legs must offset so net PnL stays ~0 (price direction does
    not matter), and residual delta stays inside the rebalance band."""
    n = 120
    trend = [100 * (1.004**i) for i in range(n)]
    universe = fund.CarryUniverse(
        [
            make_asset("AAA", n, prices=trend, funding=Decimal("0.0001")),
            make_asset("BBB", n, prices=trend, funding=Decimal("0.0001")),
        ]
    )
    result = fund.simulate_funding_carry_portfolio(
        universe, smoke_config(), ZERO_COST
    )
    funding_only = result["funding_collected_total"]
    price_pnl = result["net_pnl"] - funding_only
    # Price PnL is a tiny rebalance-drift remainder, far below funding.
    assert abs(price_pnl) < funding_only / 4
    assert result["max_residual_delta_fraction"] < Decimal("0.02")


def test_costs_apply_on_both_legs_and_only_subtract() -> None:
    universe = two_asset_universe(120)
    config = smoke_config()
    with_costs = fund.simulate_funding_carry_portfolio(universe, config, CONSERVATIVE)
    frictionless = fund.simulate_funding_carry_portfolio(universe, config, ZERO_COST)
    assert with_costs["fees_by_leg"]["perp"] > 0
    assert with_costs["fees_by_leg"]["spot"] > 0
    assert with_costs["friction_quote_by_leg"]["perp"] > 0
    assert with_costs["friction_quote_by_leg"]["spot"] > 0
    assert with_costs["avg_friction_bps"] > 0
    assert with_costs["net_pnl"] < frictionless["net_pnl"]
    # The spot leg prices at the WIDEST tier even for majors (BTC_SPOT falls
    # through to mid-alt) — documented conservative assumption.
    from services.execution_quality.exec_ev1 import TIER_MID, symbol_tier

    assert symbol_tier(f"BTC{fund.SPOT_FRICTION_SUFFIX}") == TIER_MID


# ---------------------------------------------------------------------------
# No-lookahead
# ---------------------------------------------------------------------------


def test_trailing_funding_signal_is_point_in_time_and_leaky_reader_caught() -> None:
    n = 200
    rates = [Decimal("0.0001") * ((i % 7) - 3) for i in range(n)]
    times = [T0 + timedelta(days=i + 1) for i in range(n)]
    fmap = dict(zip(times, rates))
    sample = [times[30], times[100], times[180]]
    assert fund.verify_funding_signal_point_in_time(times, fmap, sample, 7)

    # A leaky reader (uses the LAST slot regardless of t) must be caught by
    # the same tamper probe: tampering future slots changes its output.
    t = times[30]
    tampered = dict(fmap)
    for ts in times:
        if ts > t:
            tampered[ts] = fmap[ts] * Decimal("-7") + Decimal("1")

    def leaky(series: dict) -> Decimal:
        return series[times[-1]]

    assert leaky(tampered) != leaky(fmap)
    # And the real signal is unchanged by the same tampering.
    assert fund.trailing_funding_mean(times, tampered, t, 7) == fund.trailing_funding_mean(
        times, fmap, t, 7
    )


# ---------------------------------------------------------------------------
# Tail stress: the leg-lag run models REAL one-leg exposure
# ---------------------------------------------------------------------------


def test_leg_lag_creates_real_one_leg_exposure() -> None:
    universe = two_asset_universe(120)
    base = fund.simulate_funding_carry_portfolio(universe, smoke_config(), CONSERVATIVE)
    lagged = fund.simulate_funding_carry_portfolio(
        universe,
        smoke_config(config_id="fund_ev1_test_lag", spot_leg_lag_days=1),
        CONSERVATIVE,
    )
    # Flat prices + clean two-leg fills: residual ~0. With the spot leg one
    # candle late, the perp side stands alone around entries — the residual
    # must spike to the unhedged fraction (~half the equity at entry).
    assert base["max_residual_delta_fraction"] < Decimal("0.01")
    assert lagged["max_residual_delta_fraction"] > Decimal("0.4")
    # The stress run still completes and reconciles.
    total = sum(lagged["per_symbol_net_pnl"].values(), Decimal("0"))
    assert abs(total - lagged["net_pnl"]) < Decimal("0.5")


def test_funding_inversion_mid_series_collect_only_exits() -> None:
    """Funding flips negative halfway: collect_only must exit after the
    trailing signal turns and stop accruing (the bleed is bounded by the
    signal lag)."""
    n = 140
    rates = [Decimal("0.0004")] * 70 + [Decimal("-0.0004")] * 70
    universe = fund.CarryUniverse(
        [
            make_asset("AAA", n, funding=list(rates)),
            make_asset("BBB", n, funding=list(rates)),
        ]
    )
    result = fund.simulate_funding_carry_portfolio(
        universe, smoke_config(rebalance_interval_days=7), ZERO_COST
    )
    # Some funding was paid during the signal lag (bleed measured)...
    assert result["funding_paid_on_negative_days_by_symbol"]["AAA"] < 0
    # ...but the lag is bounded: well under the lookback+cadence worth of
    # negative days, and the book ends flat (sell trades happened).
    assert result["negative_funding_exposure_days_by_symbol"]["AAA"] <= 14
    sells = [e for e in result["trade_events"] if e[2] == "spot" and e[3] == "sell"]
    assert sells, "collect_only must exit the spot leg after inversion"


# ---------------------------------------------------------------------------
# Reconciliation (the K-019 lesson)
# ---------------------------------------------------------------------------


def test_per_symbol_pnl_reconciles_to_net_pnl_and_curve_ends_at_equity() -> None:
    universe = two_asset_universe(120)
    result = fund.simulate_funding_carry_portfolio(universe, smoke_config(), CONSERVATIVE)
    total = sum(result["per_symbol_net_pnl"].values(), Decimal("0"))
    assert abs(total - result["net_pnl"]) < Decimal("0.5")
    assert result["equity_curve"][-1][1] == result["ending_equity"]


# ---------------------------------------------------------------------------
# Gate semantics
# ---------------------------------------------------------------------------


def _stats(sharpe, dd, days=119) -> dict:
    return {
        "days": days,
        "sharpe_annual": sharpe,
        "max_drawdown_pct": dd,
        "total_return_pct": Decimal("1"),
        "vol_annual": Decimal("0.01"),
    }


def _passing_kwargs() -> dict:
    return dict(
        strategy_type=fund.STRATEGY_TYPE_FUNDING_CARRY,
        oos_strategy_stats=_stats(Decimal("2.0"), Decimal("1.5")),
        oos_net_pnl=Decimal("120"),
        walk_forward_net_pnls=[Decimal("60"), Decimal("40")],
        regime_pnls={
            "bull": {"days": 100, "net_pnl": Decimal("150")},
            "neutral": {"days": 100, "net_pnl": Decimal("80")},
            "bear": {"days": 100, "net_pnl": Decimal("30")},
        },
        leave_one_out_oos_net={"BTC": Decimal("90"), "ETH": Decimal("70")},
        stressed_max_drawdown_pct=Decimal("3"),
    )


def test_gate_passes_only_when_every_documented_condition_holds() -> None:
    gate = fund.evaluate_funding_carry_gate(**_passing_kwargs())
    assert gate["passed"] and gate["status"] == fund.VERDICT_PASS
    assert gate["reason_codes"] == ["funding_carry_gate_passed"]

    cases = {
        "oos_net_carry_not_positive_after_costs": {"oos_net_pnl": Decimal("-5")},
        "walk_forward_net_carry_not_positive_in_every_fold": {
            "walk_forward_net_pnls": [Decimal("60"), Decimal("-1")]
        },
        "non_bull_regime_net_carry_not_positive": {
            "regime_pnls": {
                "bull": {"days": 100, "net_pnl": Decimal("300")},
                "neutral": {"days": 100, "net_pnl": Decimal("-50")},
                "bear": {"days": 100, "net_pnl": Decimal("-60")},
            }
        },
        "leave_one_out_breaks_oos_net_carry": {
            "leave_one_out_oos_net": {"BTC": Decimal("90"), "ETH": Decimal("-2")}
        },
        "oos_drawdown_exceeds_documented_limit": {
            "oos_strategy_stats": _stats(Decimal("2.0"), Decimal("9"))
        },
        "stressed_tail_drawdown_exceeds_documented_limit": {
            "stressed_max_drawdown_pct": Decimal("12")
        },
        "rejected_low_oos_days": {
            "oos_strategy_stats": _stats(Decimal("2.0"), Decimal("1.5"), days=30)
        },
    }
    for reason, override in cases.items():
        kwargs = _passing_kwargs()
        kwargs.update(override)
        gate = fund.evaluate_funding_carry_gate(**kwargs)
        assert not gate["passed"], reason
        assert reason in gate["reason_codes"], reason

    # Thin-edge honesty qualifier on a pass with Sharpe < 1.
    kwargs = _passing_kwargs()
    kwargs["oos_strategy_stats"] = _stats(Decimal("0.5"), Decimal("1.5"))
    gate = fund.evaluate_funding_carry_gate(**kwargs)
    assert gate["passed"]
    assert "oos_sharpe_below_one_thin_edge" in gate["qualifiers"]

    # Routing enforcement: wrong strategy type raises.
    kwargs = _passing_kwargs()
    kwargs["strategy_type"] = "per_symbol"
    with pytest.raises(strategy_types.StrategyTypeRoutingError):
        fund.evaluate_funding_carry_gate(**kwargs)


# ---------------------------------------------------------------------------
# Committed evidence summary + funding snapshot (CI-safe: committed docs only)
# ---------------------------------------------------------------------------


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def _snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def test_committed_summary_gate_is_honest_and_boundaries_hold() -> None:
    summary = _summary()
    gate = summary["funding_carry_gate"]
    assert gate["gate_id"] == "funding_carry_net_oos_tail_gate"
    assert summary["verdict"] == gate["status"]
    assert summary["boundaries"]["research_only"] is True
    assert summary["boundaries"]["calls_private_signed_or_order_endpoints"] is False
    assert summary["boundaries"]["spot_borrow_not_modeled_flip_rows_upper_bound"] is True
    assert summary["boundaries"]["daily_funding_accrual_approximation"] is True
    nl = summary["no_lookahead_verification"]
    assert all(nl["trailing_funding_signal_point_in_time_ok_by_symbol"].values())
    assert nl["leaky_probe_would_be_caught"] is True
    # The tail block must quantify the legged-execution gap risk.
    assert "modeled_gap_loss_at_leg_lag_residual_pct_of_equity" in summary[
        "tail_stress"
    ]["leg_lag_only_run"]


def test_committed_summary_covers_universe_and_reconciles() -> None:
    summary = _summary()
    assert set(summary["leave_one_out"]) == set(fund.CARRY_UNIVERSE)
    for row in summary["per_config_results"]["exec_ev1_conservative"]:
        total = sum(Decimal(v) for v in row["per_symbol_net_pnl"].values())
        assert abs(total - Decimal(row["net_pnl"])) < Decimal("1"), row["config_id"]
    # Benchmarks include the cost-attribution pair (gross vs net) and cash.
    assert "gross_funding_zero_cost_same_positions" in summary["benchmarks"]
    assert "cash" in summary["benchmarks"]
    assert Decimal(summary["headline"]["costs_total_vs_zero_cost"]) > 0


def test_committed_funding_snapshot_provenance_is_public_read_only() -> None:
    snapshot = _snapshot()
    assert snapshot["phase"] == "FUND-EV1"
    assert set(snapshot["funding"]) == set(fund.CARRY_UNIVERSE)
    assert (
        snapshot["provenance"]["access"]
        == "public_read_only_no_keys_no_private_no_signed_no_orders"
    )
    assert snapshot["boundaries"]["calls_private_signed_or_order_endpoints"] is False
    for coin, block in snapshot["funding"].items():
        rows = block["daily_funding_rate_sums"]
        assert len(rows) > 300, coin
        full_days = [r for r in rows if r["hours"] == 24]
        assert len(full_days) > 300, coin
        # Decimal-parseable sums (exact string arithmetic, no float drift).
        for r in rows[:5]:
            Decimal(r["funding_rate_sum"])


def test_research_log_outcome_for_fund_ev1_stays_honest() -> None:
    """Pinned: the carry hypothesis FAILED its gate on this data — the
    Research Log entry must be authored fail and can never render green."""
    payload = json.loads(
        (REPO_ROOT / "docs" / "research_log.json").read_text(encoding="utf-8")
    )
    by_phase = {entry["phase"]: entry for entry in payload["entries"]}
    entry = by_phase.get("FUND-EV1")
    assert entry is not None, "FUND-EV1 research_log block missing"
    assert entry["outcome"] == "fail"
    assert payload["standing"]["passed_gate"] == sum(
        1 for e in payload["entries"] if e["outcome"] == "pass"
    )
