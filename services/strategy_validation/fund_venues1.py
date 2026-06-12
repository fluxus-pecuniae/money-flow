"""FUND-VENUES1 — funding carry on the deep venues, with leverage.

RESEARCH / EVIDENCE ONLY. The funding-carry family was closed at retail
(FUND-EV2) and at scale (FUND-SCALE1) on Hyperliquid(+Kraken) citations —
thin spot, unfavorable fees, 2.5 years of single-venue data. The gross edge
itself was REAL in every regime; what died was capture after costs on that
venue. DATA1 changed the evidence base: Binance and Bybit now provide 6-7
years of funding history with deep same-venue spot and published fee
schedules across multiple market cycles. FUND-VENUES1 is the structural
re-open those phases sanctioned: same hypothesis family, NEW venues, NEW
citations, deeper OOS — never a re-tune of the closed HL grids.

THE DISCIPLINE GUARD (where hope creeps in):
  - Fees are real and cited (published Binance/Bybit/OKX standard-tier
    schedules below). The operating tier is the one a 10k USDC account's
    OWN flow earns (FUND-SCALE1 lesson: fee tiers are a flow privilege —
    VIP tiers requiring $1M+ 30d volume are not assumed).
  - The GATEABLE verdict prices every fill as TAKER. Maker fills (and the
    maker-rebate ceiling at unreachable VIP tiers) are reported as an
    optimistic non-gateable bound — non-fill risk is unmodeled.
  - The venue-fair window comes from DATA1 coverage (K-036): venues whose
    public funding history cannot cover deep OOS (OKX ~3 months, Kraken ~1
    year, Hyperliquid 2023-05+) are EXCLUDED from the verdict with the
    exclusion recorded — never silently padded.
  - The cost-sensitivity sweep and the leverage sweep are reported in full;
    a pass that exists only under optimistic fees/leverage/fill assumptions
    is a fail.

Leverage (the new variable): the delta-neutral book is price-hedged, so
gross leverage L in {1, 3, 5} multiplies funding capture per unit capital —
and costs, financing, legged-gap exposure, and liquidation risk. The margin
model is explicit (borrow on the cash shortfall at a documented swept rate;
account-level intraday liquidation check with every leg marked at its worst
same-day extreme; liquidation force-closes the whole book at those stressed
prices). A liquidation event in OOS or in the stressed run fails the tail.

Constructions:
  - binance_single (primary): Binance USDT-M perp short + Binance spot long,
    all seven DATA1 assets (BTC ETH SOL XRP DOGE BNB AVAX — BNB/SOL carry
    near-zero/negative mean funding and are kept: selectivity must earn its
    keep, the universe is the venue's listing reality, not a winners list).
  - bybit_single (primary): same construction on Bybit (venue-fair window
    starts at Bybit's youngest spot listing, BNB 2022-03 — documented).
  - binance_cross_coinbase (variant): Binance perp + Coinbase spot. Deep
    spot book but retail Coinbase fees + cross-venue legging + transfers;
    XRP is excluded from this construction ONLY for its real 904-day
    Coinbase delisting hole (documented; not performance-based), BNB is not
    listed on Coinbase.

Reuses FUND-EV1's delta-neutral simulator verbatim through its seams
(``leg_cost_model`` for cited costs, ``margin_model`` for financing +
liquidation, the pending-fill queue for legged-execution stress) and
FUND-EV2's selectivity (2x entry margin, hold-while-favorable), sweep
machinery, and gate bar. Routed under the SAME ``funding_carry`` type and
gate id; the verdict labels are FUND-EV2's realistic-cost vocabulary.

Pure and deterministic: Decimal arithmetic, no I/O, no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Mapping, Sequence

try:  # pragma: no cover - exercised implicitly by both import contexts
    from services.strategy_validation import fund_ev1 as _fund_ev1
    from services.strategy_validation import fund_ev2 as _fund_ev2
    from services.strategy_validation import goal_strat1 as _goal_strat1
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

    _goal_strat1 = _load_sibling("goal_strat1.py", "fund_venues1_goal_strat1")
    _fund_ev1 = _load_sibling("fund_ev1.py", "fund_venues1_fund_ev1")
    _fund_ev2 = _load_sibling("fund_ev2.py", "fund_venues1_fund_ev2")

fund_ev1 = _fund_ev1
fund_ev2 = _fund_ev2
Candle = _goal_strat1.Candle
Dataset = _goal_strat1.Dataset
FundingCarryConfig = _fund_ev1.FundingCarryConfig
CarryAsset = _fund_ev1.CarryAsset
CarryUniverse = _fund_ev1.CarryUniverse
LegCostSpec = _fund_ev2.LegCostSpec
VenueCostModel = _fund_ev2.VenueCostModel
STRATEGY_TYPE_FUNDING_CARRY = _fund_ev1.STRATEGY_TYPE_FUNDING_CARRY
FUNDING_CARRY_GATE_ID = _fund_ev1.FUNDING_CARRY_GATE_ID
_money = _fund_ev1._money
BPS = Decimal("10000")

PHASE = "FUND-VENUES1"

VERDICT_PASS = _fund_ev2.VERDICT_PASS_V2  # carry_survives_realistic_costs_and_tail_oos
VERDICT_FAIL = _fund_ev2.VERDICT_FAIL_V2

CONSTRUCTION_BINANCE_SINGLE = "binance_single"
CONSTRUCTION_BYBIT_SINGLE = "bybit_single"
CONSTRUCTION_BINANCE_CROSS_COINBASE = "binance_cross_coinbase"
CONSTRUCTIONS = (
    CONSTRUCTION_BINANCE_SINGLE,
    CONSTRUCTION_BYBIT_SINGLE,
    CONSTRUCTION_BINANCE_CROSS_COINBASE,
)
PRIMARY_CONSTRUCTIONS = (CONSTRUCTION_BINANCE_SINGLE, CONSTRUCTION_BYBIT_SINGLE)

LEVERAGE_LEVELS = (Decimal("1"), Decimal("3"), Decimal("5"))

# Universe per construction (listing reality, not a winners list):
ASSETS_BINANCE = ("AVAX", "BNB", "BTC", "DOGE", "ETH", "SOL", "XRP")
ASSETS_BYBIT = ("AVAX", "BNB", "BTC", "DOGE", "ETH", "SOL", "XRP")
# Coinbase lists no BNB; XRP excluded ONLY for the real 904-day delisting
# hole (2021-01-19 -> 2023-07-13) that would gut the aligned window.
ASSETS_CROSS_COINBASE = ("AVAX", "BTC", "DOGE", "ETH", "SOL")
ASSETS_BY_CONSTRUCTION = {
    CONSTRUCTION_BINANCE_SINGLE: ASSETS_BINANCE,
    CONSTRUCTION_BYBIT_SINGLE: ASSETS_BYBIT,
    CONSTRUCTION_BINANCE_CROSS_COINBASE: ASSETS_CROSS_COINBASE,
}

# Venue-fair window enforcement (K-036): a venue enters the deep-OOS verdict
# only if its funding history can cover multiple cycles. OKX (~92d), Kraken
# (~366d) and Hyperliquid (1126d; already answered by FUND-EV2 on better
# calibration than DATA1 carries) are excluded WITH the reason recorded.
MIN_FUNDING_DAYS_FOR_DEEP_OOS = 1500
VENUE_EXCLUSIONS = {
    "okx": "funding_history_below_min_for_deep_oos (~92 days public window)",
    "kraken": "funding_history_below_min_for_deep_oos (~366 days public window)",
    "hyperliquid": (
        "funding_history_below_min_for_deep_oos (1126 days) and already answered "
        "by FUND-EV2 at cited HL costs (reference, not re-tested)"
    ),
}

# Grid (bounded, chosen up front): cadence x top_k per (construction,
# leverage) cell; selectivity fixed at FUND-EV2's documented values.
CADENCES_DAYS = (14, 28)
TOP_K_CHOICES = (2, 4)
ENTRY_MARGIN_MULTIPLE = _fund_ev2.ENTRY_MARGIN_MULTIPLE  # 2x round-trip
WIDE_BAND_FRACTION = _fund_ev2.WIDE_BAND_FRACTION  # 2% of equity
BASE_LEG_FRACTION = Decimal("0.5")  # leverage L => leg fraction 0.5*L

MIN_REGIME_DAYS_FOR_GATE = 30

# ---------------------------------------------------------------------------
# Cited fee schedules (the operating tier a 10k account's own flow earns).
# Sources fetched 2026-06-12 (published public fee pages; figures are the
# standard/entry tier — VIP tiers require 30d volume the strategy's own flow
# cannot earn at 10k, per the FUND-SCALE1 own-volume rule):
#   - Binance: USDS-M futures Regular user maker 2.0 / taker 5.0 bps; spot
#     Regular user maker 10 / taker 10 bps. BNB fee discounts NOT assumed.
#     VIP1 needs >= $1M 30d futures volume — out of reach at 10k carry flow.
#   - Bybit: non-VIP derivatives maker 2.0 / taker 5.5 bps; spot non-VIP
#     maker 10 / taker 10 bps.
#   - OKX (cited for the record; venue excluded for funding depth): regular
#     user Lv1 perp maker 2.0 / taker 5.0 bps; spot maker 8 / taker 10 bps.
#   - Coinbase Advanced (cross variant spot leg): taker 60 bps at the retail
#     volume tier (per the FUND-EV2 citation 2026-06-11; maker 40 bps).
#   - Maker REBATES exist only at top VIP/market-maker tiers (e.g. Binance
#     VIP9 futures maker rebate) — unreachable at this account; reported
#     only as the non-gateable ceiling, never gated on.
# ---------------------------------------------------------------------------

_BINANCE_FEES = (
    "Binance fee schedule (public fee page, fetched 2026-06-12, Regular user/VIP0): "
    "USDS-M perp maker 2.0 / taker 5.0 bps; spot maker 10 / taker 10 bps; "
    "BNB discount not assumed; VIP1 requires >=$1M 30d futures volume (own flow cannot earn it at 10k)"
)
_BYBIT_FEES = (
    "Bybit fee schedule (public fee page, fetched 2026-06-12, non-VIP): "
    "derivatives maker 2.0 / taker 5.5 bps; spot maker 10 / taker 10 bps"
)
_OKX_FEES = (
    "OKX fee schedule (public fee page, fetched 2026-06-12, regular user Lv1): "
    "perp maker 2.0 / taker 5.0 bps; spot maker 8 / taker 10 bps (cited for the record; venue excluded for funding depth)"
)
_COINBASE_FEES = (
    "Coinbase Advanced retail volume tier (per FUND-EV2 citation 2026-06-11): "
    "spot taker 60 bps, maker 40 bps"
)
_XFER = (
    "flat 2 USDC per cross-venue spot fill (on-chain transfer/settlement amortization, "
    "documented assumption carried over from FUND-EV2)"
)
_SPREAD_BASIS = (
    "modeled half-spreads with headroom over typical top-of-book on the deepest books "
    "(BTC/ETH 0.5 bps, other majors 1.0 bps; Binance/Bybit/Coinbase books are far deeper "
    "than the HL books FUND-EV2 calibrated at 0.08-2.4 bps); no per-venue l2 calibration "
    "in DATA1 — the cost-sensitivity sweep covers the residual uncertainty"
)
_MARGIN_BASIS = (
    "perp initial margin 10% (10x perp-side margin; venues allow far more on majors — "
    "conservative), maintenance 1.0% of gross notional (Binance USDS-M tier-1 maintenance "
    "0.4-0.65% for majors at small notional, modeled with buffer), borrow 0.02%/day on the "
    "cash shortfall (documented assumption at the published Binance Cross Margin USDT "
    "VIP0 ballpark; swept with the cost sweep), borrow call buffer 5% of borrowed"
)

TAKER = "taker"
MAKER = "maker"

_PERP_FEE_BPS = {
    (CONSTRUCTION_BINANCE_SINGLE, TAKER): Decimal("5.0"),
    (CONSTRUCTION_BINANCE_SINGLE, MAKER): Decimal("2.0"),
    (CONSTRUCTION_BYBIT_SINGLE, TAKER): Decimal("5.5"),
    (CONSTRUCTION_BYBIT_SINGLE, MAKER): Decimal("2.0"),
    (CONSTRUCTION_BINANCE_CROSS_COINBASE, TAKER): Decimal("5.0"),
    (CONSTRUCTION_BINANCE_CROSS_COINBASE, MAKER): Decimal("2.0"),
}
_SPOT_FEE_BPS = {
    (CONSTRUCTION_BINANCE_SINGLE, TAKER): Decimal("10.0"),
    (CONSTRUCTION_BINANCE_SINGLE, MAKER): Decimal("10.0"),
    (CONSTRUCTION_BYBIT_SINGLE, TAKER): Decimal("10.0"),
    (CONSTRUCTION_BYBIT_SINGLE, MAKER): Decimal("10.0"),
    (CONSTRUCTION_BINANCE_CROSS_COINBASE, TAKER): Decimal("60.0"),
    (CONSTRUCTION_BINANCE_CROSS_COINBASE, MAKER): Decimal("40.0"),
}
_FEE_BASIS = {
    CONSTRUCTION_BINANCE_SINGLE: _BINANCE_FEES,
    CONSTRUCTION_BYBIT_SINGLE: _BYBIT_FEES,
    CONSTRUCTION_BINANCE_CROSS_COINBASE: f"{_BINANCE_FEES}; {_COINBASE_FEES}; {_XFER}",
}

_MAJOR_HALF_SPREAD = {"BTC": Decimal("0.5"), "ETH": Decimal("0.5")}
_DEFAULT_HALF_SPREAD = Decimal("1.0")
_SLIPPAGE_BPS = Decimal("2.0")  # next-open taker aggression/timing allowance
_IMPACT_COEFF = Decimal("5")  # deepest books; DATA1 daily $ volumes are huge


def _half_spread(symbol: str) -> Decimal:
    return _MAJOR_HALF_SPREAD.get(symbol, _DEFAULT_HALF_SPREAD)


def cost_model_for(
    construction: str, scale: Decimal = Decimal("1.0"), *, fill_side: str = TAKER
) -> VenueCostModel:
    """Cited per-construction cost model. ``fill_side='maker'`` builds the
    OPTIMISTIC NON-GATEABLE bound (non-fill risk unmodeled) — the gateable
    verdict always prices taker."""
    if construction not in CONSTRUCTIONS:
        raise ValueError(f"unknown_construction:{construction}")
    if fill_side not in (TAKER, MAKER):
        raise ValueError(f"unknown_fill_side:{fill_side}")
    flat_spot = (
        Decimal("2.00") if construction == CONSTRUCTION_BINANCE_CROSS_COINBASE else Decimal("0")
    )
    specs: dict[tuple[str, str], LegCostSpec] = {}
    for symbol in ASSETS_BY_CONSTRUCTION[construction]:
        specs[(symbol, "perp")] = LegCostSpec(
            half_spread_bps=_half_spread(symbol),
            fee_bps=_PERP_FEE_BPS[(construction, fill_side)],
            impact_coefficient_bps=_IMPACT_COEFF,
            slippage_bps=_SLIPPAGE_BPS,
            flat_cost_quote=Decimal("0"),
            basis=f"{_FEE_BASIS[construction]}; {_SPREAD_BASIS}",
        )
        specs[(symbol, "spot")] = LegCostSpec(
            half_spread_bps=_half_spread(symbol),
            fee_bps=_SPOT_FEE_BPS[(construction, fill_side)],
            impact_coefficient_bps=_IMPACT_COEFF,
            slippage_bps=_SLIPPAGE_BPS,
            flat_cost_quote=flat_spot,
            basis=f"{_FEE_BASIS[construction]}; {_SPREAD_BASIS}",
        )
    return VenueCostModel(construction, specs, scale)


# ---------------------------------------------------------------------------
# Margin / financing / liquidation model (the leverage variable, explicit)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MarginModel:
    """Account-level financing + liquidation parameters for gross leverage L.

    Borrowed = max(0, spot_gross + perp_initial_margin * perp_gross - equity)
    accrues ``borrow_daily_rate`` per day. The liquidation check marks every
    leg at its worst same-day extreme (perp short at the HIGH, spot long at
    the LOW — adversarial simultaneity, conservative for basis risk):
    stressed equity below ``maintenance_rate * gross_notional +
    borrow_call_buffer * borrowed`` force-closes the whole book at those
    stressed prices. The cost sweep scales the borrow rate together with
    every other cost term (``with_scale``)."""

    leverage: Decimal
    perp_initial_margin: Decimal = Decimal("0.10")
    maintenance_rate: Decimal = Decimal("0.01")
    borrow_daily_rate: Decimal = Decimal("0.0002")  # 0.02%/day, documented + swept
    borrow_call_buffer: Decimal = Decimal("0.05")
    basis: str = _MARGIN_BASIS

    def with_scale(self, scale: Decimal) -> "MarginModel":
        from dataclasses import replace

        return replace(self, borrow_daily_rate=self.borrow_daily_rate * scale)


def margin_model_for(leverage: Decimal, scale: Decimal = Decimal("1.0")) -> MarginModel:
    if leverage not in LEVERAGE_LEVELS:
        raise ValueError(f"leverage_not_in_documented_levels:{leverage}")
    return MarginModel(leverage=leverage).with_scale(scale)


# ---------------------------------------------------------------------------
# Config grid per (construction, leverage) cell
# ---------------------------------------------------------------------------


def config_for(
    construction: str, leverage: Decimal, cadence: int, top_k: int
) -> FundingCarryConfig:
    return FundingCarryConfig(
        config_id=(
            f"fund_venues1_{construction}_lev{leverage}_cad{cadence}_top{top_k}_1d"
        ),
        strategy_type=STRATEGY_TYPE_FUNDING_CARRY,
        mode="collect_only",  # flip side needs coin borrow — not leaned on
        rebalance_interval_days=cadence,
        top_k=top_k,
        leg_notional_fraction=BASE_LEG_FRACTION * leverage,
        min_trade_notional_fraction=WIDE_BAND_FRACTION,
        entry_margin_multiple=ENTRY_MARGIN_MULTIPLE,
        planned_hold_days=cadence,
        venue_construction=construction,
    )


def generate_cell_configs(construction: str, leverage: Decimal) -> list[FundingCarryConfig]:
    return [
        config_for(construction, leverage, cadence, top_k)
        for cadence in CADENCES_DAYS
        for top_k in TOP_K_CHOICES
    ]


# ---------------------------------------------------------------------------
# DATA1 -> CarryUniverse adapter (pure: takes plain row dicts)
# ---------------------------------------------------------------------------


class ZeroVolumeCandleError(ValueError):
    """A used candle series contains zero-volume (venue-backfill) rows."""


def _parse_close(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def dataset_from_data1_rows(
    symbol: str,
    venue: str,
    series: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    forbid_zero_volume: bool = True,
) -> Dataset:
    """DATA1 normalized daily candles -> the goal_strat1 Dataset the FUND
    simulators consume. Candles are keyed by CLOSE time (the FUND-EV1
    convention). Zero-volume rows are venue backfill, not market history
    (K-036) — using one is refused, never silently included."""
    candles: list[Candle] = []
    for row in rows:
        volume = Decimal(str(row["volume_base"]))
        if forbid_zero_volume and volume == 0:
            raise ZeroVolumeCandleError(
                f"zero_volume_backfill_candle:{venue}:{symbol}:{series}:{row['close_time']}"
            )
        candles.append(
            Candle(
                symbol=symbol,
                timeframe="1d",
                timestamp=_parse_close(str(row["close_time"])),
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=volume,
                source_path=f"data1:{venue}:{symbol}:{series}",
            )
        )
    candles.sort(key=lambda c: c.timestamp)
    return Dataset(
        symbol=symbol,
        timeframe="1d",
        source_path=f"data1:{venue}:{symbol}:{series}",
        source_provenance=f"data1_multi_venue_snapshot:{venue}",
        canonical_evidence_status="research_data1_multi_venue",
        candles=tuple(candles),
    )


def funding_maps_from_data1(
    daily_rows: Sequence[Mapping[str, Any]],
    *,
    interval_hours: Decimal | float,
) -> tuple[dict[datetime, Decimal], dict[datetime, int]]:
    """DATA1 daily funding sums -> (funding_by_close, hours_by_close).

    DATA1 records per-day EVENT counts at the venue's native interval (8h
    venues: 3/day; 1h venues: 24/day). The FUND-EV1 ``CarryUniverse`` keeps
    a day only when its funding slot is COMPLETE (hours == 24); a complete
    day here is one with at least the expected event count for the observed
    interval (intervals can shorten under venue stress — more events is
    still complete coverage; fewer is a partial day and stays excluded,
    never scaled or filled)."""
    expected = max(1, round(24.0 / float(interval_hours)))
    funding_by_close: dict[datetime, Decimal] = {}
    hours_by_close: dict[datetime, int] = {}
    for row in daily_rows:
        t = _parse_close(str(row["close_time"]))
        events = int(row["events"])
        funding_by_close[t] = Decimal(str(row["funding_rate_sum"]))
        hours_by_close[t] = 24 if events >= expected else events
    return funding_by_close, hours_by_close


def venue_fair_funding_check(
    funding_days_by_venue: Mapping[str, int],
    *,
    min_days: int = MIN_FUNDING_DAYS_FOR_DEEP_OOS,
) -> dict[str, dict[str, Any]]:
    """The K-036 enforcement, auditable: which venues may carry a deep-OOS
    funding verdict, and the explicit exclusion reason for the rest."""
    table: dict[str, dict[str, Any]] = {}
    for venue, days in sorted(funding_days_by_venue.items()):
        eligible = days >= min_days
        reason = None
        if not eligible:
            reason = VENUE_EXCLUSIONS.get(
                venue, f"funding_history_below_min_for_deep_oos ({days} days)"
            )
        table[venue] = {
            "funding_days": days,
            "eligible_for_deep_oos_verdict": eligible,
            "exclusion_reason": reason,
        }
    return table


def build_carry_universe(
    assets_rows: Mapping[str, Mapping[str, Any]],
) -> CarryUniverse:
    """Assemble the CarryUniverse from per-symbol DATA1 row bundles:
    ``{symbol: {perp_rows, spot_rows, funding_rows, interval_hours,
    perp_venue, spot_venue}}``. The aligned timeline is the intersection
    where EVERY asset has a perp candle, a spot candle, and a complete
    funding day (the FUND-EV1 rule; listing offsets shrink the window —
    documented, never padded)."""
    carry_assets: list[CarryAsset] = []
    for symbol, bundle in sorted(assets_rows.items()):
        perp = dataset_from_data1_rows(
            symbol, str(bundle["perp_venue"]), "perp_1d", bundle["perp_rows"]
        )
        spot = dataset_from_data1_rows(
            symbol, str(bundle["spot_venue"]), "spot_1d", bundle["spot_rows"]
        )
        funding_by_close, hours_by_close = funding_maps_from_data1(
            bundle["funding_rows"], interval_hours=bundle["interval_hours"]
        )
        carry_assets.append(
            CarryAsset(
                symbol=symbol,
                perp=perp,
                spot=spot,
                funding_by_close=funding_by_close,
                funding_hours_by_close=hours_by_close,
            )
        )
    return CarryUniverse(carry_assets)


# ---------------------------------------------------------------------------
# Calendar-cycle segments (reported alongside the point-in-time regimes)
# ---------------------------------------------------------------------------

CYCLE_SEGMENTS: tuple[tuple[str, str, str], ...] = (
    ("2020_2021_bull", "2020-01-01T00:00:00Z", "2022-01-01T00:00:00Z"),
    ("2022_bear", "2022-01-01T00:00:00Z", "2023-01-01T00:00:00Z"),
    ("2023_2024_recovery", "2023-01-01T00:00:00Z", "2025-01-01T00:00:00Z"),
    ("2025_2026_current", "2025-01-01T00:00:00Z", "2027-01-01T00:00:00Z"),
)


def cycle_segment_nets(
    equity_curve: Sequence[tuple[datetime, Decimal]],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for label, start_s, end_s in CYCLE_SEGMENTS:
        start, end = _parse_close(start_s), _parse_close(end_s)
        window = [(t, v) for t, v in equity_curve if start < t <= end]
        out[label] = {
            "days": len(window),
            "net_pnl": _money(window[-1][1] - window[0][1]) if len(window) >= 2 else None,
        }
    return out


def regime_pnls_in_window(
    equity_curve: Sequence[tuple[datetime, Decimal]],
    regimes: Mapping[datetime, str],
    *,
    after: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Point-in-time regime attribution restricted to (after, end] — the
    per-OOS-regime breakdown the v3 gate judges."""
    window = [(t, v) for t, v in equity_curve if after is None or t > after]
    out: dict[str, dict[str, Any]] = {
        label: {"days": 0, "net_pnl": Decimal("0")} for label in ("bull", "neutral", "bear")
    }
    for i in range(1, len(window)):
        t, value = window[i]
        label = regimes.get(t, "neutral")
        out[label]["days"] += 1
        out[label]["net_pnl"] += value - window[i - 1][1]
    for label in out:
        out[label]["net_pnl"] = _money(out[label]["net_pnl"])
    return out


# ---------------------------------------------------------------------------
# The v3 gate: EV2's realistic-cost bar + every-OOS-regime + liquidation
# ---------------------------------------------------------------------------


def evaluate_funding_carry_gate_v3(
    *,
    leverage: Decimal,
    oos_regime_pnls: Mapping[str, Mapping[str, Any]],
    liquidation_count_oos: int,
    liquidation_count_stressed: int,
    cost_sensitivity_sweep: Sequence[dict[str, Any]],
    min_regime_days: int = MIN_REGIME_DAYS_FOR_GATE,
    **gate_kwargs: Any,
) -> dict[str, Any]:
    """FUND-EV2's full bar (OOS net positive at cited taker costs,
    walk-forward folds, non-bull, leave-one-out, tail/stress drawdown
    limits, cost-sensitivity breakpoint + fragility) PLUS, per the
    FUND-VENUES1 brief:
      - net positive in EVERY point-in-time regime bucket of the OOS window
        that has at least ``min_regime_days`` days (a bucket too small to
        judge is a non-failing qualifier, never a silent pass);
      - ZERO liquidation events in the OOS window AND in the stressed run
        at this leverage (a 'neutral' book that can be liquidated on a gap
        has no tested edge).
    The drawdown limits are FUND-EV1's absolute account limits — leverage
    that blows them fails the tail; the bar does not stretch with L."""
    gate = _fund_ev2.evaluate_funding_carry_gate_v2(
        cost_sensitivity_sweep=cost_sensitivity_sweep, **gate_kwargs
    )
    extra_reasons: list[str] = []
    extra_qualifiers: list[str] = []
    for label in ("bear", "neutral", "bull"):
        row = oos_regime_pnls.get(label, {})
        days = int(row.get("days", 0))
        net = row.get("net_pnl")
        if days >= min_regime_days:
            if net is None or Decimal(str(net)) <= 0:
                extra_reasons.append(f"oos_regime_{label}_net_carry_not_positive")
        else:
            extra_qualifiers.append(
                f"oos_regime_{label}_sample_too_small_to_judge_{days}d"
            )
    if liquidation_count_oos > 0:
        extra_reasons.append("liquidation_event_in_oos")
    if liquidation_count_stressed > 0:
        extra_reasons.append("liquidation_event_in_stressed_run")

    passed = bool(gate["passed"]) and not extra_reasons
    reasons = (
        ["funding_carry_gate_passed_at_cited_realistic_costs"]
        if passed
        else [r for r in gate["reason_codes"] if r != "funding_carry_gate_passed_at_cited_realistic_costs"]
        + extra_reasons
    )
    out = dict(gate)
    out["status"] = VERDICT_PASS if passed else VERDICT_FAIL
    out["passed"] = passed
    out["reason_codes"] = reasons
    out["qualifiers"] = list(gate["qualifiers"]) + extra_qualifiers
    out["leverage_gross"] = str(leverage)
    out["oos_regime_pnls"] = {
        label: {"days": row.get("days", 0), "net_pnl": str(row.get("net_pnl"))}
        for label, row in oos_regime_pnls.items()
    }
    out["liquidation_count_oos"] = liquidation_count_oos
    out["liquidation_count_stressed"] = liquidation_count_stressed
    out["min_regime_days_for_gate"] = min_regime_days
    return out


def boundary_flags() -> dict[str, bool]:
    flags = dict(_fund_ev2.boundary_flags())
    flags.update(
        {
            "venue_fair_window_enforced_from_data1_coverage": True,
            "maker_fills_reported_as_non_gateable_bound_only": True,
            "leverage_financing_and_liquidation_modeled": True,
            "borrow_rate_documented_assumption_swept": True,
            "no_per_venue_l2_calibration_spreads_modeled_with_headroom_swept": True,
        }
    )
    return flags
