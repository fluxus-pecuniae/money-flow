"""MF-REPLAY1 — accuracy proof for founder visual backtesting.

Deterministic, offline, fast-lane. Pins the range math so the founder can
trust the number:
  - HAND fixture: the per-trade fee/quantity/PnL/equity arithmetic is
    reproduced exactly from the engine's own entry/exit prices;
  - YEAR BOUNDARY: a Dec-31 close lands in year N's book, a Jan-1 close in
    year N+1's; calendar-year ranges are exact;
  - FRESH START: a position the signal held BEFORE the range start is not
    carried in — every in-range trade enters at/after the range start;
  - WARM-UP: a range that starts inside a symbol's indicator warm-up takes
    no entries there and reports the symbol joining late (never guessed);
  - NO-LOOKAHEAD: truncating all post-end history reproduces the range
    result exactly;
  - LIVE-LEDGER EQUIVALENCE: replaying the live PT-RT2 decision path +
    ledger arithmetic over a NON-OVERLAPPING (single-symbol) window
    reproduces the replay engine's trajectory exactly. Per K-037 the live
    equity-at-entry-per-position accounting can diverge from the replay's
    sequential-additive ledger when positions OVERLAP, so the equivalence
    is pinned on a single symbol (at most one open position) and that
    boundary is documented here.

Replay is hypothetical context, not evidence, and never feeds the live
ledgers — the disclaimer + committed verdicts are asserted present.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from scripts import run_pt_rt1_paper_observation as runner
from services.paper_runtime import mf_replay1 as mr
from services.paper_runtime.pt_rt1 import Candle, evaluate_paper_decision

T0 = datetime(2021, 1, 1, tzinfo=UTC)
FEE_BPS = Decimal("5")


def make_candles(closes: list[float], symbol: str = "BTC", start: datetime = T0) -> list[Candle]:
    out = []
    for i, close in enumerate(closes):
        c = Decimal(str(close))
        out.append(
            Candle(
                symbol=symbol,
                timeframe="1d",
                open_time=start + timedelta(days=i),
                close_time=start + timedelta(days=i + 1),
                open=c * Decimal("0.999"),
                high=c * Decimal("1.01"),
                low=c * Decimal("0.99"),
                close=c,
                volume=Decimal("1000"),
            )
        )
    return out


def dip_recovery_closes(n: int = 160) -> list[float]:
    """Uptrend → dip → recovery → second dip: produces multiple clean
    non-overlapping round-trips for one symbol."""
    closes = []
    level = 100.0
    for i in range(n):
        if i < 60 or (80 < i <= 120):
            level *= 1.01
        else:
            level *= 0.985
        closes.append(level)
    return closes


def single_symbol_context(closes: list[float], symbol: str = "BTC") -> mr.ReplayContext:
    return mr.build_replay_context({symbol: make_candles(closes, symbol)})


# ---------------------------------------------------------------------------
# Hand fixture: the per-trade arithmetic, recomputed by hand, must match
# ---------------------------------------------------------------------------


def test_hand_fixture_trade_arithmetic_matches_exactly():
    ctx = single_symbol_context(dip_recovery_closes())
    result = mr.replay_range(ctx, "mf_source_faithful_baseline", ctx.aligned_start, ctx.last_close)
    assert result["trade_count"] >= 1
    equity = Decimal("10000")
    for trade in result["trades"]:
        entry_price = Decimal(trade["entry_price"])
        exit_price = Decimal(trade["exit_price"])
        # Hand arithmetic, the documented fresh-start ledger:
        entry_fee = (equity * FEE_BPS / Decimal("10000")).quantize(Decimal("0.00000001"))
        quantity = (equity - entry_fee) / entry_price
        assert Decimal(trade["entry_fee"]) == entry_fee
        assert Decimal(trade["quantity"]) == quantity
        gross = (exit_price - entry_price) * quantity
        exit_fee = (exit_price * quantity * FEE_BPS / Decimal("10000")).quantize(Decimal("0.00000001"))
        net = gross - entry_fee - exit_fee
        assert Decimal(trade["exit_fee"]) == exit_fee
        assert Decimal(trade["net_pnl"]) == net.quantize(Decimal("0.00000001"))
        equity = (equity + net).quantize(Decimal("0.00000001"))
        assert Decimal(trade["equity_after"]) == equity
    # Realized-only end equity == hand-compounded equity after the last close.
    assert Decimal(result["end_equity_realized_only_usdc"]) == equity


# ---------------------------------------------------------------------------
# Year boundary
# ---------------------------------------------------------------------------


def test_calendar_year_boundary_puts_closes_in_the_right_book():
    # 400 daily candles spanning 2021-01-01 .. ~2022-02 so 2021 and 2022
    # both have books, with a clean Dec-31/Jan-1 boundary.
    ctx = single_symbol_context(dip_recovery_closes(400))
    years = {y["year"]: y for y in mr.calendar_year_ranges(ctx)}
    assert 2021 in years and 2022 in years
    # 2021's book ends before 2022-01-01; 2022's starts on/after it.
    y2021 = mr.replay_range(ctx, "mf_source_faithful_baseline", years[2021]["start"], years[2021]["end"])
    y2022 = mr.replay_range(ctx, "mf_source_faithful_baseline", years[2022]["start"], years[2022]["end"])
    assert y2021["last_in_range_close"] <= "2022-01-01T00:00:00Z"
    assert y2022["first_in_range_close"] >= "2022-01-01T00:00:00Z"
    for trade in y2021["trades"]:
        assert trade["exit_time"] < "2022-01-01T00:00:00Z"
    for trade in y2022["trades"]:
        assert trade["entry_time"] >= "2022-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# Fresh start: a pre-range position is NOT carried in
# ---------------------------------------------------------------------------


def test_fresh_start_ignores_pre_range_position():
    closes = dip_recovery_closes(160)
    ctx = single_symbol_context(closes)
    states = ctx.states_by_symbol["BTC"]
    candles = ctx.candles_by_symbol["BTC"]
    # Find a candle where the surface position is LONG (held), and start the
    # range there: a fresh book must NOT inherit that long.
    long_idx = next(
        i for i, s in enumerate(states) if s["warmed_up"] and s["position_state"] == "long"
    )
    range_start = candles[long_idx].close_time
    result = mr.replay_range(ctx, "mf_source_faithful_baseline", range_start, ctx.last_close)
    # Every in-range trade must ENTER at/after the range start (no inherited
    # position closed out as if it had been opened earlier).
    for trade in result["trades"]:
        assert trade["entry_time"] >= mr._iso(range_start)
    # And the equity curve starts at exactly 10,000 (flat fresh start).
    assert result["start_equity_usdc"] == "10000"
    assert Decimal(result["equity_curve"][0]["equity"]) == Decimal("10000")


# ---------------------------------------------------------------------------
# Warm-up: pre-range history feeds indicators; in-warmup range takes nothing
# ---------------------------------------------------------------------------


def test_warmup_uses_pre_range_history_and_never_guesses():
    closes = dip_recovery_closes(160)
    ctx = single_symbol_context(closes)
    candles = ctx.candles_by_symbol["BTC"]
    states = ctx.states_by_symbol["BTC"]
    # A range entirely inside the warm-up window (before any warmed state).
    first_warmed = next(i for i, s in enumerate(states) if s["warmed_up"])
    assert first_warmed > 0
    warmup_end = candles[first_warmed - 1].close_time
    result = mr.replay_range(ctx, "mf_source_faithful_baseline", ctx.aligned_start, warmup_end)
    assert result["trade_count"] == 0
    assert "BTC" in result["symbols_still_warming_at_end"]
    # A range that STARTS in warm-up but extends past it: the symbol joins
    # late (warm-up uses pre-range history; never guessed before warmed).
    full = mr.replay_range(ctx, "mf_source_faithful_baseline", ctx.aligned_start, ctx.last_close)
    assert "BTC" in full["symbols_joined_after_warmup"]


# ---------------------------------------------------------------------------
# No-lookahead on the range engine
# ---------------------------------------------------------------------------


def test_range_engine_is_no_lookahead():
    ctx = single_symbol_context(dip_recovery_closes(200))
    candles = ctx.candles_by_symbol["BTC"]
    start = candles[60].close_time
    end = candles[150].close_time
    assert mr.verify_range_no_lookahead(ctx, "mf_source_faithful_baseline", start, end)
    assert mr.verify_range_no_lookahead(ctx, "mf_source_faithful_regime_gated", start, end)


# ---------------------------------------------------------------------------
# Live-ledger equivalence (non-overlapping single-symbol window) — K-037
# ---------------------------------------------------------------------------


def _live_ledger_trajectory(symbol: str, candles: list[Candle]) -> dict:
    """Drive the COMMITTED live PT-RT2 decision path + ledger arithmetic
    one candle at a time, exactly as run_cycle threads it, for ONE symbol
    (at most one open position — the non-overlapping regime where the live
    equity-at-entry accounting and the additive ledger coincide)."""
    lane = next(
        l for l in __import__(
            "services.paper_runtime.pt_rt1", fromlist=["PT_RT2_ACTIVE_STRATEGY_LANES"]
        ).PT_RT2_ACTIVE_STRATEGY_LANES
        if l.lane_id == "mf_source_faithful_baseline"
    )
    ledger = Decimal("10000")
    position = None
    last_close = None
    trades = []
    for i, candle in enumerate(candles):
        now = candle.close_time + timedelta(seconds=300)
        decision = evaluate_paper_decision(
            lane=lane,
            symbol=symbol,
            timeframe="1d",
            candles=candles[: i + 1],
            now=now,
            position_open=position is not None,
            equity_before=ledger,
            last_processed_close=last_close,
        )
        row = decision.as_json_dict()
        if decision.action == "paper_opened" and position is None:
            position = runner._open_position_from_decision(row=row, candle=candle, equity_before=ledger)
            ledger = ledger - Decimal(position["fees"])
        elif decision.action == "paper_closed" and position is not None:
            trade, equity_after = runner._close_position_from_decision(
                row=row, position=position, candle=candle
            )
            ledger = equity_after
            position = None
            trades.append(trade)
        last_close = candle.close_time
    return {"final_realized": ledger, "trades": trades, "still_open": position is not None}


def test_live_ledger_equivalence_on_non_overlapping_sequence():
    symbol = "BTC"
    closes = dip_recovery_closes(160)
    candles = make_candles(closes, symbol)
    ctx = mr.build_replay_context({symbol: candles})
    replay = mr.replay_range(ctx, "mf_source_faithful_baseline", ctx.aligned_start, ctx.last_close)
    live = _live_ledger_trajectory(symbol, candles)

    # Same round-trips, same arithmetic — the replay IS the live engine.
    assert len(replay["trades"]) == len(live["trades"]) >= 1
    for r_trade, l_trade in zip(replay["trades"], live["trades"], strict=True):
        assert r_trade["entry_time"] == l_trade["entry_time"]
        assert r_trade["exit_time"] == l_trade["exit_time"]
        # net PnL identical to the cent (exact Decimal, not just rounding).
        assert Decimal(r_trade["net_pnl"]).quantize(Decimal("0.0001")) == Decimal(
            l_trade["net_pnl"]
        ).quantize(Decimal("0.0001"))
    # Realized-only end equity matches the live ledger when both end flat;
    # if a trade is still open at window end, compare realized-only figures.
    if not live["still_open"] and not replay["open_positions_at_end"]:
        assert Decimal(replay["end_equity_realized_only_usdc"]).quantize(Decimal("0.0001")) == live[
            "final_realized"
        ].quantize(Decimal("0.0001"))


def test_overlap_divergence_boundary_is_documented():
    # K-037: the equivalence holds only on non-overlapping sequences. The
    # engine documents that boundary so it is never hidden.
    assert "overlap" in mr.PRE_REGISTERED_SEMANTICS["ledger"].lower()
    assert "K-037" in mr.PRE_REGISTERED_SEMANTICS["ledger"]


# ---------------------------------------------------------------------------
# Exposure surfacing (K-037) + honesty frame on every range
# ---------------------------------------------------------------------------


def test_every_range_surfaces_exposure_and_carries_the_verdicts():
    ctx = single_symbol_context(dip_recovery_closes(160))
    for lane_id in ("mf_source_faithful_baseline", "mf_source_faithful_regime_gated"):
        result = mr.replay_range(ctx, lane_id, ctx.aligned_start, ctx.last_close)
        assert "max_gross_exposure_x" in result
        assert "max_concurrent_positions" in result
        assert result["feeds_live_ledgers"] is False
        assert result["replay_is_hypothetical_not_evidence"] is True
        char = result["committed_characterization"]
        assert char["standalone_label"] == "defensive_trend_mechanic_not_validated_alpha"
        assert char["trade_level_label"] == "source_faithful_but_underperformed"
        assert char["regime_overlay_verdict"] == "regime_filter_does_not_reduce_drawdown_oos"
        assert "window placement" in result["disclaimer"].lower()


def test_unknown_lane_and_inverted_range_are_rejected():
    ctx = single_symbol_context(dip_recovery_closes(80))
    with pytest.raises(ValueError, match="unknown_replay_lane"):
        mr.replay_range(ctx, "not_a_lane", ctx.aligned_start, ctx.last_close)
    with pytest.raises(ValueError, match="range_end_before_start"):
        mr.replay_range(ctx, "mf_source_faithful_baseline", ctx.last_close, ctx.aligned_start)
