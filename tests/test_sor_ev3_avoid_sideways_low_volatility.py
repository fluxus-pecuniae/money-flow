from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from services.strategy_validation.sor_ev3 import (
    FEATURE_DEFINITIONS,
    SOR_EV3_VARIANTS,
    _variant_block_reasons,
    build_sor_ev3_report_sync,
    sor_ev3_report_to_markdown,
)
from tests.test_sor_ev2_true_forward_replay import _seeded_canonical_pack


def test_sor_ev3_uses_canonical_sv202_paths_and_baseline_parity(tmp_path: Path) -> None:
    _, _, service, pack = _seeded_canonical_pack(tmp_path)

    report = build_sor_ev3_report_sync([pack], backtest_service=service)

    assert report["phase"] == "SOR-EV3"
    assert report["founder_selected_candidate_family"] == "avoid_sideways_low_volatility"
    assert report["baseline_evidence_references"] == [str(pack)]
    assert report["baseline_parity_summary"]["status_counts"] == {"baseline_parity_passed": 1}
    assert report["boundary_flags"]["uses_dashboard_date_filter_recalculation"] is False
    assert report["boundary_flags"]["uses_hyperliquid_testnet_prices"] is False
    assert report["boundary_flags"]["changes_production_money_flow_rules"] is False


def test_sor_ev3_feature_definitions_and_controlled_variants_exist(tmp_path: Path) -> None:
    _, _, service, pack = _seeded_canonical_pack(tmp_path)

    report = build_sor_ev3_report_sync([pack], backtest_service=service)
    variant_ids = {row["variant_id"] for row in report["variant_summary"]}
    feature_names = {row["feature"] for row in FEATURE_DEFINITIONS}

    assert set(SOR_EV3_VARIANTS) == {
        "avoid_low_atr_percentile_20",
        "avoid_low_atr_percentile_30",
        "avoid_flat_sma20_slope",
        "avoid_flat_ema10_slope",
        "avoid_low_rolling_range_20",
        "avoid_low_rolling_range_50",
        "avoid_macd_flat_chop",
        "avoid_sideways_low_volatility_conservative",
    }
    assert variant_ids == set(SOR_EV3_VARIANTS)
    assert {"atr_pct", "atr_percentile_lookback_50", "atr_percentile_lookback_100"} <= feature_names
    assert {"sma20_slope_pct", "ema10_slope_pct", "rolling_range_pct_20", "macd_histogram_abs_pct"} <= feature_names
    for row in report["variant_summary"]:
        assert row["methodology"] == "true_forward_replay"
        assert row["production_approved"] is False


def test_sor_ev3_block_reason_logic_is_objective_and_no_zero_fill() -> None:
    low_vol_features = {
        "atr_percentile_lookback_100": Decimal("15"),
        "sma20_slope_pct": Decimal("0.001"),
        "ema10_slope_pct": Decimal("0.001"),
        "rolling_range_pct_20": Decimal("0.02"),
        "rolling_range_pct_50": Decimal("0.04"),
        "macd_histogram_abs_pct": Decimal("0.00001"),
        "macd_histogram_slope_pct": Decimal("0.00001"),
        "macd_signal_spread_abs_pct": Decimal("0.00001"),
    }
    missing_features = {"atr_percentile_lookback_100": None}

    assert _variant_block_reasons("avoid_low_atr_percentile_20", low_vol_features) == ["blocked_low_atr_percentile"]
    assert _variant_block_reasons("avoid_flat_sma20_slope", low_vol_features) == ["blocked_flat_sma20_slope"]
    assert _variant_block_reasons("avoid_low_rolling_range_20", low_vol_features) == ["blocked_low_rolling_range"]
    assert _variant_block_reasons("avoid_macd_flat_chop", low_vol_features) == ["blocked_macd_flat_chop"]
    combined = _variant_block_reasons("avoid_sideways_low_volatility_conservative", low_vol_features)
    assert "blocked_combined_sideways_low_volatility" in combined
    assert _variant_block_reasons("avoid_low_atr_percentile_20", missing_features) == []


def test_sor_ev3_attribution_control_pockets_and_report_language(tmp_path: Path) -> None:
    _, _, service, pack = _seeded_canonical_pack(tmp_path)

    report = build_sor_ev3_report_sync([pack], backtest_service=service)
    markdown = sor_ev3_report_to_markdown(report).lower()

    assert "blocked_entry_attribution" in report
    assert "blocked_entry_summary" in report
    assert "total_blocked_open_signals" in report["blocked_entry_summary"]
    assert "canonical_blocked_entries" in report["blocked_entry_summary"]
    assert "blocked_open_signals" in report["variant_summary"][0]
    assert "avoided_losers" in report["blocked_entry_summary"]["by_variant"][0]
    assert "missed_winners" in report["blocked_entry_summary"]["by_variant"][0]
    assert "control_pocket_impact" in report
    assert "loss_concentration_summary" in report
    assert "true-forward" in markdown
    assert "production money flow rules are unchanged" in markdown
    assert "no order endpoints are called" in markdown
    for forbidden in ("proven", "optimal", "approved for live", "guaranteed", "ready for real trading", "production-approved"):
        assert forbidden not in markdown


def test_sor_ev3_outputs_exist_after_generation() -> None:
    assert Path("docs/sor_ev3_avoid_sideways_low_volatility.md").exists()
    assert Path("docs/sor_ev3_avoid_sideways_low_volatility_summary.json").exists()


def test_sor_ev3_does_not_modify_production_money_flow_rules() -> None:
    source = Path("services/strategy/money_flow.py").read_text()
    assert "avoid_sideways_low_volatility_conservative" not in source
    assert "avoid_low_atr_percentile_20" not in source
    assert "SOR-EV3" not in source
