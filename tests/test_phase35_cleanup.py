from __future__ import annotations

from pathlib import Path

import db.models as orm_models


def test_legacy_deployment_models_are_not_exported_from_active_orm_surface() -> None:
    assert "StrategyDeploymentModel" not in orm_models.__all__
    assert "SleeveDeploymentConfigModel" not in orm_models.__all__
    assert not hasattr(orm_models, "StrategyDeploymentModel")
    assert not hasattr(orm_models, "SleeveDeploymentConfigModel")


def test_env_example_uses_mandate_top_runtime_selection() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")
    assert "ACTIVE_CLIENT_KEY=" in env_example
    assert "ACTIVE_MANDATE_KEY=" in env_example
    assert "ACTIVE_DEPLOYMENT_KEY=" not in env_example


def test_gitignore_excludes_local_repo_artifacts() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    for expected in [".venv/", ".pytest_cache/", ".pgdata/", ".pgsocket/", ".DS_Store"]:
        assert expected in gitignore
