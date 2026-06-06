from __future__ import annotations

import json
import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path


def _load_strat_disc1_module():
    module_path = Path(__file__).resolve().parents[1] / "services" / "strategy_validation" / "strat_disc1.py"
    spec = importlib.util.spec_from_file_location("strat_disc1_test_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load STRAT-DISC1 module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


strat_disc1 = _load_strat_disc1_module()
STARTING_EQUITY = strat_disc1.STARTING_EQUITY
STRAT_DISC1_STATUS_CANDIDATE = strat_disc1.STRAT_DISC1_STATUS_CANDIDATE
Metrics = strat_disc1.Metrics
SimulatedTrade = strat_disc1.SimulatedTrade
StrategyHypothesis = strat_disc1.StrategyHypothesis
boundary_flags = strat_disc1.boundary_flags
build_data_inventory = strat_disc1.build_data_inventory
build_strat_disc1_report = strat_disc1.build_strat_disc1_report
candidate_gate_policy = strat_disc1.candidate_gate_policy
evaluate_candidate_gate = strat_disc1.evaluate_candidate_gate
load_replay_datasets = strat_disc1.load_replay_datasets
write_strat_disc1_outputs = strat_disc1.write_strat_disc1_outputs


def _write_replay(tmp_path: Path, *, symbol: str = "BTC", timeframe: str = "1h", rows: int = 140) -> Path:
    selected = tmp_path / "reports" / "strategy_validation" / "sv2_0_2_dashboard_chart_data" / "20260101T000000Z" / "selected"
    selected.mkdir(parents=True)
    path = selected / f"{symbol}_{timeframe}_money_flow_v1_2_canonical_next_candle_open_replay.json"
    start = datetime(2026, 1, 1, tzinfo=UTC)
    step = {"15m": timedelta(minutes=15), "1h": timedelta(hours=1), "4h": timedelta(hours=4), "1d": timedelta(days=1)}[timeframe]
    price = Decimal("100")
    candles: list[dict[str, str]] = []
    for idx in range(rows):
        wave = Decimal(idx % 11) / Decimal("100")
        drift = Decimal(idx) / Decimal("80")
        close = price + drift + wave
        open_ = close - Decimal("0.35")
        candles.append(
            {
                "timestamp_utc": (start + (step * idx)).isoformat().replace("+00:00", "Z"),
                "open": str(open_),
                "high": str(close + Decimal("0.8")),
                "low": str(open_ - Decimal("0.7")),
                "close": str(close),
                "volume": "1000",
            }
        )
    payload = {
        "symbol": symbol,
        "timeframe": timeframe,
        "replays": [
            {
                "strategy_id": "money_flow_v1_2_canonical",
                "fill_assumption": "next_candle_open",
                "symbol": symbol,
                "timeframe": timeframe,
                "candles": candles,
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _metrics(
    *,
    trade_count: int = 60,
    net_pnl: Decimal = Decimal("1000"),
    profit_factor: Decimal | None = Decimal("1.60"),
    max_drawdown_pct: Decimal = Decimal("0.08"),
    largest_loss: Decimal | None = Decimal("-120"),
) -> Metrics:
    return Metrics(
        starting_equity=STARTING_EQUITY,
        ending_equity=STARTING_EQUITY + net_pnl,
        net_pnl=net_pnl,
        max_drawdown=STARTING_EQUITY * max_drawdown_pct,
        max_drawdown_pct=max_drawdown_pct,
        trade_count=trade_count,
        winning_trades=max(1, trade_count // 2),
        losing_trades=max(1, trade_count // 3),
        win_rate=Decimal("0.55"),
        profit_factor=profit_factor,
        largest_win=Decimal("250"),
        largest_loss=largest_loss,
        average_win=Decimal("75"),
        average_loss=Decimal("-45"),
        max_consecutive_losses=3,
        worst_losing_streak_pnl=Decimal("-150"),
    )


def _trade(symbol: str, timeframe: str, index: int) -> SimulatedTrade:
    entry = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(hours=index)
    return SimulatedTrade(
        strategy_id="candidate",
        symbol=symbol,
        timeframe=timeframe,
        entry_time=entry,
        exit_time=entry + timedelta(hours=1),
        entry_price=Decimal("100"),
        exit_price=Decimal("101"),
        quantity=Decimal("1"),
        gross_pnl=Decimal("1"),
        fees=Decimal("0.1"),
        slippage=Decimal("0.1"),
        net_pnl=Decimal("0.8"),
        equity_after=STARTING_EQUITY + Decimal(index),
        entry_reason="test",
        exit_reason="test_exit",
    )


def test_data_inventory_generation_accepts_valid_public_replay(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    replay = _write_replay(tmp_path, symbol="ETH", timeframe="1h")

    datasets = load_replay_datasets((str(replay.relative_to(tmp_path)),))
    inventory = build_data_inventory(datasets)

    assert len(datasets) == 1
    assert inventory[0].symbol == "ETH"
    assert inventory[0].timeframe == "1h"
    assert inventory[0].candle_count == 140
    assert inventory[0].data_quality_status == "accepted"
    assert inventory[0].source_provenance == "sv2_0_2_canonical_selected_replay"


def test_candidate_gate_promotes_only_when_all_thresholds_pass() -> None:
    hypothesis = StrategyHypothesis("good_candidate", "Good Candidate", "trend_following", "test")
    trades = [_trade(["BTC", "ETH", "SOL"][idx % 3], "1h", idx) for idx in range(60)]
    result = evaluate_candidate_gate(
        hypothesis=hypothesis,
        metrics=_metrics(),
        active_metrics=_metrics(),
        out_sample_metrics=_metrics(net_pnl=Decimal("200")),
        trades=trades,
        symbol_concentration={"BTC": "0.34", "ETH": "0.33", "SOL": "0.33"},
        timeframe_concentration={"1h": "1.0"},
        period_concentration={"2026-H1": "0.50", "2026-H2": "0.50"},
    )

    assert result["status"] == STRAT_DISC1_STATUS_CANDIDATE
    assert result["passed"] is True


def test_candidate_gate_rejects_low_sample_profit_factor_drawdown_and_concentration() -> None:
    hypothesis = StrategyHypothesis("weak_candidate", "Weak Candidate", "trend_following", "test")
    trades = [_trade("BTC", "1h", idx) for idx in range(10)]
    low_sample = evaluate_candidate_gate(
        hypothesis=hypothesis,
        metrics=_metrics(trade_count=10),
        active_metrics=_metrics(trade_count=10),
        out_sample_metrics=_metrics(net_pnl=Decimal("1")),
        trades=trades,
        symbol_concentration={"BTC": "1.0"},
        timeframe_concentration={"1h": "1.0"},
        period_concentration={"2026-H1": "1.0"},
    )
    weak_pf = evaluate_candidate_gate(
        hypothesis=hypothesis,
        metrics=_metrics(profit_factor=Decimal("1.01")),
        active_metrics=_metrics(profit_factor=Decimal("1.01")),
        out_sample_metrics=_metrics(net_pnl=Decimal("1")),
        trades=[_trade(["BTC", "ETH", "SOL"][idx % 3], "1h", idx) for idx in range(60)],
        symbol_concentration={"BTC": "0.34", "ETH": "0.33", "SOL": "0.33"},
        timeframe_concentration={"1h": "1.0"},
        period_concentration={"2026-H1": "0.50", "2026-H2": "0.50"},
    )
    high_drawdown = evaluate_candidate_gate(
        hypothesis=hypothesis,
        metrics=_metrics(max_drawdown_pct=Decimal("0.40")),
        active_metrics=_metrics(max_drawdown_pct=Decimal("0.40")),
        out_sample_metrics=_metrics(net_pnl=Decimal("1")),
        trades=[_trade(["BTC", "ETH", "SOL"][idx % 3], "1h", idx) for idx in range(60)],
        symbol_concentration={"BTC": "0.34", "ETH": "0.33", "SOL": "0.33"},
        timeframe_concentration={"1h": "1.0"},
        period_concentration={"2026-H1": "0.50", "2026-H2": "0.50"},
    )

    assert low_sample["status"] == "rejected_low_sample"
    assert "profit_factor_below_threshold" in weak_pf["reason_codes"]
    assert high_drawdown["status"] == "rejected_drawdown"


def test_strat_disc1_boundaries_do_not_touch_runtime_or_order_paths() -> None:
    flags = boundary_flags()
    assert flags["research_only"] is True
    assert flags["mutates_active_pt_rt_runtime"] is False
    assert flags["creates_order_intent"] is False
    assert flags["creates_prepared_venue_order"] is False
    assert flags["creates_submitted_order"] is False
    assert flags["submits_live_orders"] is False
    assert flags["submits_testnet_orders"] is False
    assert flags["calls_private_signed_or_order_endpoints"] is False

    source = Path("services/strategy_validation/strat_disc1.py").read_text()
    forbidden_fragments = [
        "services.exchange",
        "services.execution",
        "services.routing",
        "OrderIntent",
        "PreparedVenueOrder",
        "SubmittedOrder",
        "clearinghouseState",
        "openOrders",
        "orderStatus",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_lookahead_oos_and_no_approval_policy_are_explicit(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    replay = _write_replay(tmp_path, symbol="BTC", timeframe="1h")
    report = build_strat_disc1_report(selected_replay_globs=(str(replay.relative_to(tmp_path)),), max_total_candidate_runs=3)

    assert candidate_gate_policy()["lookahead_allowed"] is False
    assert candidate_gate_policy()["same_candle_optimistic_fill_allowed"] is False
    assert report["boundary_flags"]["approves_live_trading"] is False
    assert report["boundary_flags"]["approves_production_strategy"] is False
    for run in report["candidate_runs"]:
        assert run["oos_slice_results"]["split_time"].endswith("Z")
        assert run["status"] not in {"production_ready", "live_ready", "guaranteed_profitable"}


def test_summary_and_candidate_artifacts_are_written(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    replay = _write_replay(tmp_path, symbol="BTC", timeframe="1h")
    report = build_strat_disc1_report(selected_replay_globs=(str(replay.relative_to(tmp_path)),), max_total_candidate_runs=2)

    write_strat_disc1_outputs(
        report,
        docs / "strat_disc1_autonomous_strategy_discovery.md",
        docs / "strat_disc1_autonomous_strategy_discovery_summary.json",
    )

    assert (docs / "strat_disc1_autonomous_strategy_discovery.md").exists()
    assert (docs / "strat_disc1_autonomous_strategy_discovery_summary.json").exists()
    summary = json.loads((docs / "strat_disc1_autonomous_strategy_discovery_summary.json").read_text())
    assert "data_inventory" in summary
    assert "candidate_runs" in summary
    assert "top_3_candidates" in summary
    for index, candidate in enumerate(summary["top_3_candidates"][:3], start=1):
        assert (docs / f"strat_disc1_candidate_{index}_{candidate['strategy_id']}.md").exists()


def test_repo_strat_disc1_report_files_exist_after_generation() -> None:
    assert Path("docs/strat_disc1_autonomous_strategy_discovery.md").exists()
    assert Path("docs/strat_disc1_autonomous_strategy_discovery_summary.json").exists()
