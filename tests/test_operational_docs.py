from __future__ import annotations

from pathlib import Path
import re
import zipfile

from scripts.create_review_bundle import create_review_bundle


REQUIRED_FILES = [
    "AGENTS.md",
    "CHANGELOG.md",
    "REPO_TREE.md",
    "KNOWN_ISSUES.md",
    "TODO.md",
    "money_flow_project_memory.md",
    "money-flow/00_Money_Flow_Command_Center.md",
    "money-flow/01_Current_Phase.md",
    "money-flow/03_Decision_Log.md",
    "money-flow/05_Agent_Coordination.md",
    "money-flow/Project_Memory/money_flow_project_memory.md",
    "README.md",
    "docs/architecture.md",
    "docs/investors.md",
    "docs/strategy_validation_sv1_7_first_evidence_review.md",
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

    assert "required Obsidian brain entrypoint" in command_center
    assert re.search(r"Current implemented phase: `SV1\.7`", current_phase)
    assert "SV1.7" in command_center
    assert "Active Work" in coordination
    assert "Quant Engineer" in moved_memory
    assert "canonical strategic project memory has moved" in root_pointer
    assert "The original starting point" not in root_pointer


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
    for name in [".env", ".pgdata", ".pgsocket", ".venv", ".pytest_cache", ".DS_Store", "*.zip"]:
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
