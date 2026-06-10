"""EXEC-EV1 depth-aware friction model — deterministic, offline tests.

No network, no runtime, no DB. Asserts the model's documented properties:
  - market impact scales with size and inversely with the liquidity proxy
  - impact follows the square-root participation law
  - spread (per tier) and fill-probability terms are applied
  - EXEC-EV1 total friction >= the SV2.3 parent terms (structural reason that
    EXEC-EV1 net PnL <= SV2.3 net PnL), and the end-to-end replay confirms
    net PnL <= SV2.3 on a synthetic fixture that produces real trades
  - the late-entry / entry-timing metric is monotonic in lateness
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from decimal import Decimal

from scripts.run_exec_ev1_execution_quality import replay_exec_ev1_strategy
from scripts.run_sv22_hyperliquid_research_refresh import indicators, iso_utc
from scripts.run_sv23_realistic_backtest import (
    EXECUTION_SCENARIOS,
    replay_realistic_strategy,
    stage_rows_for,
)
from services.execution_quality.exec_ev1 import (
    DEPTH_AWARE_SCENARIOS,
    candle_dollar_volume,
    depth_aware_execution_price,
    entry_timing_cost_bps,
    fill_friction_bps,
    half_spread_bps,
    market_impact_bps,
    participation_rate,
    scenario_by_id,
    symbol_tier,
    unfilled_chase_bps,
)

BASE_SCENARIO = scenario_by_id("exec_ev1_base")


# ---------------------------------------------------------------------------
# Market impact: size + liquidity scaling, sqrt law
# ---------------------------------------------------------------------------


def test_market_impact_scales_with_size() -> None:
    proxy = Decimal("1000000")
    coef = Decimal("20")
    small = market_impact_bps(Decimal("1000"), proxy, coef)
    large = market_impact_bps(Decimal("100000"), proxy, coef)
    assert large > small > 0


def test_market_impact_inverse_with_liquidity() -> None:
    notional = Decimal("50000")
    coef = Decimal("20")
    thin = market_impact_bps(notional, Decimal("100000"), coef)
    deep = market_impact_bps(notional, Decimal("100000000"), coef)
    assert thin > deep > 0


def test_market_impact_follows_sqrt_law() -> None:
    coef = Decimal("40")
    # participation == 1.0 → impact == coefficient
    full = market_impact_bps(Decimal("1000"), Decimal("1000"), coef)
    assert full == coef
    # participation == 0.25 → impact == coefficient * 0.5 (sqrt(0.25) = 0.5)
    quarter = market_impact_bps(Decimal("250"), Decimal("1000"), coef)
    assert abs(quarter - coef * Decimal("0.5")) < Decimal("0.01")


def test_participation_rate_clamped() -> None:
    # Order larger than interval volume clamps to full participation.
    assert participation_rate(Decimal("2000"), Decimal("1000")) == Decimal("1")
    # Zero / non-positive liquidity is worst case (=1).
    assert participation_rate(Decimal("1000"), Decimal("0")) == Decimal("1")
    # Zero notional is no participation.
    assert participation_rate(Decimal("0"), Decimal("1000")) == Decimal("0")


# ---------------------------------------------------------------------------
# Spread per tier + fill probability
# ---------------------------------------------------------------------------


def test_spread_tiers_ordered_major_tight_to_mid_wide() -> None:
    assert symbol_tier("BTC") == "major_perp"
    assert symbol_tier("SOL") == "large_perp"
    assert symbol_tier("HYPE") == "mid_alt_perp"
    assert half_spread_bps("BTC") < half_spread_bps("SOL") < half_spread_bps("HYPE")


def test_unknown_symbol_defaults_to_widest_tier() -> None:
    assert symbol_tier("SOMETHINGNEW") == "mid_alt_perp"
    assert half_spread_bps("SOMETHINGNEW") == half_spread_bps("HYPE")


def test_fill_probability_chase_applied() -> None:
    # fill_probability < 1 → positive chase cost; == 1 → zero.
    assert unfilled_chase_bps(Decimal("0.95"), Decimal("120")) == Decimal("6")
    assert unfilled_chase_bps(Decimal("1.00"), Decimal("120")) == Decimal("0")


def test_fill_friction_includes_spread_and_is_positive() -> None:
    breakdown = fill_friction_bps(
        scenario=BASE_SCENARIO,
        symbol="BTC",
        notional=Decimal("10000"),
        liquidity_proxy=Decimal("50000000"),
        adverse_gap=Decimal("0"),
    )
    assert breakdown.spread_bps > 0
    assert breakdown.total_bps >= breakdown.spread_bps + breakdown.slippage_bps
    assert breakdown.total_bps > 0


def test_depth_aware_execution_price_buy_costs_more_sell_less() -> None:
    raw = Decimal("100")
    buy = depth_aware_execution_price(raw_price=raw, side="buy", friction_total_bps=Decimal("100"))
    sell = depth_aware_execution_price(
        raw_price=raw, side="sell", friction_total_bps=Decimal("100")
    )
    assert buy > raw > sell


# ---------------------------------------------------------------------------
# Structural guarantee: EXEC-EV1 friction >= SV2.3 parent terms
# ---------------------------------------------------------------------------


def test_exec_ev1_friction_ge_sv23_parent_terms() -> None:
    sv23_by_id = {s.scenario_id: s for s in EXECUTION_SCENARIOS}
    for scenario in DEPTH_AWARE_SCENARIOS:
        parent = sv23_by_id[scenario.sv23_parent_scenario]
        breakdown = fill_friction_bps(
            scenario=scenario,
            symbol="BTC",
            notional=Decimal("10000"),
            liquidity_proxy=Decimal("50000000"),
            adverse_gap=Decimal("100"),
        )
        # EXEC-EV1 keeps the parent slippage + adverse-gap and only adds more.
        parent_terms = parent.slippage_bps + parent.adverse_gap_penalty_bps
        assert breakdown.total_bps >= parent_terms


# ---------------------------------------------------------------------------
# Synthetic fixture: end-to-end EXEC-EV1 net PnL <= SV2.3 net PnL
# ---------------------------------------------------------------------------


def _synthetic_candles(n: int = 320) -> list[dict]:
    """Deterministic rising series with mild oscillation that triggers baseline
    entries (ema5 > ema10 > sma20, constructive RSI, pullback/continuation)."""
    candles: list[dict] = []
    price = 100.0
    base_ts = 1_700_000_000  # fixed epoch seconds; deterministic
    day = 86_400
    for i in range(n):
        drift = 1.0 + 0.004  # gentle uptrend
        osc = 1.0 + 0.015 * math.sin(i / 6.0)  # mild pullbacks
        close = price * drift * osc
        open_ = price
        high = max(open_, close) * 1.005
        low = min(open_, close) * 0.995
        open_ts = base_ts + i * day
        close_ts = open_ts + day
        candles.append(
            {
                "symbol": "BTC",
                "timeframe": "1d",
                "open": f"{open_:.4f}",
                "high": f"{high:.4f}",
                "low": f"{low:.4f}",
                "close": f"{close:.4f}",
                "open_time": iso_utc(datetime.fromtimestamp(open_ts, tz=UTC)),
                "close_time": iso_utc(datetime.fromtimestamp(close_ts, tz=UTC)),
                "volume": "5000",
            }
        )
        price = close
    return candles


def test_exec_ev1_net_pnl_le_sv23_on_fixture() -> None:
    candles = _synthetic_candles()
    indicator_rows = indicators(candles)
    stages = stage_rows_for(candles, indicator_rows)
    strategy_id = "money_flow_v1_2_baseline"

    sv23_by_id = {s.scenario_id: s for s in EXECUTION_SCENARIOS}
    produced_trades = False
    for scenario in DEPTH_AWARE_SCENARIOS:
        parent = sv23_by_id[scenario.sv23_parent_scenario]
        sv23 = replay_realistic_strategy(
            strategy_id=strategy_id,
            symbol="BTC",
            timeframe="1d",
            candles=candles,
            scenario=parent,
            indicator_rows=indicator_rows,
            stages=stages,
        )
        exec_ev1 = replay_exec_ev1_strategy(
            strategy_id=strategy_id,
            symbol="BTC",
            timeframe="1d",
            candles=candles,
            scenario=scenario,
            indicator_rows=indicator_rows,
            stages=stages,
        )
        sv23_net = Decimal(sv23["summary"]["net_pnl"])
        exec_net = Decimal(exec_ev1["summary"]["net_pnl"])
        # Friction can only subtract: EXEC-EV1 net PnL must not exceed SV2.3's.
        assert exec_net <= sv23_net, f"{scenario.scenario_id}: {exec_net} > {sv23_net}"
        if exec_ev1["summary"]["trade_count"] > 0:
            produced_trades = True
    # The fixture must actually exercise the trade path, else the test is hollow.
    assert produced_trades, "synthetic fixture produced no trades — test is not exercising fills"


# ---------------------------------------------------------------------------
# Late-entry / entry-timing metric monotonic in lateness
# ---------------------------------------------------------------------------


def test_entry_timing_cost_monotonic_in_lateness_for_buy() -> None:
    # Strictly rising opens → entering later is strictly more expensive for a buy.
    candles = [
        {
            "open": f"{100 + i:.4f}",
            "high": f"{100 + i + 1:.4f}",
            "low": f"{100 + i - 1:.4f}",
            "close": f"{100 + i:.4f}",
            "volume": "1000",
        }
        for i in range(10)
    ]
    signal_index = 2
    c0 = entry_timing_cost_bps(candles, signal_index, 0, "buy")
    c1 = entry_timing_cost_bps(candles, signal_index, 1, "buy")
    c2 = entry_timing_cost_bps(candles, signal_index, 2, "buy")
    assert c0 is not None and c1 is not None and c2 is not None
    assert c0 < c1 < c2


def test_entry_timing_cost_none_past_end() -> None:
    candles = [{"open": "100", "high": "101", "low": "99", "close": "100", "volume": "1"}]
    assert entry_timing_cost_bps(candles, 0, 0, "buy") is None


# ---------------------------------------------------------------------------
# Liquidity proxy
# ---------------------------------------------------------------------------


def test_candle_dollar_volume_uses_typical_price() -> None:
    candle = {"high": "110", "low": "90", "close": "100", "volume": "10"}
    # typical = (110+90+100)/3 = 100; dollar volume = 10 * 100 = 1000
    assert candle_dollar_volume(candle) == Decimal("1000")
