from __future__ import annotations

from pathlib import Path
import re
import zipfile

from scripts.create_review_bundle import create_review_bundle


def _coordination_row_for(task_name: str) -> str:
    coordination = Path("money-flow/05_Agent_Coordination.md").read_text()
    for line in coordination.splitlines():
        if line.startswith("|") and task_name in line:
            return line
    raise AssertionError(f"Missing coordination row for {task_name}")


def _has_paper_boundary(note: str) -> bool:
    return (
        "PAPER TRADING IS APPROVED." in note
        or "Paper trading is approved for Hyperliquid testnet/sandbox only" in note
        or "PT-RT1 synthetic paper observation" in note
        or "PT0 separately approves" in note
    )


def _has_top20_boundary(note: str) -> bool:
    return (
        "BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED." in note
        or "broader top-20 Hyperliquid-supported paper/sandbox trading is approved" in note
        or ("top-20" in note and "PT-RT1" in note)
        or ("top 20" in note and "UAT" in note)
    )


REQUIRED_FILES = [
    "AGENTS.md",
    "CHANGELOG.md",
    "REPO_TREE.md",
    "KNOWN_ISSUES.md",
    "TODO.md",
    "money_flow_project_memory.md",
    "money-flow/00_Money_Flow_Command_Center.md",
    "money-flow/01_Current_Phase.md",
    "money-flow/02_Product_North_Star.md",
    "money-flow/03_Decision_Log.md",
    "money-flow/04_Phase_Timeline.md",
    "money-flow/05_Agent_Coordination.md",
    "money-flow/00 Maps/Strategy Validation Map.md",
    "money-flow/00 Maps/UAT Roadmap.md",
    "money-flow/00 Maps/Platform Architecture Map.md",
    "money-flow/30 Strategy/Strategy Validation Summary.md",
    "money-flow/30 Strategy/SV Evidence Closeout.md",
    "money-flow/30 Strategy/UAT Candidate Freeze.md",
    "money-flow/30 Strategy/Excluded Strategy Candidates.md",
    "money-flow/40 Operations/UAT0 Safety Runtime Hardening.md",
    "money-flow/40 Operations/Agent Workflow.md",
    "money-flow/40 Operations/Review Bundle Hygiene.md",
    "money-flow/Project_Memory/money_flow_project_memory.md",
    "README.md",
    "docs/architecture.md",
    "docs/investors.md",
    "docs/strategy_validation_sv1_7_first_evidence_review.md",
    "docs/strategy_validation_sv1_8_historical_data_bootstrap.md",
    "docs/strategy_validation_sv1_8_1_schema_truth_hotfix.md",
    "docs/strategy_validation_sv1_9_first_real_evidence_status.md",
    "docs/strategy_validation_sv1_9_1_evidence_target_truth_hotfix.md",
    "docs/strategy_validation_sv1_10_first_real_evidence_status.md",
    "docs/strategy_validation_sv1_11_market_identity_and_import_preflight.md",
    "docs/strategy_validation_sv1_11_1_preflight_and_identity_guard_hardening.md",
    "docs/strategy_validation_sv1_11_2_seed_and_preflight_governance_hotfix.md",
    "docs/strategy_validation_sv1_12_canonical_candle_import_status.md",
    "docs/strategy_validation_sv1_12_1_canonical_candle_import_run.md",
    "docs/strategy_validation_sv1_12_2_identity_and_file_readiness.md",
    "docs/strategy_validation_sv1_12_3_guarded_import_result.md",
    "docs/strategy_validation_sv1_13_hyperliquid_public_evidence_review.md",
    "docs/strategy_validation_sv1_13_1_hyperliquid_evidence_interpretation.md",
    "docs/strategy_validation_sv1_13_2_dynamic_equity_evidence.md",
    "docs/strategy_validation_sv1_14_trade_anatomy_and_market_structure.md",
    "docs/strategy_validation_sv1_15_hypothesis_experiments.md",
    "docs/strategy_validation_sv1_16_rejected_signal_replay.md",
    "docs/strategy_validation_sv1_17_true_replay_experiments.md",
    "docs/strategy_validation_sv1_18_evidence_closeout_and_uat_candidate_freeze.md",
    "docs/uat0_safety_security_runtime_hardening.md",
    "docs/uat0_1_api_auth_runtime_lockout.md",
    "docs/uat0_2_adapter_runtime_policy_and_redaction.md",
    "docs/uat0_3_top20_universe_and_drawdown_readiness.md",
    "docs/uat1_public_read_only_connectivity_and_top20_universe.md",
    "docs/uat1_public_read_only_connectivity_and_top20_universe_summary.json",
    "docs/uat1_1_shadow_signal_audit_and_drawdown_readiness.md",
    "docs/uat2_shadow_strategy_top20_observation.md",
    "docs/uat2_shadow_strategy_top20_observation_summary.json",
    "docs/uat2_1_dashboard_visualization_and_approval_readiness.md",
    "docs/uat3_0_sandbox_order_design_and_readiness.md",
    "docs/uat3_0_1_sandbox_runtime_approval_risk_readiness.md",
    "docs/uat3_0_2_sandbox_gate_integration_dry_run.md",
    "docs/uat3_0_3_sandbox_gate_wiring_and_label_enforcement.md",
    "docs/uat3_0_4_sandbox_private_read_only_drawdown.md",
    "docs/uat3_0_5_sandbox_private_read_only_drawdown_verification.md",
    "docs/uat3_0_6_sandbox_submit_path_dry_run_wiring.md",
    "docs/uat3_1_first_sandbox_order_attempt.md",
    "docs/uat3_1_first_sandbox_order_attempt_summary.json",
    "docs/uat3_2_second_sandbox_order_attempt.md",
    "docs/uat3_2_second_sandbox_order_attempt_summary.json",
    "docs/uat3_3_hyperliquid_account_targeting_precision_and_order_attempt.md",
    "docs/uat3_3_hyperliquid_account_targeting_precision_and_order_attempt_summary.json",
    "docs/uat3_4_sandbox_routing_pipeline_and_order_ledger.md",
    "docs/uat3_4_sandbox_routing_pipeline_and_order_ledger_summary.json",
    "docs/uat4_0_live_uat_dashboard_chart_cockpit.md",
    "docs/uat4_1_exchange_style_dashboard_redesign.md",
    "docs/uat4_2_live_market_dashboard_and_paper_equity_monitor.md",
    "docs/uat4_2_live_market_dashboard_and_paper_equity_monitor_summary.json",
    "docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime.md",
    "docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime_summary.json",
    "docs/pt0_0_1_tradingview_chart_stability_hotfix.md",
    "docs/pt0_0_2_historical_strategy_replay_cockpit.md",
    "docs/pt0_0_2_historical_strategy_replay_summary.json",
    "docs/pt0_0_3_historical_data_horizon_and_1d_readiness.md",
    "docs/pt0_0_3_historical_strategy_replay_summary.json",
    "docs/sv2_0_historical_data_refresh_1d_and_expanded_universe_readiness.md",
    "docs/sv2_0_money_flow_1d_sleeve_expanded_universe_evidence_rebuild.md",
    "docs/sv2_0_1_canonical_evidence_truth_hotfix.md",
    "docs/sv2_0_2_canonical_sv2_evidence_packs.md",
    "docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants.md",
    "docs/sor_ev1_money_flow_trade_loss_anatomy_and_variants_summary.json",
    "docs/sor_ev2_true_forward_stop_and_rejected_signal_replay.md",
    "docs/sor_ev2_true_forward_stop_and_rejected_signal_replay_summary.json",
    "docs/sor_ev2_1_evidence_lab_ui.md",
    "docs/sor_ev2_2_variant_chart_overlay.md",
    "docs/sor_ev3_avoid_sideways_low_volatility.md",
    "docs/sor_ev3_avoid_sideways_low_volatility_summary.json",
    "docs/mf_orig_ev1_original_money_flow_spec_and_gap_matrix.md",
    "docs/mf_orig_ev1_original_money_flow_reconstruction.md",
    "docs/mf_orig_ev1_original_money_flow_reconstruction_summary.json",
    "docs/mf_orig_ev2_multitimeframe_evidence_packs.md",
    "docs/mf_orig_ev2_multitimeframe_evidence_summary.json",
    "docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review.md",
    "docs/ev_audit1_full_hypothesis_data_and_paper_readiness_review_summary.json",
    "docs/ob2_0_obsidian_strategy_brain_refresh.md",
    "docs/ob2_0_obsidian_strategy_brain_refresh_summary.json",
    "docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing.md",
    "docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json",
    "docs/pt_rt1_24h_dry_run_probes_disabled.md",
    "docs/pt_rt1_24h_testnet_plumbing_probe_run.md",
    "docs/pt_rt1_60_day_forward_observation_plan.md",
    "docs/pt_rt1_1_24h_probes_disabled_dry_run.md",
    "docs/pt_rt1_1_24h_probes_disabled_dry_run_summary.json",
    "docs/pt_rt1_1a_expanded_universe_and_strategy_lanes.md",
    "docs/pt_rt1_1a_expanded_universe_and_strategy_lanes_summary.json",
    "docs/pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness.md",
    "docs/pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness_summary.json",
    "docs/pt_rt1_1c_24h_runtime_collection_start.md",
    "docs/pt_rt1_1c_24h_runtime_collection_start_summary.json",
    "money-flow/00 Maps/Strategy Family Map.md",
    "money-flow/00 Maps/Evidence and Backtesting Map.md",
    "money-flow/00 Maps/Data Source and Market Data Map.md",
    "money-flow/00 Maps/Dashboard and UI Map.md",
    "money-flow/00 Maps/Paper Observation Roadmap.md",
    "money-flow/10 Strategy/Strategy Status Register.md",
    "money-flow/10 Strategy/Original Money Flow Source Notes.md",
    "money-flow/20 Evidence/EV-AUDIT1 Summary.md",
    "money-flow/90 Reference/The Money Flow Trading System - Gerald Peters - 2019 Edition 2.pdf",
]


def test_required_operational_docs_exist() -> None:
    for relative_path in REQUIRED_FILES:
        assert Path(relative_path).exists(), f"Missing required operational doc: {relative_path}"


def test_agents_references_required_operational_docs() -> None:
    agents = Path("AGENTS.md").read_text()
    for required_name in ["AGENTS.md", "CHANGELOG.md", "REPO_TREE.md", "KNOWN_ISSUES.md", "TODO.md"]:
        assert required_name in agents
    assert "money_flow_project_memory.md" in agents
    assert "Obsidian" in agents
    assert "money-flow/00_Money_Flow_Command_Center.md" in agents
    assert "money-flow/05_Agent_Coordination.md" in agents
    assert "money-flow/00 Maps/UAT Roadmap.md" in agents
    assert "Do not create duplicate command centers" in agents
    assert "Mark your coordination row" in agents
    assert "not a substitute" in agents


def test_readme_mentions_operational_memory() -> None:
    readme = Path("README.md").read_text()
    assert "Operational Memory" in readme
    assert "Obsidian" in readme
    assert "AGENTS.md" in readme
    assert "CHANGELOG.md" in readme
    assert "Money Flow For Investors" in readme


def test_investor_overview_is_plain_language_and_discoverable() -> None:
    investor_page = Path("docs/investors.md").read_text()
    assert "# Money Flow For Investors" in investor_page
    assert "plain English" in investor_page
    assert "What Money Flow Is Today" in investor_page
    assert "Where Money Flow Is Going Tomorrow" in investor_page
    assert "What Money Flow Is Not Yet" in investor_page


def test_obsidian_brain_workflow_exists() -> None:
    command_center = Path("money-flow/00_Money_Flow_Command_Center.md").read_text()
    current_phase = Path("money-flow/01_Current_Phase.md").read_text()
    coordination = Path("money-flow/05_Agent_Coordination.md").read_text()
    moved_memory = Path("money-flow/Project_Memory/money_flow_project_memory.md").read_text()
    root_pointer = Path("money_flow_project_memory.md").read_text()

    assert "canonical Obsidian command center" in command_center
    assert "`OB2.0` Obsidian Strategy Brain + Evidence Architecture Refresh" in current_phase
    assert "EV-AUDIT1" in current_phase
    assert "PT-RT1" in current_phase
    assert "PT-RT1.1" in current_phase
    assert "PT-RT1.2" in current_phase
    assert "PT-RT1.3" in current_phase
    assert "stale/thin/missing/nonpositive Hyperliquid public mids are warning-only" in current_phase
    assert "Signed testnet transport is present only as an explicit gated path" in current_phase
    assert "`MF-ORIG-EV2` Original Money Flow multi-timeframe evidence packs and Historical Replay UI are complete" in current_phase
    assert "MF-ORIG-EV1.1" in current_phase
    assert "SOR-EV2" in current_phase
    assert "72 scenario rows" in current_phase
    assert "SV1.18" in command_center
    assert "UAT0" in command_center
    assert "UAT1 public read-only connectivity is complete" in command_center
    assert "UAT2 no-order shadow observation" in command_center
    assert "UAT2.1 dashboard visualization is complete" in command_center
    assert "UAT3.0.6 sandbox submit path dry-run wiring" in command_center
    assert "UAT3.1 first sandbox/testnet lifecycle probe is complete" in command_center
    assert "UAT3.2 fixed-key readiness preflight" in command_center
    assert "UAT3.4 fixed-target sandbox routing ledger" in command_center
    assert "UAT4.0 read-only chart cockpit" in command_center
    assert "UAT4.1 exchange-style dashboard redesign" in command_center
    assert "UAT4.2 live-market/paper-equity monitoring" in command_center
    assert "PT0 TradingView charts" in command_center
    assert "PT0.0.1 chart stability hotfix" in command_center
    assert "PT0.0.2 historical replay cockpit" in command_center
    assert "PT0.0.3 historical data horizon" in command_center
    assert "SV2.0 is complete" in command_center
    assert "SV2.0.1 is complete" in command_center
    assert "SV2.0.2 is complete" in command_center
    assert "SOR-EV1 is complete" in command_center
    assert "SOR-EV2 is complete" in command_center
    assert "SOR-EV2.1 is complete" in command_center
    assert "SOR-EV2.2 is complete" in command_center
    assert "MF-ORIG-EV2 is complete as an evidence-only multi-timeframe expansion" in command_center
    assert "Original source" in command_center
    assert "Gerald Peters PDF is now present" in command_center
    assert "PT-RT1" in command_center
    assert "PT-RT1.1" in command_center
    assert "PT-RT1.2" in command_center
    assert "repeated same-candle" in command_center
    assert "signed testnet transport is an explicit PT-RT1.2 gated path" in command_center
    assert "Evidence and Backtesting Map" in command_center
    assert "Active Work" in coordination
    assert "Founder Vision" in moved_memory
    assert "Strategy Validation" in moved_memory
    assert "SV1.18-SV1.18.1" in moved_memory
    assert "money_flow_hyperliquid_eth_1h_baseline_uat_candidate" in moved_memory
    assert "PAPER TRADING IS APPROVED." in moved_memory
    assert "BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED." in moved_memory
    assert "UAT1 public read-only connectivity is complete" in moved_memory
    assert "UAT2 bounded no-order shadow observation is complete" in moved_memory
    assert "UAT2.1 dashboard visualization is complete" in moved_memory
    assert "UAT3.0.6 sandbox submit path dry-run wiring is complete" in moved_memory
    assert "UAT3.1 first sandbox/testnet lifecycle probe is complete" in moved_memory
    assert "UAT3.2 fixed-key readiness preflight" in moved_memory
    assert "UAT3.3 Hyperliquid account-targeting / precision hardening is complete" in moved_memory
    assert "UAT3.4 production-like sandbox routing pipeline and routed-order ledger are complete" in moved_memory
    assert "UAT4.0 read-only dashboard/chart cockpit is complete" in moved_memory
    assert "UAT4.1 exchange-style dashboard redesign is complete" in moved_memory
    assert "UAT4.2 live market dashboard and paper-equity monitor is complete" in moved_memory
    assert "PT0 TradingView charting and top-20 paper/sandbox runtime foundation is complete" in moved_memory
    assert "PT0.0.2 historical strategy replay cockpit is complete" in moved_memory
    assert "PT0.0.3 historical data horizon and 1D replay support is complete" in moved_memory
    assert "SV2.0 Money Flow 1D sleeve and expanded public-mainnet evidence refresh is complete" in moved_memory
    assert "SV2.0.1 canonical evidence truth hotfix" in moved_memory
    assert "SV2.0.2 hardened DB import and canonical evidence-pack generation is complete" in moved_memory
    assert "MF-ORIG-EV1.1 accounting/drawdown evidence hotpatch" in moved_memory
    assert "MF-ORIG-EV2 multi-timeframe Original Money Flow evidence packs plus full-equity comparison Historical Replay UI" in moved_memory
    assert "EV-AUDIT1 full evidence/data/paper-readiness audit" in moved_memory
    assert "OB2.0 Obsidian strategy brain refresh" in moved_memory
    assert "PT-RT1 real-time public-market paper-observation substrate" in moved_memory
    assert "PT-RT1.1" in moved_memory
    assert "PT-RT1.1A" in moved_memory
    assert "blocked because the expected ignored runtime artifact directory" in moved_memory
    assert "canonical strategic project memory has moved" in root_pointer
    assert "The original starting point" not in root_pointer


def test_obsidian_brain_overhaul_maps_exist_and_are_current() -> None:
    command_center = Path("money-flow/00_Money_Flow_Command_Center.md").read_text()
    compatibility_command_center = Path("money-flow/Money Flow Command Center.md").read_text()
    current_dashboard = Path("money-flow/00 Maps/Current State Dashboard.md").read_text()
    sv_map = Path("money-flow/00 Maps/Strategy Validation Map.md").read_text()
    uat_roadmap = Path("money-flow/00 Maps/UAT Roadmap.md").read_text()
    candidate_freeze = Path("money-flow/30 Strategy/UAT Candidate Freeze.md").read_text()
    project_memory = Path("money-flow/Project_Memory/money_flow_project_memory.md").read_text()

    assert "Current implemented milestone | `PT-RT1.3` candle-truth data-health semantics" in command_center
    assert "Canonical command center" in compatibility_command_center
    assert "PT-RT1 now implements the public-mainnet paper-observation substrate" in current_dashboard
    assert "SV2.0.2 canonical evidence" in current_dashboard
    assert "EV-AUDIT1" in current_dashboard
    assert "PT-RT1" in current_dashboard
    assert "UAT3.3" in command_center
    assert "UAT0 safety" in current_dashboard
    assert "UAT4.2" in current_dashboard
    assert "PT0" in current_dashboard
    assert "PT0.0.3" in current_dashboard
    assert "SV2.0" in current_dashboard
    assert "SV2.0.1" in current_dashboard
    assert "SV2.0.2" in current_dashboard
    assert "SOR-EV1" in command_center
    assert "SOR-EV2" in command_center
    assert "SOR-EV2.1" in command_center
    assert "SOR-EV2.2" in command_center
    assert "SOR-EV3" in command_center
    assert "SOR-EV3" in sv_map
    assert "EV-AUDIT1" in command_center
    assert "EV-AUDIT1" in sv_map
    assert "no clean strategy candidate" in command_center
    assert "SOR-EV1-SOR-EV3" in project_memory
    assert "EV-AUDIT1" in project_memory
    assert "Strategy Validation is now its own major track" in Path("money-flow/00 Maps/Phase Timeline.md").read_text()
    assert "What Strategy Validation Did" in sv_map
    assert "What Strategy Validation Did Not Prove" in sv_map
    assert "Original Money Flow" in Path("money-flow/00 Maps/Strategy Family Map.md").read_text()
    assert "canonical_evidence" in Path("money-flow/00 Maps/Evidence and Backtesting Map.md").read_text()
    assert "Dashboard date filters are display-only recalculations" in Path("money-flow/00 Maps/Data Source and Market Data Map.md").read_text()
    assert "Historical Replay" in Path("money-flow/00 Maps/Dashboard and UI Map.md").read_text()
    assert "PT-RT1" in Path("money-flow/00 Maps/Paper Observation Roadmap.md").read_text()
    assert "Money Flow v1.2" in Path("money-flow/10 Strategy/Strategy Status Register.md").read_text()
    assert "Gerald Peters" in Path("money-flow/10 Strategy/Original Money Flow Source Notes.md").read_text()
    assert "paper_observation_ready_with_conditions" in Path("money-flow/20 Evidence/EV-AUDIT1 Summary.md").read_text()
    assert "UAT0 - Safety / Security / Runtime Hardening" in uat_roadmap
    assert "UAT1 - Top-20 Universe + Read-Only Venue/Market Metadata" in uat_roadmap
    assert "UAT validates plumbing and behavior" in uat_roadmap
    assert "money_flow_hyperliquid_eth_1h_baseline_uat_candidate" in candidate_freeze
    assert "UAT1 public read-only connectivity is complete" in project_memory


def test_current_state_notes_keep_uat_boundaries() -> None:
    current_state_paths = [
        Path("money-flow/00_Money_Flow_Command_Center.md"),
        Path("money-flow/Money Flow Command Center.md"),
        Path("money-flow/01_Current_Phase.md"),
        Path("money-flow/00 Maps/Current State Dashboard.md"),
        Path("money-flow/00 Maps/Strategy Validation Map.md"),
        Path("money-flow/00 Maps/UAT Roadmap.md"),
        Path("money-flow/30 Strategy/UAT Candidate Freeze.md"),
        Path("money-flow/40 Operations/Future Work Roadmap.md"),
    ]

    for path in current_state_paths:
        note = path.read_text()
        assert _has_paper_boundary(note)
        assert _has_top20_boundary(note)
        assert "Live trading is not approved" in note
        assert (
            "Exchange order submission is not approved" in note
            or "No exchange order submission approved" in note
            or "Additional exchange order submission is not approved" in note
            or "Live exchange order submission is not approved" in note
        )
        assert "Hyperliquid" in note
        assert "ETH" in note
        assert "sleeve_1h" in note


def test_obsidian_current_state_notes_do_not_have_stale_current_truth() -> None:
    current_state_paths = [
        Path("money-flow/00_Money_Flow_Command_Center.md"),
        Path("money-flow/Money Flow Command Center.md"),
        Path("money-flow/01_Current_Phase.md"),
        Path("money-flow/00 Maps/Current State Dashboard.md"),
        Path("money-flow/00 Maps/Phase Timeline.md"),
        Path("money-flow/40 Operations/Future Work Roadmap.md"),
    ]
    stale_current_truth_phrases = [
        "Current branch observed: `phase-7.6`",
        "Phase observed in repo memory: `SV1.7`",
        "next proposed phase is Phase 8.0",
        "The immediate next phase should be Phase 8.0",
        "routing is current priority",
        "Current implemented phase: `SV1.10`",
        "Phase observed in repo memory: `SV1.10`",
        "Current implemented phase: `SV1.11`",
        "Phase observed in repo memory: `SV1.11`",
        "Current implemented phase: `SV1.11.1`",
        "Phase observed in repo memory: `SV1.11.1`",
        "Current implemented phase: `SV1.11.2`",
        "Phase observed in repo memory: `SV1.11.2`",
        "Current implemented phase: `SV1.12`",
        "Phase observed in repo memory: `SV1.12`",
        "Current implemented phase: `SV1.12.1`",
        "Phase observed in repo memory: `SV1.12.1`",
        "Current implemented phase: `SV1.12.2`",
        "Phase observed in repo memory: `SV1.12.2`",
        "Current implemented phase: `SV1.12.3`",
        "Phase observed in repo memory: `SV1.12.3`",
        "Current implemented phase: `SV1.12.4`",
        "Phase observed in repo memory: `SV1.12.4`",
        "Current implemented phase: `SV1.12.5`",
        "Phase observed in repo memory: `SV1.12.5`",
        "Current implemented phase: `SV1.12.5.1`",
        "Phase observed in repo memory: `SV1.12.5.1`",
        "Current implemented phase: `SV1.13`",
        "Phase observed in repo memory: `SV1.13`",
        "Current implemented phase: `SV1.13.1`",
        "Phase observed in repo memory: `SV1.13.1`",
        "Current implemented phase: `SV1.13.2`",
        "Phase observed in repo memory: `SV1.13.2`",
        "Current implemented phase: `SV1.14`",
        "Phase observed in repo memory: `SV1.14`",
        "Current implemented phase: `SV1.15`",
        "Phase observed in repo memory: `SV1.15`",
        "Current implemented phase: `SV1.15.1`",
        "Phase observed in repo memory: `SV1.15.1`",
        "Current implemented phase: `SV1.16`",
        "Phase observed in repo memory: `SV1.16`",
        "Current implemented phase: `SV1.16.1`",
        "Phase observed in repo memory: `SV1.16.1`",
        "Current implemented phase: `SV1.17`",
        "Phase observed in repo memory: `SV1.17`",
        "Current Strategy Validation focus: `SV1.13`",
        "Current implemented phase is `SV1.13`",
        "Phase 8.0 as next",
        "Phase 8 Focus as current",
        "ready for paper trading",
        "paper trading approved",
        "live trading approved",
        "proven profitable",
    ]

    for path in current_state_paths:
        contents = path.read_text()
        assert "SV1.18" in contents or "UAT0" in contents, f"{path} does not reflect current UAT0/SV1.18 work"
        assert "UAT0" in contents, f"{path} does not point to UAT0"
        for phrase in stale_current_truth_phrases:
            assert phrase not in contents, f"{path} still contains stale current truth: {phrase}"


def test_ob2_0_obsidian_strategy_brain_refresh_is_current() -> None:
    command_center = Path("money-flow/00_Money_Flow_Command_Center.md").read_text()
    current_phase = Path("money-flow/01_Current_Phase.md").read_text()
    project_memory = Path("money-flow/Project_Memory/money_flow_project_memory.md").read_text()
    strategy_family_map = Path("money-flow/00 Maps/Strategy Family Map.md").read_text()
    evidence_map = Path("money-flow/00 Maps/Evidence and Backtesting Map.md").read_text()
    data_map = Path("money-flow/00 Maps/Data Source and Market Data Map.md").read_text()
    dashboard_map = Path("money-flow/00 Maps/Dashboard and UI Map.md").read_text()
    paper_roadmap = Path("money-flow/00 Maps/Paper Observation Roadmap.md").read_text()
    strategy_register = Path("money-flow/10 Strategy/Strategy Status Register.md").read_text()
    original_source_note = Path("money-flow/10 Strategy/Original Money Flow Source Notes.md").read_text()
    audit_summary = Path("money-flow/20 Evidence/EV-AUDIT1 Summary.md").read_text()
    ob_report = Path("docs/ob2_0_obsidian_strategy_brain_refresh.md").read_text()

    assert "OB2.0" in command_center
    assert "not production-ready" in strategy_register
    assert "no clean strategy candidate" in strategy_register
    assert "No strategy is production-ready" in current_phase or "no clean strategy candidate is promoted" in current_phase
    assert "PT-RT1" in current_phase
    assert "Run a fresh `PT-RT1.3` observation session" in current_phase
    assert "compact-log suppression/size stats" in current_phase
    assert "duplicate same-candle open blocking" in current_phase
    assert "mid-warning rollups" in current_phase
    assert "Signed testnet transport should remain off" in current_phase
    assert "SV2.0.2" in project_memory
    assert "MF-ORIG" in project_memory
    assert "EV-AUDIT1" in project_memory
    assert "OB2.0" in project_memory
    assert "Money Flow v1.2" in strategy_family_map
    assert "Original Money Flow" in strategy_family_map
    assert "SOR Repair Variants" in strategy_family_map
    assert "STRAT-EV" in strategy_family_map
    assert "canonical_evidence" in evidence_map
    assert "dashboard_display_only" in evidence_map
    assert "display-only recalculations" in evidence_map
    assert "Hyperliquid testnet data is not strategy truth" in data_map
    assert "Private/signed/order endpoints are not required for historical evidence" in data_map
    assert "Date filters are display-only" in dashboard_map
    assert "old `Experiments` tab" in dashboard_map
    assert "public" in paper_roadmap
    assert "mainnet market data" in paper_roadmap
    assert "no exchange orders" in paper_roadmap
    assert "implemented_runtime_state_and_transport_gates" in paper_roadmap
    assert "reports/paper_runtime/pt_rt1_1c_24h_dry_run/" in paper_roadmap
    assert "Gerald Peters" in original_source_note
    assert "source-faithful reconstruction" in original_source_note
    assert "paper_observation_ready_with_conditions" in audit_summary
    assert "promotes no clean strategy candidate" in audit_summary
    assert "OB2.0 refreshes the Obsidian strategy brain" in ob_report
    assert "Production Money Flow rules changed: `false`" in ob_report
    assert "Live trading approved: `false`" in ob_report


def test_pt_rt1_operational_docs_are_current() -> None:
    command_center = Path("money-flow/00_Money_Flow_Command_Center.md").read_text()
    current_phase = Path("money-flow/01_Current_Phase.md").read_text()
    project_memory = Path("money-flow/Project_Memory/money_flow_project_memory.md").read_text()
    paper_roadmap = Path("money-flow/00 Maps/Paper Observation Roadmap.md").read_text()
    report = Path("docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing.md").read_text()
    summary = Path("docs/pt_rt1_real_time_paper_observation_and_testnet_plumbing_summary.json").read_text()
    dry_run = Path("docs/pt_rt1_24h_dry_run_probes_disabled.md").read_text()
    probe_run = Path("docs/pt_rt1_24h_testnet_plumbing_probe_run.md").read_text()
    observation_plan = Path("docs/pt_rt1_60_day_forward_observation_plan.md").read_text()
    dry_run_report = Path("docs/pt_rt1_1_24h_probes_disabled_dry_run.md").read_text()
    dry_run_summary = Path("docs/pt_rt1_1_24h_probes_disabled_dry_run_summary.json").read_text()
    expanded_report = Path("docs/pt_rt1_1a_expanded_universe_and_strategy_lanes.md").read_text()
    expanded_summary = Path("docs/pt_rt1_1a_expanded_universe_and_strategy_lanes_summary.json").read_text()
    runtime_report = Path("docs/pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness.md").read_text()
    runtime_summary = Path("docs/pt_rt1_1b_hyperliquid_live_market_data_and_runtime_readiness_summary.json").read_text()
    start_report = Path("docs/pt_rt1_1c_24h_runtime_collection_start.md").read_text()
    start_summary = Path("docs/pt_rt1_1c_24h_runtime_collection_start_summary.json").read_text()

    for contents in (command_center, current_phase, project_memory, paper_roadmap, report, expanded_report, runtime_report, start_report):
        assert "PT-RT1" in contents
        assert "public mainnet" in contents or "Public mainnet" in contents
        assert "testnet" in contents
        assert "Live trading is not approved" in contents or "live trading" in contents

    assert "strategy-truth lane is Hyperliquid public mainnet market data only" in command_center
    assert "PT-RT1.3 is the current runtime data-health layer" in command_center
    assert "state persists processed signal keys" in command_center
    assert "normal dashboard path remains audit/order-shape only" in command_center
    assert "not production approval" in report
    assert "live approval" in report
    assert "paper-runtime approval" in report
    assert "public-read-only `/info` connector" in report
    assert "exactly 10 lanes" in report
    assert "wildcard_btc_regime_guard" in report
    assert "TRON" in report
    assert "kPEPE" in report
    assert "notional cap is `20 USDC`" in paper_roadmap
    assert "dashboard-started PT-RT1.3 currently creates probe audit/order-shape rows only" in paper_roadmap
    assert "signed transport requires the explicit PT-RT1.2" in paper_roadmap
    assert "testnet fills never update strategy paper PnL" in paper_roadmap
    assert "runtime_collection_started" in start_summary
    assert "PT-RT1.1D may evaluate 24-hour runtime artifacts after completion" in start_report
    assert "PT-RT1.1A status: `implemented_expanded_readiness`" in paper_roadmap
    assert "PT-RT1.2 blocked" in dry_run_report
    assert "not_verified_runtime_absent" in dry_run_summary
    assert "PT_RT1_TESTNET_DAILY_PROBE_CAP" in dry_run_summary
    assert "PT-RT1.1A" in expanded_report
    assert "PT-RT1.1B may connect public mainnet data and prepare PT-RT1.1C" in expanded_report
    assert "PT-RT1.1B Hyperliquid Live Market Data And Runtime Readiness" in runtime_report
    assert "PT-RT1.1C may start 24-hour probes-disabled runtime collection" in runtime_report
    assert "\"public_mainnet_status\": \"connected\"" in runtime_summary
    assert "\"next_phase_decision\": \"PT-RT1.1C may start 24-hour probes-disabled runtime collection\"" in runtime_summary
    assert "wildcard_volatility_expansion_breakout" in expanded_summary
    assert "pepe_kpepe_unit_semantics_deferred" in expanded_summary
    assert "okb_support_not_confirmed" in expanded_summary
    assert "money_flow_v1_2_baseline" in summary
    assert "avoid_low_rolling_range_50" in summary
    assert "avoid_low_rolling_range_20" in summary
    assert "mf_orig_stage_filter_only_full_equity" in summary
    assert "mf_orig_stage2_pullback_reclaim_full_equity" in summary
    assert "mf_orig_1d_stage2_5_20_crossover_full_equity" in summary
    assert "mf_orig_1d_stage2_breakout_resistance_full_equity" in summary
    assert "wildcard_multi_timeframe_alignment" in summary
    assert "TRX" in summary
    assert "kPEPE" in summary
    assert "no testnet order endpoint calls" in dry_run.lower()
    assert "approval captured" in probe_run.lower()
    assert "60-day" in observation_plan.lower()


def test_uat0_operational_truth_is_current() -> None:
    report = Path("docs/uat0_safety_security_runtime_hardening.md").read_text()
    uat01_report = Path("docs/uat0_1_api_auth_runtime_lockout.md").read_text()
    uat02_report = Path("docs/uat0_2_adapter_runtime_policy_and_redaction.md").read_text()
    uat03_report = Path("docs/uat0_3_top20_universe_and_drawdown_readiness.md").read_text()
    uat1_report = Path("docs/uat1_public_read_only_connectivity_and_top20_universe.md").read_text()
    uat11_report = Path("docs/uat1_1_shadow_signal_audit_and_drawdown_readiness.md").read_text()
    uat2_report = Path("docs/uat2_shadow_strategy_top20_observation.md").read_text()
    uat301_report = Path("docs/uat3_0_1_sandbox_runtime_approval_risk_readiness.md").read_text()
    uat302_report = Path("docs/uat3_0_2_sandbox_gate_integration_dry_run.md").read_text()
    uat303_report = Path("docs/uat3_0_3_sandbox_gate_wiring_and_label_enforcement.md").read_text()
    uat304_report = Path("docs/uat3_0_4_sandbox_private_read_only_drawdown.md").read_text()
    uat305_report = Path("docs/uat3_0_5_sandbox_private_read_only_drawdown_verification.md").read_text()
    uat306_report = Path("docs/uat3_0_6_sandbox_submit_path_dry_run_wiring.md").read_text()
    uat31_report = Path("docs/uat3_1_first_sandbox_order_attempt.md").read_text()
    uat32_report = Path("docs/uat3_2_second_sandbox_order_attempt.md").read_text()
    uat33_report = Path("docs/uat3_3_hyperliquid_account_targeting_precision_and_order_attempt.md").read_text()
    uat34_report = Path("docs/uat3_4_sandbox_routing_pipeline_and_order_ledger.md").read_text()
    uat40_report = Path("docs/uat4_0_live_uat_dashboard_chart_cockpit.md").read_text()
    uat41_report = Path("docs/uat4_1_exchange_style_dashboard_redesign.md").read_text()
    uat42_report = Path("docs/uat4_2_live_market_dashboard_and_paper_equity_monitor.md").read_text()
    pt0_report = Path("docs/pt0_tradingview_charts_and_top20_paper_sandbox_runtime.md").read_text()
    pt001_report = Path("docs/pt0_0_1_tradingview_chart_stability_hotfix.md").read_text()
    pt002_report = Path("docs/pt0_0_2_historical_strategy_replay_cockpit.md").read_text()
    pt003_report = Path("docs/pt0_0_3_historical_data_horizon_and_1d_readiness.md").read_text()
    sv20_readiness_report = Path("docs/sv2_0_historical_data_refresh_1d_and_expanded_universe_readiness.md").read_text()
    sv20_evidence_report = Path("docs/sv2_0_money_flow_1d_sleeve_expanded_universe_evidence_rebuild.md").read_text()
    sv201_report = Path("docs/sv2_0_1_canonical_evidence_truth_hotfix.md").read_text()
    current_notes = [
        Path("money-flow/00_Money_Flow_Command_Center.md").read_text(),
        Path("money-flow/01_Current_Phase.md").read_text(),
        Path("money-flow/00 Maps/Current State Dashboard.md").read_text(),
        Path("money-flow/00 Maps/UAT Roadmap.md").read_text(),
        Path("money-flow/40 Operations/UAT0 Safety Runtime Hardening.md").read_text(),
    ]

    assert "UAT1 read-only connectivity may proceed" in report
    assert "API authentication / authorization" in report
    assert "UAT0.1" in report
    assert "RuntimeSafetyPolicy" in report
    assert "Sensitive `/api/v1` routes now require scoped bearer auth" in report
    assert "top 20 high-volume crypto assets supported by the selected UAT venue/environment" in report
    assert "next_candle_open" in report
    assert "next_candle_close" in report
    assert "same_candle_close_research_only" in report

    assert "Sensitive Route Inventory" in uat01_report
    assert "read_only_operator" in uat01_report
    assert "automation_admin" in uat01_report
    assert "Runtime Mode Policy" in uat01_report
    assert "live_endpoint_lockout_enabled" in uat01_report
    assert "`UAT1 is blocked`" in uat01_report
    assert "Partially closed by UAT0.2" in uat01_report
    assert "Paper trading is not approved" in uat01_report
    assert "Live trading is not approved" in uat01_report
    assert "Exchange order submission is not approved" in uat01_report

    assert "Adapter Safety Inventory" in uat02_report
    assert "Hyperliquid UAT1 Read-Only Allowlist" in uat02_report
    assert "Forbidden Endpoint Categories" in uat02_report
    assert "Redaction Verification Status" in uat02_report
    assert "UAT0.2 decision at the time: `UAT1 is blocked`" in uat02_report
    assert "UAT0.3 updated decision: `UAT1 read-only connectivity may proceed`" in uat02_report
    assert "Paper trading is not approved" in uat02_report
    assert "Live trading is not approved" in uat02_report
    assert "Exchange order submission is not approved" in uat02_report

    assert "Top-20 Universe Policy" in uat03_report
    assert "Hyperliquid Market Intersection Logic" in uat03_report
    assert "Runtime Drawdown Monitoring Policy" in uat03_report
    assert "`UAT1 read-only connectivity may proceed`" in uat03_report
    assert "does not connect to exchanges" in uat03_report
    assert "does not submit orders" in uat03_report
    assert "Paper trading is not approved" in uat03_report
    assert "Live trading is not approved" in uat03_report
    assert "Exchange order submission is not approved" in uat03_report

    assert "UAT1 Public Read-Only Connectivity And Top-20 Universe" in uat1_report
    assert "UAT1 is public read-only connectivity" in uat1_report
    assert "API keys used | `false`" in uat1_report
    assert "Private endpoints used: `false`" in uat1_report
    assert "Signed endpoints used: `false`" in uat1_report
    assert "Order endpoints used: `false`" in uat1_report
    assert "Strategy decisions created: `false`" in uat1_report
    assert "Order intents created: `false`" in uat1_report
    assert "Submitted orders created: `false`" in uat1_report
    assert "Top-20 inclusion means observation candidate only" in uat1_report
    assert "Historical UAT1 decision at the time: `UAT2 is blocked`" in uat1_report

    assert "UAT1.1 Shadow Signal Audit And Drawdown Readiness" in uat11_report
    assert "next_candle_open" in uat11_report
    assert "next_candle_close" in uat11_report
    assert "same_candle_close_research_only" in uat11_report
    assert "Shadow audit no-live-artifact check: `true`" in uat11_report
    assert "not_live_account_drawdown" in uat11_report
    assert "Historical UAT1.1 decision at the time: `UAT2 shadow strategy run may proceed`" in uat11_report
    assert "StrategyDecision" in uat11_report
    assert "OrderIntent" in uat11_report
    assert "SubmittedOrder" in uat11_report

    assert "UAT2 Shadow Strategy Top-20 Observation" in uat2_report
    assert "UAT2 is a bounded no-order shadow strategy observation run" in uat2_report
    assert "API keys used | `false`" in uat2_report
    assert "Private endpoints allowed | `false`" in uat2_report
    assert "Signed endpoints allowed | `false`" in uat2_report
    assert "Order endpoints allowed | `false`" in uat2_report
    assert "Shadow audit records | `45`" in uat2_report
    assert "`would_open` | `11`" in uat2_report
    assert "`no_trade` | `34`" in uat2_report
    assert "not_live_account_drawdown" in uat2_report
    assert "`UAT3 is blocked`" in uat2_report
    assert "StrategyDecision" in uat2_report
    assert "OrderIntent" in uat2_report
    assert "SubmittedOrder" in uat2_report

    assert "UAT3.0.1 Sandbox Runtime / Approval / Risk Readiness" in uat301_report
    assert "Sandbox Runtime Policy Status" in uat301_report
    assert "Sandbox Artifact Label Validation" in uat301_report
    assert "Actual Sandbox Order Approval Template" in uat301_report
    assert "Approval Scope Fixture Validation" in uat301_report
    assert "Sandbox Risk Gate Fixture Validation" in uat301_report
    assert "Sandbox Drawdown Feed Fixture Status" in uat301_report
    assert "Submit Lease / Duplicate Prevention Fixture Status" in uat301_report
    assert "`UAT3.1 is blocked`" in uat301_report
    assert "Actual sandbox order submission is not approved" in uat301_report
    assert "Paper trading is not approved" in uat301_report
    assert "Live trading is not approved" in uat301_report

    assert "UAT3.0.2 Sandbox Gate Integration Dry-Run" in uat302_report
    assert "Runtime Policy Blocker Propagation" in uat302_report
    assert "Non-Positive Quantity / Limit Validation" in uat302_report
    assert "Unified Dry-Run Sandbox Gate Preflight" in uat302_report
    assert "founder_operator_actual_sandbox_submission_approval_required" in uat302_report
    assert "sandbox_drawdown_feed_live_fed_required" in uat302_report
    assert "sandbox_artifact_labeling_not_enforced_on_persistence" in uat302_report
    assert "`UAT3.1 is blocked`" in uat302_report
    assert "Actual sandbox order submission is not approved" in uat302_report
    assert "Paper trading is not approved" in uat302_report
    assert "Live trading is not approved" in uat302_report

    assert "UAT3.0.3 Sandbox Gate Wiring And Label Enforcement" in uat303_report
    assert "Sandbox Artifact Label Boundary Enforcement" in uat303_report
    assert "Dry-Run Executable Gate Service" in uat303_report
    assert "Runtime Policy Semantics" in uat303_report
    assert "Approval-Scope Dry-Run Wiring" in uat303_report
    assert "Risk-Gate Dry-Run Wiring" in uat303_report
    assert "Submit-Lease Dry-Run Wiring" in uat303_report
    assert "`UAT3.1 is blocked`" in uat303_report
    assert "Actual sandbox order submission is not approved" in uat303_report
    assert "Paper trading is not approved" in uat303_report
    assert "Live trading is not approved" in uat303_report

    assert "UAT3.0.4 Sandbox Private Read-Only Drawdown" in uat304_report
    assert "approval status for private read-only credentials" in uat304_report
    assert "Private Read-Only Account Policy" in uat304_report
    assert "Endpoint Classification" in uat304_report
    assert "Sandbox Account Drawdown Feed Status" in uat304_report
    assert "No-Order Endpoint Confirmation" in uat304_report
    assert "sandbox_drawdown_feed_live_fed_verified" in uat304_report
    assert "`UAT3.1 is blocked`" in uat304_report
    assert "Actual sandbox order submission is not approved" in uat304_report
    assert "Paper trading is not approved" in uat304_report
    assert "Live trading is not approved" in uat304_report

    assert "UAT3.0.5 Sandbox Private Read-Only Drawdown Verification" in uat305_report
    assert "approval status | `verified`" in uat305_report
    assert "credential source status | `verified_local_environment`" in uat305_report
    assert "sandbox_drawdown_feed_live_fed_verified" in uat305_report
    assert "private account endpoints called | `true_read_only_account_state_only`" in uat305_report
    assert "order endpoints called | `false`" in uat305_report
    assert "`UAT3.1 is blocked`" in uat305_report
    assert "Actual sandbox order submission is not approved" in uat305_report
    assert "Paper trading is not approved" in uat305_report
    assert "Live trading is not approved" in uat305_report

    assert "UAT3.0.6 Sandbox Submit Path Dry-Run Wiring" in uat306_report
    assert "Dry-Run Submission Plan" in uat306_report
    assert "Executable Gate Chain" in uat306_report
    assert "founder_operator_actual_sandbox_submission_approval_required" in uat306_report
    assert "sandbox_drawdown_feed_live_fed_verified" in uat306_report
    assert "sandbox_order_submission" in uat306_report
    assert "OrderIntent rows created | `false`" in uat306_report
    assert "PreparedVenueOrder rows created | `false`" in uat306_report
    assert "SubmittedOrder rows created | `false`" in uat306_report
    assert "Executable approvals created | `false`" in uat306_report
    assert "`UAT3.1 is blocked`" in uat306_report
    assert "Actual sandbox order submission is not approved" in uat306_report
    assert "Paper trading is not approved" in uat306_report
    assert "Live trading is not approved" in uat306_report

    assert "UAT3.1 First Sandbox Order Attempt" in uat31_report
    assert "Approval text presence: `verified`" in uat31_report
    assert "Order attempt count | `1`" in uat31_report
    assert "Order status | `rejected`" in uat31_report
    assert "hyperliquid_testnet_user_or_api_wallet_not_found" in uat31_report
    assert "Cancel status | `not_required`" in uat31_report
    assert "Reconciliation status | `completed`" in uat31_report
    assert "OrderIntent | `false`" in uat31_report
    assert "PreparedVenueOrder | `false`" in uat31_report
    assert "SubmittedOrder | `false`" in uat31_report
    assert "Executable approval | `false`" in uat31_report
    assert "`UAT3.2 additional sandbox lifecycle testing may be scoped`" in uat31_report
    assert "Paper trading is not approved" in uat31_report
    assert "Live trading is not approved" in uat31_report

    assert "UAT3.2 Second Sandbox Order Attempt" in uat32_report
    assert "Approval text presence: `verified`" in uat32_report
    assert "Fixed-Key Account / API-Wallet Readiness" in uat32_report
    assert "Status: `blocked`" in uat32_report
    assert "Order attempt count | `0`" in uat32_report
    assert "Order status | `blocked`" in uat32_report
    assert "hyperliquid_testnet_user_not_found" in uat32_report
    assert "hyperliquid_testnet_api_wallet_not_found" in uat32_report
    assert "sandbox_account_equity_insufficient" in uat32_report
    assert "OrderIntent | `false`" in uat32_report
    assert "PreparedVenueOrder | `false`" in uat32_report
    assert "SubmittedOrder | `false`" in uat32_report
    assert "Executable approval | `false`" in uat32_report
    assert "`UAT3.3 is blocked`" in uat32_report
    assert "UAT4.0 — Live UAT Trading Dashboard / Chart Cockpit" in uat32_report
    assert "Paper trading is not approved" in uat32_report
    assert "Live trading is not approved" in uat32_report

    assert "UAT3.3 Hyperliquid Account Targeting Precision And Order Attempt" in uat33_report
    assert "Approval text presence: `verified`" in uat33_report
    assert "Normal master/user account mode omits `vaultAddress`" in uat33_report
    assert "Subaccount/vault mode uses `vaultAddress` only for the explicit subaccount/vault target" in uat33_report
    assert "Price formatting enforces up to five significant figures" in uat33_report or "five significant figures" in uat33_report
    assert "ETH" in uat33_report
    assert "Order attempt count | `1`" in uat33_report
    assert "Order status | `rejected`" in uat33_report
    assert "Order must have minimum value of $10. asset=4" in uat33_report
    assert "Successful Follow-Up Sandbox Lifecycle" in uat33_report
    assert "order accepted open" in uat33_report
    assert "Cancel response: `success`" in uat33_report
    assert "OrderIntent | `false`" in uat33_report
    assert "PreparedVenueOrder | `false`" in uat33_report
    assert "SubmittedOrder | `false`" in uat33_report
    assert "Executable approval | `false`" in uat33_report
    assert "`UAT3.4 additional sandbox lifecycle testing may be scoped`" in uat33_report
    assert "Paper trading" in uat33_report
    assert "Live trading" in uat33_report

    assert "UAT3.4 Sandbox Routing Pipeline And Order Ledger" in uat34_report
    assert "UAT3.4 operationalizes the successful sandbox route" in uat34_report
    assert "standard_perp_clearinghouse" in uat34_report
    assert "unified_margin_spot_clearinghouse" in uat34_report
    assert "fixed_target_hyperliquid_testnet_eth" in uat34_report
    assert "| uat3_4_sandbox_routing_pipeline_order_ledger | fixed_target_hyperliquid_testnet_eth" in uat34_report
    assert "| UAT3.4 lifecycle attempts | `1` |" in uat34_report
    assert "| Order endpoint calls | `1` |" in uat34_report
    assert "| Cancel endpoint calls | `1` |" in uat34_report
    assert "Top-20 order submission: `false`" in uat34_report
    assert "Live endpoint used: `false`" in uat34_report
    assert "Paper trading: `not approved`" in uat34_report
    assert "Live trading: `not approved`" in uat34_report
    assert "UAT4.0 live UAT dashboard/chart cockpit is complete" in uat34_report
    assert "UAT3.5 is blocked" in uat34_report

    assert "UAT4.0 Live UAT Dashboard / Chart Cockpit" in uat40_report
    assert "UAT4.0 is dashboard/chart cockpit only" in uat40_report
    assert "UAT Chart Cockpit" in uat40_report
    assert "Routed Orders" in uat40_report
    assert "fixed_target_hyperliquid_testnet_eth" in uat40_report
    assert "Paper trading is not approved" in uat40_report
    assert "Live trading is not approved" in uat40_report
    assert "No private/signed/order endpoints" in uat40_report

    assert "UAT4.1 Exchange-Style Dashboard Redesign" in uat41_report
    assert "UAT4.1 is dashboard redesign only" in uat41_report
    assert "exchange-style UAT workstation" in uat41_report
    assert "DESIGN.md Replacement Status" in uat41_report
    assert "Routed Orders" in uat41_report
    assert "no order controls" in uat41_report
    assert "Paper trading is not approved" in uat41_report
    assert "Live trading is not approved" in uat41_report

    assert "UAT4.2 Live Market Dashboard + Paper-Equity Runtime Monitor" in uat42_report
    assert "Live public market data service" in uat42_report
    assert "Internal 10,000 USDC Paper-Equity Ledger" in uat42_report
    assert "60-second sandbox private-read-only polling policy" in uat42_report
    assert "No-Order-Control Confirmation" in uat42_report
    assert "PT0 has superseded the prior roadmap-only PT0 state" in uat42_report
    assert "does not submit orders" in uat42_report
    assert "Live trading is not approved" in uat42_report
    assert "PT0 TradingView Charts + Top-20 Paper/Sandbox Runtime Foundation" in pt0_report
    assert "PAPER TRADING IS APPROVED." in pt0_report
    assert "BROADER TOP-20 HYPERLIQUID-SUPPORTED PAPER/SANDBOX TRADING IS APPROVED." in pt0_report
    assert "TradingView Lightweight Charts" in pt0_report
    assert "Live trading is not approved" in pt0_report
    assert "PT0.1 — Supervised Top-20 Paper/Sandbox Runtime Week" in pt0_report
    assert "PT0.0.1 TradingView Chart Stability Hotfix" in pt001_report
    assert "The page/chart scrolled or grew downward" in pt001_report
    assert "stable bounded container height" in pt001_report
    assert "PT0.0.1 does not change PT0 paper-equity math" in pt0_report
    assert "Live trading is not approved" in pt001_report
    assert "Orders submitted by PT0.0.1 | `verified: false`" in pt001_report
    assert "PT0.0.2 Historical Strategy Replay Cockpit" in pt002_report
    assert "Hyperliquid testnet market data is not strategy truth" in pt002_report
    assert "Historical/mainnet candle data is strategy truth" in pt002_report
    assert "No orders are submitted by PT0.0.2" in pt002_report
    assert "Money Flow rules are unchanged" in pt002_report
    assert "PT0.0.3 Historical Data Horizon + 1D Replay Support" in pt003_report
    assert "2025-01-01T00:00:00Z" in pt003_report
    assert "1D candles aggregated from 4h historical replay candles" in pt003_report
    assert "Hyperliquid testnet market data is not strategy truth" in pt003_report
    assert "No orders were submitted" in pt003_report
    assert "Money Flow rules are unchanged" in pt003_report
    assert "SV2.0 Historical Data Refresh + 1D + Expanded Universe Readiness" in sv20_readiness_report
    assert "SV2.0 Money Flow 1D Sleeve + Expanded Universe Evidence Rebuild" in sv20_evidence_report
    assert "Money Flow v1.2" in sv20_evidence_report
    assert "sleeve_1d" in sv20_evidence_report
    assert "SHIB | kSHIB" in sv20_readiness_report
    assert "Hyperliquid public mainnet" in sv20_readiness_report
    assert "Testnet market data is not strategy truth" in sv20_evidence_report
    assert "No orders were submitted" in sv20_readiness_report
    assert "SV2.0.1 Canonical Evidence Truth Hotfix" in sv201_report
    assert "compact_replay_rows_not_canonical_evidence" in sv201_report
    assert "canonical_sv2_evidence_packs_missing" in sv201_report
    assert "db_imported = false" in sv201_report
    assert "Live trading is not approved" in sv201_report

    for note in current_notes:
        assert "UAT0" in note
        assert "UAT0.1" in note
        assert "UAT0.2" in note
        assert "UAT0.3" in note
        assert "UAT1 public read-only connectivity" in note
        assert "UAT1.1" in note
        assert "complete" in note.lower()
        assert "UAT2" in note
        assert "complete" in note.lower()
        assert "UAT3" in note
        assert "UAT3.0.6" in note
        assert "UAT3.1" in note
        assert "UAT3.2" in note
        assert "UAT3.3" in note
        assert "UAT4.0" in note
        assert "UAT4.1" in note
        assert "UAT4.2" in note
        assert "PT0.0.1" in note
        assert "PT0.0.2" in note
        assert "PT0.0.3" in note
        assert _has_paper_boundary(note)
        assert "Live trading is not approved" in note
        assert (
            "Exchange order submission is not approved" in note
            or "Additional exchange order submission is not approved" in note
            or "Live exchange order submission is not approved" in note
        )
    for note in current_notes[:4]:
        assert "SV2.0" in note
        assert "SV2.0.1" in note


def test_current_phase_handoff_and_coordination_are_closed() -> None:
    coordination_row = _coordination_row_for("SV1.18 evidence credibility closeout")
    command_center = Path("money-flow/00_Money_Flow_Command_Center.md").read_text()
    current_phase = Path("money-flow/01_Current_Phase.md").read_text()
    current_dashboard = Path("money-flow/00 Maps/Current State Dashboard.md").read_text()

    assert "| done " in coordination_row
    assert "| active " not in coordination_row
    assert "In progress" not in coordination_row
    assert "commit `f55a17d`" in coordination_row.lower()
    assert "/Users/tercirafael/money-flow-sv1.18-review.zip" in coordination_row

    for note in (command_center, current_phase, current_dashboard):
        assert "SV1.18" in note
        assert "SV2.0" in note
        assert "UAT0" in note
        assert _has_paper_boundary(note)
        assert "Live trading is not approved" in note
        assert (
            "Exchange order submission is not approved" in note
            or "Additional exchange order submission is not approved" in note
            or "Live exchange order submission is not approved" in note
        )
        assert "plumbing and behavior validation" in note
        assert "Hyperliquid ETH" in note
        assert "sleeve_1h" in note
        assert "current baseline" in note.lower()


def test_changelog_has_versioned_entries() -> None:
    changelog = Path("CHANGELOG.md").read_text()
    versions = re.findall(r"## v\d{4}\.\d{2}\.\d{2}\.\d{3}", changelog)
    timestamps = re.findall(r"`\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z`", changelog)
    assert len(versions) >= 7
    assert len(timestamps) >= 7


def test_archiveignore_excludes_local_review_artifacts() -> None:
    archiveignore = Path(".archiveignore")
    assert archiveignore.exists()
    contents = archiveignore.read_text()
    for name in [
        ".env",
        ".pgdata",
        ".pgsocket",
        ".venv",
        ".pytest_cache",
        ".DS_Store",
        "*.zip",
        "reports/strategy_validation",
        "reports/strategy_validation_reviews",
        "reports/strategy_validation_imports",
        "data/strategy_validation/imports",
        "data/strategy_validation/candles",
    ]:
        assert name in contents


def test_review_bundle_excludes_local_artifacts(tmp_path: Path) -> None:
    output_path = tmp_path / "money-flow-review.zip"
    create_review_bundle(source_dir=Path.cwd(), output_path=output_path)

    assert output_path.exists()
    with zipfile.ZipFile(output_path) as archive:
        names = archive.namelist()

    assert names
    forbidden_prefixes = [
        ".venv/",
        ".pgdata/",
        ".pgsocket/",
        ".pytest_cache/",
        "money-flow/.obsidian/",
        "__MACOSX/",
    ]
    forbidden_names = {".DS_Store"}

    for name in names:
        assert name != ".env"
        assert all(not name.startswith(prefix) for prefix in forbidden_prefixes)
        assert Path(name).name not in forbidden_names


def test_canonical_docs_do_not_reference_deleted_draft_docs() -> None:
    stale_doc_names = [
        "architecture_updated.md",
        "architecture_preserve_refresh.md",
        "strategy_updated.md",
        "strategy_preserve_refresh.md",
    ]
    guarded_files = [
        "docs/architecture.md",
        "docs/strategy.md",
        "REPO_TREE.md",
        "CHANGELOG.md",
    ]

    for relative_path in guarded_files:
        contents = Path(relative_path).read_text()
        for stale_name in stale_doc_names:
            assert stale_name not in contents, f"{relative_path} still references deleted draft doc {stale_name}"


def test_canonical_docs_describe_private_state_boundary_truth() -> None:
    readme = Path("README.md").read_text()
    architecture = Path("docs/architecture.md").read_text()
    strategy = Path("docs/strategy.md").read_text()

    assert "adapter/runtime" in readme
    assert "adapter/runtime" in architecture
    assert "adapter/runtime" in strategy
    assert "venue-private open-order" in readme
    assert "venue-private open-order" in architecture
    assert "SubmittedOrder" in readme
    assert "SubmittedOrder" in architecture
