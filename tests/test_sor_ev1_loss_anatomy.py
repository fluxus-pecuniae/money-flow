from __future__ import annotations

from pathlib import Path

from services.strategy_validation.sor_ev1 import (
    CANONICAL_SV202_TIMESTAMP,
    build_sor_ev1_report,
    canonical_sv202_batch_report_paths,
    sor_ev1_report_to_markdown,
)


def test_sor_ev1_uses_canonical_sv202_pack_paths_only() -> None:
    paths = canonical_sv202_batch_report_paths()

    assert len(paths) == 36
    assert all("money_flow_sv2_0_2_hyperliquid_public_" in str(path) for path in paths)
    assert all(CANONICAL_SV202_TIMESTAMP in str(path) for path in paths)
    forbidden = ("dashboard", "pt0_0_3", "sv1_13", "compact")
    assert not any(any(token in str(path).lower() for token in forbidden) for path in paths)


def test_sor_ev1_report_contains_loss_anatomy_and_methodology_truth() -> None:
    report = build_sor_ev1_report()

    assert report["phase"] == "SOR-EV1"
    assert report["canonical_baseline"]["path_count"] == 36
    assert len(report["baseline_evidence_references"]) == 36
    assert all("20260512T064916Z" in path for path in report["baseline_evidence_references"])
    assert report["baseline_summary"]["scenario_count"] == 72
    assert report["worst_trades"]
    assert report["worst_trades"][0]["loss_rank"] == 1
    assert "losses_from_large_down_candles" in report["big_red_candle_summary"]
    assert report["late_entry_classifications"]
    assert report["rsi_macd_rejection_summary"]["status"] == "deferred_requires_rejected_signal_replay"
    assert report["methodology_labels"]["completed_trade_overlay_estimate"]
    assert report["methodology_labels"]["true_forward_replay"]


def test_sor_ev1_variants_are_evidence_only_and_not_candidates() -> None:
    report = build_sor_ev1_report()
    variants = {row["variant_id"]: row for row in report["variant_summary"]}

    for variant_id in (
        "fixed_stop_loss_pct_1",
        "fixed_stop_loss_pct_1_5",
        "fixed_stop_loss_pct_2",
        "atr_stop_1_5x",
        "atr_stop_2x",
        "recent_low_stop_lookback_5",
        "recent_low_stop_lookback_10",
        "large_bear_candle_exit",
        "macd_histogram_improving_entry",
        "macd_histogram_above_negative_threshold",
        "lower_rsi_trend_intact_entry",
        "reject_entry_if_price_too_far_above_ema10",
        "reject_entry_if_price_too_far_above_sma20",
        "avoid_sideways_low_volatility",
        "avoid_macd_flat_chop",
    ):
        assert variant_id in variants

    assert report["candidate_variants"] == []
    assert variants["fixed_stop_loss_pct_1"]["methodology"] == "completed_trade_overlay_estimate"
    assert variants["atr_stop_1_5x"]["outcome"] == "insufficient_data"
    assert report["boundary_flags"]["changes_production_money_flow_rules"] is False
    assert report["boundary_flags"]["creates_orders"] is False
    assert report["boundary_flags"]["calls_private_signed_or_order_endpoints"] is False


def test_sor_ev1_control_pockets_and_outputs_exist() -> None:
    report = build_sor_ev1_report()

    assert report["control_pocket_impact"]
    assert any(row["variant_id"] == "fixed_stop_loss_pct_2" for row in report["control_pocket_impact"])
    assert Path("docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants.md").exists()
    assert Path("docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json").exists()


def test_sor_ev1_markdown_avoids_proof_and_live_approval_language() -> None:
    markdown = sor_ev1_report_to_markdown(build_sor_ev1_report()).lower()

    assert "canonical sv2.0.2" in markdown
    assert "top 20" not in markdown  # avoid confusing with PT/UAT top-20 runtime scope
    for forbidden in ("proven", "optimal", "approved for live", "guaranteed", "ready for real trading"):
        assert forbidden not in markdown
    assert "no order endpoints are called" in markdown
    assert "production money flow rules are unchanged" in markdown
