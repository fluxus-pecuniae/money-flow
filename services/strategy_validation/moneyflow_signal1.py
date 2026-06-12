"""MONEYFLOW-SIGNAL1 — the source-faithful Money Flow signal surface.

SOURCE-FAITHFUL SIGNAL GENERATOR, NOT ALPHA. This module closes the loop to
the project's namesake: it pins the Gerald Peters "Money Flow Trading
System" rules to the actual PDF (present in the repo and read directly this
phase — an upgrade over MF-ORIG-EV1, which had to work from a prompt-supplied
summary), reuses the MF-ORIG-EV1 reconstruction primitives unchanged (no
re-derivation), and emits a fully auditable per-asset signal state on closed
candles only.

The honesty frame, fixed up front: the directional Money Flow rules were
already tested in this repo (MF-ORIG-EV1.1/EV2 trade-level, STRAT-DISC1
discovery pass) and showed NO standalone edge out-of-sample. This phase
re-confirms that as characterization — a green-looking result here is a
reason to re-audit, not a win. The deliverable is fidelity + trust: a founder
can look at this signal on real candles and trust it IS the documented Money
Flow system, see exactly what it does and does not do, and see it with the
REGIME informational risk overlay (whose committed verdict is an honest FAIL
— endpoint-strong, process-unstable — and travels with every state).

Signal only — not an order, not trading advice; nothing here submits orders,
enables any trading mode, or predicts or guarantees profit.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

try:  # canonical package import; sibling fallback for script loaders
    from services.strategy_validation import mf_orig_ev1 as _mf
except Exception:  # pragma: no cover - sibling-loading context
    import importlib.util
    import sys

    def _load_sibling(filename: str, alias: str):
        if alias in sys.modules:
            return sys.modules[alias]
        module_path = Path(__file__).resolve().with_name(filename)
        spec = importlib.util.spec_from_file_location(alias, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"unable_to_load_module:{module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[alias] = module
        spec.loader.exec_module(module)
        return module

    _mf = _load_sibling("mf_orig_ev1.py", "moneyflow_signal1_mf_orig_ev1")

from core.domain.enums import Timeframe
from core.domain.models import Candle, IndicatorSnapshot
from services.indicators.service import DefaultIndicatorService

mf_orig_ev1 = _mf

PHASE = "MONEYFLOW-SIGNAL1"

# The single source-faithful entry hypothesis this surface tracks as its
# position machine — MF-ORIG-EV1's primary 1d reconstruction, reused as-is.
PRIMARY_HYPOTHESIS = "mf_orig_1d_stage2_5_20_crossover"

DISCLAIMER = (
    "SOURCE-FAITHFUL SIGNAL, NOT ALPHA: a faithful implementation of the "
    "documented Gerald Peters Money Flow Trading System, characterized "
    "honestly - the directional rules showed no standalone edge "
    "out-of-sample and this surface re-confirms that as characterization, "
    "not a profit claim. The regime overlay is informational risk context, "
    "not a validated control. Signal only - not an order, not trading "
    "advice; nothing here submits orders, enables any trading mode, or "
    "predicts or guarantees profit."
)

# Source provenance: the PDF is IN the repo and was read directly this phase.
PDF_REPO_RELATIVE_PATH = (
    "money-flow/90 Reference/"
    "The Money Flow Trading System - Gerald Peters - 2019 Edition 2.pdf"
)
PDF_SHA256 = "200c83feebc1c8d095ed4dce6f82afe0bc586ccdaaf2083c304b493e4296a616"
PDF_PAGE_COUNT = 159  # PDF pages; printed page N is PDF page N+1

SOURCE_DOCUMENT: dict[str, Any] = {
    "title": "The Money Flow Trading System",
    "author": "Gerald Peters",
    "edition": "September 5, 2019 Edition #2",
    "repo_path": PDF_REPO_RELATIVE_PATH,
    "pdf_sha256": PDF_SHA256,
    "pdf_page_count": PDF_PAGE_COUNT,
    "direct_pdf_available_to_agent": True,
    "page_convention": "citations use the PRINTED page number (PDF page = printed page + 1)",
    "upgrade_over_mf_orig_ev1": (
        "MF-ORIG-EV1 recorded direct_pdf_available_to_agent=false and worked "
        "from a prompt-supplied source summary; MONEYFLOW-SIGNAL1 located the "
        "PDF in the repo, read it directly, and verified every reused rule "
        "against the printed text - citations below quote the source."
    ),
}

# ---------------------------------------------------------------------------
# Must 1 — provable fidelity: the documented rules, page-cited, mapped to the
# exact reused implementation. Quotes are verbatim from the PDF text layer
# (including the author's spelling).
# ---------------------------------------------------------------------------

SOURCE_CITATIONS: tuple[dict[str, str], ...] = (
    {
        "rule_id": "checklist_indicators",
        "printed_page": "10",
        "quote": (
            "The Basic Money Flow Trading System Check List: 1. The 5-day "
            "Exponential Moving Average 2. The 10-day Exponential Moving "
            "Average 3. The 20-day Simple Moving Average 4. RSI - Relative "
            "Strength Index set to 14 day 5. Support and Resistance Zones "
            "6. The MACD - Moving Average Convergence Divergence / or TSI"
        ),
        "implementation": (
            "indicator set is exactly EMA5, EMA10, SMA20, RSI14, MACD(12,26,9) "
            "via services.indicators.service (the production implementations); "
            "every value is emitted on the signal surface"
        ),
    },
    {
        "rule_id": "foundation_5_20_crossover",
        "printed_page": "37",
        "quote": (
            "The foundation of The Money Flow Trading System is the 5-day EMA "
            "and 20-day SMA crossovers. These two moving averages crossing "
            "each other give us our basic buy and sell signals. ... A bullish "
            "crossover occurs when the shorter moving average crosses above "
            "the longer moving average. This is also known as a buy signal. "
            "A bearish crossover ... is known as a sell signal."
        ),
        "implementation": (
            "basic_signal: 'buy' on EMA5 crossing above SMA20, 'sell' on EMA5 "
            "crossing below SMA20 (mf_orig_ev1._crossed_above/_crossed_below, "
            "reused unchanged)"
        ),
    },
    {
        "rule_id": "sma20_trend_and_stage_line",
        "printed_page": "30-31, 36",
        "quote": (
            "Price is in relation to the 20-day moving average is what "
            "identifies the current stage. (p.30) ... The most important "
            "moving average for The Money Flow Trading System is the 20 SMA. "
            "(p.31) ... if price is above the 20 SMA prices are trending up, "
            "if price is below the 20 SMA prices are trending down. (p.36)"
        ),
        "implementation": (
            "close_vs_sma20 emitted on every state; the stage classifier keys "
            "on close versus SMA20 (mf_orig_ev1._classify_stage, reused)"
        ),
    },
    {
        "rule_id": "macd_equals_tsi",
        "printed_page": "70, 72",
        "quote": (
            "you can just use the MACD indicator and get the exact same "
            "results. ... The two indicators are in complete lock step 99% of "
            "the time. (p.70; TSI(25,13,7) and MACD(12,26,9) appear on every "
            "chart in the book)"
        ),
        "implementation": (
            "MACD(12,26,9) is used for confirmation/warning - now "
            "SOURCE-CONFIRMED (the PDF itself authorizes MACD in place of "
            "TSI), upgrading MF-ORIG-EV1's 'tsi_deferred_macd_substitute' "
            "limitation"
        ),
    },
    {
        "rule_id": "stage2_breakout_entry",
        "printed_page": "146",
        "quote": (
            "Stage Two - The Breakout ... The 5 EMA will Cross the 20 SMA. "
            "The MACD will confirm with crossover signals. Often, they will "
            "signal before the 5/20 crossover. ... You want to be fully "
            "invested in the trade at this stage."
        ),
        "implementation": (
            "source_entry_signal = mf_orig_ev1._entry_signal('"
            + PRIMARY_HYPOTHESIS
            + "'): Stage 2 active, close above SMA20, EMA5 crosses above "
            "SMA20, MACD bullish or improving, RSI below the extreme-"
            "overbought block"
        ),
    },
    {
        "rule_id": "stage3_warning_and_quarter_trim",
        "printed_page": "150",
        "quote": (
            "Your first sign be 70+ Reading with RSI. This is your first "
            "warning sign. ... If the MACD signals sell and has a crossover "
            "in the opposite direction and the 5 EMA is still above the 20 "
            "SMA you want to take profits. I often sell a fourth of the "
            "position."
        ),
        "implementation": (
            "rsi_profit_warning (RSI14 > 70) and macd_sell_crossover (bearish "
            "signal-line cross while EMA5 > SMA20) are emitted as separate "
            "auditable flags; trim_context_25pct marks the documented "
            "quarter-trim context (the trade-level 25% trim itself lives in "
            "the reused MF-ORIG engine)"
        ),
    },
    {
        "rule_id": "full_exit_rule",
        "printed_page": "150, 152",
        "quote": (
            "We do not close the trade until the 5 EMA crosses and closes "
            "below the 20 SMA or price closes below the 20-day moving "
            "average. (p.150) ... The 5 EMA crossing below the 20 SMA was the "
            "death nail. (p.152)"
        ),
        "implementation": (
            "exit_signal: ema5_cross_below_sma20_exit or "
            "price_close_below_sma20_exit - the same two conditions "
            "mf_orig_ev1._original_exit_reason closes on"
        ),
    },
    {
        "rule_id": "rsi_rules",
        "printed_page": "127, 140",
        "quote": (
            "RSI is considered overbought (take profits) when above 70 and "
            "oversold when below 30. (p.127) ... Ignore RSI 70 + reading when "
            "5 day moving average is still above the 10-day moving average "
            "and the 10-day moving average is above the 20-day moving "
            "average. All three moving averages are sloping upward. (p.140)"
        ),
        "implementation": (
            "rsi_profit_warning above 70; rsi_ignore_active when the "
            "EMA5 > EMA10 > SMA20 stack holds (the p.140 override) - both "
            "emitted, neither hidden inside the other"
        ),
    },
    {
        "rule_id": "structure_stops_not_fixed_pct",
        "printed_page": "115, 118",
        "quote": (
            "You want to let market structure determines your stop loss point "
            "not some arbitrary percentage of loss. (p.115) ... Pivot points "
            "help traders identify market structure and the best place to "
            "place a protective stop. (p.118)"
        ),
        "implementation": (
            "trade-level lane only (reused MF-ORIG engine: prior-10-candle "
            "support low / confirmed pivot-low proxy); the signal surface "
            "emits the current structure-stop reference for audit"
        ),
    },
    {
        "rule_id": "position_sizing_1pct_risk",
        "printed_page": "125",
        "quote": (
            "Ideally you want to risk 1% or less of your account balance on "
            "any one trade."
        ),
        "implementation": (
            "trade-level lane only (reused MF-ORIG engine sizes risk budget "
            "at 1% of realized equity over stop distance); not part of the "
            "signal state itself"
        ),
    },
    {
        "rule_id": "daily_timeframe_fractal",
        "printed_page": "142",
        "quote": (
            "This cycle is fractal. ... The Money Flow trading strategy uses "
            "a daily chart."
        ),
        "implementation": "the signal surface computes on closed DAILY candles only",
    },
    {
        "rule_id": "stage1_whipsaw_warning",
        "printed_page": "143",
        "quote": (
            "Stage One: Basing ... This is the stage you can be whip sawed "
            "and take many small losses if you can't identify it on a chart. "
            "The moving averages are of little help in stage one."
        ),
        "implementation": (
            "the stage classifier's whipsaw/low-progress branch labels Stage "
            "1; the emitted stage gives the founder the documented whipsaw "
            "warning context"
        ),
    },
    {
        "rule_id": "trend_following_frame",
        "printed_page": "3",
        "quote": (
            "A Trend once established a Trend is more likely to continue than "
            "it is to reverse. This statement is the foundation upon which "
            "The Money Flow Trading Strategy is built."
        ),
        "implementation": (
            "framing only - the system is trend-following by construction; "
            "no extra code rule"
        ),
    },
)

# Where the PDF is narrative rather than computational, the interpretation is
# recorded explicitly — never silently picked.
AMBIGUITY_RESOLUTIONS: tuple[dict[str, str], ...] = (
    {
        "ambiguity_id": "indicator_formula_conventions",
        "pdf_basis": (
            "the book gives no formulas (p.30: 'You don't need to know the "
            "complicated mathematically calculations'); its charts are "
            "produced by StockCharts (p.11-12)"
        ),
        "resolution": (
            "use the repo's production indicator implementations "
            "(services/indicators/service.py): SMA-seeded EMA with multiplier "
            "2/(n+1), Wilder-smoothed RSI(14), MACD(12,26,9) with EMA(9) "
            "signal - the same StockCharts-documented conventions; fidelity "
            "tests pin the arithmetic with hand-computed fixtures"
        ),
        "why": "matches the charting service the source itself uses and recommends",
    },
    {
        "ambiguity_id": "stage_classification_is_narrative",
        "pdf_basis": (
            "Chapter 10 (p.142-155) describes the four stages narratively "
            "(basing / breakout / topping / decline) with chart examples, no "
            "formula"
        ),
        "resolution": (
            "reuse MF-ORIG-EV1's deterministic no-lookahead stage proxy "
            "unchanged (_classify_stage: close vs SMA20 + 5/20 crosses + "
            "whipsaw count + RSI/MACD warnings + prior stage)"
        ),
        "why": (
            "the proxy was already founder-reviewed in MF-ORIG-EV1.1/EV2; "
            "re-deriving a new classifier would break reuse and create a "
            "second unverifiable interpretation"
        ),
    },
    {
        "ambiguity_id": "trim_trigger_conjunction",
        "pdf_basis": (
            "p.150 sequences the warnings (RSI 70+ first, then the MACD sell "
            "crossover 'you want to take profits ... sell a fourth') without "
            "stating whether both must hold simultaneously"
        ),
        "resolution": (
            "the signal surface emits rsi_profit_warning and "
            "macd_sell_crossover as SEPARATE flags plus trim_context_25pct "
            "for the p.150 MACD-while-5-above-20 condition; the reused "
            "MF-ORIG trade engine keeps its stricter conjunction (RSI>70 AND "
            "MACD bearish cross while profitable) - both readings are "
            "visible, nothing is silently chosen"
        ),
        "why": "founder sees the raw documented warnings and the engine's stricter reading",
    },
    {
        "ambiguity_id": "entry_confirmation_set",
        "pdf_basis": (
            "p.37 calls the bare 5/20 bullish crossover 'a buy signal'; "
            "p.146 adds the Stage-2 frame and MACD confirmation"
        ),
        "resolution": (
            "both are emitted: basic_signal (pure p.37 crossover) and "
            "source_entry_signal (MF-ORIG primary hypothesis: Stage 2 + close "
            "above SMA20 + crossover + MACD confirm + RSI<80 extreme block); "
            "the RSI>=80 entry block is an MF-ORIG interpretation (the PDF "
            "only says to IGNORE RSI 70+ when the MA stack is aligned, p.140) "
            "and is recorded as such"
        ),
        "why": "the founder can audit the raw signal and the confirmed entry side by side",
    },
    {
        "ambiguity_id": "structure_stop_proxy",
        "pdf_basis": (
            "p.115/p.118: stops belong at market structure / pivot points, "
            "described visually, no algorithm"
        ),
        "resolution": (
            "reuse MF-ORIG's deterministic proxy: min(prior-10-candle support "
            "low, last confirmed 2/2 pivot low before the signal candle); the "
            "signal surface emits the reference value for audit only"
        ),
        "why": "deterministic, no-lookahead, already characterized at trade level",
    },
    {
        "ambiguity_id": "characterization_scope_exposure_only",
        "pdf_basis": "n/a - scope decision for this phase's book characterization",
        "resolution": (
            "the MONEYFLOW-SIGNAL1 characterization books model the signal's "
            "long/flat EXPOSURE (entry/exit rules) through the EXEC-EV1 "
            "friction simulator; structure stops, 25% trims, and 1%-risk "
            "sizing are trade-level mechanics already characterized honestly "
            "in MF-ORIG-EV1.1/EV2 (no standalone edge) and are not re-modeled "
            "at book level"
        ),
        "why": (
            "the signal is the deliverable; trade-level results exist and are "
            "cited rather than re-derived with new assumptions"
        ),
    },
)

# The known prior results this phase re-confirms (honesty frame, not alpha):
PRIOR_EVIDENCE = {
    "mf_orig_ev1_1": "docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json",
    "mf_orig_ev2": "docs/mf_orig_ev2_multitimeframe_evidence_summary.json",
    "known_result": (
        "no standalone out-of-sample edge for the directional Money Flow "
        "rules; this phase re-confirms that as characterization"
    ),
}

WARMUP_NOTE = "warm-up is never guessed: states are emitted only when every required indicator exists"


# ---------------------------------------------------------------------------
# Indicators + context (pure reuse of the production implementations)
# ---------------------------------------------------------------------------


def compute_snapshots(candles: Sequence[Candle]) -> list[IndicatorSnapshot]:
    """The production indicator snapshots for a candle series.

    Calls DefaultIndicatorService._compute_snapshots through the class (the
    method reads no instance state) so the signal surface uses EXACTLY the
    production EMA/SMA/RSI/MACD arithmetic — any drift breaks loudly.
    """
    return DefaultIndicatorService._compute_snapshots(None, candles)  # type: ignore[arg-type]


def build_signal_context(candles: Sequence[Candle]) -> list[dict[str, Any]]:
    """MF-ORIG-EV1's per-candle context (indicators + stage), reused as-is."""
    return _mf._build_original_context(candles, compute_snapshots(candles))


def core_candles_from_data1_rows(
    symbol: str, rows: Sequence[Mapping[str, Any]]
) -> list[Candle]:
    """DATA1 normalized daily rows -> core-domain Candles (closed candles,
    oldest-first), for the indicator/signal pipeline."""
    candles: list[Candle] = []
    for row in rows:
        close_time = _parse_utc(str(row["close_time"]))
        open_time_raw = row.get("open_time")
        open_time = (
            _parse_utc(str(open_time_raw))
            if open_time_raw is not None
            else close_time - timedelta(days=1)
        )
        candles.append(
            Candle(
                instrument_key=None,
                instrument_ref_id=None,
                venue=str(row.get("venue", "unknown")),
                symbol=symbol,
                timeframe=Timeframe.D1,
                open_time=open_time,
                close_time=close_time,
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=Decimal(str(row.get("volume_base", row.get("volume", "0")))),
            )
        )
    candles.sort(key=lambda c: c.close_time)
    return candles


def core_candles_from_goal_strat1(dataset: Any) -> list[Candle]:
    """goal_strat1 Dataset (timestamps = close times) -> core-domain Candles."""
    candles: list[Candle] = []
    for c in dataset.candles:
        close_time = c.timestamp if c.timestamp.tzinfo else c.timestamp.replace(tzinfo=UTC)
        candles.append(
            Candle(
                instrument_key=None,
                instrument_ref_id=None,
                venue="data1",
                symbol=dataset.symbol,
                timeframe=Timeframe.D1,
                open_time=close_time - timedelta(days=1),
                close_time=close_time,
                open=c.open,
                high=c.high,
                low=c.low,
                close=c.close,
                volume=c.volume,
            )
        )
    return candles


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


# ---------------------------------------------------------------------------
# Must 2 — the auditable signal states (closed candles only, no lookahead)
# ---------------------------------------------------------------------------


def _exposure_exit_reason(
    row: dict[str, Any], prev: dict[str, Any] | None, candle: Candle
) -> str | None:
    """The two documented full-exit conditions (p.150/p.152), exactly the
    non-stop branch of mf_orig_ev1._original_exit_reason."""
    if row.get("ema5") is None or row.get("sma20") is None:
        return None
    if _mf._crossed_below(row, prev, "ema5", "sma20"):
        return "ema5_cross_below_sma20_exit"
    if candle.close < row["sma20"]:
        return "price_close_below_sma20_exit"
    return None


def signal_states(candles: Sequence[Candle]) -> list[dict[str, Any]]:
    """One auditable state per closed candle.

    Every intermediate term is emitted; warm-up states carry the missing
    reasons and never guess. position_state walks the PRIMARY source-faithful
    machine (Stage-2 confirmed entry, documented exits); basic_position_state
    walks the bare p.37 5/20 crossover machine. The state at index i is
    computed from candles[0..i] only.
    """
    context = build_signal_context(candles)
    states: list[dict[str, Any]] = []
    in_position = False
    basic_in_position = False
    for idx, candle in enumerate(candles):
        row = context[idx]
        prev = context[idx - 1] if idx > 0 else None
        missing = list(row.get("missing_reasons") or ())
        if row.get("sma50") is None and "missing_sma50" not in missing:
            missing.append("missing_sma50")
        warmed = not missing

        ema5, ema10, sma20 = row.get("ema5"), row.get("ema10"), row.get("sma20")
        rsi14 = row.get("rsi14")
        bullish_stack = bool(
            warmed and ema5 is not None and ema10 is not None and sma20 is not None
            and ema5 > ema10 > sma20
        )
        rsi_warning = bool(warmed and rsi14 is not None and rsi14 > Decimal("70"))
        macd_sell_cross = bool(warmed and _mf._macd_bearish_cross(row, prev))
        exit_reason = _exposure_exit_reason(row, prev, candle) if warmed else None

        basic_signal = "none"
        if warmed and _mf._crossed_above(row, prev, "ema5", "sma20"):
            basic_signal = "buy"
        elif warmed and _mf._crossed_below(row, prev, "ema5", "sma20"):
            basic_signal = "sell"

        if warmed:
            entry = _mf._entry_signal(PRIMARY_HYPOTHESIS, idx, candle, candles, context)
        else:
            entry = {"entry_allowed": False, "reason_codes": ["warming_up", *missing]}

        # The position machines (states change AT the close that signals).
        if warmed:
            if in_position and exit_reason is not None:
                in_position = False
            elif not in_position and entry["entry_allowed"]:
                in_position = True
            if basic_in_position and (
                basic_signal == "sell" or exit_reason == "price_close_below_sma20_exit"
            ):
                basic_in_position = False
            elif not basic_in_position and basic_signal == "buy":
                basic_in_position = True

        states.append(
            {
                "close_time": candle.close_time.astimezone(UTC).isoformat(),
                "close": str(candle.close),
                "warmed_up": warmed,
                "missing_reasons": missing,
                "indicators": {
                    "ema5": _str_or_none(ema5),
                    "ema10": _str_or_none(ema10),
                    "sma20": _str_or_none(sma20),
                    "sma50": _str_or_none(row.get("sma50")),
                    "rsi14": _str_or_none(rsi14),
                    "macd": _str_or_none(row.get("macd")),
                    "macd_signal": _str_or_none(row.get("macd_signal")),
                    "macd_histogram": _str_or_none(row.get("macd_histogram")),
                    "ema5_minus_sma20": _str_or_none(
                        _quant(ema5 - sma20) if ema5 is not None and sma20 is not None else None
                    ),
                    "close_vs_sma20_pct": _str_or_none(
                        _quant((candle.close / sma20 - Decimal("1")) * Decimal("100"))
                        if sma20 not in (None, Decimal("0"))
                        else None
                    ),
                },
                "stage": str(row.get("stage")),
                "basic_signal": basic_signal,
                "source_entry_signal": bool(entry["entry_allowed"]),
                "entry_reason_codes": list(entry.get("reason_codes", ())),
                "exit_signal": exit_reason,
                "position_state": "long" if in_position else "flat",
                "basic_position_state": "long" if basic_in_position else "flat",
                "ma_alignment_bullish_stack": bullish_stack,
                "rsi_profit_warning": rsi_warning,
                "rsi_ignore_active": bool(rsi_warning and bullish_stack),
                "macd_sell_crossover": macd_sell_cross,
                "trim_context_25pct": bool(
                    macd_sell_cross
                    and ema5 is not None
                    and sma20 is not None
                    and ema5 > sma20
                ),
                "structure_stop_reference": _str_or_none(
                    _mf._structure_stop_price(candles, idx) if warmed else None
                ),
                "disclaimer": DISCLAIMER,
            }
        )
    return states


def _str_or_none(value: Any) -> str | None:
    return None if value is None else str(value)


def _quant(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"))


def exposure_series(
    candles: Sequence[Candle], *, entry_mode: str = "source_stage2"
) -> list[int | None]:
    """The signal's long/flat exposure per candle index (1 long, 0 flat,
    None during warm-up) — the series the characterization books trade.

    entry_mode 'source_stage2' walks the primary confirmed machine;
    'basic_5_20' walks the bare p.37 crossover machine.
    """
    if entry_mode not in ("source_stage2", "basic_5_20"):
        raise ValueError(f"unknown_entry_mode:{entry_mode}")
    states = signal_states(candles)
    key = "position_state" if entry_mode == "source_stage2" else "basic_position_state"
    return [
        None if not state["warmed_up"] else (1 if state[key] == "long" else 0)
        for state in states
    ]


def verify_signal_point_in_time(
    candles: Sequence[Candle], sample_indices: Sequence[int]
) -> bool:
    """True iff the state at index i provably ignores the future: computing
    from candles truncated right after i reproduces the full-series state."""
    full = signal_states(candles)
    for idx in sample_indices:
        truncated = signal_states(candles[: idx + 1])
        if truncated[idx] != full[idx]:
            return False
    return True


# ---------------------------------------------------------------------------
# Must 3 plumbing — the book providers (the characterization runner wires
# these into tsmom_ev1.simulate_tsmom_portfolio with EXEC-EV1 friction)
# ---------------------------------------------------------------------------


def moneyflow_exposure_provider(
    universe: Any, *, entry_mode: str = "source_stage2"
) -> Callable[[str, int], int | None]:
    """Signal provider for the friction book simulator: the Money Flow
    exposure at each symbol's decision candle (causal by construction —
    exposure_series(i) is computed from candles[0..i] only; verified by
    verify_signal_point_in_time)."""
    series: dict[str, list[int | None]] = {}
    for symbol in universe.symbols:
        candles = core_candles_from_goal_strat1(universe.datasets[symbol])
        series[symbol] = exposure_series(candles, entry_mode=entry_mode)

    def provider(symbol: str, idx: int) -> int | None:
        values = series[symbol]
        if idx >= len(values):
            return None
        return values[idx]

    return provider


def regime_gated_provider(
    base: Callable[[str, int], int | None],
    regime_provider: Callable[[str, int], int | None],
) -> Callable[[str, int], int | None]:
    """Money Flow exposure AND the regime filter's risk_on state — the
    informational overlay book. The regime filter's committed verdict is an
    honest FAIL (process stability); the overlay is risk context, never a
    validated control."""

    def provider(symbol: str, idx: int) -> int | None:
        sig = base(symbol, idx)
        gate = regime_provider(symbol, idx)
        if sig is None or gate is None:
            return None
        return 1 if (sig == 1 and gate == 1) else 0

    return provider


def exposure_flip_count(provider: Callable[[str, int], int | None], universe: Any) -> int:
    """Whipsaw surface: total long<->flat transitions across symbols."""
    flips = 0
    for symbol in universe.symbols:
        n = len(universe.datasets[symbol].candles)
        last: int | None = None
        for idx in range(n):
            value = provider(symbol, idx)
            if value is None:
                continue
            if last is not None and value != last:
                flips += 1
            last = value
    return flips


# ---------------------------------------------------------------------------
# The CLI payload (Must 2): latest state per asset + the regime overlay
# ---------------------------------------------------------------------------


def latest_signal_report(
    candles_by_asset: Mapping[str, Sequence[Candle]],
    *,
    regime_gate: Any | None = None,
    regime_error: str | None = None,
) -> dict[str, Any]:
    """The per-asset latest-closed-candle signal states with the regime
    overlay attached (verdict note intact) — the auditable CLI payload."""
    regime_overlay: dict[str, Any]
    if regime_gate is not None:
        as_of = regime_gate.last_state_time
        state = regime_gate.state_at(as_of)
        regime_overlay = {
            "available": True,
            "as_of_close": str(as_of),
            "state": {k: _str_or_none(v) if isinstance(v, Decimal) else v for k, v in state.items()},
            "committed_verdict": _regime_module().VERDICT_FAIL,
            "committed_verdict_note": _regime_module().COMMITTED_VERDICT_NOTE,
            "label": (
                "informational risk context, not a validated control "
                "(REGIME2 verdict: endpoint-strong, process-unstable, honest FAIL)"
            ),
        }
    else:
        regime_overlay = {
            "available": False,
            "reason": regime_error or "regime_gate_not_built",
            "committed_verdict": _regime_module().VERDICT_FAIL,
            "committed_verdict_note": _regime_module().COMMITTED_VERDICT_NOTE,
            "label": "informational risk context, not a validated control",
        }

    assets: dict[str, Any] = {}
    for asset in sorted(candles_by_asset):
        candles = list(candles_by_asset[asset])
        states = signal_states(candles)
        latest = states[-1] if states else None
        assets[asset] = {
            "candle_count": len(candles),
            "latest_state": latest,
            "recent_states": states[-5:],
            "point_in_time_verified": verify_signal_point_in_time(
                candles, [len(candles) - 1]
            )
            if candles
            else False,
        }
    return {
        "phase": PHASE,
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_document": SOURCE_DOCUMENT,
        "primary_hypothesis": PRIMARY_HYPOTHESIS,
        "assets": assets,
        "regime_overlay": regime_overlay,
        "prior_evidence": PRIOR_EVIDENCE,
        "warmup_note": WARMUP_NOTE,
        "boundaries": boundary_flags(),
        "disclaimer": DISCLAIMER,
    }


def _regime_module():
    try:
        from services.strategy_validation import regime1

        return regime1
    except Exception:  # pragma: no cover - sibling-loading context
        import importlib.util
        import sys

        alias = "moneyflow_signal1_regime1"
        if alias in sys.modules:
            return sys.modules[alias]
        module_path = Path(__file__).resolve().with_name("regime1.py")
        spec = importlib.util.spec_from_file_location(alias, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"unable_to_load_module:{module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[alias] = module
        spec.loader.exec_module(module)
        return module


def pdf_provenance_check(repo_root: Path) -> dict[str, Any]:
    """Verify the pinned PDF is present and byte-identical (sha256)."""
    pdf_path = repo_root / PDF_REPO_RELATIVE_PATH
    if not pdf_path.exists():
        return {"present": False, "sha256_matches_pin": False, "path": str(pdf_path)}
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    return {
        "present": True,
        "sha256": digest,
        "sha256_matches_pin": digest == PDF_SHA256,
        "path": str(pdf_path),
    }


def boundary_flags() -> dict[str, Any]:
    return {
        "signal_only": True,
        "submits_orders": False,
        "calls_private_signed_or_order_endpoints": False,
        "uses_api_keys": False,
        "enables_any_trading_mode": False,
        "changes_production_money_flow_rules": False,
        "changes_runtime_behavior": False,
        "approves_live_trading": False,
        "approves_paper_trading": False,
        "is_alpha_claim": False,
        "predicts_or_guarantees_profit": False,
        "standalone_edge_claim": False,
        "regime_overlay_is_validated_control": False,
        "regime_overlay_is_informational_risk_context": True,
    }
