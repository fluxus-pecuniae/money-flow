"""Tests for the review-bundle hygiene rules defined in .archiveignore.

ArchiveRuleSet.matches() is called in two contexts inside iter_bundle_paths:
  1. On directory paths (relative to repo root) to prune whole subtrees.
  2. On file paths for top-level files that are not inside a pruned directory.

PurePosixPath.match() in Python 3.12 does not support '**'; the actual exclusion
of subtree contents relies on the directory-pruning step in iter_bundle_paths, not on
individual file matching.  Tests here reflect that actual contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.create_review_bundle import ArchiveRuleSet, load_archive_rules

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rules(patterns: list[str]) -> ArchiveRuleSet:
    return ArchiveRuleSet(patterns=tuple(patterns))


# ---------------------------------------------------------------------------
# Directory-level exclusion (how iter_bundle_paths prunes subtrees)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "dir_path",
    [
        ".env",  # top-level file exact match
        ".git",  # exact match
        ".venv",  # exact match
        ".pytest_cache",  # exact match
        ".mypy_cache",  # exact match
        ".ruff_cache",  # exact match
        "reports/paper_runtime",  # exact match with path separator
        "reports/strategy_validation",  # exact match
        "reports/paper_reviews",  # exact match
        "data/strategy_validation/candles",  # exact match
        "money-flow/.obsidian",  # exact match
        "core/__pycache__",  # plain-name match (no '/', no glob)
        "services/exchange/__pycache__",  # plain-name match
    ],
)
def test_archiveignore_excludes_dir(dir_path: str) -> None:
    rules = load_archive_rules(REPO_ROOT)
    assert rules.matches(dir_path), f"Expected {dir_path!r} to be excluded by .archiveignore"


# ---------------------------------------------------------------------------
# File-level exclusion (top-level files matched directly)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "file_path",
    [
        "secrets.zip",
        "bundle.tar",
        "archive.tgz",
        ".DS_Store",
    ],
)
def test_archiveignore_excludes_file(file_path: str) -> None:
    rules = load_archive_rules(REPO_ROOT)
    assert rules.matches(file_path), f"Expected {file_path!r} to be excluded by .archiveignore"


# ---------------------------------------------------------------------------
# Source paths that must be INCLUDED in the bundle
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "CHANGELOG.md",
        "CURRENT_TRUTH.md",
        "current_truth.json",
        "AGENTS.md",
        ".env.example",
        "apps/dashboard/index.html",
        "core/config/settings.py",
        "services/exchange/safety.py",
        "scripts/export_current_truth.py",
        "tests/test_trading_safety_invariants.py",
        "money-flow/01_Current_Phase.md",
        "money-flow/03_Decision_Log.md",
    ],
)
def test_archiveignore_includes_source_path(path: str) -> None:
    rules = load_archive_rules(REPO_ROOT)
    assert not rules.matches(path), f"Expected {path!r} to be included in bundle"


# ---------------------------------------------------------------------------
# ArchiveRuleSet.matches() behaviour contracts
# ---------------------------------------------------------------------------


def test_empty_string_never_matches() -> None:
    rules = _rules([".env", ".git"])
    assert not rules.matches("")


def test_slash_only_never_matches() -> None:
    rules = _rules([".env", ".git"])
    assert not rules.matches("/")


def test_exact_pattern_matches_exact_path() -> None:
    rules = _rules(["reports/paper_runtime"])
    assert rules.matches("reports/paper_runtime")
    assert not rules.matches("reports/paper_runtime_extra")


def test_plain_name_matches_basename_in_nested_dir() -> None:
    # No "/" and no glob chars → matched against path.name anywhere in the tree
    rules = _rules(["__pycache__"])
    assert rules.matches("core/__pycache__")
    assert rules.matches("services/exchange/__pycache__")


def test_plain_name_does_not_match_prefix() -> None:
    rules = _rules(["__pycache__"])
    assert not rules.matches("__pycache__extra")


def test_dotenv_example_not_excluded() -> None:
    rules = load_archive_rules(REPO_ROOT)
    assert not rules.matches(".env.example")


def test_dotenv_excluded() -> None:
    rules = load_archive_rules(REPO_ROOT)
    assert rules.matches(".env")


def test_ds_store_excluded_by_glob() -> None:
    rules = load_archive_rules(REPO_ROOT)
    assert rules.matches(".DS_Store")


def test_zip_excluded_by_glob() -> None:
    rules = load_archive_rules(REPO_ROOT)
    assert rules.matches("review.zip")
    assert rules.matches("some/nested/archive.zip")
