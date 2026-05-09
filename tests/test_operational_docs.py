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
    assert "`UAT0` safety / security / runtime audit is complete" in current_phase
    assert "SV1.18" in command_center
    assert "UAT0" in command_center
    assert "UAT1 is blocked" in command_center
    assert "Active Work" in coordination
    assert "Founder Vision" in moved_memory
    assert "Strategy Validation" in moved_memory
    assert "SV1.18-SV1.18.1" in moved_memory
    assert "money_flow_hyperliquid_eth_1h_baseline_uat_candidate" in moved_memory
    assert "Paper trading is not approved" in moved_memory
    assert "UAT1 is blocked" in moved_memory
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

    assert "Current implemented milestone | `UAT0` safety audit complete" in command_center
    assert "Canonical command center" in compatibility_command_center
    assert "SV1 is closed for now" in current_dashboard
    assert "UAT1 is blocked" in current_dashboard
    assert "Strategy Validation is now its own major track" in Path("money-flow/00 Maps/Phase Timeline.md").read_text()
    assert "What Strategy Validation Did" in sv_map
    assert "What Strategy Validation Did Not Prove" in sv_map
    assert "UAT0 - Safety / Security / Runtime Hardening" in uat_roadmap
    assert "UAT1 - Top-20 Universe + Read-Only Venue/Market Metadata" in uat_roadmap
    assert "UAT validates plumbing and behavior" in uat_roadmap
    assert "money_flow_hyperliquid_eth_1h_baseline_uat_candidate" in candidate_freeze
    assert "UAT1 is blocked" in project_memory


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
        assert "Paper trading is not approved" in note
        assert "Live trading is not approved" in note
        assert "Exchange order submission is not approved" in note or "No exchange order submission approved" in note
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


def test_uat0_operational_truth_is_current() -> None:
    report = Path("docs/uat0_safety_security_runtime_hardening.md").read_text()
    current_notes = [
        Path("money-flow/00_Money_Flow_Command_Center.md").read_text(),
        Path("money-flow/01_Current_Phase.md").read_text(),
        Path("money-flow/00 Maps/Current State Dashboard.md").read_text(),
        Path("money-flow/00 Maps/UAT Roadmap.md").read_text(),
        Path("money-flow/40 Operations/UAT0 Safety Runtime Hardening.md").read_text(),
    ]

    assert "UAT1 is blocked" in report
    assert "API authentication / authorization" in report
    assert "top 20 high-volume crypto assets supported by the selected UAT venue/environment" in report
    assert "next_candle_open" in report
    assert "next_candle_close" in report
    assert "same_candle_close_research_only" in report

    for note in current_notes:
        assert "UAT0" in note
        assert "UAT1 is blocked" in note
        assert "Paper trading is not approved" in note
        assert "Live trading is not approved" in note
        assert "Exchange order submission is not approved" in note


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
        assert "SV1.18 is complete" in note
        assert "UAT0" in note
        assert "Paper trading is not approved" in note
        assert "Live trading is not approved" in note
        assert "Exchange order submission is not approved" in note
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
