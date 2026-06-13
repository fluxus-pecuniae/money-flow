"""MF-REPLAY1 — founder visual backtesting: range-accurate replay of the
PT-RT2 lanes over the full DATA1 history.

HYPOTHETICAL REPLAY CONTEXT FOR FOUNDER JUDGMENT — NOT NEW EVIDENCE, NOT A
VALIDATED STRATEGY, AND IT NEVER FEEDS THE LIVE LEDGERS. The committed
characterization stands and travels with every range result:
`defensive_trend_mechanic_not_validated_alpha` standalone; trade-level
`source_faithful_but_underperformed`; the regime overlay carries REGIME2's
honest-FAIL verdict (informational risk context, not a validated control).
A green range is WINDOW PLACEMENT, not alpha — the project committed exactly
this lesson (TSMOM-EV1's OOS window was absolutely negative;
MONEYFLOW-SIGNAL1's was positive; same mechanic, different window).

One code path: the replay consumes the committed MONEYFLOW-SIGNAL1 surface
(`signal_states`) and the PT-RT2 lane semantics — never a parallel signal
calculator. Decision parity with `pt_rt1.evaluate_paper_decision` and ledger
parity with the live runtime's open/close arithmetic are test-pinned.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, Mapping, Sequence

from services.paper_runtime.pt_rt1 import (
    PT_RT2_ACTIVE_STRATEGY_LANE_IDS,
    PT_RT2_CHARACTERIZATION_LABEL,
    PT_RT2_REGIME_COMMITTED_VERDICT,
    PT_RT2_REGIME_COMMITTED_VERDICT_NOTE,
    PT_RT2_REGIME_OVERLAY_LABEL,
    PT_RT2_TRADE_LEVEL_LABEL,
    PT_RT2_UNIVERSE_SYMBOLS,
    Candle,
    core_candles_for_mf_signal1,
    parse_utc_timestamp,
)

PHASE = "MF-REPLAY1"

# The live paper ledger's friction (drift-pinned by test against the runtime
# arithmetic): 5 bps per side, fills at the signal candle's close.
FEE_BPS = Decimal("5")
START_EQUITY = Decimal("10000")

REPLAY_DISCLAIMER = (
    "HYPOTHETICAL REPLAY, NOT EVIDENCE: range replay of the committed PT-RT2 "
    "lane semantics for founder judgment only - not a validated strategy, "
    "not new evidence, and it never feeds or backfills the live synthetic "
    "ledgers. A green range is window placement, not alpha (TSMOM-EV1's OOS "
    "window was absolutely negative; MONEYFLOW-SIGNAL1's was positive; same "
    "defensive trend mechanic). Committed labels travel: "
    "defensive_trend_mechanic_not_validated_alpha (standalone); "
    "source_faithful_but_underperformed (trade level); the regime overlay is "
    "informational risk context, not a validated control. Signal/replay only "
    "- no orders, no live, no approval surface; does not predict or "
    "guarantee profit."
)

# Pre-registered BEFORE the UI was wired (Must 2). These semantics are the
# contract the accuracy-proof tests pin; changing any of them is a new
# founder decision, not a tweak.
PRE_REGISTERED_SEMANTICS: dict[str, str] = {
    "fresh_start": (
        "the range book starts FLAT with 10,000 USDC at the range's first "
        "aligned closed candle and takes only entries that fire INSIDE the "
        "range; a position the signal held before the range start is ignored "
        "until its next fresh entry (this answers: 'if I had started running "
        "it on that date')"
    ),
    "warm_up": (
        "indicator warm-up uses PRE-RANGE history (warm-up is about data; "
        "fresh-start is about position state); if the range start predates a "
        "symbol's data + warm-up, that symbol joins when its surface state "
        "is warmed and the output says so - never guessed"
    ),
    "closed_candles_no_lookahead": (
        "closed daily candles only; the range result is provably computable "
        "from candles up to the range end (truncation probe test-pinned)"
    ),
    "fills_and_fees": (
        "entries and exits fill at the SIGNAL candle's close with 5 bps per "
        "side - the live paper ledger's exact arithmetic (equivalence "
        "test-pinned); quantity = (equity - entry_fee) / fill_price"
    ),
    "ledger": (
        "sequential-additive full-equity lane ledger: each open is sized at "
        "the lane's CURRENT equity; each close adds its net PnL to the "
        "lane's CURRENT equity. NOTE the live runtime stores equity at entry "
        "per position and can diverge from additive accounting when "
        "positions OVERLAP across symbols (recorded in KNOWN_ISSUES K-037); "
        "the replay uses the additive ledger because it is the arithmetic "
        "that answers 'where did 10,000 USDC end'"
    ),
    "leverage_warning": (
        "full-equity sizing PER SYMBOL POSITION (the committed live-lane "
        "accounting) means concurrent positions LEVER the book - up to 7x "
        "gross with all majors long at once; range returns AND drawdowns "
        "include that leverage (the all-time book draws down ~99% in the "
        "2022 bear); max_gross_exposure_x and max_concurrent_positions are "
        "reported on every range so the founder sees it"
    ),
    "end_equity": (
        "end equity is mark-to-market at the range's last closed candle: "
        "realized equity plus open positions valued at their last in-range "
        "close (open positions are reported open, never force-closed); the "
        "realized-only figure is also reported"
    ),
    "calendar_years": (
        "a calendar-year book runs from the first aligned close on/after "
        "Jan 1 00:00Z to the last close before the next Jan 1; years without "
        "full coverage are labeled partial"
    ),
    "regime_gate": (
        "the gated lane consults the committed regime filter point-in-time "
        "over the same history (REGIME2 pinned config); before the gate's "
        "first computable state the gated lane cannot enter (flagged, never "
        "guessed) - exposure = signal AND risk_on, the characterization's "
        "gated-twin semantics"
    ),
}

COMMITTED_CHARACTERIZATION = {
    "standalone_label": PT_RT2_CHARACTERIZATION_LABEL,
    "trade_level_label": PT_RT2_TRADE_LEVEL_LABEL,
    "regime_overlay_verdict": PT_RT2_REGIME_COMMITTED_VERDICT,
    "regime_overlay_verdict_note": PT_RT2_REGIME_COMMITTED_VERDICT_NOTE,
    "regime_overlay_label": PT_RT2_REGIME_OVERLAY_LABEL,
    "window_placement_note": (
        "a green range is window placement, not alpha: TSMOM-EV1's OOS "
        "window was absolutely negative, MONEYFLOW-SIGNAL1's was positive - "
        "same defensive trend mechanic, different window"
    ),
}


@dataclass
class ReplayContext:
    """Everything computed ONCE from full history (point-in-time safe)."""

    symbols: tuple[str, ...]
    candles_by_symbol: dict[str, list[Candle]]
    states_by_symbol: dict[str, list[dict[str, Any]]]
    regime_gate: Any | None
    regime_error: str | None = None

    @property
    def aligned_start(self) -> datetime:
        return max(c[0].close_time for c in self.candles_by_symbol.values() if c)

    @property
    def last_close(self) -> datetime:
        return max(c[-1].close_time for c in self.candles_by_symbol.values() if c)


@dataclass
class _OpenPosition:
    symbol: str
    entry_time: datetime
    entry_price: Decimal
    quantity: Decimal
    entry_fee: Decimal
    entry_equity: Decimal
    entry_reasons: tuple[str, ...] = field(default_factory=tuple)


def replay_candles_from_data1(
    summary_path: Any = None, *, symbols: Sequence[str] = PT_RT2_UNIVERSE_SYMBOLS
) -> dict[str, list[Candle]]:
    """DATA1 Binance perp daily candles -> the runtime Candle shape the
    PT-RT2 lanes consume (closed candles keyed by close time)."""
    from services.market_data.data1_multi_venue import load_data1_dataset

    ds = load_data1_dataset(summary_path) if summary_path is not None else load_data1_dataset()
    out: dict[str, list[Candle]] = {}
    for symbol in symbols:
        series = ds.series("binance", symbol, "perp_1d")
        if series.status != "ok":
            raise RuntimeError(f"data1_series_not_ok:binance:{symbol}:{series.status}")
        candles = []
        for row in series.rows:
            close_time = parse_utc_timestamp(str(row["close_time"]))
            candles.append(
                Candle(
                    symbol=symbol,
                    timeframe="1d",
                    open_time=close_time - timedelta(days=1),
                    close_time=close_time,
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=Decimal(str(row["volume_base"])),
                )
            )
        out[symbol] = candles
    return out


def build_replay_context(candles_by_symbol: Mapping[str, Sequence[Candle]]) -> ReplayContext:
    """Compute the surface states (once per symbol, full history — the
    surface is point-in-time verified) and the committed regime gate."""
    from services.paper_runtime.pt_rt1 import _mf_signal1_module

    ms = _mf_signal1_module()
    symbols = tuple(sorted(candles_by_symbol))
    states: dict[str, list[dict[str, Any]]] = {}
    for symbol in symbols:
        states[symbol] = ms.signal_states(core_candles_for_mf_signal1(list(candles_by_symbol[symbol])))

    regime_gate = None
    regime_error: str | None = None
    try:
        from services.strategy_validation.goal_strat1 import Candle as GCandle
        from services.strategy_validation.goal_strat1 import Dataset
        from services.strategy_validation.strategy_types import resolve_regime_filter

        datasets = []
        for symbol in symbols:
            datasets.append(
                Dataset(
                    symbol=symbol,
                    timeframe="1d",
                    source_path="mf_replay1_data1_binance_perp_1d",
                    source_provenance="data1_committed_snapshot",
                    canonical_evidence_status="replay_context_not_canonical_evidence",
                    candles=tuple(
                        GCandle(
                            symbol=symbol,
                            timeframe="1d",
                            timestamp=c.close_time,
                            open=c.open,
                            high=c.high,
                            low=c.low,
                            close=c.close,
                            volume=c.volume,
                            source_path="mf_replay1",
                        )
                        for c in candles_by_symbol[symbol]
                    ),
                )
            )
        regime_gate = resolve_regime_filter()(datasets)
    except Exception as exc:  # explicit, never silent
        regime_error = f"regime_gate_build_failed:{type(exc).__name__}:{exc}"

    return ReplayContext(
        symbols=symbols,
        candles_by_symbol={s: list(candles_by_symbol[s]) for s in symbols},
        states_by_symbol=states,
        regime_gate=regime_gate,
        regime_error=regime_error,
    )


def _risk_on_at(context: ReplayContext, as_of: datetime) -> bool | None:
    """Point-in-time regime state; None = not computable (warm-up/error)."""
    if context.regime_gate is None:
        return None
    try:
        return bool(context.regime_gate.state_at(as_of)["risk_on"])
    except Exception:
        return None  # before the gate's first state: never guessed


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.00000001"))


def replay_range(
    context: ReplayContext,
    lane_id: str,
    start: datetime | str,
    end: datetime | str,
) -> dict[str, Any]:
    """The range book under the pre-registered semantics. Deterministic
    Decimal arithmetic; auditable per-symbol trade list; every output
    carries the disclaimer + committed characterization."""
    if lane_id not in PT_RT2_ACTIVE_STRATEGY_LANE_IDS:
        raise ValueError(f"unknown_replay_lane:{lane_id}")
    gated = lane_id == "mf_source_faithful_regime_gated"
    start_at = parse_utc_timestamp(start)
    end_at = parse_utc_timestamp(end)
    if end_at < start_at:
        raise ValueError("range_end_before_start")

    # The merged in-range event stream, in (close_time, symbol) order — the
    # deterministic processing order the ledger compounds through.
    stream: list[tuple[datetime, str, int]] = []
    for symbol in context.symbols:
        for idx, candle in enumerate(context.candles_by_symbol[symbol]):
            if start_at <= candle.close_time <= end_at:
                stream.append((candle.close_time, symbol, idx))
    stream.sort(key=lambda item: (item[0], item[1]))
    if not stream:
        raise ValueError("range_has_no_aligned_closed_candles")

    equity = START_EQUITY
    open_positions: dict[str, _OpenPosition] = {}
    trades: list[dict[str, Any]] = []
    curve: list[dict[str, str]] = []
    flips = 0
    warming_symbols: set[str] = set()
    joined_late: dict[str, str] = {}
    gate_unavailable_days = 0
    last_marks: dict[str, Decimal] = {}
    peak = START_EQUITY
    max_drawdown_pct = Decimal("0")
    max_concurrent = 0
    max_gross_x = Decimal("0")
    current_day: datetime | None = None

    def mtm_equity() -> Decimal:
        unrealized = sum(
            (last_marks.get(p.symbol, p.entry_price) - p.entry_price) * p.quantity
            for p in open_positions.values()
        )
        return _money(equity + unrealized)

    def flush_day(day: datetime) -> None:
        nonlocal peak, max_drawdown_pct, max_concurrent, max_gross_x
        value = mtm_equity()
        curve.append({"close_time": _iso(day), "equity": str(value)})
        if value > peak:
            peak = value
        elif peak > 0:
            drawdown = (peak - value) / peak * Decimal("100")
            if drawdown > max_drawdown_pct:
                max_drawdown_pct = drawdown
        max_concurrent = max(max_concurrent, len(open_positions))
        if value > 0 and open_positions:
            gross = sum(
                last_marks.get(p.symbol, p.entry_price) * p.quantity
                for p in open_positions.values()
            )
            gross_x = gross / value
            if gross_x > max_gross_x:
                max_gross_x = gross_x

    for close_time, symbol, idx in stream:
        if current_day is not None and close_time != current_day:
            flush_day(current_day)
        current_day = close_time
        candle = context.candles_by_symbol[symbol][idx]
        state = context.states_by_symbol[symbol][idx]
        last_marks[symbol] = candle.close

        if not state["warmed_up"]:
            warming_symbols.add(symbol)
            continue
        if symbol in warming_symbols and symbol not in joined_late:
            joined_late[symbol] = _iso(close_time)

        position = open_positions.get(symbol)
        entry_fired = bool(state["source_entry_signal"])
        exit_reason = state["exit_signal"]
        risk_on = _risk_on_at(context, close_time) if gated else True
        if gated and risk_on is None:
            gate_unavailable_days += 1

        if position is not None:
            close_because_gate = gated and risk_on is False
            if exit_reason is not None or close_because_gate:
                gross = (candle.close - position.entry_price) * position.quantity
                exit_fee = _money(candle.close * position.quantity * FEE_BPS / Decimal("10000"))
                net = gross - position.entry_fee - exit_fee
                equity = _money(equity + net)
                flips += 1
                trades.append(
                    {
                        "symbol": symbol,
                        "entry_time": _iso(position.entry_time),
                        "exit_time": _iso(close_time),
                        "entry_price": str(position.entry_price),
                        "exit_price": str(candle.close),
                        "quantity": str(position.quantity),
                        "entry_fee": str(position.entry_fee),
                        "exit_fee": str(exit_fee),
                        "net_pnl": str(_money(net)),
                        "exit_reason": exit_reason or "regime_risk_off_exit",
                        "entry_reasons": list(position.entry_reasons),
                        "equity_after": str(equity),
                    }
                )
                del open_positions[symbol]
            continue

        # Flat in this symbol: fresh-start — only IN-RANGE entries are taken,
        # and the surface itself only fires entries when its machine is flat
        # (a pre-range position is ignored until its next fresh entry).
        if entry_fired and (not gated or risk_on is True):
            entry_fee = _money(equity * FEE_BPS / Decimal("10000"))
            quantity = (equity - entry_fee) / candle.close if candle.close > 0 else Decimal("0")
            if quantity <= 0:
                continue
            flips += 1
            open_positions[symbol] = _OpenPosition(
                symbol=symbol,
                entry_time=close_time,
                entry_price=candle.close,
                quantity=quantity,
                entry_fee=entry_fee,
                entry_equity=equity,
                entry_reasons=tuple(state["entry_reason_codes"]),
            )

    if current_day is not None:
        flush_day(current_day)

    end_equity = mtm_equity()
    return {
        "phase": PHASE,
        "lane_id": lane_id,
        "range": {"start": _iso(start_at), "end": _iso(end_at)},
        "first_in_range_close": curve[0]["close_time"],
        "last_in_range_close": curve[-1]["close_time"],
        "start_equity_usdc": str(START_EQUITY),
        "end_equity_usdc": str(end_equity),
        "end_equity_realized_only_usdc": str(_money(equity)),
        "return_pct": str(_money((end_equity / START_EQUITY - Decimal("1")) * Decimal("100"))),
        "max_drawdown_pct": str(_money(max_drawdown_pct)),
        "trade_count": len(trades),
        "flip_count": flips,
        "max_concurrent_positions": max_concurrent,
        "max_gross_exposure_x": str(_money(max_gross_x)),
        "leverage_warning": PRE_REGISTERED_SEMANTICS["leverage_warning"],
        "open_positions_at_end": [
            {
                "symbol": p.symbol,
                "entry_time": _iso(p.entry_time),
                "entry_price": str(p.entry_price),
                "quantity": str(p.quantity),
                "last_mark": str(last_marks.get(p.symbol, p.entry_price)),
                "unrealized_pnl": str(
                    _money((last_marks.get(p.symbol, p.entry_price) - p.entry_price) * p.quantity)
                ),
                "note": "left open, valued at the range's last close - never force-closed",
            }
            for p in open_positions.values()
        ],
        "trades": trades,
        "equity_curve": curve,
        "symbols_joined_after_warmup": joined_late,
        "symbols_still_warming_at_end": sorted(warming_symbols - set(joined_late)),
        "gate_unavailable_days": gate_unavailable_days if gated else 0,
        "regime_gate_available": context.regime_gate is not None,
        "regime_gate_error": context.regime_error,
        "semantics": PRE_REGISTERED_SEMANTICS,
        "committed_characterization": COMMITTED_CHARACTERIZATION,
        "replay_is_hypothetical_not_evidence": True,
        "feeds_live_ledgers": False,
        "disclaimer": REPLAY_DISCLAIMER,
    }


def calendar_year_ranges(context: ReplayContext) -> list[dict[str, Any]]:
    """Every calendar year with aligned data; partial years labeled."""
    first = context.aligned_start
    last = context.last_close
    out = []
    for year in range(first.year, last.year + 1):
        year_start = datetime(year, 1, 1, tzinfo=UTC)
        year_end = datetime(year + 1, 1, 1, tzinfo=UTC) - timedelta(seconds=1)
        start_at = max(year_start, first)
        end_at = min(year_end, last)
        if end_at < start_at:
            continue
        partial = start_at > year_start or last < datetime(year, 12, 31, tzinfo=UTC)
        out.append(
            {
                "label": f"{year}" + (" (partial)" if partial else ""),
                "year": year,
                "start": _iso(start_at),
                "end": _iso(end_at),
                "partial": partial,
            }
        )
    return out


def verify_range_no_lookahead(
    context: ReplayContext, lane_id: str, start: datetime | str, end: datetime | str
) -> bool:
    """The range result must be computable from candles up to the range end
    alone: truncating all post-end history reproduces the result exactly."""
    end_at = parse_utc_timestamp(end)
    truncated = {
        symbol: [c for c in candles if c.close_time <= end_at]
        for symbol, candles in context.candles_by_symbol.items()
    }
    truncated_context = build_replay_context(truncated)
    full = replay_range(context, lane_id, start, end)
    cut = replay_range(truncated_context, lane_id, start, end)
    keys = ("end_equity_usdc", "return_pct", "max_drawdown_pct", "trade_count", "equity_curve", "trades")
    return all(full[key] == cut[key] for key in keys)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
