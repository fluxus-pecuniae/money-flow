from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from services.paper_runtime.pt_rt1 import (
    PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
    PT_RT1_MAINNET_INFO_URL,
    PT_RT1_STRATEGY_LANES,
    PT_RT1_TESTNET_INFO_URL,
    Candle,
    PaperLedger,
    PaperSignalKey,
    StrategyTruthPayloadValidation,
    TestnetProbeCandidate as PTRT1ProbeCandidate,
    TestnetProbePolicy as PTRT1ProbePolicy,
    build_pt_rt1_summary,
    compute_indicator_snapshot,
    evaluate_closed_candle_gate,
    resolve_top20_universe,
    validate_strategy_truth_payload,
)


def _candle(index: int, close: str | None = None) -> Candle:
    base = Decimal(close or str(100 + index))
    return Candle(
        symbol="ETH",
        timeframe="1h",
        open_time=datetime(2026, 5, 1, tzinfo=UTC) + timedelta(hours=index),
        open=base - Decimal("1"),
        high=base + Decimal("2"),
        low=base - Decimal("2"),
        close=base,
        volume=Decimal("100"),
    )


def test_strategy_truth_lane_allows_only_public_mainnet_info_payloads() -> None:
    allowed = validate_strategy_truth_payload(endpoint=PT_RT1_MAINNET_INFO_URL, payload={"type": "candleSnapshot"})
    testnet = validate_strategy_truth_payload(endpoint=PT_RT1_TESTNET_INFO_URL, payload={"type": "candleSnapshot"})
    private = validate_strategy_truth_payload(endpoint=PT_RT1_MAINNET_INFO_URL, payload={"type": "clearinghouseState"})
    keyed = validate_strategy_truth_payload(
        endpoint=PT_RT1_MAINNET_INFO_URL,
        payload={"type": "meta"},
        headers={"Authorization": "Bearer nope"},
    )

    assert isinstance(allowed, StrategyTruthPayloadValidation)
    assert allowed.allowed is True
    assert testnet.allowed is False
    assert "strategy_truth_requires_public_mainnet_info_endpoint" in testnet.reason_codes
    assert private.allowed is False
    assert "private_or_account_state_forbidden_for_strategy_truth" in private.reason_codes
    assert keyed.allowed is False
    assert "strategy_truth_uses_no_api_keys" in keyed.reason_codes


def test_top20_scanner_blocks_unsupported_precision_failed_stablecoin_and_shib_unit_risk() -> None:
    rows = resolve_top20_universe(
        ["BTC", "ETH", "USDT", "SHIB", "TON", "DOGE"],
        hyperliquid_meta=[
            {"name": "BTC", "szDecimals": 5},
            {"name": "ETH", "szDecimals": 4},
            {"name": "DOGE"},
        ],
        mids={"BTC": "65000", "ETH": "3200"},
    )
    by_symbol = {row.requested_symbol: row for row in rows}

    assert by_symbol["BTC"].scanner_eligible is True
    assert by_symbol["ETH"].scanner_eligible is True
    assert by_symbol["USDT"].scanner_eligible is False
    assert "stablecoin_excluded" in by_symbol["USDT"].reason_codes
    assert by_symbol["SHIB"].scanner_eligible is False
    assert "venue_symbol_unit_semantics_deferred" in by_symbol["SHIB"].reason_codes
    assert by_symbol["TON"].scanner_eligible is False
    assert "unsupported_by_hyperliquid" in by_symbol["TON"].reason_codes
    assert by_symbol["DOGE"].scanner_eligible is False
    assert "precision_missing" in by_symbol["DOGE"].reason_codes


def test_fully_closed_candle_gating_rejects_incomplete_duplicate_gap_and_out_of_order() -> None:
    candle = _candle(0)

    incomplete = evaluate_closed_candle_gate(candle, now=candle.open_time + timedelta(minutes=30))
    accepted = evaluate_closed_candle_gate(candle, now=candle.open_time + timedelta(hours=1, seconds=1))
    duplicate = evaluate_closed_candle_gate(
        candle,
        now=candle.open_time + timedelta(hours=1, seconds=1),
        last_processed_close=candle.open_time + timedelta(hours=1),
    )
    gap = evaluate_closed_candle_gate(
        _candle(3),
        now=_candle(3).open_time + timedelta(hours=1, seconds=1),
        last_processed_close=candle.open_time + timedelta(hours=1),
    )
    out_of_order = evaluate_closed_candle_gate(
        candle,
        now=candle.open_time + timedelta(hours=1, seconds=1),
        last_processed_close=candle.open_time + timedelta(hours=2),
    )

    assert incomplete.accepted is False
    assert "candle_not_closed" in incomplete.reason_codes
    assert accepted.accepted is True
    assert duplicate.accepted is False
    assert "duplicate_candle_ignored" in duplicate.reason_codes
    assert gap.accepted is False
    assert "missing_candle_gap_detected" in gap.reason_codes
    assert out_of_order.accepted is False
    assert "out_of_order_candle" in out_of_order.reason_codes


def test_missing_indicators_do_not_default_to_zero() -> None:
    snapshot = compute_indicator_snapshot([_candle(0), _candle(1), _candle(2)])

    assert snapshot.ema5 is None
    assert snapshot.macd is None
    assert "missing_indicator_field" in snapshot.reason_codes
    assert "missing_ema5" in snapshot.reason_codes
    assert "missing_macd" in snapshot.reason_codes
    assert "insufficient_history" in snapshot.reason_codes


def test_paper_ledger_starts_at_10000_compounds_and_tracks_drawdown_and_losing_streaks() -> None:
    ledger = PaperLedger(PT_RT1_STRATEGY_LANES[0])

    assert ledger.realized_equity == Decimal("10000")
    ledger.apply_closed_trade_result(net_pnl=Decimal("2000"))
    ledger.apply_closed_trade_result(net_pnl=Decimal("-1000"))
    ledger.apply_closed_trade_result(net_pnl=Decimal("-1300"))

    assert ledger.realized_equity == Decimal("9700")
    assert ledger.max_equity == Decimal("12000")
    assert ledger.max_drawdown == Decimal("2300")
    assert ledger.consecutive_losses == 2
    assert ledger.max_consecutive_losses == 2
    assert ledger.worst_losing_streak_pnl == Decimal("-2300")


def test_paper_ledger_duplicate_signal_prevention_and_unrealized_pnl() -> None:
    ledger = PaperLedger(PT_RT1_STRATEGY_LANES[1])
    signal = PaperSignalKey(
        lane_id=ledger.lane.lane_id,
        strategy_id=ledger.lane.strategy_id,
        symbol="ETH",
        timeframe="1h",
        signal_candle_time="2026-05-14T01:00:00Z",
        action="entry",
    )

    assert ledger.register_signal(signal) == (True, ())
    assert ledger.register_signal(signal) == (False, ("duplicate_ignored",))
    position, reasons = ledger.open_synthetic_position(
        symbol="ETH",
        timeframe="1h",
        signal_time=signal.signal_candle_time,
        fill_time="2026-05-14T02:00:00Z",
        fill_price=Decimal("100"),
        reason_codes=("paper_entry",),
    )
    assert reasons == ()
    assert position is not None
    pnl, reasons = ledger.update_unrealized(symbol="ETH", timeframe="1h", current_price=Decimal("105"))
    assert reasons == ()
    assert pnl > 0
    assert ledger.total_equity > ledger.realized_equity
    assert ledger.duplicate_signal_blocks == 1
    assert ledger.created_execution_artifacts is False


def test_paper_ledger_close_trade_compounds_without_resetting_after_loss() -> None:
    ledger = PaperLedger(PT_RT1_STRATEGY_LANES[0])
    ledger.open_synthetic_position(
        symbol="ETH",
        timeframe="1h",
        signal_time="2026-05-14T01:00:00Z",
        fill_time="2026-05-14T02:00:00Z",
        fill_price=Decimal("100"),
    )
    trade, reasons = ledger.close_synthetic_position(
        symbol="ETH",
        timeframe="1h",
        exit_time="2026-05-14T03:00:00Z",
        exit_price=Decimal("99"),
        reason_codes=("paper_exit",),
    )

    assert reasons == ()
    assert trade is not None
    assert trade.equity_after == ledger.realized_equity
    assert trade.net_pnl == trade.equity_after - trade.equity_before
    assert ledger.consecutive_losses == 1
    assert ledger.realized_equity < Decimal("10000")


def test_strategy_lanes_are_independent_and_evidence_only_where_required() -> None:
    by_strategy = {lane.strategy_id: lane for lane in PT_RT1_STRATEGY_LANES}

    assert set(by_strategy) == {
        "money_flow_v1_2_baseline",
        "avoid_low_rolling_range_50",
        "avoid_low_rolling_range_20",
        "mf_orig_1d_stage2_breakout_resistance_full_equity",
    }
    assert by_strategy["avoid_low_rolling_range_50"].production_approved is False
    assert "evidence_only_candidate_lane" in by_strategy["avoid_low_rolling_range_50"].reason_codes
    assert "mf_orig_reference_lane" in by_strategy["mf_orig_1d_stage2_breakout_resistance_full_equity"].reason_codes
    assert by_strategy["mf_orig_1d_stage2_breakout_resistance_full_equity"].live_trading_approved is False


def test_testnet_probe_path_is_disabled_by_default_and_requires_exact_approval() -> None:
    policy = PTRT1ProbePolicy()
    default_result = policy.evaluate(PTRT1ProbeCandidate())
    missing_approval = policy.evaluate(
        PTRT1ProbeCandidate(probes_enabled=True, kill_switch=False, approval_text="almost")
    )

    assert default_result.eligible is False
    assert "testnet_probes_disabled" in default_result.reason_codes
    assert "testnet_probe_kill_switch_enabled" in default_result.reason_codes
    assert default_result.audit_row["testnet_fills_update_strategy_pnl"] is False
    assert missing_approval.eligible is False
    assert "testnet_probe_approval_missing" in missing_approval.reason_codes


def test_testnet_probe_caps_unknown_state_and_post_only_shape() -> None:
    policy = PTRT1ProbePolicy()
    approved = PTRT1ProbeCandidate(
        approval_text=PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
        probes_enabled=True,
        kill_switch=False,
        account_mode="main",
        account_address="0xabc",
        symbol="ETH",
        asset_id=1,
        sz_decimals=4,
        price=Decimal("3000.123456"),
        quantity=Decimal("0.0023456"),
        notional=Decimal("7"),
    )
    result = policy.evaluate(approved)
    capped = policy.evaluate(approved.__class__(**{**approved.__dict__, "notional": Decimal("10")}))
    unknown = policy.evaluate(approved.__class__(**{**approved.__dict__, "unknown_or_open_probe_state": True}))

    assert result.eligible is True
    assert result.order_shape is not None
    assert "vaultAddress" not in result.order_shape
    assert result.order_shape["action"]["orders"][0]["t"]["limit"]["tif"] == "Alo"
    assert capped.eligible is False
    assert "testnet_probe_notional_cap_exceeded" in capped.reason_codes
    assert unknown.eligible is False
    assert "unknown_probe_state_blocks_future_probes" in unknown.reason_codes


def test_probe_account_targeting_main_omits_vault_and_subaccount_requires_explicit_vault() -> None:
    policy = PTRT1ProbePolicy()
    base = PTRT1ProbeCandidate(
        approval_text=PT_RT1_EXACT_TESTNET_PROBE_APPROVAL,
        probes_enabled=True,
        kill_switch=False,
        account_address="0xabc",
        symbol="ETH",
        asset_id=1,
        sz_decimals=4,
        notional=Decimal("5"),
    )
    main_with_vault = policy.evaluate(base.__class__(**{**base.__dict__, "account_mode": "main", "vault_address": "0xvault"}))
    sub_without_vault = policy.evaluate(base.__class__(**{**base.__dict__, "account_mode": "subaccount", "vault_address": None}))
    sub_with_vault = policy.evaluate(base.__class__(**{**base.__dict__, "account_mode": "subaccount", "vault_address": "0xvault"}))

    assert "vault_address_forbidden_for_main_user" in main_with_vault.reason_codes
    assert "vault_address_required_for_subaccount_or_vault" in sub_without_vault.reason_codes
    assert sub_with_vault.eligible is True
    assert sub_with_vault.order_shape is not None
    assert sub_with_vault.order_shape["vaultAddress"] == "0xvault"


def test_summary_and_report_files_exist_and_expose_boundaries() -> None:
    summary_path = Path("docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json")
    report_path = Path("docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing.md")

    summary = build_pt_rt1_summary()
    assert summary_path.exists()
    assert report_path.exists()
    assert summary["strategy_truth_lane"]["endpoint"] == PT_RT1_MAINNET_INFO_URL
    assert summary["strategy_truth_lane"]["uses_api_keys"] is False
    assert summary["testnet_probe_policy"]["PT_RT1_TESTNET_PROBES_ENABLED"] is False
    assert summary["boundaries"]["live_exchange_orders_submitted"] is False
    assert summary["paper_equity_policy"]["starting_equity_usdc_per_lane"] == "10000"


def test_pt_rt1_strategy_lane_does_not_construct_production_execution_artifacts() -> None:
    source = Path("services/paper_runtime/pt_rt1.py").read_text(encoding="utf-8")

    assert "from db.models" not in source
    assert "submit_order(" not in source
    assert "OrderIntent(" not in source
    assert "PreparedVenueOrder(" not in source
    assert "SubmittedOrder(" not in source
