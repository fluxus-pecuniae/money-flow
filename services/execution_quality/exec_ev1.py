"""EXEC-EV1 — depth-aware modeled execution-friction layer.

RESEARCH / EVIDENCE ASSUMPTION LAYER ONLY. Every cost here is a MODELED
assumption with a documented rationale; none of it is real fill data.

IMPORTANT — modeled, not real, depth:
    The liquidity/depth inputs below are derived from historical *candle volume*,
    NOT from real historical order-book depth. Historical order-book depth does
    not exist for this data: Hyperliquid public ``l2Book`` is a current snapshot
    only. Treat every number produced here as an assumption, never as observed
    execution. This partially addresses K-001 (no real depth-aware execution
    quality) with a modeled layer; it does not resolve it.

SV2.3 already models a flat ``fee + slippage + adverse_gap`` per fill. EXEC-EV1
keeps those terms and ADDS three depth-aware terms on top, so for the same lane,
candles, and parent scenario the EXEC-EV1 cost is always >= the SV2.3 cost
(friction can only subtract from PnL):

  1. Spread cost      — a per-symbol liquidity-tier half-spread (bps). Majors
                        (BTC/ETH) are tightest; large alts wider; mid alts widest.
  2. Market impact    — size-aware. Scales with the *participation rate*
                        ``notional / liquidity_proxy`` under a square-root impact
                        law (Almgren-style): impact grows with the square root of
                        the fraction of the interval's dollar-volume consumed.
  3. Fill probability — an explicit ``fill_probability`` for the chosen
                        market-style next-open fill; the unfilled fraction is
                        assumed to chase the market at ``chase_penalty_bps``.

The model is pure and deterministic (Decimal arithmetic, no I/O, no network) so
it is importable from tests and runs in CI without external data.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

BPS = Decimal("10000")


def _dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Liquidity tiers (documented assumption table)
# ---------------------------------------------------------------------------
# Half-spread assumptions in bps per liquidity tier. These are MODELED typical
# perp half-spreads on a liquid venue, not measured quotes. A future, clearly
# optional one-shot read-only public l2Book calibration could refine these; it
# is NOT part of any deterministic evidence run.

TIER_MAJOR = "major_perp"
TIER_LARGE = "large_perp"
TIER_MID = "mid_alt_perp"

TIER_HALF_SPREAD_BPS: dict[str, Decimal] = {
    TIER_MAJOR: Decimal("1.0"),
    TIER_LARGE: Decimal("2.5"),
    TIER_MID: Decimal("5.0"),
}

# Founder 23-symbol universe tiered by assumed liquidity. Anything not listed
# falls back to the widest (mid-alt) tier — a conservative default.
SYMBOL_TIERS: dict[str, str] = {
    "BTC": TIER_MAJOR,
    "ETH": TIER_MAJOR,
    "SOL": TIER_LARGE,
    "XRP": TIER_LARGE,
    "DOGE": TIER_LARGE,
    "BNB": TIER_LARGE,
    "SUI": TIER_LARGE,
    "AVAX": TIER_LARGE,
    "TRX": TIER_LARGE,
    "ADA": TIER_LARGE,
    "LINK": TIER_LARGE,
    "LTC": TIER_LARGE,
    "UNI": TIER_LARGE,
    "DOT": TIER_LARGE,
    "AAVE": TIER_LARGE,
    # Mid alts (explicit for clarity; same as the default fallback).
    "HYPE": TIER_MID,
    "ZEC": TIER_MID,
    "XMR": TIER_MID,
    "TON": TIER_MID,
    "ASTER": TIER_MID,
    "POL": TIER_MID,
    "FIL": TIER_MID,
    "TRUMP": TIER_MID,
}


def symbol_tier(symbol: str) -> str:
    return SYMBOL_TIERS.get(symbol.upper(), TIER_MID)


def half_spread_bps(symbol: str) -> Decimal:
    return TIER_HALF_SPREAD_BPS[symbol_tier(symbol)]


# ---------------------------------------------------------------------------
# Liquidity proxy + participation rate
# ---------------------------------------------------------------------------


def candle_typical_price(candle: dict[str, Any]) -> Decimal:
    """(high + low + close) / 3 — the standard typical-price proxy."""
    return (
        _dec(candle.get("high")) + _dec(candle.get("low")) + _dec(candle.get("close"))
    ) / Decimal("3")


def candle_dollar_volume(candle: dict[str, Any]) -> Decimal:
    """Modeled interval liquidity proxy = base-asset volume * typical price.

    This is the dollar value traded during the candle and is the only
    liquidity signal available from historical candles. It is a PROXY for
    available depth, not real depth.
    """
    return _dec(candle.get("volume")) * candle_typical_price(candle)


def participation_rate(notional: Decimal, liquidity_proxy: Decimal) -> Decimal:
    """Fraction of the interval's dollar-volume consumed by the order.

    Clamped to [0, 1]. A non-positive liquidity proxy (no/zero volume) is the
    worst case and maps to full participation (=1).
    """
    if notional <= 0:
        return Decimal("0")
    if liquidity_proxy <= 0:
        return Decimal("1")
    return min(Decimal("1"), notional / liquidity_proxy)


# ---------------------------------------------------------------------------
# Cost components
# ---------------------------------------------------------------------------


def market_impact_bps(
    notional: Decimal, liquidity_proxy: Decimal, impact_coefficient_bps: Decimal
) -> Decimal:
    """Square-root market-impact law (Almgren-style).

    impact_bps = impact_coefficient_bps * sqrt(participation_rate)

    Grows with order size (notional) and shrinks as the liquidity proxy grows —
    so the same order costs more in a thin interval than a deep one. At full
    participation (order == interval volume) the cost equals the coefficient.
    """
    p = participation_rate(notional, liquidity_proxy)
    if p <= 0:
        return Decimal("0")
    return _money(impact_coefficient_bps * p.sqrt())


def unfilled_chase_bps(fill_probability: Decimal, chase_penalty_bps: Decimal) -> Decimal:
    """Fill-probability term.

    For market-style next-open fills the order is ~fully filled, but in fast
    markets a fraction may not fill at the quoted level and must chase. The
    unfilled fraction ``(1 - fill_probability)`` is charged ``chase_penalty_bps``.
    """
    shortfall = max(Decimal("0"), Decimal("1") - fill_probability)
    return _money(shortfall * chase_penalty_bps)


# ---------------------------------------------------------------------------
# Scenario + friction breakdown
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DepthAwareScenario:
    """An EXEC-EV1 scenario: the SV2.3 parent terms plus depth-aware additions.

    The SV2.3 terms (fee/slippage/adverse-gap) are inherited verbatim from
    ``sv23_parent_scenario`` so EXEC-EV1 cost >= SV2.3 cost on identical data.
    """

    scenario_id: str
    label: str
    # Inherited SV2.3 terms (kept verbatim from the parent scenario):
    fee_bps: Decimal
    slippage_bps: Decimal
    adverse_gap_penalty_bps: Decimal
    adverse_gap_warn_bps: Decimal
    # EXEC-EV1 added depth-aware terms:
    spread_tier_multiplier: Decimal
    impact_coefficient_bps: Decimal
    fill_probability: Decimal
    chase_penalty_bps: Decimal
    sv23_parent_scenario: str
    description: str


@dataclass(frozen=True, slots=True)
class FrictionBreakdown:
    spread_bps: Decimal
    impact_bps: Decimal
    slippage_bps: Decimal
    adverse_gap_bps: Decimal
    chase_bps: Decimal
    total_bps: Decimal


def fill_friction_bps(
    *,
    scenario: DepthAwareScenario,
    symbol: str,
    notional: Decimal,
    liquidity_proxy: Decimal,
    adverse_gap: Decimal,
) -> FrictionBreakdown:
    """Per-fill, per-side friction in bps. All terms are non-negative, so the
    total is always >= the SV2.3 parent's (slippage + adverse-gap) total."""
    spread = _money(half_spread_bps(symbol) * scenario.spread_tier_multiplier)
    impact = market_impact_bps(notional, liquidity_proxy, scenario.impact_coefficient_bps)
    slippage = scenario.slippage_bps
    gap = scenario.adverse_gap_penalty_bps if adverse_gap > 0 else Decimal("0")
    chase = unfilled_chase_bps(scenario.fill_probability, scenario.chase_penalty_bps)
    total = _money(spread + impact + slippage + gap + chase)
    return FrictionBreakdown(
        spread_bps=spread,
        impact_bps=impact,
        slippage_bps=slippage,
        adverse_gap_bps=gap,
        chase_bps=chase,
        total_bps=total,
    )


def depth_aware_execution_price(
    *, raw_price: Decimal, side: str, friction_total_bps: Decimal
) -> Decimal:
    """Adjust a raw fill price by the total friction (buy pays more, sell receives less)."""
    rate = friction_total_bps / BPS
    if side == "buy":
        return _money(raw_price * (Decimal("1") + rate))
    return _money(raw_price * (Decimal("1") - rate))


# ---------------------------------------------------------------------------
# Entry-timing (late-entry) cost — Must 3
# ---------------------------------------------------------------------------


def entry_timing_cost_bps(
    candles: list[dict[str, Any]], signal_index: int, lateness: int, side: str
) -> Decimal | None:
    """Adverse price move (bps) from the signal candle close to a *late* fill.

    ``lateness == 0`` is the SV2.3 baseline (fill at the next candle's open).
    ``lateness == k`` fills ``k`` candles later still. A positive result means
    entering late was more expensive than the signal-implied reference price.

    Returns None when there is no candle at the requested lateness.
    """
    if signal_index < 0 or signal_index >= len(candles):
        return None
    signal_close = _dec(candles[signal_index].get("close"))
    if signal_close <= 0:
        return None
    fill_index = signal_index + 1 + lateness
    if fill_index >= len(candles):
        return None
    fill_open = _dec(candles[fill_index].get("open"))
    if side == "buy":
        return (fill_open - signal_close) / signal_close * BPS
    return (signal_close - fill_open) / signal_close * BPS


# ---------------------------------------------------------------------------
# EXEC-EV1 scenarios (parented to the three SV2.3 scenarios)
# ---------------------------------------------------------------------------

DEPTH_AWARE_SCENARIOS: tuple[DepthAwareScenario, ...] = (
    DepthAwareScenario(
        scenario_id="exec_ev1_base",
        label="EXEC-EV1 base depth-aware",
        fee_bps=Decimal("5"),
        slippage_bps=Decimal("3"),
        adverse_gap_penalty_bps=Decimal("0"),
        adverse_gap_warn_bps=Decimal("250"),
        spread_tier_multiplier=Decimal("1.0"),
        impact_coefficient_bps=Decimal("20"),
        fill_probability=Decimal("1.00"),
        chase_penalty_bps=Decimal("50"),
        sv23_parent_scenario="base_next_open",
        description=(
            "SV2.3 base terms plus tier half-spread, square-root impact "
            "(coef 20 bps), and full market-style fill probability."
        ),
    ),
    DepthAwareScenario(
        scenario_id="exec_ev1_conservative",
        label="EXEC-EV1 conservative depth-aware",
        fee_bps=Decimal("5"),
        slippage_bps=Decimal("8"),
        adverse_gap_penalty_bps=Decimal("2"),
        adverse_gap_warn_bps=Decimal("150"),
        spread_tier_multiplier=Decimal("1.5"),
        impact_coefficient_bps=Decimal("40"),
        fill_probability=Decimal("0.98"),
        chase_penalty_bps=Decimal("80"),
        sv23_parent_scenario="conservative_next_open",
        description=(
            "SV2.3 conservative terms plus 1.5x tier half-spread, square-root "
            "impact (coef 40 bps), and a 2% unfilled-chase term."
        ),
    ),
    DepthAwareScenario(
        scenario_id="exec_ev1_stress",
        label="EXEC-EV1 stress depth-aware",
        fee_bps=Decimal("5"),
        slippage_bps=Decimal("15"),
        adverse_gap_penalty_bps=Decimal("5"),
        adverse_gap_warn_bps=Decimal("75"),
        spread_tier_multiplier=Decimal("2.0"),
        impact_coefficient_bps=Decimal("80"),
        fill_probability=Decimal("0.95"),
        chase_penalty_bps=Decimal("120"),
        sv23_parent_scenario="stress_next_open",
        description=(
            "SV2.3 stress terms plus 2x tier half-spread, square-root impact "
            "(coef 80 bps), and a 5% unfilled-chase term."
        ),
    ),
)


def scenario_by_id(scenario_id: str) -> DepthAwareScenario:
    for scenario in DEPTH_AWARE_SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(scenario_id)
