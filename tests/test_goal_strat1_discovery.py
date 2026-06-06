from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "services" / "strategy_validation" / "goal_strat1.py"
    spec = importlib.util.spec_from_file_location("goal_strat1_test_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load GOAL-STRAT1 module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


goal_strat1 = _load_module()


def _write_replay(tmp_path: Path, *, symbol: str = "BTC", timeframe: str = "1h", rows: int = 320) -> Path:
    selected = tmp_path / "reports" / "strategy_validation" / "sv2_0_2_dashboard_chart_data" / "20260101T000000Z" / "selected"
    selected.mkdir(parents=True)
    path = selected / f"{symbol}_{timeframe}_money_flow_v1_2_canonical_next_candle_open_replay.json"
    start = datetime(2025, 1, 1, tzinfo=UTC)
    step = {"15m": timedelta(minutes=15), "1h": timedelta(hours=1), "4h": timedelta(hours=4), "1d": timedelta(days=1)}[timeframe]
    candles: list[dict[str, str]] = []
    for idx in range(rows):
        base = Decimal("100") + (Decimal(idx) / Decimal("20"))
        close = base + (Decimal(idx % 9) / Decimal("10"))
        open_ = close - Decimal("0.25")
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
) -> object:
    return goal_strat1.Metrics(
        starting_equity=goal_strat1.STARTING_EQUITY,
        ending_equity=goal_strat1.STARTING_EQUITY + net_pnl,
        net_pnl=net_pnl,
        max_drawdown=goal_strat1.STARTING_EQUITY * max_drawdown_pct,
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


def _trade(symbol: str, timeframe: str, idx: int, pnl: Decimal = Decimal("10")) -> object:
    entry = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(hours=idx)
    return goal_strat1.Trade(
        strategy_id="candidate",
        symbol=symbol,
        timeframe=timeframe,
        entry_time=entry,
        exit_time=entry + timedelta(hours=1),
        entry_price=Decimal("100"),
        exit_price=Decimal("101"),
        quantity=Decimal("1"),
        gross_pnl=pnl,
        fees=Decimal("0.1"),
        slippage=Decimal("0.1"),
        net_pnl=pnl,
        equity_after=goal_strat1.STARTING_EQUITY + Decimal(idx),
        entry_reason="entry",
        exit_reason="exit",
    )


def _config() -> object:
    return goal_strat1.StrategyConfig(
        strategy_id="candidate",
        display_name="Candidate",
        family="trend_breakout",
        entry_model="donchian_breakout",
        exit_model="atr_trail",
        risk_model="equity_10pct",
        regime_filter="sma200",
        timeframe_scope=("1h",),
    )


def test_goal_strat1_data_inventory_generation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    replay = _write_replay(tmp_path, symbol="ETH", timeframe="1h")

    datasets = goal_strat1.load_replay_datasets((str(replay.relative_to(tmp_path)),))
    inventory = goal_strat1.build_data_inventory(datasets)

    assert len(datasets) == 1
    assert inventory[0].symbol == "ETH"
    assert inventory[0].timeframe == "1h"
    assert inventory[0].candle_count == 320
    assert inventory[0].data_quality_status == "accepted"
    assert inventory[0].source_provenance == "sv2_0_2_canonical_selected_replay"


def test_goal_strat1_candidate_gate_pass_and_fail_modes() -> None:
    trades = [_trade(["BTC", "ETH", "SOL"][idx % 3], "1h", idx) for idx in range(60)]
    passed = goal_strat1.evaluate_candidate_gate(
        config=_config(),
        metrics=_metrics(),
        active_metrics=_metrics(),
        chronological_oos=_metrics(net_pnl=Decimal("200")),
        anchored_oos=_metrics(net_pnl=Decimal("150")),
        trades=trades,
        symbol_concentration={"BTC": "0.34", "ETH": "0.33", "SOL": "0.33"},
        period_concentration={"2025-H1": "0.50", "2025-H2": "0.50"},
    )
    failed = goal_strat1.evaluate_candidate_gate(
        config=_config(),
        metrics=_metrics(trade_count=10, profit_factor=Decimal("1.01"), max_drawdown_pct=Decimal("0.40")),
        active_metrics=_metrics(trade_count=10, profit_factor=Decimal("1.01"), max_drawdown_pct=Decimal("0.40")),
        chronological_oos=_metrics(net_pnl=Decimal("-1")),
        anchored_oos=_metrics(net_pnl=Decimal("-1")),
        trades=[_trade("BTC", "1h", idx) for idx in range(10)],
        symbol_concentration={"BTC": "1.0"},
        period_concentration={"2025-H1": "1.0"},
    )

    assert passed["status"] == goal_strat1.CANDIDATE_STATUS
    assert passed["passed"] is True
    assert "rejected_low_sample" in failed["reason_codes"]
    assert "profit_factor_below_threshold" in failed["reason_codes"]
    assert "rejected_drawdown" in failed["reason_codes"]
    assert "chronological_oos_net_pnl_negative" in failed["reason_codes"]
    assert "anchored_walk_forward_oos_net_pnl_negative" in failed["reason_codes"]


def test_goal_strat1_metrics_drawdown_profit_factor_and_concentration() -> None:
    trades = [
        _trade("BTC", "1h", 1, Decimal("100")),
        _trade("ETH", "1h", 2, Decimal("-50")),
        _trade("SOL", "1h", 3, Decimal("75")),
        _trade("BTC", "1h", 4, Decimal("-25")),
    ]
    metrics = goal_strat1._metrics(trades)
    concentration = goal_strat1._concentration_by(trades, lambda trade: trade.symbol)

    assert metrics.net_pnl == Decimal("100.00000000")
    assert metrics.profit_factor == Decimal("2.33333333")
    assert metrics.max_drawdown == Decimal("50.00000000")
    assert concentration["BTC"] == "0.57142857"


def test_goal_strat1_report_outputs_and_failure_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    replay = _write_replay(tmp_path, symbol="BTC", timeframe="1h")
    docs = tmp_path / "docs"
    docs.mkdir()

    report = goal_strat1.build_goal_strat1_report(
        selected_replay_globs=(str(replay.relative_to(tmp_path)),),
        max_total_candidate_runs=4,
    )
    goal_strat1.write_goal_strat1_outputs(
        report,
        docs / "goal_strat1_strategy_discovery.md",
        docs / "goal_strat1_strategy_discovery_summary.json",
    )

    assert (docs / "goal_strat1_strategy_discovery.md").exists()
    assert (docs / "goal_strat1_strategy_discovery_summary.json").exists()
    assert (docs / "goal_strat1_no_three_candidates_found.md").exists()
    summary = json.loads((docs / "goal_strat1_strategy_discovery_summary.json").read_text())
    assert "data_inventory" in summary
    assert "candidate_runs" in summary
    assert summary["search_budget_used"]["candidate_runs"] == 4


def test_goal_strat1_boundaries_and_static_no_order_paths() -> None:
    flags = goal_strat1.boundary_flags()
    assert flags["research_only"] is True
    assert flags["mutates_active_pt_rt_runtime"] is False
    assert flags["mutates_runtime_artifacts"] is False
    assert flags["creates_order_intent"] is False
    assert flags["creates_prepared_venue_order"] is False
    assert flags["creates_submitted_order"] is False
    assert flags["submits_live_orders"] is False
    assert flags["submits_testnet_orders"] is False
    assert flags["calls_private_signed_or_order_endpoints"] is False

    source = Path("services/strategy_validation/goal_strat1.py").read_text()
    forbidden_fragments = [
        "from services.exchange",
        "import services.exchange",
        "from services.execution",
        "import services.execution",
        "from services.routing",
        "import services.routing",
        "OrderIntent(",
        "PreparedVenueOrder(",
        "SubmittedOrder(",
        "clearinghouseState",
        "openOrders",
        "orderStatus",
        "api.hyperliquid",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_goal_strat1_policy_has_oos_and_no_approval_labels() -> None:
    policy = goal_strat1.candidate_gate_policy()
    assert policy["lookahead_allowed"] is False
    assert policy["same_candle_optimistic_fill_allowed"] is False
    assert policy["chronological_70_30_oos_net_pnl_nonnegative"] is True
    assert policy["anchored_walk_forward_thirds_oos_net_pnl_nonnegative"] is True
    assert policy["production_or_live_approval"] is False

    for config in goal_strat1.generate_strategy_configs():
        for banned in goal_strat1.FORBIDDEN_STATUS_WORDS:
            assert banned not in config.strategy_id
