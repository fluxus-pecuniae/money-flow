from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from services.strategy_validation.sv2 import (
    HYPERLIQUID_MAINNET_PUBLIC_INFO_URL,
    SV20CandleDataset,
    normalize_hyperliquid_candle_snapshot,
    resolve_hyperliquid_market_identities,
)
from scripts.run_sv202_canonical_import_and_evidence import (
    build_market_identity_manifest,
    canonical_evidence_rows_from_packs,
    db_status_blocking_reason_codes,
    effective_closed_end_at_by_timeframe,
    filter_closed_candles,
    hyperliquid_request_end_for_close_boundary,
    latest_fully_closed_boundary,
    render_sv202_report,
    sor_ev1_readiness_decision,
    summarize_open_position_handling,
    sv202_canonical_evidence_identities,
    write_import_candle_file,
    write_sv202_campaign_configs,
)


def _candles(*, count: int = 3, timeframe: str = "1h", start: datetime | None = None) -> tuple[dict[str, str], ...]:
    start = start or datetime(2026, 1, 1, tzinfo=UTC)
    step = {"15m": timedelta(minutes=15), "1h": timedelta(hours=1), "4h": timedelta(hours=4), "1d": timedelta(days=1)}[
        timeframe
    ]
    rows: list[dict[str, str]] = []
    for index in range(count):
        open_time = start + (step * index)
        close_time = open_time + step
        rows.append(
            {
                "symbol": "BTC",
                "venue_symbol": "BTC",
                "timeframe": timeframe,
                "display_timeframe": "1D" if timeframe == "1d" else timeframe,
                "open_time": open_time.isoformat().replace("+00:00", "Z"),
                "close_time": close_time.isoformat().replace("+00:00", "Z"),
                "raw_venue_close_time": close_time.isoformat().replace("+00:00", "Z"),
                "open": "100",
                "high": "105",
                "low": "95",
                "close": "101",
                "volume": "10",
                "trade_count": None,
                "source": "hyperliquid_public_mainnet_candleSnapshot",
            }
        )
    return tuple(rows)


def _dataset(symbol: str, timeframe: str) -> SV20CandleDataset:
    candles = tuple({**row, "symbol": symbol, "venue_symbol": symbol} for row in _candles(timeframe=timeframe))
    return SV20CandleDataset(
        requested_symbol=symbol,
        resolved_venue_symbol=symbol,
        timeframe=timeframe,
        fetch_attempted=True,
        fetched=True,
        normalized=True,
        raw_file_written=True,
        staged_for_replay=True,
        db_imported=True,
        canonical_evidence_ready=False,
        target_window_ready=True,
        candles=candles,
        fetch_reason_codes=("hyperliquid_public_mainnet_fetch_succeeded",),
        import_reason_codes=("historical_import_succeeded", "canonical_hardened_import_succeeded", "db_imported_true"),
    )


def test_db_target_must_be_reachable_intended_and_schema_ready() -> None:
    status = SimpleNamespace(
        reachable=False,
        intended_strategy_validation_database=True,
        database_target_ready_for_evidence_generation=True,
        schema_ready_for_evidence_generation=False,
        required_schema_tables_missing=("candles",),
        candles_table_exists=False,
    )

    reasons = db_status_blocking_reason_codes(status)

    assert "strategy_validation_db_unreachable" in reasons
    assert "strategy_validation_schema_not_current" in reasons
    assert "strategy_validation_required_table_missing" in reasons


def test_effective_closed_boundaries_are_timeframe_specific() -> None:
    value = datetime(2026, 5, 12, 4, 41, 57, tzinfo=UTC)

    boundaries = effective_closed_end_at_by_timeframe(value)

    assert boundaries["15m"] == datetime(2026, 5, 12, 4, 30, tzinfo=UTC)
    assert boundaries["1h"] == datetime(2026, 5, 12, 4, 0, tzinfo=UTC)
    assert boundaries["4h"] == datetime(2026, 5, 12, 4, 0, tzinfo=UTC)
    assert boundaries["1d"] == datetime(2026, 5, 12, 0, 0, tzinfo=UTC)
    assert latest_fully_closed_boundary(datetime(2026, 5, 12, 5, 0, tzinfo=UTC), "1h") == datetime(
        2026, 5, 12, 5, 0, tzinfo=UTC
    )


def test_hyperliquid_request_end_uses_open_boundary_for_desired_last_close() -> None:
    assert hyperliquid_request_end_for_close_boundary(
        datetime(2026, 5, 12, 4, 30, tzinfo=UTC),
        "15m",
    ) == datetime(2026, 5, 12, 4, 15, tzinfo=UTC)
    assert hyperliquid_request_end_for_close_boundary(
        datetime(2026, 5, 12, 0, 0, tzinfo=UTC),
        "1d",
    ) == datetime(2026, 5, 11, 0, 0, tzinfo=UTC)


def test_filter_closed_candles_removes_unclosed_or_future_slots() -> None:
    candles = _candles(count=3, timeframe="15m", start=datetime(2026, 5, 12, 4, 0, tzinfo=UTC))

    filtered, filtered_count = filter_closed_candles(
        candles,
        effective_end_at=datetime(2026, 5, 12, 4, 30, tzinfo=UTC),
    )

    assert filtered_count == 1
    assert [row["close_time"] for row in filtered] == [
        "2026-05-12T04:15:00Z",
        "2026-05-12T04:30:00Z",
    ]


def test_shib_kshib_alias_is_deferred_for_canonical_evidence() -> None:
    identities = resolve_hyperliquid_market_identities(
        {"universe": [{"name": "BTC", "szDecimals": 5}, {"name": "kSHIB", "szDecimals": 0}]},
        requested_symbols=("BTC", "SHIB"),
    )

    adjusted = sv202_canonical_evidence_identities(identities)
    by_symbol = {row.requested_symbol: row for row in adjusted}

    assert by_symbol["BTC"].supported is True
    assert by_symbol["SHIB"].resolved_venue_symbol == "kSHIB"
    assert by_symbol["SHIB"].supported is False
    assert "venue_symbol_unit_semantics_deferred" in by_symbol["SHIB"].reason_codes
    assert "canonical_evidence_excluded_symbol_deferred" in by_symbol["SHIB"].reason_codes


def test_market_identity_manifest_is_research_only_and_uses_hyperliquid_metadata() -> None:
    meta = {"universe": [{"name": "BTC", "szDecimals": 5, "maxLeverage": 40}]}
    identities = sv202_canonical_evidence_identities(
        resolve_hyperliquid_market_identities(meta, requested_symbols=("BTC",))
    )

    manifest = build_market_identity_manifest(
        identities=identities,
        meta_payload=meta,
        generated_at=datetime(2026, 5, 11, tzinfo=UTC),
    )
    market = manifest["markets"][0]

    assert manifest["research_only"] is True
    assert market["instrument"]["instrument_key"] == "perpetual:linear:BTC:USDC:USDC"
    assert market["symbol"]["symbol"] == "BTC"
    assert market["symbol"]["exchange_symbol"] == "BTC"
    assert market["symbol"]["is_strategy_eligible"] is False
    assert market["symbol"]["is_trading_eligible"] is False
    assert market["symbol"]["quantity_step_size"] == "0.00001"
    assert market["symbol"]["price_tick_size"] == "0.1"


def test_import_file_contains_normalized_close_slots_and_instrument_key(tmp_path: Path) -> None:
    identity = resolve_hyperliquid_market_identities(
        {"universe": [{"name": "ETH", "szDecimals": 4}]},
        requested_symbols=("ETH",),
    )[0]
    candles = normalize_hyperliquid_candle_snapshot(
        [{"t": 1735689600000, "T": 1735775999999, "o": "100", "h": "101", "l": "99", "c": "100", "v": "1"}],
        requested_symbol="ETH",
        resolved_venue_symbol="ETH",
        timeframe="1d",
    )

    path = write_import_candle_file(work_dir=tmp_path, identity=identity, timeframe="1d", candles=candles)
    payload = json.loads(path.read_text(encoding="utf-8"))
    row = payload["candles"][0]

    assert row["instrument_key"] == "perpetual:linear:ETH:USDC:USDC"
    assert row["close_time"] == "2025-01-02T00:00:00Z"
    assert row["raw_venue_close_time"] == "2025-01-01T23:59:59.999000Z"


def test_campaign_configs_include_1d_v12_dynamic_equity_and_no_testnet_truth(tmp_path: Path) -> None:
    identities = resolve_hyperliquid_market_identities(
        {"universe": [{"name": "BTC", "szDecimals": 5}, {"name": "ETH", "szDecimals": 4}]},
        requested_symbols=("BTC", "ETH"),
    )
    datasets = [_dataset(symbol, timeframe) for symbol in ("BTC", "ETH") for timeframe in ("15m", "1h", "4h", "1d")]

    paths = write_sv202_campaign_configs(datasets=datasets, identities=identities, output_dir=tmp_path)
    by_name = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in paths}

    assert len(paths) == 8
    assert "money_flow_sv2_0_2_hyperliquid_public_btc_1d_canonical.json" in by_name
    one_day = by_name["money_flow_sv2_0_2_hyperliquid_public_btc_1d_canonical.json"]
    assert one_day["money_flow_version"] == "money_flow_v1_2"
    assert one_day["components"] == ["sleeve_1d"]
    assert one_day["symbols"] == [{"instrument_key": "perpetual:linear:BTC:USDC:USDC", "symbol": "BTC"}]
    assert "full_available_window" in one_day["windows"][0]["label"]
    assert one_day["capital_sizing_modes"] == ["dynamic_equity_pct"]
    assert one_day["initial_capital"] == "10000"
    assert one_day["testnet_prices_used_as_strategy_truth"] is False
    assert one_day["research_boundaries"]["calls_order_endpoints"] is False
    assert one_day["windows"][0]["start"].endswith("+00:00") or one_day["windows"][0]["start"].endswith("Z")


def test_canonical_pack_rows_and_open_position_summary_are_explicit(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    pack.mkdir()
    (pack / "batch_report.json").write_text(
        json.dumps(
            {
                "comparison_summary": {
                    "run_summaries": [
                        {
                            "status": "completed",
                            "symbol": "BTC",
                            "component_keys": ["sleeve_1d"],
                            "fill_timing": "next_candle_open",
                            "metrics": {
                                "ending_equity": "10050",
                                "net_pnl": "50",
                                "number_of_trades": 1,
                                "win_rate": "1",
                                "mark_to_market_max_drawdown": "25",
                            },
                        }
                    ]
                },
                "run_reports": [
                    {
                        "report": {
                            "components": [
                                {
                                    "trades": [
                                        {"trade_id": "t1", "forced_exit": True},
                                    ]
                                }
                            ]
                        }
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rows = canonical_evidence_rows_from_packs([str(pack)])
    open_summary = summarize_open_position_handling([str(pack)])

    assert rows[0]["timeframe"] == "1d"
    assert rows[0]["display_timeframe"] == "1D"
    assert rows[0]["status"] == "canonical_evidence_ready"
    assert rows[0]["ending_equity"] == "10050"
    assert open_summary["policy"] == "force_close_at_dataset_end"
    assert open_summary["forced_close_count"] == 1
    assert open_summary["excluded_open_position_count"] == 0


def test_sor_ev1_requires_canonical_paths_and_1d_ready() -> None:
    assert (
        sor_ev1_readiness_decision(
            db_blockers=["strategy_validation_db_unreachable"],
            evidence_pack_paths=[],
            readiness_rows=[],
        )
        == "SOR-EV1 remains blocked"
    )
    assert (
        sor_ev1_readiness_decision(
            db_blockers=[],
            evidence_pack_paths=["reports/strategy_validation/pack"],
            readiness_rows=[
                {"timeframe": "1d", "canonical_evidence_ready": True, "db_imported": True, "evidence_ready": True}
            ],
        )
        == "SOR-EV1 may proceed"
    )


def test_report_and_script_keep_no_order_no_live_boundaries() -> None:
    script = Path("scripts/run_sv202_canonical_import_and_evidence.py").read_text(encoding="utf-8")
    assert HYPERLIQUID_MAINNET_PUBLIC_INFO_URL == "https://api.hyperliquid.xyz/info"
    assert "testnet" in script
    assert "order endpoints" in script
    assert "exchange(" not in script

    dashboard = Path("apps/dashboard/evidence-dashboard.js").read_text(encoding="utf-8")
    assert "Canonical evidence:" in dashboard
    assert "DB imported:" in dashboard
    assert "Compact replay canonical:" in dashboard

    report = render_sv202_report(
        {
            "money_flow_version": "money_flow_v1_2",
            "canonical_evidence_status": {"status": "blocked", "evidence_pack_paths": []},
            "market_identities": [],
            "data_readiness": [],
            "excluded_symbols": [],
            "evidence_rows": [],
            "sv2_0_2": {
                "sor_ev1_readiness_decision": "SOR-EV1 remains blocked",
                "db_status": {
                    "configured_database_url": "postgresql+psycopg://money_flow:***@127.0.0.1:5432/money_flow",
                    "reachable": False,
                    "schema_status": "database_unreachable",
                    "migrations_current": None,
                    "persisted_candle_count": None,
                },
                "db_blocking_reason_codes": ["strategy_validation_db_unreachable"],
                "import_results": [],
                "campaign_config_paths": [],
                "open_position_handling": {
                    "policy": "force_close_at_dataset_end",
                    "open_position_handling_explicit": False,
                    "forced_close_count": 0,
                    "mtm_count": 0,
                    "excluded_open_position_count": 0,
                },
                "boundary_flags": {
                    "submits_orders": False,
                    "calls_order_endpoints": False,
                    "calls_private_or_signed_endpoints": False,
                    "uses_api_keys": False,
                    "uses_testnet_prices_as_strategy_truth": False,
                    "enables_live_trading": False,
                },
            },
        }
    )
    assert "No-Order / No-Live Confirmation" in report
    assert "SV2.0.2 Canonical SV2 Evidence Packs" in report
