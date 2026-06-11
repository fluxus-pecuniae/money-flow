"""TREND-OVERLAY1 — deterministic, offline tests (no network, no DB).

Asserts the tool's documented guarantees:
  - the defaults are PINNED to the TSMOM-EV1 train-chosen config from the
    committed evidence summary (changing them = silent re-tune = CI fail);
  - trend sign is computed by the reused TSMOM-EV1 machinery (uptrend ->
    hold, downtrend -> flat, exact-zero drift -> flat);
  - vol targeting equalizes per-asset risk contribution and the caps apply;
  - closed-candle-only / no-lookahead: in-progress and future candles are
    excluded and cannot change the output;
  - a downtrend (or a vol spike) reduces target exposure — the
    drawdown-control action;
  - the honest disclaimer + signal-only boundaries are present in EVERY
    output surface (JSON and rendered table);
  - the offline CLI path works end-to-end without network.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from services.strategy_validation import trend_overlay1 as overlay

REPO_ROOT = Path(__file__).resolve().parents[1]
TSMOM_SUMMARY = REPO_ROOT / "docs" / "tsmom_ev1_vol_targeted_momentum_evidence_summary.json"
T0 = datetime(2026, 1, 1, tzinfo=UTC)
AS_OF = T0 + timedelta(days=80)


def make_candles(closes: list[float]) -> list[dict]:
    rows = []
    for i, close in enumerate(closes):
        open_time = T0 + timedelta(days=i)
        rows.append(
            {
                "open_time": open_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "close_time": (open_time + timedelta(days=1)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "open": str(close),
                "high": str(close * 1.01),
                "low": str(close * 0.99),
                "close": str(close),
                "volume": "1000000",
            }
        )
    return rows


def trending(up: bool, n: int = 75, daily: float = 0.004, base: float = 100.0):
    step = 1 + daily if up else 1 - daily
    return make_candles([base * (step**i) for i in range(n)])


def choppy_zero_drift(n: int = 75, base: float = 100.0):
    # Exactly repeating every 2 days -> trailing 30d return is exactly zero.
    return make_candles([base if i % 2 == 0 else base * 1.01 for i in range(n)])


# ---------------------------------------------------------------------------
# Defaults pinned to the validated TSMOM-EV1 choice (no silent re-tune)
# ---------------------------------------------------------------------------


def test_defaults_are_pinned_to_tsmom_ev1_train_chosen_config() -> None:
    summary = json.loads(TSMOM_SUMMARY.read_text(encoding="utf-8"))
    chosen = summary["train_only_choice"]["chosen_config"]
    assert chosen == overlay.VALIDATED_CONFIG_ID == "tsmom_ev1_lb30_vt20_long_only_1d"
    # lb30 / vt 0.20 / long_only, straight from the config id the evidence chose.
    assert overlay.DEFAULT_LOOKBACK_DAYS == 30
    assert overlay.DEFAULT_PORTFOLIO_VOL_TARGET == Decimal("0.20")
    assert overlay.DEFAULT_MODE == "long_only"
    assert "0.20" in summary["design"]["portfolio_vol_targets_annualized"]
    assert overlay.LIQUID_UNIVERSE == tuple(summary["universe"]["liquid_subset"])
    result = overlay.compute_overlay({"BTC": trending(True)}, as_of=AS_OF)
    assert result["config"]["config_id"] == chosen
    assert result["config"]["not_retuned"] is True


# ---------------------------------------------------------------------------
# Trend states + drawdown-control action
# ---------------------------------------------------------------------------


def test_uptrend_holds_downtrend_flattens_zero_drift_flat() -> None:
    result = overlay.compute_overlay(
        {"UP": trending(True), "DOWN": trending(False), "CHOP": choppy_zero_drift()},
        as_of=AS_OF,
    )
    rows = {r["symbol"]: r for r in result["per_asset"]}
    assert rows["UP"]["trend_state"] == overlay.STATE_HOLD
    assert Decimal(rows["UP"]["target_weight"]) > 0
    assert rows["DOWN"]["trend_state"] == overlay.STATE_FLAT_DOWNTREND
    assert Decimal(rows["DOWN"]["target_weight"]) == 0
    assert rows["CHOP"]["trend_state"] == overlay.STATE_FLAT_NO_DRIFT
    assert Decimal(rows["CHOP"]["target_weight"]) == 0
    assert result["portfolio"]["assets_held"] == 1
    assert result["portfolio"]["assets_flat"] == 2


def test_downtrend_universe_goes_fully_flat_and_uptrend_does_not() -> None:
    down = overlay.compute_overlay(
        {"A": trending(False), "B": trending(False)}, as_of=AS_OF
    )
    up = overlay.compute_overlay(
        {"A": trending(True), "B": trending(True)}, as_of=AS_OF
    )
    assert Decimal(down["portfolio"]["gross_target_weight"]) == 0
    assert Decimal(down["portfolio"]["gross_target_exposure_usdc"]) == 0
    assert Decimal(up["portfolio"]["gross_target_weight"]) > 0


def test_vol_targeting_equalizes_risk_and_vol_spike_reduces_exposure() -> None:
    calm = trending(True, daily=0.004)
    # Same drift, wilder path: alternate strong up/down days around the trend.
    wild_closes = []
    base = 100.0
    for i in range(75):
        base *= 1.004
        wild_closes.append(base * (1.06 if i % 2 == 0 else 0.95))
    wild = make_candles(wild_closes)
    result = overlay.compute_overlay({"CALM": calm, "WILD": wild}, as_of=AS_OF)
    rows = {r["symbol"]: r for r in result["per_asset"]}
    w_calm = Decimal(rows["CALM"]["target_weight"])
    w_wild = Decimal(rows["WILD"]["target_weight"])
    v_calm = Decimal(rows["CALM"]["realized_vol_annual"])
    v_wild = Decimal(rows["WILD"]["realized_vol_annual"])
    assert v_wild > v_calm
    assert w_wild < w_calm  # the vol spike REDUCES exposure (the overlay action)
    # Equal risk contribution while uncapped: weight x vol matches budget.
    budget = overlay.DEFAULT_PORTFOLIO_VOL_TARGET / 2
    if w_calm < overlay.tsmom.MAX_SINGLE_ASSET_WEIGHT:
        assert abs(w_calm * v_calm - budget) < Decimal("0.002")
    if w_wild < overlay.tsmom.MAX_SINGLE_ASSET_WEIGHT:
        assert abs(w_wild * v_wild - budget) < Decimal("0.002")


def test_weight_and_gross_caps_apply() -> None:
    # One nearly-flat-vol uptrend asset would demand a huge weight -> capped.
    quiet_closes = [100.0 * (1.0005**i) for i in range(75)]
    result = overlay.compute_overlay(
        {"QUIET": make_candles(quiet_closes)}, as_of=AS_OF
    )
    row = result["per_asset"][0]
    assert Decimal(row["target_weight"]) == overlay.tsmom.MAX_SINGLE_ASSET_WEIGHT
    assert Decimal(result["portfolio"]["gross_target_weight"]) <= Decimal(
        str(overlay.tsmom.MAX_GROSS_LEVERAGE)
    )


# ---------------------------------------------------------------------------
# Closed-candle-only / no-lookahead
# ---------------------------------------------------------------------------


def test_in_progress_and_future_candles_are_excluded_and_change_nothing() -> None:
    candles = trending(True)
    base = overlay.compute_overlay({"BTC": candles}, as_of=AS_OF)
    # Append an in-progress candle (closes after as_of) and an absurd future
    # candle: both must be dropped and the output must not move.
    in_progress = dict(candles[-1])
    in_progress["open_time"] = AS_OF.strftime("%Y-%m-%dT%H:%M:%SZ")
    in_progress["close_time"] = (AS_OF + timedelta(hours=6)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    in_progress["close"] = "1.0"  # would flip the trend if leaked
    future = dict(in_progress)
    future["close_time"] = (AS_OF + timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%SZ")
    tampered = overlay.compute_overlay(
        {"BTC": candles + [in_progress, future]}, as_of=AS_OF
    )

    def signal_fields(rows):
        return [
            {k: v for k, v in row.items() if k != "dropped_not_closed"}
            for row in rows
        ]

    assert signal_fields(tampered["per_asset"]) == signal_fields(base["per_asset"])
    assert tampered["portfolio"] == base["portfolio"]
    assert tampered["dropped_not_closed_total"] == 2
    assert tampered["data_as_of_utc"] == base["data_as_of_utc"]


def test_insufficient_history_is_flat_and_labeled() -> None:
    result = overlay.compute_overlay({"NEW": trending(True, n=20)}, as_of=AS_OF)
    row = result["per_asset"][0]
    assert row["trend_state"] == overlay.STATE_INSUFFICIENT
    assert Decimal(row["target_weight"]) == 0


# ---------------------------------------------------------------------------
# Honest framing on every surface
# ---------------------------------------------------------------------------


def test_disclaimer_and_signal_only_boundaries_in_every_output() -> None:
    result = overlay.compute_overlay({"BTC": trending(True)}, as_of=AS_OF)
    assert result["disclaimer"] == overlay.DISCLAIMER
    for required in (
        "DRAWDOWN-CONTROL OVERLAY, NOT ALPHA",
        "does not aim to make money",
        "SIGNAL ONLY",
        "no production approval",
    ):
        assert required in result["disclaimer"]
    table = overlay.render_table(result)
    assert "DRAWDOWN-CONTROL OVERLAY, NOT ALPHA" in table
    b = result["boundaries"]
    assert b["signal_only_not_an_order"] is True
    assert b["drawdown_control_not_alpha"] is True
    assert b["auto_execution"] is False
    assert b["submits_live_orders"] is False
    assert b["calls_private_signed_or_order_endpoints"] is False
    assert b["approves_live_trading"] is False
    assert b["signal_retuned"] is False


# ---------------------------------------------------------------------------
# Offline CLI path (no network)
# ---------------------------------------------------------------------------


def test_cli_offline_replay_writes_output_with_disclaimer(tmp_path) -> None:
    payload = {
        "candles_by_symbol": {
            "BTC": trending(True),
            "ETH": trending(False),
        }
    }
    input_path = tmp_path / "candles.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    output_path = tmp_path / "current_trend_overlay.json"

    spec = importlib.util.spec_from_file_location(
        "trend_overlay_cli_test", REPO_ROOT / "scripts" / "run_trend_overlay.py"
    )
    cli = importlib.util.module_from_spec(spec)
    sys.modules["trend_overlay_cli_test"] = cli
    spec.loader.exec_module(cli)
    rc = cli.main(
        [
            "--input-json", str(input_path),
            "--output", str(output_path),
            "--as-of", AS_OF.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "--account-size", "25000",
        ]
    )
    assert rc == 0
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["disclaimer"] == overlay.DISCLAIMER
    assert written["data_source"].startswith("offline_replay:")
    assert written["account_size_usdc"] == "25000"
    rows = {r["symbol"]: r for r in written["per_asset"]}
    assert rows["BTC"]["trend_state"] == overlay.STATE_HOLD
    assert rows["ETH"]["trend_state"] == overlay.STATE_FLAT_DOWNTREND
