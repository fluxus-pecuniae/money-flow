"""FUND-SCALE1 — funding carry: scale & fee-tier viability map.

RESEARCH / EVIDENCE ONLY. FUND-EV2 closed funding carry AT 10K RETAIL under
cited realistic costs and explicitly sanctioned ONE follow-up axis as new
evidence: account size + cited institutional fee tiers. FUND-SCALE1 maps
that axis: at what capital and fee tier does net-after-cost OOS funding
cross positive — and where does growing market impact eat it again? This is
NOT a re-tune of the retail case (FUND-EV2's retail verdict stands; the 10k
@ base-tier cell here simply reproduces it); it is the size/fee axis.

THE DISCIPLINE GUARD (same standard as FUND-EV2):
  - Fee tiers are the PUBLISHED schedules, cited below — never invented.
  - Both effects of size are modeled: lower fees / amortized fixed costs
    (helps) AND higher market impact via EXEC-EV1's square-root law driven
    by the actual per-size traded notional (hurts) — the deliverable is a
    viability BAND, not "bigger always wins".
  - HONESTY ON TIER QUALIFICATION: a fee tier is only "achieved" if the
    strategy's OWN traded volume at that size reaches the published
    qualifying volume (HL: 14-day weighted volume, spot counted DOUBLE per
    the docs; Kraken: 30-day volume). Cells priced at tiers the strategy's
    own flow cannot reach are marked `tier_assumed_not_achieved` — they
    answer "what would it take", they are not the operator's path.
  - IMPACT PLAUSIBILITY: cells where any single fill exceeds
    ``PARTICIPATION_PLAUSIBILITY_MAX`` (10%) of that candle's dollar volume
    are outside the impact model's credible range and CANNOT pass, however
    good the modeled number looks.

Cited fee schedules (fetched 2026-06-11):
  - Hyperliquid docs, volume tiers (14d weighted volume; spot counts 2x):
    perps taker/maker — T0 base 4.5/1.5, T1 >$5M 4.0/1.2, T2 >$25M 3.5/0.8,
    T3 >$100M 3.0/0.4, T4 >$500M 2.8/0.0, T5 >$2B 2.6/0.0, T6 >$7B 2.4/0.0
    (bps); spot taker/maker — T0 7.0/4.0, T1 6.0/3.0, T2 5.0/2.0, T3
    4.0/1.0, T4 3.5/0.0, T5 3.0/0.0, T6 2.5/0.0 (bps). Maker-volume-share
    rebates (-0.1/-0.2/-0.3 bps at >0.5%/1.5%/3% maker share) require being
    a top-of-book market maker — out of scope, noted not modeled.
  - Kraken Pro spot tiers (30d volume): taker 40 bps base, 35 >$10k,
    24 >$50k, 22 >$100k, 20 >$250k, 18 >$500k, 16 >$1M, 14 >$2.5M,
    12 >$5M, 10 >$10M, 8 >$100M, 5 >$500M.

Spreads/impact/slippage/settlement stay the FUND-EV2 cited model (l2Book
calibration + flat 2 USDC cross-venue settlement, which now AMORTIZES with
size); only the FEE term moves with the published tier, and impact moves
with the actual traded notional.

Maker-bound line: an explicitly OPTIMISTIC, NON-GATEABLE upper bound (all
fills passive at maker fees, zero half-spread paid) — passive fills carry
unmodeled non-fill/chase risk, so this line can inform but never pass.

Pure and deterministic: Decimal arithmetic, no I/O, no network.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any, Sequence

try:  # pragma: no cover - exercised implicitly by both import contexts
    from services.strategy_validation import fund_ev2 as _fund_ev2
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

    _fund_ev2 = _load_sibling("fund_ev2.py", "fund_scale1_fund_ev2")

fund_ev2 = _fund_ev2
fund_ev1 = _fund_ev2.fund_ev1
_money = fund_ev1._money
BPS = Decimal("10000")

PHASE = "FUND-SCALE1"

ACCOUNT_SIZES_USDC: tuple[Decimal, ...] = (
    Decimal("10000"),
    Decimal("50000"),
    Decimal("250000"),
    Decimal("1000000"),
    Decimal("5000000"),
)

# A single fill above this fraction of its candle's dollar volume is outside
# the EXEC-EV1 sqrt-impact model's credible range (documented threshold).
PARTICIPATION_PLAUSIBILITY_MAX = Decimal("0.10")

VERDICT_VIABLE_PREFIX = "carry_viable_in_band"
VERDICT_NOT_VIABLE = "carry_does_not_reach_viability_at_credible_scale"

_HL_TIER_BASIS = (
    "Hyperliquid docs fee tiers (fetched 2026-06-11): 14d weighted volume, "
    "spot counted double toward the tier"
)
_KRAKEN_TIER_BASIS = "Kraken Pro fee schedule (fetched 2026-06-11): 30d volume tiers"


@dataclass(frozen=True, slots=True)
class HlFeeTier:
    tier_id: str
    qualifying_weighted_14d_volume_usd: Decimal  # 0 = base
    perp_taker_bps: Decimal
    perp_maker_bps: Decimal
    spot_taker_bps: Decimal
    spot_maker_bps: Decimal
    basis: str = _HL_TIER_BASIS


HL_FEE_TIERS: tuple[HlFeeTier, ...] = (
    HlFeeTier("hl_tier_0", Decimal("0"), Decimal("4.5"), Decimal("1.5"), Decimal("7.0"), Decimal("4.0")),
    HlFeeTier("hl_tier_1", Decimal("5000000"), Decimal("4.0"), Decimal("1.2"), Decimal("6.0"), Decimal("3.0")),
    HlFeeTier("hl_tier_2", Decimal("25000000"), Decimal("3.5"), Decimal("0.8"), Decimal("5.0"), Decimal("2.0")),
    HlFeeTier("hl_tier_3", Decimal("100000000"), Decimal("3.0"), Decimal("0.4"), Decimal("4.0"), Decimal("1.0")),
    HlFeeTier("hl_tier_4", Decimal("500000000"), Decimal("2.8"), Decimal("0.0"), Decimal("3.5"), Decimal("0.0")),
    HlFeeTier("hl_tier_5", Decimal("2000000000"), Decimal("2.6"), Decimal("0.0"), Decimal("3.0"), Decimal("0.0")),
    HlFeeTier("hl_tier_6", Decimal("7000000000"), Decimal("2.4"), Decimal("0.0"), Decimal("2.5"), Decimal("0.0")),
)

# The sweep prices tiers 0-4; tiers 5/6 differ by 0.2-0.4 bps from tier 4
# and require $2B-$7B 14d volume — included in the cited table above for
# completeness, excluded from the sweep as economically indistinguishable.
HL_SWEEP_TIERS: tuple[HlFeeTier, ...] = HL_FEE_TIERS[:5]


@dataclass(frozen=True, slots=True)
class KrakenFeeTier:
    tier_id: str
    qualifying_30d_volume_usd: Decimal
    taker_bps: Decimal
    maker_bps: Decimal
    basis: str = _KRAKEN_TIER_BASIS


KRAKEN_FEE_TIERS: tuple[KrakenFeeTier, ...] = (
    KrakenFeeTier("kraken_tier_0", Decimal("0"), Decimal("40"), Decimal("25")),
    KrakenFeeTier("kraken_tier_10k", Decimal("10000"), Decimal("35"), Decimal("20")),
    KrakenFeeTier("kraken_tier_50k", Decimal("50000"), Decimal("24"), Decimal("14")),
    KrakenFeeTier("kraken_tier_100k", Decimal("100000"), Decimal("22"), Decimal("12")),
    KrakenFeeTier("kraken_tier_250k", Decimal("250000"), Decimal("20"), Decimal("10")),
    KrakenFeeTier("kraken_tier_500k", Decimal("500000"), Decimal("18"), Decimal("8")),
    KrakenFeeTier("kraken_tier_1m", Decimal("1000000"), Decimal("16"), Decimal("6")),
    KrakenFeeTier("kraken_tier_2_5m", Decimal("2500000"), Decimal("14"), Decimal("4")),
    KrakenFeeTier("kraken_tier_5m", Decimal("5000000"), Decimal("12"), Decimal("2")),
    KrakenFeeTier("kraken_tier_10m", Decimal("10000000"), Decimal("10"), Decimal("0")),
    KrakenFeeTier("kraken_tier_100m", Decimal("100000000"), Decimal("8"), Decimal("0")),
    KrakenFeeTier("kraken_tier_500m", Decimal("500000000"), Decimal("5"), Decimal("0")),
)

# Cross-venue sweep ladder (representative VIP rungs; HL perp leg stays at
# its own achieved/swept tier separately — second-order next to spot fees).
KRAKEN_SWEEP_TIERS: tuple[KrakenFeeTier, ...] = (
    KRAKEN_FEE_TIERS[0],   # 40 bps base
    KRAKEN_FEE_TIERS[3],   # 22 bps >$100k
    KRAKEN_FEE_TIERS[6],   # 16 bps >$1M
    KRAKEN_FEE_TIERS[9],   # 10 bps >$10M
    KRAKEN_FEE_TIERS[10],  # 8 bps  >$100M
)


# ---------------------------------------------------------------------------
# Tiered cost models (FUND-EV2 cited spreads/impact; only the FEE term moves)
# ---------------------------------------------------------------------------


def hl_tier_cost_model(tier: HlFeeTier) -> Any:
    base = fund_ev2.hl_single_cost_model()
    specs: dict[tuple[str, str], Any] = {}
    for symbol in fund_ev1.CARRY_UNIVERSE:
        perp = base.spec(symbol, "perp")
        spot = base.spec(symbol, "spot")
        specs[(symbol, "perp")] = replace(
            perp,
            fee_bps=tier.perp_taker_bps,
            basis=f"{perp.basis}; {tier.tier_id}: {tier.basis}",
        )
        specs[(symbol, "spot")] = replace(
            spot,
            fee_bps=tier.spot_taker_bps,
            basis=f"{spot.basis}; {tier.tier_id}: {tier.basis}",
        )
    return fund_ev2.VenueCostModel(fund_ev2.CONSTRUCTION_HL_SINGLE, specs)


def cross_venue_tier_cost_model(
    kraken_tier: KrakenFeeTier, hl_tier: HlFeeTier = HL_FEE_TIERS[0]
) -> Any:
    base = fund_ev2.cross_venue_cost_model()
    specs: dict[tuple[str, str], Any] = {}
    for symbol in fund_ev1.CARRY_UNIVERSE:
        perp = base.spec(symbol, "perp")
        spot = base.spec(symbol, "spot")
        specs[(symbol, "perp")] = replace(
            perp,
            fee_bps=hl_tier.perp_taker_bps,
            basis=f"{perp.basis}; {hl_tier.tier_id}: {hl_tier.basis}",
        )
        specs[(symbol, "spot")] = replace(
            spot,
            fee_bps=kraken_tier.taker_bps,
            basis=f"{spot.basis}; {kraken_tier.tier_id}: {kraken_tier.basis}",
        )
    return fund_ev2.VenueCostModel(fund_ev2.CONSTRUCTION_CROSS_VENUE, specs)


def maker_bound_cost_model() -> Any:
    """OPTIMISTIC, NON-GATEABLE upper bound: every fill passive at HL base
    maker fees, zero half-spread paid. Passive fills carry unmodeled
    non-fill/chase risk; this line informs, it never passes a gate."""
    base = fund_ev2.hl_single_cost_model()
    tier = HL_FEE_TIERS[0]
    specs: dict[tuple[str, str], Any] = {}
    for symbol in fund_ev1.CARRY_UNIVERSE:
        for leg, fee in (("perp", tier.perp_maker_bps), ("spot", tier.spot_maker_bps)):
            spec = base.spec(symbol, leg)
            specs[(symbol, leg)] = replace(
                spec,
                half_spread_bps=Decimal("0"),
                fee_bps=fee,
                basis=(
                    f"{spec.basis}; OPTIMISTIC maker bound (base-tier maker fees, "
                    "no half-spread paid; non-fill risk NOT modeled)"
                ),
            )
    return fund_ev2.VenueCostModel("hl_single_maker_bound", specs)


# ---------------------------------------------------------------------------
# Tier qualification from the strategy's OWN traded volume (the honesty rule)
# ---------------------------------------------------------------------------


def leg_traded_notional(result: dict[str, Any]) -> dict[str, Decimal]:
    totals = {"perp": Decimal("0"), "spot": Decimal("0")}
    for _, _, leg, _, notional in result["trade_events"]:
        totals[leg] += notional
    return totals


def hl_weighted_14d_volume(result: dict[str, Any], window_days: int) -> Decimal:
    """HL tier volume: 14-day weighted, spot counted DOUBLE (cited)."""
    legs = leg_traded_notional(result)
    if window_days <= 0:
        return Decimal("0")
    weighted_total = legs["perp"] + legs["spot"] * 2
    return _money(weighted_total / Decimal(window_days) * Decimal("14"))


def kraken_30d_volume(result: dict[str, Any], window_days: int) -> Decimal:
    legs = leg_traded_notional(result)
    if window_days <= 0:
        return Decimal("0")
    return _money(legs["spot"] / Decimal(window_days) * Decimal("30"))


def achieved_hl_tier(weighted_14d_volume: Decimal) -> HlFeeTier:
    achieved = HL_FEE_TIERS[0]
    for tier in HL_FEE_TIERS:
        if weighted_14d_volume >= tier.qualifying_weighted_14d_volume_usd:
            achieved = tier
    return achieved


def achieved_kraken_tier(volume_30d: Decimal) -> KrakenFeeTier:
    achieved = KRAKEN_FEE_TIERS[0]
    for tier in KRAKEN_FEE_TIERS:
        if volume_30d >= tier.qualifying_30d_volume_usd:
            achieved = tier
    return achieved


# ---------------------------------------------------------------------------
# Viability band from gated cells (computed, never hard-coded)
# ---------------------------------------------------------------------------


def viability_band(
    cells: Sequence[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """The phase verdict from the evaluated cells.

    A cell counts toward the ACHIEVED band only if its gate passed, its
    impact is plausible, AND its fee tier is achieved by the strategy's own
    volume at that size. The band is the contiguous run of account sizes
    with at least one such cell. If the achieved band is empty the verdict
    is NOT viable at credible scale — regardless of how many assumed-tier
    cells look positive (they are reported as "what it would take").
    """
    passing_achieved = [
        cell
        for cell in cells
        if cell["gate_passed"]
        and cell["impact_plausible"]
        and cell["tier_achieved_by_own_volume"]
    ]
    if not passing_achieved:
        return VERDICT_NOT_VIABLE, []
    sizes = sorted({Decimal(str(cell["account_size"])) for cell in passing_achieved})
    ordered = [s for s in ACCOUNT_SIZES_USDC if s in sizes]
    # Contiguous run containing the smallest passing size.
    band: list[Decimal] = []
    for size in ACCOUNT_SIZES_USDC:
        if size in ordered:
            band.append(size)
        elif band:
            break
    band_cells = [
        cell for cell in passing_achieved if Decimal(str(cell["account_size"])) in band
    ]
    lo, hi = band[0], band[-1]
    tier_label = band_cells[0]["tier_id"]
    verdict = f"{VERDICT_VIABLE_PREFIX} [{lo:,.0f}-{hi:,.0f} @ {tier_label}]"
    return verdict, band_cells


def boundary_flags() -> dict[str, bool]:
    flags = dict(fund_ev2.boundary_flags())
    flags.update(
        {
            "fee_tiers_published_schedules_cited": True,
            "tier_achievement_derived_from_own_strategy_volume": True,
            "impact_scaled_by_actual_traded_notional": True,
            "implausible_participation_cells_cannot_pass": True,
            "maker_bound_line_optimistic_non_gateable": True,
            "retail_verdict_not_relitigated": True,
        }
    )
    return flags
