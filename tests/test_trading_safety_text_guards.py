"""Tests for the trading-safety text guard script.

Verifies: negation-aware logic, label-only false-positive handling,
forbidden-phrase-list-item skip, and that the scanner is clean on the
actual repo sources.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from scripts.check_trading_safety_text import scan_file, scan_targets

# ---------------------------------------------------------------------------
# scan_file unit tests (using tmp_path fixtures)
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def test_plain_approval_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "bad.py", "print('live trading is approved for ETH')\n")
    assert scan_file(p)


def test_negation_not_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "ok.py", "assert live trading is not approved\n")
    assert not scan_file(p)


def test_not_production_approved_not_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "ok.html", "<span>not production-approved</span>\n")
    assert not scan_file(p)


def test_evidence_only_not_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "ok.py", "# This lane is evidence-only and not production-approved\n")
    assert not scan_file(p)


def test_label_only_markup_not_flagged(tmp_path: Path) -> None:
    # Entire text content of element is the forbidden phrase — false positive
    p = _write(tmp_path, "ok.html", "<th>Production Approved</th>\n")
    assert not scan_file(p)


def test_span_label_with_dynamic_value_not_flagged(tmp_path: Path) -> None:
    # <span>Production approved</span><strong>No</strong>
    p = _write(
        tmp_path,
        "ok.html",
        "<span>Production approved</span><strong>No</strong>\n",
    )
    assert not scan_file(p)


def test_markdown_table_no_value_not_flagged(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        "ok.md",
        "| Production approved | **No** | `settings.py` |\n",
    )
    assert not scan_file(p)


def test_forbidden_phrase_list_item_not_flagged(tmp_path: Path) -> None:
    # Python string in a forbidden-words tuple
    content = """\
    FORBIDDEN = (
        "proven",
        "approved for live",
        "guaranteed",
    )
    """
    p = _write(tmp_path, "ok.py", content)
    assert not scan_file(p)


def test_live_trading_enabled_true_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "bad.env", "LIVE_TRADING_ENABLED=true\n")
    assert scan_file(p)


def test_exchange_allow_live_mode_true_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path, "bad.env", "EXCHANGE_ALLOW_LIVE_MODE_WITHOUT_API_KEY=true\n")
    assert scan_file(p)


def test_no_strategy_was_flagged_correctly_negated(tmp_path: Path) -> None:
    p = _write(tmp_path, "ok.py", '"- No strategy was production-approved.",\n')
    assert not scan_file(p)


# ---------------------------------------------------------------------------
# Full repo scan must be clean
# ---------------------------------------------------------------------------


def test_repo_scan_clean() -> None:
    results = scan_targets()
    violations: list[str] = []
    repo_root = Path(__file__).resolve().parent.parent
    for path, hits in sorted(results.items()):
        rel = path.relative_to(repo_root)
        for lineno, name, line in hits:
            violations.append(f"{rel}:{lineno} [{name}] {line[:100]}")
    assert not violations, "Trading-safety text violations found in repo:\n" + "\n".join(violations)
