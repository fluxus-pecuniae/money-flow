"""FUND-EV2 — funding carry under REALISTIC, CITED costs + selectivity.

RESEARCH / EVIDENCE ONLY. FUND-EV1 found the gross funding edge real and
positive but killed it with a deliberately conservative cost model (the HL
spot leg was priced at the widest mid-alt tier — 5 bps half-spread x1.5 —
while the live UBTC book quotes ~0.08 bps). FUND-EV2 re-tests ONE question:
was that verdict our cost conservatism, or a real absence of capturable
edge? It replaces the tier guess with per-venue, per-asset, CITED costs,
adds entry selectivity + longer holds, models both venue constructions with
their honest risks, and reports a cost-sensitivity sweep so "did we just
assume it cheaper?" is auditable.

THE DISCIPLINE GUARD: costs here are grounded in named sources, not chosen
to flip the verdict. If the edge survives only at implausibly low cost
scales, that is a FAIL. One honest re-test; no FUND-EV3 cost tweak.

Cited cost basis (each spec carries its `basis` string):
  - Hyperliquid fee schedule (docs, fetched 2026-06-11, base tier):
    perp taker 0.045% (4.5 bps), spot taker 0.070% (7 bps).
  - Hyperliquid live order books (public read-only l2Book one-shot
    calibration, docs/fund_ev2_l2book_calibration_summary.json,
    2026-06-11): half-spreads BTC perp 0.08 / UBTC spot 0.08 / ETH 0.30 /
    UETH 0.30 / SOL 0.08 / USOL 2.37 / HYPE 0.09 / HYPE spot 0.36 bps;
    visible +-10 bps depth $0.18M-$26M per book — a 1.25-2.5k USDC fill is
    <1.5% of visible depth everywhere. Modeled half-spreads below carry
    2-6x headroom over the snapshot (it is point-in-time, not history).
  - Kraken Pro fee schedule (fetched 2026-06-11, base tier <$10k 30d
    volume): spot taker 0.40% (40 bps), maker 0.25%. Coinbase Advanced
    base tier is WORSE at retail (taker 0.60%), so the cross-venue
    construction models the cheaper Kraken side; at a 10k USDC account the
    retail CEX FEE — not the spread — dominates the spot leg.
  - Cross-venue settlement: flat 2.00 USDC per spot fill (on-chain USDC
    transfer/withdrawal amortized; documented assumption). At 1.25-2.5k
    fills that alone is 8-16 bps — split capital and transfers are real.

Both constructions, each with its honest costs AND risks (Must 2):
  - hl_single: HL perp + HL spot. Tighter coupling (same venue, near-atomic
    legging) but HL spot fees (7 bps) and thinner books (USOL).
  - cross_venue: HL perp + Kraken spot. Deeper/tighter spot book but 40 bps
    retail taker fee + transfer friction + NO atomic cross-venue fill — its
    gate must survive the legged-execution stress (pending-fill queue holds
    REAL one-leg exposure; at daily resolution the 1-candle lag OVERSTATES
    typical minutes-hours legging duration but honestly bounds the gap).

Selectivity + longer holds (Must 3): enter only when trailing-funding
expectation over the planned hold clears the round-trip cost by a 2x
documented margin; hold while the (causal) trailing signal stays favorable;
wider rebalance band (2% of equity) and 14/28-day cadences cut churn.

Routed under the SAME ``funding_carry`` type and gate bar as FUND-EV1
(net carry after costs positive OOS, not bull-only, leave-one-out, tail
limits) — only the verdict labels say "realistic costs" and the gate output
carries the cost-sensitivity breakpoint + a fragility qualifier.

Pure and deterministic: Decimal arithmetic, no I/O, no network.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any, Sequence

try:  # pragma: no cover - exercised implicitly by both import contexts
    from services.strategy_validation import fund_ev1 as _fund_ev1
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

    _fund_ev1 = _load_sibling("fund_ev1.py", "fund_ev2_fund_ev1")

fund_ev1 = _fund_ev1
FundingCarryConfig = _fund_ev1.FundingCarryConfig
STRATEGY_TYPE_FUNDING_CARRY = _fund_ev1.STRATEGY_TYPE_FUNDING_CARRY
FUNDING_CARRY_GATE_ID = _fund_ev1.FUNDING_CARRY_GATE_ID
_money = _fund_ev1._money
BPS = Decimal("10000")

PHASE = "FUND-EV2"

CONSTRUCTION_HL_SINGLE = "hl_single"
CONSTRUCTION_CROSS_VENUE = "cross_venue"
CONSTRUCTIONS = (CONSTRUCTION_HL_SINGLE, CONSTRUCTION_CROSS_VENUE)

VERDICT_PASS_V2 = "carry_survives_realistic_costs_and_tail_oos"
VERDICT_FAIL_V2 = "carry_does_not_survive_realistic_costs_and_tail_oos"

# Selectivity + hold discipline (Must 3, documented):
ENTRY_MARGIN_MULTIPLE = Decimal("2.0")  # expected funding >= 2x round-trip cost
WIDE_BAND_FRACTION = Decimal("0.02")  # 2% of equity rebalance band (vs 0.5%)
V2_CADENCES_DAYS = (14, 28)
V2_TOP_K_CHOICES = (2, 4)

# Cost-sensitivity sweep (the discipline guard made auditable): scale 1.0 is
# the cited realistic baseline; <1 optimistic; >1 conservative. FUND-EV1's
# conservative model sits near scale ~2.5-3 for the hl_single spot leg.
SWEEP_SCALES = (
    Decimal("0.25"),
    Decimal("0.5"),
    Decimal("0.75"),
    Decimal("1.0"),
    Decimal("1.25"),
    Decimal("1.5"),
    Decimal("2.0"),
    Decimal("3.0"),
    Decimal("5.0"),
)
FRAGILITY_BREAKPOINT_SCALE = Decimal("1.5")  # pass with breakpoint below this is fragile


@dataclass(frozen=True, slots=True)
class LegCostSpec:
    """One leg's per-fill cost terms (all bps of notional unless noted)."""

    half_spread_bps: Decimal
    fee_bps: Decimal
    impact_coefficient_bps: Decimal
    slippage_bps: Decimal
    flat_cost_quote: Decimal  # flat USDC per fill (cross-venue settlement)
    basis: str  # the citation


class VenueCostModel:
    """Per-venue, per-asset, per-leg cited cost model with a sweep scale.

    ``scale`` multiplies every cost term (spreads, fees, slippage, impact
    coefficient, flat settlement) so the sensitivity sweep moves ALL cost
    assumptions together — optimistic and conservative are explicit dial
    positions, never silent re-assumptions.
    """

    def __init__(
        self,
        construction: str,
        specs: dict[tuple[str, str], LegCostSpec],
        scale: Decimal = Decimal("1.0"),
    ) -> None:
        self.construction = construction
        self.scale = scale
        self._specs = specs

    def spec(self, symbol: str, leg: str) -> LegCostSpec:
        base = self._specs[(symbol, leg)]
        if self.scale == 1:
            return base
        return replace(
            base,
            half_spread_bps=base.half_spread_bps * self.scale,
            fee_bps=base.fee_bps * self.scale,
            impact_coefficient_bps=base.impact_coefficient_bps * self.scale,
            slippage_bps=base.slippage_bps * self.scale,
            flat_cost_quote=base.flat_cost_quote * self.scale,
        )

    def with_scale(self, scale: Decimal) -> "VenueCostModel":
        return VenueCostModel(self.construction, self._specs, scale)

    def round_trip_cost_bps(self, symbol: str, notional: Decimal) -> Decimal:
        """Entry+exit, BOTH legs, in bps of one leg's notional — the number
        the selectivity margin is measured against. Impact is omitted from
        the ESTIMATE (sub-1 bp at 10k sizing against measured depth); the
        simulator still charges it on every actual fill."""
        total = Decimal("0")
        for leg in ("perp", "spot"):
            spec = self.spec(symbol, leg)
            per_fill = spec.half_spread_bps + spec.slippage_bps + spec.fee_bps
            if notional > 0:
                per_fill += spec.flat_cost_quote / notional * BPS
            total += per_fill * 2  # entry + exit
        return _money(total)

    def describe(self) -> dict[str, Any]:
        return {
            "construction": self.construction,
            "scale": str(self.scale),
            "legs": {
                f"{symbol}:{leg}": {
                    "half_spread_bps": str(self.spec(symbol, leg).half_spread_bps),
                    "fee_bps": str(self.spec(symbol, leg).fee_bps),
                    "impact_coefficient_bps": str(
                        self.spec(symbol, leg).impact_coefficient_bps
                    ),
                    "slippage_bps": str(self.spec(symbol, leg).slippage_bps),
                    "flat_cost_quote": str(self.spec(symbol, leg).flat_cost_quote),
                    "basis": self._specs[(symbol, leg)].basis,
                }
                for (symbol, leg) in sorted(self._specs)
            },
        }


_HL_FEES = "Hyperliquid fee schedule (docs, fetched 2026-06-11, base tier): perp taker 4.5 bps, spot taker 7 bps"
_L2 = "Hyperliquid public l2Book one-shot calibration 2026-06-11 (docs/fund_ev2_l2book_calibration_summary.json)"
_KRAKEN = "Kraken Pro fee schedule (fetched 2026-06-11, base tier): spot taker 40 bps; Coinbase Advanced base tier worse (60 bps)"
_XFER = "flat 2 USDC/fill cross-venue USDC transfer/settlement amortization (documented assumption)"

# Modeled half-spreads carry 2-6x headroom over the live snapshot because it
# is point-in-time; the sweep covers the residual uncertainty.
_PERP_HALF_SPREAD = {
    "BTC": Decimal("0.5"),   # measured 0.08
    "ETH": Decimal("1.0"),   # measured 0.30
    "SOL": Decimal("0.5"),   # measured 0.08
    "HYPE": Decimal("1.0"),  # measured 0.09
}
_HL_SPOT_HALF_SPREAD = {
    "BTC": Decimal("0.5"),   # UBTC measured 0.08
    "ETH": Decimal("1.0"),   # UETH measured 0.30
    "SOL": Decimal("5.0"),   # USOL measured 2.37 (thinnest book)
    "HYPE": Decimal("1.0"),  # measured 0.36
}
_KRAKEN_SPOT_HALF_SPREAD = {
    "BTC": Decimal("0.5"),
    "ETH": Decimal("0.5"),
    "SOL": Decimal("1.0"),
    "HYPE": Decimal("2.0"),  # newer listing, thinner CEX book
}
_SLIPPAGE_BPS = Decimal("2.0")  # next-open taker aggression/timing allowance


def hl_single_cost_model(scale: Decimal = Decimal("1.0")) -> VenueCostModel:
    specs: dict[tuple[str, str], LegCostSpec] = {}
    for symbol in fund_ev1.CARRY_UNIVERSE:
        specs[(symbol, "perp")] = LegCostSpec(
            half_spread_bps=_PERP_HALF_SPREAD[symbol],
            fee_bps=Decimal("4.5"),
            impact_coefficient_bps=Decimal("10"),
            slippage_bps=_SLIPPAGE_BPS,
            flat_cost_quote=Decimal("0"),
            basis=f"{_HL_FEES}; {_L2}",
        )
        specs[(symbol, "spot")] = LegCostSpec(
            half_spread_bps=_HL_SPOT_HALF_SPREAD[symbol],
            fee_bps=Decimal("7.0"),
            impact_coefficient_bps=Decimal("15"),
            slippage_bps=_SLIPPAGE_BPS,
            flat_cost_quote=Decimal("0"),
            basis=f"{_HL_FEES}; {_L2}",
        )
    return VenueCostModel(CONSTRUCTION_HL_SINGLE, specs, scale)


def cross_venue_cost_model(scale: Decimal = Decimal("1.0")) -> VenueCostModel:
    specs: dict[tuple[str, str], LegCostSpec] = {}
    for symbol in fund_ev1.CARRY_UNIVERSE:
        specs[(symbol, "perp")] = LegCostSpec(
            half_spread_bps=_PERP_HALF_SPREAD[symbol],
            fee_bps=Decimal("4.5"),
            impact_coefficient_bps=Decimal("10"),
            slippage_bps=_SLIPPAGE_BPS,
            flat_cost_quote=Decimal("0"),
            basis=f"{_HL_FEES}; {_L2}",
        )
        specs[(symbol, "spot")] = LegCostSpec(
            half_spread_bps=_KRAKEN_SPOT_HALF_SPREAD[symbol],
            fee_bps=Decimal("40.0"),
            impact_coefficient_bps=Decimal("5"),
            slippage_bps=_SLIPPAGE_BPS,
            flat_cost_quote=Decimal("2.00"),
            basis=f"{_KRAKEN}; {_XFER}",
        )
    return VenueCostModel(CONSTRUCTION_CROSS_VENUE, specs, scale)


def cost_model_for(construction: str, scale: Decimal = Decimal("1.0")) -> VenueCostModel:
    if construction == CONSTRUCTION_HL_SINGLE:
        return hl_single_cost_model(scale)
    if construction == CONSTRUCTION_CROSS_VENUE:
        return cross_venue_cost_model(scale)
    raise ValueError(f"unknown_construction:{construction}")


def generate_fund_ev2_configs() -> list[FundingCarryConfig]:
    """Bounded grid (8): construction x cadence 14/28 x top 2/4; collect
    side only (the flip side needs spot borrow — FUND-EV1 documented those
    rows as upper bounds; the realistic re-test does not lean on them);
    2x entry margin and the 2% band fixed by design, chosen up front, not
    tuned on outcomes."""
    configs: list[FundingCarryConfig] = []
    for construction in CONSTRUCTIONS:
        for cadence in V2_CADENCES_DAYS:
            for top_k in V2_TOP_K_CHOICES:
                configs.append(
                    FundingCarryConfig(
                        config_id=(
                            f"fund_ev2_{construction}_cad{cadence}_top{top_k}_1d"
                        ),
                        strategy_type=STRATEGY_TYPE_FUNDING_CARRY,
                        mode="collect_only",
                        rebalance_interval_days=cadence,
                        top_k=top_k,
                        min_trade_notional_fraction=WIDE_BAND_FRACTION,
                        entry_margin_multiple=ENTRY_MARGIN_MULTIPLE,
                        planned_hold_days=cadence,
                        venue_construction=construction,
                    )
                )
    return configs


def construction_of(config: FundingCarryConfig) -> str:
    return config.venue_construction


# ---------------------------------------------------------------------------
# Cost-sensitivity breakpoint (the discipline guard, auditable)
# ---------------------------------------------------------------------------


def sweep_breakpoint_scale(
    sweep_rows: Sequence[dict[str, Any]],
) -> Decimal | None:
    """The lowest swept scale at which OOS net carry is no longer positive
    (linear in audit terms: 'the edge dies at scale X'). None if it stays
    positive through the whole sweep; the minimum scale if it is already
    non-positive at the most optimistic point (no edge at any cost)."""
    rows = sorted(sweep_rows, key=lambda r: Decimal(str(r["scale"])))
    for row in rows:
        net = row["oos_net_pnl"]
        if net is None or Decimal(str(net)) <= 0:
            return Decimal(str(row["scale"]))
    return None


def evaluate_funding_carry_gate_v2(
    *,
    cost_sensitivity_sweep: Sequence[dict[str, Any]],
    **gate_kwargs: Any,
) -> dict[str, Any]:
    """The SAME funding_carry bar as FUND-EV1 (net after costs positive OOS
    chronological + walk-forward, not bull-only, leave-one-out, tail/gap
    limits), evaluated at the CITED realistic cost level — plus the
    sensitivity verdict: where does the edge flip? A pass whose breakpoint
    sits just above the realistic level is flagged fragile (non-failing
    qualifier); a 'pass' that exists only below the realistic level is
    simply a fail, because the main OOS check already runs at scale 1.0."""
    gate = fund_ev1.evaluate_funding_carry_gate(**gate_kwargs)
    status = VERDICT_PASS_V2 if gate["passed"] else VERDICT_FAIL_V2
    breakpoint_scale = sweep_breakpoint_scale(cost_sensitivity_sweep)
    qualifiers = list(gate["qualifiers"])
    if gate["passed"] and breakpoint_scale is not None and (
        breakpoint_scale < FRAGILITY_BREAKPOINT_SCALE
    ):
        qualifiers.append("oos_edge_fragile_to_cost_assumptions")
    out = dict(gate)
    out["status"] = status
    out["passed"] = status == VERDICT_PASS_V2
    out["qualifiers"] = qualifiers
    out["reason_codes"] = (
        ["funding_carry_gate_passed_at_cited_realistic_costs"]
        if gate["passed"]
        else gate["reason_codes"]
    )
    out["cost_sensitivity"] = {
        "sweep": list(cost_sensitivity_sweep),
        "breakpoint_scale_where_oos_edge_dies": (
            str(breakpoint_scale) if breakpoint_scale is not None else None
        ),
        "realistic_scale": "1.0",
        "fragility_threshold_scale": str(FRAGILITY_BREAKPOINT_SCALE),
    }
    return out


def boundary_flags() -> dict[str, bool]:
    flags = dict(fund_ev1.boundary_flags())
    flags.update(
        {
            "costs_cited_not_tuned_to_verdict": True,
            "cost_sensitivity_sweep_reported": True,
            "l2book_calibration_point_in_time_not_history": True,
            "cross_venue_legging_modeled_at_daily_resolution": True,
        }
    )
    return flags
