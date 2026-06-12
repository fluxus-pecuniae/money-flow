"""MONEYFLOW-SIGNAL1 — deterministic, offline tests (no network, no DB).

Asserts the phase's documented guarantees:
  - FIDELITY: the indicator arithmetic reproduces hand-computed reference
    points (the worked-example fixtures the PDF's narrative rules pin), and
    each documented rule (p.37 crossover buy/sell, p.150 exits, p.127/p.140
    RSI rules, p.146 Stage-2 entry, p.150 quarter-trim context) fires on an
    engineered series exactly where the source says it should;
  - REUSE: the signal surface is built from MF-ORIG-EV1's primitives and the
    production indicator implementations (no re-derived lookalike);
  - NO-LOOKAHEAD: states are closed-candle-only and provably ignore the
    future; warm-up is never guessed;
  - REGIME OVERLAY: imports through the strategy_types seam with the honest
    FAIL verdict intact on every surface — informational risk context, never
    a validated control;
  - HONEST FRAMING: the disclaimer travels on every state and payload; the
    committed evidence summary records the pre-stated two-stage screens and
    the defensive-mechanic (not-validated-alpha) label; forbidden language
    is absent;
  - CLI: the offline path emits the auditable JSON.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from services.strategy_validation import mf_orig_ev1, strategy_types
from services.strategy_validation import moneyflow_signal1 as ms
from services.strategy_validation import regime1 as rg

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = (
    REPO_ROOT / "docs" / "moneyflow_signal1_source_faithful_signal_surface_evidence_summary.json"
)
T0 = datetime(2025, 1, 1, tzinfo=UTC)


def make_rows(closes: list[float], *, volume: float = 50_000_000.0) -> list[dict]:
    rows = []
    for i, close in enumerate(closes):
        rows.append(
            {
                "venue": "binance",
                "open_time": (T0 + timedelta(days=i)).isoformat(),
                "close_time": (T0 + timedelta(days=i + 1)).isoformat(),
                "open": f"{close * 0.999:.8f}",
                "high": f"{close * 1.01:.8f}",
                "low": f"{close * 0.99:.8f}",
                "close": f"{close:.8f}",
                "volume_base": f"{volume}",
            }
        )
    return rows


def make_candles(closes: list[float]) -> list:
    return ms.core_candles_from_data1_rows("BTC", make_rows(closes))


def dip_recovery_closes(n: int = 120) -> list[float]:
    """Uptrend, a sharp dip, then recovery — drives every documented rule."""
    closes = []
    level = 100.0
    for i in range(n):
        level *= 1.01 if (i < 60 or i > 80) else 0.985
        closes.append(level)
    return closes


# ---------------------------------------------------------------------------
# Must 1 — fidelity fixtures: hand-computed indicator reference points
# ---------------------------------------------------------------------------


def test_sma20_reproduces_hand_computed_average():
    closes = [float(i + 1) for i in range(25)]  # 1..25
    candles = make_candles(closes)
    snapshots = ms.compute_snapshots(candles)
    # SMA20 at index 19 = mean(1..20) = 10.5; at 24 = mean(6..25) = 15.5.
    assert snapshots[18].sma_20 is None  # warm-up: never guessed
    assert snapshots[19].sma_20 == Decimal("10.5")
    assert snapshots[24].sma_20 == Decimal("15.5")


def test_ema5_reproduces_hand_computed_recursion():
    # closes 1..10: seed at idx4 = mean(1..5) = 3; multiplier 2/(5+1) = 1/3;
    # each next close is ema+3, so ema steps by exactly 1: ema(i) = close(i)-2.
    closes = [float(i + 1) for i in range(10)]
    snapshots = ms.compute_snapshots(make_candles(closes))
    assert snapshots[3].ema_5 is None
    assert snapshots[4].ema_5 == Decimal("3")
    assert snapshots[5].ema_5 == Decimal("4")
    assert snapshots[9].ema_5 == Decimal("8")


def test_rsi14_reproduces_hand_computed_wilder_values():
    # Deltas: 7 gains of 1 then 7 losses of 1 -> avg_gain = avg_loss = 0.5
    # -> RS = 1 -> RSI = 50 exactly at idx14 (Wilder seed).
    closes = [100.0]
    for delta in [1.0] * 7 + [-1.0] * 7:
        closes.append(closes[-1] + delta)
    snapshots = ms.compute_snapshots(make_candles(closes))
    assert snapshots[13].rsi_14 is None
    assert snapshots[14].rsi_14 == Decimal("50.0000")
    # One more +1 day: avg_gain = (0.5*13 + 1)/14 = 7.5/14, avg_loss = 6.5/14
    # -> RSI = 100 * 7.5/14 / (14/14) ... = 100 - 100/(1 + 7.5/6.5) = 53.5714
    closes.append(closes[-1] + 1.0)
    snapshots = ms.compute_snapshots(make_candles(closes))
    assert snapshots[15].rsi_14 == Decimal("53.5714")
    # All-gains series: RSI pegs at 100 (documented oscillator bounds).
    snapshots = ms.compute_snapshots(make_candles([float(i + 1) for i in range(16)]))
    assert snapshots[15].rsi_14 == Decimal("100.0000")


def test_macd_12_26_9_zero_on_constant_and_positive_on_ramp():
    # Constant closes: every EMA equals the constant -> MACD = signal = 0.
    snapshots = ms.compute_snapshots(make_candles([50.0] * 40))
    assert snapshots[39].macd == Decimal("0")
    assert snapshots[39].macd_signal == Decimal("0")
    assert snapshots[39].macd_histogram == Decimal("0")
    # Rising ramp: fast EMA above slow EMA -> MACD strictly positive.
    snapshots = ms.compute_snapshots(make_candles([float(100 + i) for i in range(40)]))
    assert snapshots[39].macd is not None and snapshots[39].macd > 0


def test_indicator_set_is_the_documented_checklist():
    # p.10 checklist: EMA5, EMA10, SMA20, RSI(14), MACD-or-TSI (p.70: MACD
    # authorized). Every term is emitted on the signal surface.
    candles = make_candles(dip_recovery_closes())
    state = ms.signal_states(candles)[-1]
    for key in ("ema5", "ema10", "sma20", "rsi14", "macd", "macd_signal", "macd_histogram"):
        assert state["indicators"][key] is not None


# ---------------------------------------------------------------------------
# Must 1 — worked-example rule fixtures (page-cited behavior)
# ---------------------------------------------------------------------------


def test_p37_crossover_gives_basic_buy_and_sell_signals():
    candles = make_candles(dip_recovery_closes())
    states = ms.signal_states(candles)
    buys = [i for i, s in enumerate(states) if s["basic_signal"] == "buy"]
    sells = [i for i, s in enumerate(states) if s["basic_signal"] == "sell"]
    assert buys and sells
    # The buy candle is exactly the EMA5-crosses-above-SMA20 candle.
    context = ms.build_signal_context(candles)
    for i in buys:
        assert mf_orig_ev1._crossed_above(context[i], context[i - 1], "ema5", "sma20")
    for i in sells:
        assert mf_orig_ev1._crossed_below(context[i], context[i - 1], "ema5", "sma20")
    # The sell cross lands inside the engineered dip (indices 60..80).
    assert any(60 <= i <= 82 for i in sells)


def test_p150_full_exit_conditions_and_hierarchy():
    candles = make_candles(dip_recovery_closes())
    states = ms.signal_states(candles)
    exits = {i: s["exit_signal"] for i, s in enumerate(states) if s["exit_signal"]}
    assert set(exits.values()) <= {"ema5_cross_below_sma20_exit", "price_close_below_sma20_exit"}
    assert exits, "the dip must trigger the documented exits"
    # Once the exit fires, the primary position machine is flat.
    first_exit = min(exits)
    assert states[first_exit]["position_state"] == "flat"


def test_p146_stage2_confirmed_entry_fires_on_recovery_crossover():
    candles = make_candles(dip_recovery_closes())
    states = ms.signal_states(candles)
    entries = [i for i, s in enumerate(states) if s["source_entry_signal"]]
    assert entries, "the recovery must produce a Stage-2 confirmed entry"
    i = entries[0]
    assert i > 80  # after the dip
    assert states[i]["stage"] == "stage_2_markup"
    assert "ema5_cross_above_sma20" in states[i]["entry_reason_codes"]
    assert states[i]["position_state"] == "long"
    # And it is EXACTLY the reused MF-ORIG entry decision (no drift).
    context = ms.build_signal_context(candles)
    engine = mf_orig_ev1._entry_signal(ms.PRIMARY_HYPOTHESIS, i, candles[i], candles, context)
    assert engine["entry_allowed"] is True


def test_p127_p140_rsi_warning_and_ignore_override():
    # Strong steady uptrend pushes RSI above 70 with an aligned 5>10>20 stack:
    # the warning fires AND the p.140 ignore-override marks it.
    closes = [100.0 * (1.02**i) for i in range(80)]
    states = ms.signal_states(make_candles(closes))
    warned = [s for s in states if s["rsi_profit_warning"]]
    assert warned, "a 2%/day uptrend must push RSI14 above 70"
    aligned = [s for s in warned if s["ma_alignment_bullish_stack"]]
    assert aligned and all(s["rsi_ignore_active"] for s in aligned)
    # rsi_ignore_active never fires without the warning + the stack.
    for s in states:
        if s["rsi_ignore_active"]:
            assert s["rsi_profit_warning"] and s["ma_alignment_bullish_stack"]


def test_p150_quarter_trim_context_requires_macd_cross_while_5_above_20():
    candles = make_candles(dip_recovery_closes())
    states = ms.signal_states(candles)
    context = ms.build_signal_context(candles)
    for i, s in enumerate(states):
        if s["trim_context_25pct"]:
            assert s["macd_sell_crossover"]
            assert context[i]["ema5"] > context[i]["sma20"]


def test_signal_surface_reuses_mf_orig_primitives():
    # The surface is the MF-ORIG reconstruction, not a lookalike.
    assert ms.PRIMARY_HYPOTHESIS in mf_orig_ev1.MF_ORIG_HYPOTHESES
    assert ms.mf_orig_ev1 is mf_orig_ev1
    # The indicator path is the production implementation through the class.
    from services.indicators.service import DefaultIndicatorService

    candles = make_candles(dip_recovery_closes(60))
    assert ms.compute_snapshots(candles) == DefaultIndicatorService._compute_snapshots(
        None, candles
    )


# ---------------------------------------------------------------------------
# Must 2 — closed-candle no-lookahead + warm-up never guessed
# ---------------------------------------------------------------------------


def test_no_lookahead_truncation_and_future_tamper():
    candles = make_candles(dip_recovery_closes())
    assert ms.verify_signal_point_in_time(candles, [55, 70, 90, 119])
    # Tampering with the FUTURE cannot change the state at t.
    states = ms.signal_states(candles)
    tampered = candles[:91] + make_candles([1.0] * 29)[0:29]
    assert ms.signal_states(tampered)[90] == states[90]


def test_warmup_is_never_guessed():
    candles = make_candles(dip_recovery_closes())
    states = ms.signal_states(candles)
    exposures = ms.exposure_series(candles)
    for i, s in enumerate(states):
        if i < 49:  # SMA50 needs 50 closes; nothing may be emitted as warmed
            assert not s["warmed_up"]
            assert s["missing_reasons"]
            assert s["position_state"] == "flat" and s["basic_position_state"] == "flat"
            assert exposures[i] is None
        if not s["warmed_up"]:
            assert s["basic_signal"] == "none" and not s["source_entry_signal"]
    assert any(s["warmed_up"] for s in states)


def test_exposure_series_matches_position_states():
    candles = make_candles(dip_recovery_closes())
    states = ms.signal_states(candles)
    for mode, key in (("source_stage2", "position_state"), ("basic_5_20", "basic_position_state")):
        exposures = ms.exposure_series(candles, entry_mode=mode)
        for s, e in zip(states, exposures, strict=True):
            if e is not None:
                assert e == (1 if s[key] == "long" else 0)
    with pytest.raises(ValueError):
        ms.exposure_series(candles, entry_mode="nope")


# ---------------------------------------------------------------------------
# Must 3 plumbing — the regime overlay (verdict intact, never a control)
# ---------------------------------------------------------------------------


def _small_universe_gate():
    from services.strategy_validation.goal_strat1 import Candle as GCandle
    from services.strategy_validation.goal_strat1 import Dataset

    datasets = []
    for symbol in ("BTC", "ETH"):
        candles = []
        level = Decimal("100")
        for i in range(120):
            level = level * (Decimal("1.01") if i < 90 else Decimal("0.97"))
            candles.append(
                GCandle(
                    symbol=symbol,
                    timeframe="1d",
                    timestamp=T0 + timedelta(days=i + 1),
                    open=level,
                    high=level * Decimal("1.001"),
                    low=level * Decimal("0.999"),
                    close=level,
                    volume=Decimal("50000000"),
                    source_path="synthetic",
                )
            )
        datasets.append(
            Dataset(
                symbol=symbol,
                timeframe="1d",
                source_path="synthetic",
                source_provenance="synthetic",
                canonical_evidence_status="synthetic",
                candles=tuple(candles),
            )
        )
    builder = strategy_types.resolve_regime_filter()
    return builder(datasets)


def test_regime_overlay_imports_through_seam_with_honest_fail_verdict():
    gate = _small_universe_gate()
    assert isinstance(gate, rg.RegimeGate)
    assert gate.disclaimer == rg.DISCLAIMER
    candles = {"BTC": make_candles(dip_recovery_closes())}
    payload = ms.latest_signal_report(candles, regime_gate=gate)
    overlay = payload["regime_overlay"]
    assert overlay["available"] is True
    assert overlay["committed_verdict"] == rg.VERDICT_FAIL
    assert "not a validated control" in overlay["committed_verdict_note"]
    assert "informational risk context" in overlay["label"]
    # The verdict travels even when the gate is unavailable.
    payload = ms.latest_signal_report(candles, regime_gate=None, regime_error="x")
    assert payload["regime_overlay"]["committed_verdict"] == rg.VERDICT_FAIL


def test_regime_gated_provider_ands_and_propagates_warmup():
    base = {("BTC", 0): 1, ("BTC", 1): 1, ("BTC", 2): 0, ("BTC", 3): None}
    gatep = {("BTC", 0): 1, ("BTC", 1): 0, ("BTC", 2): 1, ("BTC", 3): 1}
    provider = ms.regime_gated_provider(
        lambda s, i: base[(s, i)], lambda s, i: gatep[(s, i)]
    )
    assert provider("BTC", 0) == 1  # long AND risk_on
    assert provider("BTC", 1) == 0  # suppressed by risk_off
    assert provider("BTC", 2) == 0  # flat stays flat
    assert provider("BTC", 3) is None  # warm-up never guessed


# ---------------------------------------------------------------------------
# Must 4 — honest framing on every surface
# ---------------------------------------------------------------------------


def test_disclaimer_carries_every_required_clause():
    for phrase in (
        "faithful implementation",
        "characterized honestly",
        "no standalone edge",
        "informational risk context",
        "not a validated control",
        "not an order",
        "predicts or guarantees profit",
    ):
        assert phrase in ms.DISCLAIMER, phrase


def test_disclaimer_and_boundaries_on_every_surface():
    candles = make_candles(dip_recovery_closes())
    for state in ms.signal_states(candles):
        assert state["disclaimer"] == ms.DISCLAIMER
    payload = ms.latest_signal_report({"BTC": candles}, regime_gate=None, regime_error="x")
    assert payload["disclaimer"] == ms.DISCLAIMER
    flags = payload["boundaries"]
    assert flags["signal_only"] is True
    assert flags["submits_orders"] is False
    assert flags["is_alpha_claim"] is False
    assert flags["regime_overlay_is_validated_control"] is False
    assert flags["regime_overlay_is_informational_risk_context"] is True


def test_source_citations_and_ambiguities_are_pinned():
    by_id = {c["rule_id"]: c for c in ms.SOURCE_CITATIONS}
    assert by_id["foundation_5_20_crossover"]["printed_page"] == "37"
    assert "basic buy and sell signals" in by_id["foundation_5_20_crossover"]["quote"]
    assert by_id["full_exit_rule"]["printed_page"] == "150, 152"
    assert by_id["position_sizing_1pct_risk"]["printed_page"] == "125"
    assert ms.SOURCE_DOCUMENT["direct_pdf_available_to_agent"] is True
    ambiguity_ids = {a["ambiguity_id"] for a in ms.AMBIGUITY_RESOLUTIONS}
    assert "trim_trigger_conjunction" in ambiguity_ids
    assert "stage_classification_is_narrative" in ambiguity_ids
    # The PDF pin matches the actual file when it is present in the checkout.
    provenance = ms.pdf_provenance_check(REPO_ROOT)
    if provenance["present"]:
        assert provenance["sha256_matches_pin"] is True


def test_committed_summary_records_the_honest_characterization():
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    assert summary["phase"] == "MONEYFLOW-SIGNAL1"
    label = summary["standalone_characterization"]["label"]
    assert label == "defensive_trend_mechanic_not_validated_alpha"
    screens = summary["standalone_characterization"]["screens"]
    assert screens["stage1_raw"]["re_audit_rule_fired"] is True
    assert (
        screens["stage2_re_audit"]["mf_beats_always_long_return_in_bull_third"] is False
    )
    overlay = summary["regime_overlay_characterization"]
    assert overlay["committed_verdict"] == rg.VERDICT_FAIL
    assert overlay["mf_source_stage2"]["label"] == "informational_overlay_not_validated_control"
    assert summary["boundaries"]["is_alpha_claim"] is False
    assert summary["disclaimer"] == ms.DISCLAIMER
    assert any(
        c["rule_id"] == "foundation_5_20_crossover" for c in summary["source_citations"]
    )
    assert summary["pdf_provenance"]["sha256_matches_pin"] is True


def test_committed_outputs_have_no_forbidden_language():
    import re

    md_path = REPO_ROOT / "docs" / "moneyflow_signal1_source_faithful_signal_surface_evidence.md"
    for path in (SUMMARY_PATH, md_path):
        lowered = path.read_text(encoding="utf-8").lower()
        for phrase in mf_orig_ev1.FORBIDDEN_REPORT_PHRASES:
            assert not re.search(rf"\b{re.escape(phrase)}\b", lowered), (path, phrase)


# ---------------------------------------------------------------------------
# Must 5 — the CLI emits the auditable signal (offline path)
# ---------------------------------------------------------------------------


def test_cli_offline_emits_auditable_json(tmp_path):
    module_path = REPO_ROOT / "scripts" / "run_moneyflow_signal.py"
    spec = importlib.util.spec_from_file_location("run_moneyflow_signal_test", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    fixture = {
        asset: make_rows(dip_recovery_closes(150))
        for asset in ("AVAX", "BNB", "BTC", "DOGE", "ETH", "SOL", "XRP")
    }
    input_path = tmp_path / "candles.json"
    input_path.write_text(json.dumps(fixture), encoding="utf-8")
    output_path = tmp_path / "signal.json"
    assert module.main(["--input-json", str(input_path), "--output", str(output_path)]) == 0

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["phase"] == "MONEYFLOW-SIGNAL1"
    assert payload["source"] == "offline_input_json_replay"
    assert payload["disclaimer"] == ms.DISCLAIMER
    assert payload["boundaries"]["submits_orders"] is False
    assert payload["regime_overlay"]["committed_verdict"] == rg.VERDICT_FAIL
    for block in payload["assets"].values():
        state = block["latest_state"]
        assert state["disclaimer"] == ms.DISCLAIMER
        assert block["point_in_time_verified"] is True
        # Auditable: every intermediate indicator term is present.
        for key in ("ema5", "ema10", "sma20", "rsi14", "macd", "macd_signal"):
            assert key in state["indicators"]
        assert len(block["recent_states"]) == 5
