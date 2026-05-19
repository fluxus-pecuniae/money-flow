from __future__ import annotations

from pathlib import Path
import tomllib


AGENTS = {
    "runtime_reviewer": {
        "required_phrases": [
            "candle-close scheduling",
            "warm-start gate",
            "synthetic ledger",
            "testnet lifecycle",
        ],
    },
    "dashboard_reviewer": {
        "required_phrases": [
            "Paper Trading",
            "active vs archived rows",
            "testnet lifecycle separation",
        ],
    },
    "quant_reviewer": {
        "required_phrases": [
            "rsi_overbought_then_late_entry",
            "lane comparison",
            "production approval",
        ],
    },
}


def _load_agent(name: str) -> dict[str, object]:
    path = Path(f".codex/agents/{name}.toml")
    assert path.exists(), f"Missing agent config: {path}"
    return tomllib.loads(path.read_text())


def test_codex_subagent_toml_files_exist_and_are_named_correctly() -> None:
    for name in AGENTS:
        data = _load_agent(name)
        assert data["name"] == name
        assert data["description"]
        assert data["developer_instructions"]


def test_codex_subagents_keep_read_only_no_live_no_production_boundaries() -> None:
    for name in AGENTS:
        data = _load_agent(name)
        instructions = str(data["developer_instructions"])
        lowered = instructions.lower()
        assert "read-only" in lowered
        assert "live trading" in lowered and "not approved" in lowered
        assert "not production-approved" in lowered or "no strategy is production-approved" in lowered
        assert "never submit orders" in lowered or "do not add order controls" in lowered or "do not approve any strategy" in lowered
        assert data.get("sandbox_mode") == "read-only"


def test_codex_subagents_include_role_specific_guardrails() -> None:
    for name, spec in AGENTS.items():
        instructions = str(_load_agent(name)["developer_instructions"])
        for phrase in spec["required_phrases"]:
            assert phrase in instructions


def test_codex_subagent_workflow_docs_and_repo_docs_reference_agents() -> None:
    workflow_doc = Path("docs/codex_subagents_money_flow_workflow.md")
    report_doc = Path("docs/subagents1_money_flow_codex_workflow.md")
    summary_json = Path("docs/subagents1_money_flow_codex_workflow_summary.json")
    agents_doc = Path("AGENTS.md").read_text()
    readme = Path("README.md").read_text()

    assert workflow_doc.exists()
    assert report_doc.exists()
    assert summary_json.exists()

    workflow_text = workflow_doc.read_text()
    for name in AGENTS:
        assert name in workflow_text
        assert name in agents_doc
        assert name in readme

    assert "docs/codex_subagents_money_flow_workflow.md" in readme
    assert "Codex Subagents" in agents_doc


def test_codex_subagent_config_limits_parallelism() -> None:
    config_path = Path(".codex/config.toml")
    assert config_path.exists()
    config = tomllib.loads(config_path.read_text())
    assert config["agents"]["max_threads"] == 3
    assert config["agents"]["max_depth"] == 1
