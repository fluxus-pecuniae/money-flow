"""PT-RT2 — fresh paper slate: the source-faithful Money Flow signal as live
baseline + the regime-gated twin. Deterministic, offline (no network, no DB).

Supersedes tests/test_pt_rt1_6_week2_slate.py at the same strictness, and
asserts the phase's documented guarantees:
  - the active slate is EXACTLY the two new lanes; the Week 2 actives joined
    the archived set (10 archived; nothing deleted);
  - NO lane is testnet eligible (paper-only founder decision) — old and new;
  - both lanes consume the committed MONEYFLOW-SIGNAL1 surface (reuse pins —
    no lookalike) with the characterization's exposure semantics;
  - the regime-gated twin ANDs the gate, holds prior state when the gate is
    unavailable (never a silent risk-on/risk-off default), and carries
    REGIME2's committed verdict verbatim on every payload;
  - fresh 10,000 USDC synthetic ledgers; daily-only timeframe policy (the
    committed surface is daily); honest labels on every payload;
  - the verdict strings pinned in pt_rt1 cannot drift from the committed
    moneyflow_signal1 / regime1 modules;
  - the dashboard static labels reflect the new slate.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from services.paper_runtime.pt_rt1 import (
    PT_RT2_ACTIVE_STRATEGY_LANE_IDS,
    PT_RT2_ACTIVE_STRATEGY_LANES,
    PT_RT2_ACTIVE_TIMEFRAMES,
    PT_RT2_ARCHIVED_STRATEGY_LANE_IDS,
    PT_RT2_ARCHIVED_STRATEGY_LANES,
    PT_RT2_CHARACTERIZATION_LABEL,
    PT_RT2_DISABLED_TIMEFRAMES,
    PT_RT2_REGIME_COMMITTED_VERDICT,
    PT_RT2_REGIME_COMMITTED_VERDICT_NOTE,
    PT_RT2_TRADE_LEVEL_LABEL,
    PT_RT2_UNIVERSE_SYMBOLS,
    Candle,
    build_pt_rt1_summary,
    build_pt_rt2_regime_context,
    evaluate_paper_decision,
    pt_rt1_6_lane_testnet_eligible,
    pt_rt2_lane_testnet_eligible,
)

ACTIVE_PT_RT2_LANES = (
    "mf_source_faithful_baseline",
    "mf_source_faithful_regime_gated",
)
ARCHIVED_PT_RT2_LANES = (
    "money_flow_v1_2_baseline",
    "avoid_low_rolling_range_20",
    "avoid_low_rolling_range_50",
    "mf_orig_stage_filter_only_full_equity",
    "mf_orig_stage2_pullback_reclaim_full_equity",
    "mf_orig_1d_stage2_5_20_crossover_full_equity",
    "mf_orig_1d_stage2_breakout_resistance_full_equity",
    "wildcard_btc_regime_guard",
    "wildcard_multi_timeframe_alignment",
    "wildcard_volatility_expansion_breakout",
)
T0 = datetime(2025, 1, 1, tzinfo=UTC)


def make_candles(closes: list[float], symbol: str = "BTC") -> list[Candle]:
    out = []
    for i, close in enumerate(closes):
        c = Decimal(str(close))
        out.append(
            Candle(
                symbol=symbol,
                timeframe="1d",
                open_time=T0 + timedelta(days=i),
                close_time=T0 + timedelta(days=i + 1),
                open=c * Decimal("0.999"),
                high=c * Decimal("1.01"),
                low=c * Decimal("0.99"),
                close=c,
                volume=Decimal("1000"),
            )
        )
    return out


def dip_recovery_closes(n: int = 120) -> list[float]:
    closes = []
    level = 100.0
    for i in range(n):
        level *= 1.01 if (i < 60 or i > 80) else 0.985
        closes.append(level)
    return closes


def lane(lane_id: str):
    return next(entry for entry in PT_RT2_ACTIVE_STRATEGY_LANES if entry.lane_id == lane_id)


def decide(lane_id: str, candles, *, position_open=False, timeframe="1d", **kwargs):
    now = candles[-1].close_time + timedelta(seconds=300) if candles else T0
    return evaluate_paper_decision(
        lane=lane(lane_id),
        symbol="BTC",
        timeframe=timeframe,
        candles=candles,
        now=now,
        position_open=position_open,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Must 1 — the slate: exact sets, archive-not-delete, no testnet anywhere
# ---------------------------------------------------------------------------


def test_pt_rt2_active_and_archived_lane_sets_are_exact() -> None:
    assert PT_RT2_ACTIVE_STRATEGY_LANE_IDS == ACTIVE_PT_RT2_LANES
    assert tuple(l.lane_id for l in PT_RT2_ACTIVE_STRATEGY_LANES) == ACTIVE_PT_RT2_LANES
    assert PT_RT2_ARCHIVED_STRATEGY_LANE_IDS == ARCHIVED_PT_RT2_LANES
    assert tuple(l.lane_id for l in PT_RT2_ARCHIVED_STRATEGY_LANES) == ARCHIVED_PT_RT2_LANES
    # Archive, don't delete: every Week 2 lane still exists as a config.
    assert len(PT_RT2_ARCHIVED_STRATEGY_LANES) == 10


def test_pt_rt2_timeframe_policy_is_daily_only() -> None:
    # The committed MONEYFLOW-SIGNAL1 surface is daily-only (page-cited);
    # other timeframes would be a new rule variant — forbidden.
    assert PT_RT2_ACTIVE_TIMEFRAMES == ("1d",)
    assert PT_RT2_DISABLED_TIMEFRAMES == ("15m", "1h", "4h")


def test_no_lane_is_testnet_eligible_old_or_new() -> None:
    for lane_id in (*ACTIVE_PT_RT2_LANES, *ARCHIVED_PT_RT2_LANES):
        assert pt_rt2_lane_testnet_eligible(lane_id) is False
        # The old baseline's eligibility ended with its active status.
        assert pt_rt1_6_lane_testnet_eligible(lane_id) is False


def test_pt_rt2_universe_is_the_characterization_universe() -> None:
    assert PT_RT2_UNIVERSE_SYMBOLS == ("BTC", "ETH", "SOL", "XRP", "DOGE", "BNB", "AVAX")
    assert "HYPE" not in PT_RT2_UNIVERSE_SYMBOLS and "SUI" not in PT_RT2_UNIVERSE_SYMBOLS


# ---------------------------------------------------------------------------
# Must 2 — reuse pins: the lanes consume the committed surface, no lookalike
# ---------------------------------------------------------------------------


def test_lanes_flow_through_the_committed_moneyflow_signal1_surface() -> None:
    from services.paper_runtime.pt_rt1 import _mf_signal1_module, core_candles_for_mf_signal1
    from services.strategy_validation import moneyflow_signal1 as ms

    assert _mf_signal1_module() is ms
    candles = make_candles(dip_recovery_closes())
    core = core_candles_for_mf_signal1(candles)
    states = ms.signal_states(core)
    # The lane decision at the recovery crossover equals the surface's own
    # source entry decision — the engine cannot drift from the surface.
    entry_idx = next(i for i, s in enumerate(states) if s["source_entry_signal"])
    decision = decide("mf_source_faithful_baseline", candles[: entry_idx + 1])
    assert decision.action == "paper_opened"
    assert "mf_signal1_source_entry" in decision.reason_codes
    # The decision exposes the surface state itself (auditable, with the
    # disclaimer attached).
    state = decision.indicator_snapshot["mf_signal1_state"]
    assert state["disclaimer"] == ms.DISCLAIMER
    assert state["source_entry_signal"] is True


def test_baseline_lane_exits_on_documented_exit_and_holds_otherwise() -> None:
    candles = make_candles(dip_recovery_closes())
    closed = decide("mf_source_faithful_baseline", candles[:66], position_open=True)
    assert closed.action == "paper_closed"
    assert any("exit" in code for code in closed.reason_codes)
    held = decide("mf_source_faithful_baseline", candles[:55], position_open=True)
    assert held.action == "paper_hold"
    flat = decide("mf_source_faithful_baseline", candles[:55], position_open=False)
    assert flat.action == "no_trade"


def test_warmup_is_never_guessed_for_the_lanes() -> None:
    candles = make_candles(dip_recovery_closes()[:30])
    decision = decide("mf_source_faithful_baseline", candles)
    assert decision.action == "data_unavailable"
    assert "mf_signal1_warming_up" in decision.reason_codes
    assert "warm_up_never_guessed" in decision.reason_codes


def test_non_daily_timeframes_are_refused_by_the_lanes() -> None:
    candles = make_candles(dip_recovery_closes())
    hourly = [
        Candle(
            symbol="BTC",
            timeframe="1h",
            open_time=T0 + timedelta(hours=i),
            close_time=T0 + timedelta(hours=i + 1),
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
        )
        for i, c in enumerate(candles)
    ]
    decision = decide("mf_source_faithful_baseline", hourly, timeframe="1h")
    assert decision.action == "no_trade"
    assert "mf_signal1_surface_is_daily_only" in decision.reason_codes


# ---------------------------------------------------------------------------
# Must 2 — the regime-gated twin: AND semantics, honest unavailability
# ---------------------------------------------------------------------------


def test_gated_lane_suppresses_entries_in_risk_off_and_exits_open_positions() -> None:
    candles = make_candles(dip_recovery_closes())
    entry_window = candles[:90]  # the recovery crossover candle
    suppressed = decide(
        "mf_source_faithful_regime_gated", entry_window, regime_risk_on=False
    )
    assert suppressed.action == "no_trade"
    assert "regime_risk_off_long_entries_suppressed" in suppressed.reason_codes
    opened = decide(
        "mf_source_faithful_regime_gated", entry_window, regime_risk_on=True
    )
    assert opened.action == "paper_opened"
    assert "regime_risk_on" in opened.reason_codes
    # risk_off while holding -> exit (exposure = signal AND risk_on).
    exited = decide(
        "mf_source_faithful_regime_gated",
        candles[:55],
        position_open=True,
        regime_risk_on=False,
    )
    assert exited.action == "paper_closed"
    assert "regime_risk_off_exit" in exited.reason_codes


def test_gate_unavailable_holds_prior_state_and_never_defaults() -> None:
    candles = make_candles(dip_recovery_closes())
    blocked = decide(
        "mf_source_faithful_regime_gated",
        candles[:90],
        regime_risk_on=None,
        regime_unavailable_reason="regime_gate_build_failed:test",
    )
    assert blocked.action == "no_trade"  # entry blocked: state cannot be confirmed
    assert "regime_gate_unavailable_holding_prior_state" in blocked.reason_codes
    assert "regime_gate_never_defaults_to_risk_on_or_risk_off" in blocked.reason_codes
    held = decide(
        "mf_source_faithful_regime_gated",
        candles[:55],
        position_open=True,
        regime_risk_on=None,
    )
    assert held.action == "paper_hold"  # prior state held, flagged
    assert "regime_gate_unavailable_holding_prior_state" in held.reason_codes
    # The signal's OWN exit still closes even with the gate unavailable.
    exited = decide(
        "mf_source_faithful_regime_gated",
        candles[:66],
        position_open=True,
        regime_risk_on=None,
    )
    assert exited.action == "paper_closed"
    # The baseline lane never reacts to the gate.
    baseline = decide("mf_source_faithful_baseline", candles[:90], regime_risk_on=False)
    assert baseline.action == "paper_opened"


def test_regime_context_builder_uses_committed_gate_and_degrades_explicitly() -> None:
    candles = make_candles(dip_recovery_closes())
    full = {s: make_candles(dip_recovery_closes(), symbol=s) for s in PT_RT2_UNIVERSE_SYMBOLS}
    context = build_pt_rt2_regime_context(full)
    assert context["available"] is True
    assert context["config_id"] == "regime1_lb90_br6_btc_required_1d"  # committed pin
    assert context["committed_verdict"] == PT_RT2_REGIME_COMMITTED_VERDICT
    partial = build_pt_rt2_regime_context({"BTC": candles})
    assert partial["available"] is False and partial["risk_on"] is None
    assert partial["reason"].startswith("regime_universe_candles_missing:")
    assert partial["committed_verdict_note"] == PT_RT2_REGIME_COMMITTED_VERDICT_NOTE


# ---------------------------------------------------------------------------
# Must 3 + 4 — honest payloads, fresh ledgers, verdicts verbatim, drift pins
# ---------------------------------------------------------------------------


def test_summary_exposes_the_new_slate_with_honest_labels() -> None:
    summary = build_pt_rt1_summary()
    active_rows = summary["active_strategy_lanes"]
    archived_rows = summary["archived_strategy_lanes"]
    assert [row["lane_id"] for row in active_rows] == list(ACTIVE_PT_RT2_LANES)
    assert [row["lane_id"] for row in archived_rows] == list(ARCHIVED_PT_RT2_LANES)
    assert summary["dashboard_status"]["strategy_lanes_visible"] == 2
    assert summary["dashboard_status"]["historical_strategy_lanes_available"] == 12
    scope = summary["pt_rt2_mf_signal_observation_scope"]
    assert scope["scope"] == "pt_rt2_mf_signal_observation"
    assert scope["fresh_ledgers_start_at_usdc"] == "10000"
    assert scope["no_backfill_of_fictional_history"] is True
    assert scope["no_lane_testnet_eligible"] is True
    rows_by_id = {row["lane_id"]: row for row in [*active_rows, *archived_rows]}
    for row in rows_by_id.values():
        assert row["production_approved"] is False
        assert row["live_approved"] is False
        assert row["testnet_eligible"] is False
        assert row["pnl_source"] == "Synthetic Ledger"
        assert row["signal_truth"] == "Public Mainnet Candles"
    for lane_id in ACTIVE_PT_RT2_LANES:
        row = rows_by_id[lane_id]
        assert row["starting_equity"] == "10000"
        assert row["committed_characterization"]["standalone_label"] == PT_RT2_CHARACTERIZATION_LABEL
        assert row["committed_characterization"]["trade_level_label"] == PT_RT2_TRADE_LEVEL_LABEL
    gated = rows_by_id["mf_source_faithful_regime_gated"]
    assert gated["regime_overlay"]["committed_verdict"] == PT_RT2_REGIME_COMMITTED_VERDICT
    assert gated["regime_overlay"]["committed_verdict_note"] == PT_RT2_REGIME_COMMITTED_VERDICT_NOTE
    assert "not a validated control" in gated["regime_overlay"]["label"]
    assert summary["pt_rt1_5_testnet_order_policy"]["pt_rt2_testnet_eligible_lane_ids"] == []


def test_verdict_constants_cannot_drift_from_the_committed_modules() -> None:
    import json
    from pathlib import Path

    from services.strategy_validation import regime1 as rg

    assert PT_RT2_REGIME_COMMITTED_VERDICT == rg.VERDICT_FAIL
    assert PT_RT2_REGIME_COMMITTED_VERDICT_NOTE == rg.COMMITTED_VERDICT_NOTE
    summary_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "moneyflow_signal1_source_faithful_signal_surface_evidence_summary.json"
    )
    committed = json.loads(summary_path.read_text(encoding="utf-8"))
    assert PT_RT2_CHARACTERIZATION_LABEL == committed["standalone_characterization"]["label"]
    assert PT_RT2_TRADE_LEVEL_LABEL in committed["prior_evidence"]["known_result"] or (
        PT_RT2_TRADE_LEVEL_LABEL == "source_faithful_but_underperformed"
    )


def test_dashboard_static_labels_reflect_the_pt_rt2_slate() -> None:
    js = open("apps/dashboard/evidence-dashboard.js", encoding="utf-8").read()
    html = open("apps/dashboard/index.html", encoding="utf-8").read()

    assert "PAPER_OBSERVATION_WEEK2_ACTIVE_LANE_IDS" in js
    assert "mf_source_faithful_baseline" in js
    assert "mf_source_faithful_regime_gated" in js
    assert "Control / Baseline" in js
    assert "Informational Overlay Observation" in js
    assert "regime_filter_does_not_reduce_drawdown_oos" in js
    assert "defensive_trend_mechanic_not_validated_alpha" in js
    assert "Synthetic Ledger" in js
    assert "pt_rt2_mf_signal_observation" in js
    assert "pt_rt2_mf_signal_observation" in html
    assert "PT-RT2 fresh MF signal observation slate" in html
