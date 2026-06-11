"""TREND-OVERLAY1 — deployable trend drawdown-control overlay (signal only).

READ-ONLY SIGNAL TOOL. This module operationalizes the TSMOM-EV1 finding —
vol-targeted time-series momentum as a DRAWDOWN-CONTROL overlay (it cut a
66% bear drawdown to 17% in evidence, while itself losing 12.2% absolute in
that OOS window; authored ``mixed`` / "defensive, not profitable") — as a
forward calculator on the latest fully-closed public-mainnet candles.

It REUSES the exact TSMOM-EV1 computation (``tsmom_signal``,
``realized_vol_annual``, ``target_weights`` with the same caps) under the
evidence run's TRAIN-CHOSEN config (lb30 / portfolio vol target 0.20 /
long-only). Nothing is re-derived or re-tuned here; the defaults are pinned
to the committed TSMOM-EV1 summary by test.

HONEST FRAMING (non-negotiable, carried in every output):
    Drawdown-control overlay, NOT alpha. It reduces downside on a held long
    crypto book; it does not predict prices and does not aim to make money
    on its own. SIGNAL ONLY: not an order, no auto-execution, no live
    trading, no production approval implied or granted — an advisory number
    an operator may read.

Closed-candle-only: the calculator accepts an explicit ``as_of`` and uses
ONLY candles whose close time is at or before it — an in-progress candle or
any future row is excluded by construction (tested).

Pure and deterministic: Decimal arithmetic, no I/O, no network. The CLI
(`scripts/run_trend_overlay.py`) owns the documented public read-only fetch.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

try:  # pragma: no cover - exercised implicitly by both import contexts
    from services.strategy_validation import tsmom_ev1 as _tsmom
except Exception:  # heavy package __init__ unavailable outside pytest
    import importlib.util
    import sys
    from pathlib import Path

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

    _tsmom = _load_sibling("tsmom_ev1.py", "trend_overlay1_tsmom_ev1")

tsmom = _tsmom
_money = _tsmom._money

PHASE = "TREND-OVERLAY1"

# The TSMOM-EV1 TRAIN-CHOSEN config (committed evidence summary:
# train_only_choice.chosen_config == tsmom_ev1_lb30_vt20_long_only_1d).
# These defaults are pinned by test against that summary — changing them
# here without new evidence is a re-tune and must fail CI.
VALIDATED_CONFIG_ID = "tsmom_ev1_lb30_vt20_long_only_1d"
DEFAULT_LOOKBACK_DAYS = 30
DEFAULT_VOL_WINDOW_DAYS = tsmom.VOL_WINDOW_DAYS  # 30
DEFAULT_PORTFOLIO_VOL_TARGET = Decimal("0.20")
DEFAULT_MODE = "long_only"
DEFAULT_ACCOUNT_SIZE_USDC = Decimal("10000")
LIQUID_UNIVERSE = tsmom.LIQUID_UNIVERSE  # BTC/ETH/SOL/XRP/DOGE/BNB/SUI/AVAX

STATE_HOLD = "hold_vol_targeted"
STATE_FLAT_DOWNTREND = "flat_downtrend"
STATE_FLAT_NO_DRIFT = "flat_no_drift"
STATE_INSUFFICIENT = "insufficient_history"

DISCLAIMER = (
    "DRAWDOWN-CONTROL OVERLAY, NOT ALPHA: this signal reduces downside on a "
    "held long crypto book by going flat / vol-targeted in downtrends "
    "(TSMOM-EV1 evidence: equal-weight buy-and-hold bear drawdown 66% vs "
    "overlay 17% - while the overlay itself LOST 12.2% absolute in that OOS "
    "window; authored outcome: mixed, defensive not profitable). It does not "
    "predict prices and does not aim to make money on its own. SIGNAL ONLY: "
    "not an order, no auto-execution, no testnet or live trading, and no "
    "production approval is implied or granted."
)


def _parse_close_time(value: str) -> datetime:
    return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def closed_candles_only(
    candles: list[dict[str, Any]], as_of: datetime
) -> tuple[list[dict[str, Any]], int]:
    """Keep only candles fully CLOSED at ``as_of`` (close_time <= as_of).

    Returns (closed, dropped_count). This is the no-lookahead boundary: an
    in-progress candle or any row from the future is excluded here, before
    any computation sees it.
    """
    closed = [c for c in candles if _parse_close_time(c["close_time"]) <= as_of]
    closed.sort(key=lambda c: c["close_time"])
    return closed, len(candles) - len(closed)


def compute_overlay(
    candles_by_symbol: dict[str, list[dict[str, Any]]],
    *,
    as_of: datetime,
    account_size_usdc: Decimal = DEFAULT_ACCOUNT_SIZE_USDC,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    vol_window_days: int = DEFAULT_VOL_WINDOW_DAYS,
    portfolio_vol_target: Decimal = DEFAULT_PORTFOLIO_VOL_TARGET,
    mode: str = DEFAULT_MODE,
) -> dict[str, Any]:
    """The overlay snapshot: per-asset trend state + vol-targeted target
    weight + portfolio target exposure, on closed candles only.

    Runs the EXACT TSMOM-EV1 machinery forward: ``tsmom_signal`` (sign of
    the trailing ``lookback_days`` return), ``realized_vol_annual`` over
    ``vol_window_days``, and ``target_weights`` (equal risk budgets,
    per-asset weight cap, gross-leverage cap).
    """
    config = tsmom.TsmomConfig(
        config_id=VALIDATED_CONFIG_ID,
        strategy_type=tsmom.STRATEGY_TYPE_TIME_SERIES_MOMENTUM,
        lookback_days=lookback_days,
        portfolio_vol_target=portfolio_vol_target,
        mode=mode,
        vol_window_days=vol_window_days,
    )
    signals: dict[str, int] = {}
    vols: dict[str, Decimal | None] = {}
    per_asset_meta: dict[str, dict[str, Any]] = {}
    dropped_total = 0
    data_as_of: datetime | None = None
    for symbol in sorted(candles_by_symbol):
        closed, dropped = closed_candles_only(candles_by_symbol[symbol], as_of)
        dropped_total += dropped
        closes = [Decimal(str(c["close"])) for c in closed]
        idx = len(closes) - 1
        signal = tsmom.tsmom_signal(closes, idx, lookback_days) if idx >= 0 else None
        vol = (
            tsmom.realized_vol_annual(closes, idx, vol_window_days)
            if idx >= 0
            else None
        )
        signals[symbol] = signal if signal is not None else 0
        vols[symbol] = vol
        last_close_time = (
            _parse_close_time(closed[-1]["close_time"]) if closed else None
        )
        if last_close_time is not None and (
            data_as_of is None or last_close_time > data_as_of
        ):
            data_as_of = last_close_time
        per_asset_meta[symbol] = {
            "candle_count_closed": len(closed),
            "dropped_not_closed": dropped,
            "last_close": str(closes[-1]) if closes else None,
            "last_close_time": (
                last_close_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                if last_close_time
                else None
            ),
            "signal_raw": signal,
            "history_sufficient": signal is not None and vol is not None,
        }
    weights = tsmom.target_weights(signals=signals, vols=vols, config=config)

    rows: list[dict[str, Any]] = []
    gross_weight = Decimal("0")
    for symbol in sorted(candles_by_symbol):
        meta = per_asset_meta[symbol]
        weight = weights.get(symbol, Decimal("0"))
        gross_weight += abs(weight)
        if not meta["history_sufficient"]:
            state = STATE_INSUFFICIENT
        elif meta["signal_raw"] is not None and meta["signal_raw"] > 0:
            state = STATE_HOLD
        elif meta["signal_raw"] is not None and meta["signal_raw"] < 0:
            state = STATE_FLAT_DOWNTREND
        else:
            state = STATE_FLAT_NO_DRIFT
        rows.append(
            {
                "symbol": symbol,
                "trend_state": state,
                "trend_sign": meta["signal_raw"],
                "realized_vol_annual": (
                    str(_money(vols[symbol])) if vols[symbol] is not None else None
                ),
                "target_weight": str(_money(weight)),
                "target_exposure_usdc": str(_money(weight * account_size_usdc)),
                "last_close": meta["last_close"],
                "last_close_time": meta["last_close_time"],
                "closed_candles_used": meta["candle_count_closed"],
                "dropped_not_closed": meta["dropped_not_closed"],
            }
        )

    return {
        "phase": PHASE,
        "report": "current_trend_overlay",
        "as_of_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_as_of_utc": (
            data_as_of.strftime("%Y-%m-%dT%H:%M:%SZ") if data_as_of else None
        ),
        "disclaimer": DISCLAIMER,
        "config": {
            "validated_source": "TSMOM-EV1 train-chosen config (committed evidence summary)",
            "config_id": VALIDATED_CONFIG_ID,
            "lookback_days": lookback_days,
            "vol_window_days": vol_window_days,
            "portfolio_vol_target_annualized": str(portfolio_vol_target),
            "mode": mode,
            "max_single_asset_weight": str(tsmom.MAX_SINGLE_ASSET_WEIGHT),
            "max_gross_leverage": str(tsmom.MAX_GROSS_LEVERAGE),
            "not_retuned": True,
        },
        "account_size_usdc": str(account_size_usdc),
        "per_asset": rows,
        "portfolio": {
            "gross_target_weight": str(_money(gross_weight)),
            "gross_target_exposure_usdc": str(_money(gross_weight * account_size_usdc)),
            "assets_held": sum(1 for r in rows if r["trend_state"] == STATE_HOLD),
            "assets_flat": sum(
                1
                for r in rows
                if r["trend_state"] in (STATE_FLAT_DOWNTREND, STATE_FLAT_NO_DRIFT)
            ),
            "reading": (
                "gross_target_weight is the vol-targeted fraction of the account "
                "the overlay would keep exposed; the remainder sits in cash - the "
                "drawdown-control action is the gap between this and fully long"
            ),
        },
        "dropped_not_closed_total": dropped_total,
        "boundaries": {
            "signal_only_not_an_order": True,
            "drawdown_control_not_alpha": True,
            "auto_execution": False,
            "creates_order_intent": False,
            "creates_prepared_venue_order": False,
            "creates_submitted_order": False,
            "submits_live_orders": False,
            "submits_testnet_orders": False,
            "calls_private_signed_or_order_endpoints": False,
            "approves_live_trading": False,
            "approves_production_strategy": False,
            "public_read_only_data": True,
            "closed_candles_only": True,
            "signal_retuned": False,
        },
    }


def render_table(overlay: dict[str, Any]) -> str:
    """Human-readable signal report (the CLI's stdout)."""
    lines = [
        f"TREND-OVERLAY1 current target exposure - as of {overlay['as_of_utc']} "
        f"(data through {overlay['data_as_of_utc']})",
        "",
        f"{'symbol':8} {'trend state':18} {'vol (ann.)':>10} {'weight':>8} {'target USDC':>12}",
        "-" * 62,
    ]
    for row in overlay["per_asset"]:
        vol = row["realized_vol_annual"]
        lines.append(
            f"{row['symbol']:8} {row['trend_state']:18} "
            f"{(vol[:8] if vol else 'n/a'):>10} "
            f"{Decimal(row['target_weight']):>8.4f} "
            f"{Decimal(row['target_exposure_usdc']):>12,.2f}"
        )
    p = overlay["portfolio"]
    lines += [
        "-" * 62,
        (
            f"{'PORTFOLIO':8} gross weight {Decimal(p['gross_target_weight']):.4f} "
            f"= {Decimal(p['gross_target_exposure_usdc']):,.2f} USDC of "
            f"{Decimal(overlay['account_size_usdc']):,.0f} "
            f"({p['assets_held']} held / {p['assets_flat']} flat)"
        ),
        "",
        overlay["disclaimer"],
    ]
    return "\n".join(lines)
