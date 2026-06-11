"""FUND-SCALE1 — deterministic, offline tests (no network, no DB, no runtime).

Asserts the phase's documented guarantees:
  - the published fee-tier tables are internally consistent (fees
    non-increasing, qualifying volumes increasing) and cited;
  - the tiered cost models move ONLY the fee term (spreads/impact stay the
    FUND-EV2 cited model) and lower-fee tiers never lower net... raise it;
  - impact grows with account size (participation/max fill notional scale)
    while fixed costs amortize (cross-venue flat fee shrinks as a fraction);
  - tier achievement is computed from the strategy's OWN volume (HL 14d
    weighted with spot double; Kraken 30d) — never assumed;
  - the viability band is COMPUTED from gated cells (assumed-tier or
    impact-implausible passes can never form it), not hard-coded;
  - starting_equity is honored end-to-end (K-019 reconciliation at size);
  - no-lookahead holds at non-retail sizes;
  - the committed summary reproduces FUND-EV2's retail cell (not
    re-litigated), carries the discipline guard, and the authored Research
    Log outcome stays honest (never green on a not-viable verdict).
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from services.execution_quality.exec_ev1 import scenario_by_id
from services.strategy_validation import fund_ev1 as fund
from services.strategy_validation import fund_ev2 as ev2
from services.strategy_validation import fund_scale1 as scale1
from services.strategy_validation.goal_strat1 import Candle, Dataset

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = REPO_ROOT / "docs" / "fund_scale1_size_fee_tier_viability_summary.json"
EV2_SUMMARY_PATH = REPO_ROOT / "docs" / "fund_ev2_realistic_cost_carry_evidence_summary.json"
CONSERVATIVE = scenario_by_id("exec_ev1_conservative")
T0 = datetime(2025, 1, 1, tzinfo=UTC)


def make_dataset(symbol: str, n: int, volume: float = 5_000_000) -> Dataset:
    candles = []
    for i in range(n):
        p = Decimal("100")
        candles.append(
            Candle(
                symbol=symbol, timeframe="1d", timestamp=T0 + timedelta(days=i + 1),
                open=p, high=p * Decimal("1.001"), low=p * Decimal("0.999"), close=p,
                volume=Decimal(str(volume)), source_path="synthetic",
            )
        )
    return Dataset(
        symbol=symbol, timeframe="1d", source_path="synthetic",
        source_provenance="synthetic", canonical_evidence_status="synthetic",
        candles=tuple(candles),
    )


def make_asset(symbol: str, n: int, funding=Decimal("0.0006")) -> fund.CarryAsset:
    fm = {T0 + timedelta(days=i + 1): funding for i in range(n)}
    return fund.CarryAsset(
        symbol=symbol, perp=make_dataset(symbol, n), spot=make_dataset(symbol, n),
        funding_by_close=fm, funding_hours_by_close={k: 24 for k in fm},
    )


def universe(n: int = 120) -> fund.CarryUniverse:
    return fund.CarryUniverse([make_asset("BTC", n), make_asset("ETH", n)])


def cfg(config_id: str = "fund_ev2_hl_single_cad28_top2_1d"):
    return {c.config_id: c for c in ev2.generate_fund_ev2_configs()}[config_id]


# ---------------------------------------------------------------------------
# Fee-tier tables: consistency + citation
# ---------------------------------------------------------------------------


def test_fee_tier_tables_are_monotonic_and_cited() -> None:
    for tiers, taker_attr, vol_attr in (
        (scale1.HL_FEE_TIERS, "perp_taker_bps", "qualifying_weighted_14d_volume_usd"),
        (scale1.HL_FEE_TIERS, "spot_taker_bps", "qualifying_weighted_14d_volume_usd"),
        (scale1.KRAKEN_FEE_TIERS, "taker_bps", "qualifying_30d_volume_usd"),
    ):
        takers = [getattr(t, taker_attr) for t in tiers]
        volumes = [getattr(t, vol_attr) for t in tiers]
        assert all(takers[i] >= takers[i + 1] for i in range(len(takers) - 1))
        assert all(volumes[i] < volumes[i + 1] for i in range(len(volumes) - 1))
        assert all(t.basis for t in tiers)
    # Base tiers match the FUND-EV2 cited retail values exactly.
    assert scale1.HL_FEE_TIERS[0].perp_taker_bps == Decimal("4.5")
    assert scale1.HL_FEE_TIERS[0].spot_taker_bps == Decimal("7.0")
    assert scale1.KRAKEN_FEE_TIERS[0].taker_bps == Decimal("40")


def test_tiered_cost_model_moves_only_the_fee_term() -> None:
    t0 = scale1.hl_tier_cost_model(scale1.HL_FEE_TIERS[0])
    t3 = scale1.hl_tier_cost_model(scale1.HL_FEE_TIERS[3])
    base = ev2.hl_single_cost_model()
    for symbol in fund.CARRY_UNIVERSE:
        for leg in ("perp", "spot"):
            s0, s3, sb = t0.spec(symbol, leg), t3.spec(symbol, leg), base.spec(symbol, leg)
            assert s3.fee_bps < s0.fee_bps
            assert s0.half_spread_bps == s3.half_spread_bps == sb.half_spread_bps
            assert s0.impact_coefficient_bps == s3.impact_coefficient_bps
            assert "hl_tier_3" in s3.basis


def test_lower_fee_tier_never_lowers_net() -> None:
    uni = universe()
    plain = replace(cfg(), config_id="fund_scale1_plain", entry_margin_multiple=None)
    nets = []
    for tier in scale1.HL_SWEEP_TIERS:
        result = fund.simulate_funding_carry_portfolio(
            uni, plain, CONSERVATIVE,
            leg_cost_model=scale1.hl_tier_cost_model(tier),
        )
        nets.append(result["net_pnl"])
    assert all(nets[i] <= nets[i + 1] for i in range(len(nets) - 1))
    assert nets[-1] > nets[0]


# ---------------------------------------------------------------------------
# Size effects: impact grows, fixed costs amortize, equity honored
# ---------------------------------------------------------------------------


def test_impact_and_participation_grow_with_account_size() -> None:
    uni = universe()
    plain = replace(cfg(), config_id="fund_scale1_size", entry_margin_multiple=None)
    model = scale1.hl_tier_cost_model(scale1.HL_FEE_TIERS[0])
    small = fund.simulate_funding_carry_portfolio(
        uni, plain, CONSERVATIVE, leg_cost_model=model,
        starting_equity=Decimal("10000"),
    )
    big = fund.simulate_funding_carry_portfolio(
        uni, plain, CONSERVATIVE, leg_cost_model=model,
        starting_equity=Decimal("5000000"),
    )
    assert big["max_fill_notional"] > small["max_fill_notional"] * 100
    assert big["max_fill_participation"] > small["max_fill_participation"]
    # Net as a fraction of equity is strictly worse at size (impact only
    # grows; every other term is proportional on this synthetic book).
    small_pct = small["net_pnl"] / Decimal("10000")
    big_pct = big["net_pnl"] / Decimal("5000000")
    assert big_pct < small_pct
    # K-019 at size: reconciliation + starting equity honored.
    assert big["starting_equity"] == Decimal("5000000")
    total = sum(big["per_symbol_net_pnl"].values(), Decimal("0"))
    assert abs(total - big["net_pnl"]) < Decimal("2")
    assert big["equity_curve"][-1][1] == big["ending_equity"]


def test_cross_venue_flat_settlement_amortizes_with_size() -> None:
    uni = universe()
    plain = replace(
        cfg("fund_ev2_cross_venue_cad28_top2_1d"),
        config_id="fund_scale1_amortize", entry_margin_multiple=None,
    )
    model = scale1.cross_venue_tier_cost_model(scale1.KRAKEN_FEE_TIERS[0])
    small = fund.simulate_funding_carry_portfolio(
        uni, plain, CONSERVATIVE, leg_cost_model=model,
        starting_equity=Decimal("10000"),
    )
    big = fund.simulate_funding_carry_portfolio(
        uni, plain, CONSERVATIVE, leg_cost_model=model,
        starting_equity=Decimal("1000000"),
    )
    # Fees include the flat 2 USDC/fill term: as a fraction of traded
    # notional it must shrink at the larger size (same trade pattern).
    small_ratio = small["fees_total"] / small["traded_notional_total"]
    big_ratio = big["fees_total"] / big["traded_notional_total"]
    assert big_ratio < small_ratio


# ---------------------------------------------------------------------------
# Tier achievement from OWN volume
# ---------------------------------------------------------------------------


def test_tier_achievement_uses_own_volume_with_spot_counted_double() -> None:
    result = {
        "trade_events": (
            (T0, "BTC", "perp", "sell", Decimal("3000000")),
            (T0, "BTC", "spot", "buy", Decimal("2000000")),
        )
    }
    legs = scale1.leg_traded_notional(result)
    assert legs == {"perp": Decimal("3000000"), "spot": Decimal("2000000")}
    # 14d weighted: (3M + 2*2M) / 14 days window * 14 = 7M -> HL tier 1 (>5M).
    weighted = scale1.hl_weighted_14d_volume(result, window_days=14)
    assert weighted == Decimal("7000000")
    assert scale1.achieved_hl_tier(weighted).tier_id == "hl_tier_1"
    assert scale1.achieved_hl_tier(Decimal("0")).tier_id == "hl_tier_0"
    assert scale1.achieved_hl_tier(Decimal("9999999999")).tier_id == "hl_tier_6"
    # Kraken: spot only, 30d scaling.
    k30 = scale1.kraken_30d_volume(result, window_days=30)
    assert k30 == Decimal("2000000")
    assert scale1.achieved_kraken_tier(k30).tier_id == "kraken_tier_1m"


# ---------------------------------------------------------------------------
# The band is computed, never hard-coded
# ---------------------------------------------------------------------------


def _cell(size, *, passed=True, plausible=True, achieved=True, tier="hl_tier_0"):
    return {
        "account_size": str(size),
        "tier_id": tier,
        "gate_passed": passed,
        "impact_plausible": plausible,
        "tier_achieved_by_own_volume": achieved,
    }


def test_viability_band_requires_achieved_plausible_passing_cells() -> None:
    # Empty when nothing qualifies.
    verdict, band = scale1.viability_band([_cell(10000, passed=False)])
    assert verdict == scale1.VERDICT_NOT_VIABLE and band == []
    # Assumed-tier or implausible passes can NEVER form the band.
    verdict, band = scale1.viability_band(
        [_cell(50000, achieved=False), _cell(250000, plausible=False)]
    )
    assert verdict == scale1.VERDICT_NOT_VIABLE and band == []
    # A real band: contiguous sizes, labeled with the tier.
    verdict, band = scale1.viability_band(
        [_cell(50000), _cell(250000), _cell(5000000, passed=False)]
    )
    assert verdict.startswith(scale1.VERDICT_VIABLE_PREFIX)
    assert "50,000" in verdict and "250,000" in verdict and "hl_tier_0" in verdict
    assert len(band) == 2
    # Contiguity: the run stops at the first gap (5M passing beyond a gap
    # does not extend the band).
    verdict, band = scale1.viability_band([_cell(10000), _cell(5000000)])
    assert "10,000-10,000" in verdict
    assert len(band) == 1


# ---------------------------------------------------------------------------
# No-lookahead at size
# ---------------------------------------------------------------------------


def test_decisions_before_divergence_identical_at_scale() -> None:
    n = 120
    base_rates = [Decimal("0.0006")] * n
    tampered = list(base_rates)
    for i in range(80, n):
        tampered[i] = Decimal("-0.0009")
    model = scale1.hl_tier_cost_model(scale1.HL_FEE_TIERS[2])
    config = cfg("fund_ev2_hl_single_cad14_top2_1d")
    results = []
    for rates in (base_rates, tampered):
        fm_assets = []
        for sym in ("BTC", "ETH"):
            fm = {T0 + timedelta(days=i + 1): rates[i] for i in range(n)}
            fm_assets.append(
                fund.CarryAsset(
                    symbol=sym, perp=make_dataset(sym, n), spot=make_dataset(sym, n),
                    funding_by_close=fm, funding_hours_by_close={k: 24 for k in fm},
                )
            )
        results.append(
            fund.simulate_funding_carry_portfolio(
                fund.CarryUniverse(fm_assets), config, CONSERVATIVE,
                leg_cost_model=model, starting_equity=Decimal("250000"),
            )
        )
    cutoff = T0 + timedelta(days=80)
    early = [[e for e in r["trade_events"] if e[0] <= cutoff] for r in results]
    assert early[0] == early[1] and early[0]


# ---------------------------------------------------------------------------
# Committed summary (CI-safe: committed docs only)
# ---------------------------------------------------------------------------


def _summary() -> dict:
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def test_committed_summary_verdict_band_and_guard() -> None:
    summary = _summary()
    verdict = summary["verdict"]
    assert verdict == scale1.VERDICT_NOT_VIABLE or verdict.startswith(
        scale1.VERDICT_VIABLE_PREFIX
    )
    guard = summary["discipline_guard"]
    assert guard["fee_tiers_published_and_cited"] is True
    assert len(guard["sources"]) >= 3
    assert summary["boundaries"]["fee_tiers_published_schedules_cited"] is True
    assert summary["boundaries"]["implausible_participation_cells_cannot_pass"] is True
    assert summary["boundaries"]["retail_verdict_not_relitigated"] is True
    # Band cells (if any) must each be achieved + plausible + passed.
    for cell in summary["band_cells"]:
        assert cell["gate_passed"] and cell["impact_plausible"]
        assert cell["tier_achieved_by_own_volume"]
    if not summary["band_cells"]:
        assert verdict == scale1.VERDICT_NOT_VIABLE
    # The maker line is labeled non-gateable.
    assert "never passes" in summary["maker_bound_line_optimistic_non_gateable"]["note"]


def test_committed_map_covers_grid_and_marks_tier_achievement() -> None:
    summary = _summary()
    sizes = set(summary["account_sizes_usdc"])
    assert sizes == {str(s) for s in scale1.ACCOUNT_SIZES_USDC}
    by_construction: dict[str, set] = {}
    for cell in summary["viability_map"]:
        by_construction.setdefault(cell["construction"], set()).add(
            (cell["tier_id"], cell["account_size"])
        )
        # Achievement claims must be consistent with the recorded volumes.
        achieved = Decimal(cell["own_volume_for_tier"]) >= Decimal(
            cell["tier_qualifying_volume"]
        )
        assert cell["tier_achieved_by_own_volume"] == achieved
    assert len(by_construction["hl_single"]) == len(scale1.HL_SWEEP_TIERS) * len(sizes)
    assert len(by_construction["cross_venue"]) == len(scale1.KRAKEN_SWEEP_TIERS) * len(sizes)


def test_committed_retail_cell_reproduces_fund_ev2_not_relitigated() -> None:
    summary = _summary()
    ev2_summary = json.loads(EV2_SUMMARY_PATH.read_text(encoding="utf-8"))
    retail = next(
        c for c in summary["viability_map"]
        if c["construction"] == "hl_single"
        and c["tier_id"] == "hl_tier_0"
        and c["account_size"] == "10000"
    )
    assert retail["chosen_config"] == ev2_summary["train_only_choice"]["chosen_config"]
    assert abs(
        Decimal(retail["oos_net_pnl"]) - Decimal(ev2_summary["headline"]["oos_net_carry"])
    ) < Decimal("0.01")
    assert retail["gate_passed"] is False


def test_research_log_outcome_for_fund_scale1_stays_honest() -> None:
    payload = json.loads(
        (REPO_ROOT / "docs" / "research_log.json").read_text(encoding="utf-8")
    )
    by_phase = {entry["phase"]: entry for entry in payload["entries"]}
    entry = by_phase.get("FUND-SCALE1")
    assert entry is not None, "FUND-SCALE1 research_log block missing"
    if _summary()["verdict"] == scale1.VERDICT_NOT_VIABLE:
        assert entry["outcome"] == "fail"
    assert payload["standing"]["passed_gate"] == sum(
        1 for e in payload["entries"] if e["outcome"] == "pass"
    )
