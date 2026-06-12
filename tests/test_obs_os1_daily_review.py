from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path


MODULE_PATH = Path("scripts/build_pt_rt_week2_daily_review.py")
SPEC = importlib.util.spec_from_file_location("build_pt_rt_week2_daily_review", MODULE_PATH)
assert SPEC and SPEC.loader
obs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(obs)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def runtime_dir(root: Path, scope: str = "pt_rt2_mf_signal_observation") -> Path:
    return root / "reports" / "paper_runtime" / scope


def base_summary() -> dict:
    return {
        "status": "pt_rt2_fresh_slate_cycle_verified",
        "active_review_scope": "pt_rt2_mf_signal_observation",
        "connection_status": {"last_update_utc": "2026-06-08T11:59:00Z"},
        "active_strategy_lanes": [
            {
                "lane_id": "mf_source_faithful_baseline",
                "realized_equity": "10020",
                "unrealized_pnl": "5",
                "open_positions": 1,
                "closed_trades": 1,
                "testnet_eligible": False,
                "production_approved": False,
                "live_approved": False,
            },
            {
                "lane_id": "mf_source_faithful_regime_gated",
                "realized_equity": "9990",
                "unrealized_pnl": "-12",
                "open_positions": 1,
                "closed_trades": 0,
                "testnet_eligible": False,
                "production_approved": False,
                "live_approved": False,
            },
        ],
    }


def test_obs_os1_generates_daily_review_and_outputs(tmp_path: Path) -> None:
    scope_dir = runtime_dir(tmp_path)
    write_json(scope_dir / "summary.json", base_summary())
    write_json(scope_dir / "state.json", {"paper_runtime": {"open_positions_by_key": {}}})
    write_json(scope_dir / "data_health.json", {"status": "healthy"})
    write_jsonl(scope_dir / "runtime_audit.jsonl", [{"timestamp": "2026-06-08T11:50:00Z", "status": "heartbeat"}])
    write_jsonl(
        scope_dir / "decisions.jsonl",
        [
            {
                "decision_time": "2026-06-08T11:00:00Z",
                "action": "paper_opened",
                "lane_id": "mf_source_faithful_baseline",
                "symbol": "ETH",
                "timeframe": "1d",
                "reason_codes": ["fresh_entry_signal_after_runtime_start"],
            }
        ],
    )
    write_jsonl(
        scope_dir / "trades.jsonl",
        [{"exit_time": "2026-06-08T11:30:00Z", "lane_id": "mf_source_faithful_baseline", "symbol": "ETH", "net_pnl": "20"}],
    )
    # PT-RT2 is paper-only: a healthy run has NO testnet lifecycle rows.
    write_jsonl(scope_dir / "testnet_order_lifecycle.jsonl", [])
    review = obs.build_review(
        repo_root=tmp_path,
        now=datetime(2026, 6, 8, 12, 0, tzinfo=UTC),
        stale_minutes=24 * 60,
        process_lines=["123 run_pt_rt1_paper_observation.py"],
    )
    assert review["report"] == "obs_os1_week2_paper_observation_daily_review"
    assert review["week2_truth"]["active_lanes"] == obs.ACTIVE_LANES
    assert obs.ACTIVE_LANES == ["mf_source_faithful_baseline", "mf_source_faithful_regime_gated"]
    assert review["week2_truth"]["active_timeframes"] == ["1d"]
    assert review["week2_truth"]["disabled_timeframes"] == ["15m", "1h", "4h"]
    assert review["closed_trade_summary"]["count"] == 1
    assert review["testnet_lifecycle_summary"]["strategy_pnl_update_from_testnet_count"] == 0
    assert review["go_no_go"] == "observation_may_continue"
    assert not [flag for flag in review["anomaly_flags"] if flag["severity"] == "critical"]

    json_path, md_path = obs.write_review(review, tmp_path / "reports" / "paper_reviews" / "pt_rt2_mf_signal_observation")
    assert json_path.exists()
    assert md_path.exists()
    assert (json_path.parent / "latest_review.json").exists()
    assert "No live trading was approved" in md_path.read_text(encoding="utf-8")


def test_obs_os1_flags_runtime_boundary_anomalies(tmp_path: Path) -> None:
    scope_dir = runtime_dir(tmp_path)
    write_json(scope_dir / "summary.json", base_summary())
    write_json(scope_dir / "state.json", {"paper_runtime": {"open_positions_by_key": {}}})
    write_json(scope_dir / "data_health.json", {"status": "healthy"})
    write_jsonl(scope_dir / "runtime_audit.jsonl", [])
    write_jsonl(
        scope_dir / "decisions.jsonl",
        [
            {
                "decision_time": "2026-06-08T11:00:00Z",
                "action": "paper_opened",
                "lane_id": "avoid_low_rolling_range_20",
                "symbol": "ETH",
                "timeframe": "15m",
                "reason_codes": ["duplicate_candle_signal_ignored"],
            }
        ],
    )
    write_jsonl(scope_dir / "trades.jsonl", [])
    write_jsonl(
        scope_dir / "testnet_order_lifecycle.jsonl",
        [
            {
                "time": "2026-06-08T11:05:00Z",
                "trigger_lane": "avoid_low_rolling_range_20",
                "timeframe": "15m",
                "status": "unknown_state",
                "strategy_pnl_update_from_testnet": True,
            }
        ],
    )
    review = obs.build_review(
        repo_root=tmp_path,
        now=datetime(2026, 6, 8, 12, 0, tzinfo=UTC),
        process_lines=[],
    )
    codes = {flag["code"] for flag in review["anomaly_flags"]}
    assert "runtime_not_detected" in codes
    assert "new_15m_active_row_detected" in codes
    assert "candidate_lane_testnet_lifecycle_detected" in codes
    assert "testnet_unknown_state" in codes
    assert "synthetic_pnl_from_testnet_suspected" in codes
    assert review["go_no_go"] == "review_required"


def test_obs_os1_missing_runtime_files_fail_soft(tmp_path: Path) -> None:
    review = obs.build_review(
        repo_root=tmp_path,
        now=datetime(2026, 6, 8, 12, 0, tzinfo=UTC),
        process_lines=[],
    )
    codes = [flag["code"] for flag in review["anomaly_flags"]]
    assert codes.count("missing_runtime_file") == len(obs.RUNTIME_FILES)
    assert "runtime_not_detected" in codes
    assert "no_recent_decisions" in codes
    assert review["week2_truth"]["active_lanes"] == obs.ACTIVE_LANES
