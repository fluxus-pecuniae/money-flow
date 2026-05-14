from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from scripts.run_sv21_broad_1d_period_evidence import (
    SV21Dataset,
    active_hyperliquid_identities_from_meta,
    build_market_identity_manifest,
    build_summary,
    latest_closed_1d,
    render_report,
    write_period_campaign_configs,
)


def test_active_meta_universe_preserves_venue_symbols_and_research_only_identity() -> None:
    meta = {
        "universe": [
            {"name": "BTC", "szDecimals": 5, "maxLeverage": 40},
            {"name": "kPEPE", "szDecimals": 0, "maxLeverage": 3},
            {"name": "DEAD", "szDecimals": 2, "isDelisted": True},
        ]
    }

    identities = active_hyperliquid_identities_from_meta(meta)
    manifest = build_market_identity_manifest(
        identities,
        meta,
        datetime(2026, 5, 14, 22, 5, tzinfo=UTC),
    )

    assert [item.canonical_symbol for item in identities] == ["BTC", "KPEPE"]
    assert identities[1].resolved_venue_symbol == "kPEPE"
    symbol_rows = [row["symbol"] for row in manifest["markets"]]
    assert all(row["is_trading_eligible"] is False for row in symbol_rows)
    assert all(row["is_strategy_eligible"] is False for row in symbol_rows)
    assert symbol_rows[1]["exchange_symbol"] == "kPEPE"


def test_period_configs_clip_to_available_data_and_do_not_fabricate(tmp_path) -> None:
    datasets = [
        SV21Dataset(
            symbol="BTC",
            venue_symbol="BTC",
            rows=864,
            earliest_close="2024-01-02T00:00:00Z",
            latest_close="2026-05-14T00:00:00Z",
            imported=True,
            raw_path=None,
            reason_codes=("db_imported_true",),
        ),
        SV21Dataset(
            symbol="NEW",
            venue_symbol="NEW",
            rows=10,
            earliest_close="2026-05-05T00:00:00Z",
            latest_close="2026-05-14T00:00:00Z",
            imported=True,
            raw_path=None,
            reason_codes=("db_imported_true",),
        ),
    ]

    results, paths = write_period_campaign_configs(datasets=datasets, output_dir=tmp_path)

    assert len(paths) == 6
    blocked = {(row.period, row.symbol) for row in results if row.blocked}
    assert ("2024", "NEW") in blocked
    assert ("2025", "NEW") in blocked
    btc_2024 = next(row for row in results if row.period == "2024" and row.symbol == "BTC")
    assert btc_2024.start_at == "2024-01-01T00:00:00Z"
    config = json.loads(paths[0].read_text(encoding="utf-8"))
    assert config["components"] == ["sleeve_1d"]
    assert config["research_boundaries"]["submits_orders"] is False


def test_summary_and_report_expose_sv21_counts() -> None:
    generated_at = datetime(2026, 5, 14, 22, 5, tzinfo=UTC)
    end_at = latest_closed_1d(datetime(2026, 5, 14, 21, 57, tzinfo=UTC))
    datasets = [
        SV21Dataset(
            symbol="BTC",
            venue_symbol="BTC",
            rows=864,
            earliest_close="2024-01-02T00:00:00Z",
            latest_close="2026-05-14T00:00:00Z",
            imported=True,
            raw_path=None,
            reason_codes=("db_imported_true",),
        )
    ]
    with tempfile.TemporaryDirectory() as directory:
        period_results, _ = write_period_campaign_configs(datasets=datasets, output_dir=Path(directory))
    summary = build_summary(
        generated_at=generated_at,
        effective_end=end_at,
        identities=[],
        datasets=datasets,
        import_results=[],
        seed_result=None,
        period_results=period_results,
        evidence_pack_paths=["reports/strategy_validation/example/20260514T220500Z"],
        db_blockers=[],
    )
    report = render_report(summary)

    assert summary["phase"] == "SV2.1"
    assert summary["evidence_pack_count"] == 1
    assert "SV2.1 Broad Hyperliquid 1D Period Evidence" in report
    assert "Private/signed/order endpoints called: `False`" in report


def test_sv21_broad_historical_replay_builder_is_period_and_candidate_aware() -> None:
    source = Path("scripts/build_sv21_broad_1d_historical_replay.py").read_text(encoding="utf-8")

    assert "SV21_BASELINE_STRATEGY_ID = \"money_flow_v1_2_canonical\"" in source
    assert "\"avoid_low_rolling_range_50\"" in source
    assert "\"avoid_low_rolling_range_20\"" in source
    assert "\"mf_orig_1d_stage2_breakout_resistance_full_equity\"" in source
    assert "money_flow_sv2_1_hyperliquid_broad_1d_" in source
    assert "_selected_chart_path" in source
    assert "_sv21_replay.json" in source
    assert "sv2_1_broad_1d_dashboard_chart_data" in source
    assert "candidate_evidence_status" in source
    assert "mf_orig_candidate_skipped_symbols" in source
    assert "\"production_approved\": False" in source
    assert "\"submits_orders\": False" in source
    assert "\"uses_private_signed_or_order_endpoints\": False" in source
    assert "\"uses_testnet_prices_as_strategy_truth\": False" in source
