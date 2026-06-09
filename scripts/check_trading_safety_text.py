"""Scan tracked source files for positive live/production/order-approval language.

Exits non-zero if any violation is found. Negation-aware and label-aware:
- Allows lines that contain negation phrases ("not approved", "not production-approved", etc.)
- Allows lines that are clearly UI column header/value elements (text inside >…<)
- Allows Python string literals that are part of forbidden-phrase *lists* (the phrase
  appears quoted-and-isolated on its own line, used to guard reports from false positives)
- Allows Markdown table cells whose value is "No" or "**No**"

Usage:
    python scripts/check_trading_safety_text.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_SCAN_TARGETS = [
    ".env.example",
    "apps/dashboard",
    "services",
    "scripts",
    "CURRENT_TRUTH.md",
    "money-flow/01_Current_Phase.md",
]

_INCLUDE_EXTENSIONS = {".py", ".js", ".html", ".css", ".md", ".json", ".toml", ".example", ""}

_VIOLATION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "live_trading_enabled_true",
        re.compile(r"LIVE_TRADING_ENABLED\s*=\s*true", re.IGNORECASE),
    ),
    (
        "exchange_allow_live_mode_true",
        re.compile(r"EXCHANGE_ALLOW_LIVE_MODE_WITHOUT_API_KEY\s*=\s*true", re.IGNORECASE),
    ),
    (
        "approved_for_live",
        re.compile(r"approved\s+for\s+live", re.IGNORECASE),
    ),
    (
        "live_trading_is_approved",
        re.compile(r"live\s+trading\s+is\s+approved", re.IGNORECASE),
    ),
    (
        "production_approved_prose",
        re.compile(r"production[- ]approved", re.IGNORECASE),
    ),
    (
        "candidate_testnet_eligible",
        re.compile(r"candidate\s+(lane\s+)?testnet\s+eligible", re.IGNORECASE),
    ),
    (
        "mf_orig_testnet_eligible",
        re.compile(r"mf.?orig\s+testnet\s+eligible", re.IGNORECASE),
    ),
    (
        "live_submission_enabled_true",
        re.compile(r"EXECUTION_LIVE_SUBMISSION_PHASE_ENABLED\s*=\s*true", re.IGNORECASE),
    ),
]

# If ANY of these match the line, the line is considered a negation → skip
_NEGATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bnot\s+(production[- ])?approved\b", re.IGNORECASE),
    re.compile(r"\bno\s+strategy\b", re.IGNORECASE),
    re.compile(r"\bis\s+not\s+approved\b", re.IGNORECASE),
    re.compile(r"\bnever\s+approved\b", re.IGNORECASE),
    re.compile(r"\bremains\s+not\s+approved\b", re.IGNORECASE),
    re.compile(r"\bdoes\s+not\s+approve\b", re.IGNORECASE),
    re.compile(r"\bevidence.only\b", re.IGNORECASE),
    # Markdown table with explicit "No" value in same cell or adjacent cell
    re.compile(r"\|\s*\*{0,2}No\*{0,2}\s*\|", re.IGNORECASE),
    re.compile(r"\*\*No\*\*", re.IGNORECASE),
    # "not production-approved" compound (covers adjacent negation)
    re.compile(r"not\s+production", re.IGNORECASE),
    # "No strategy was production-approved", "no production approval"
    re.compile(r"\bno\s+(live|production|strategy|real)\b", re.IGNORECASE),
    # HTML span with "not" before approval phrase
    re.compile(r"not\s+production.approved", re.IGNORECASE),
]


# A match is label-only when the violation phrase is the whole content of a markup element
def _is_label_only(line: str, match: re.Match[str]) -> bool:
    before = line[: match.start()].rstrip()
    after = line[match.end() :].lstrip()
    return before.endswith(">") and after.startswith("<")


# A Python string literal on its own quoted line appearing in a FORBIDDEN_WORDS tuple.
# These tuples are used by report validators to detect bad language — not positive approvals.
_ISOLATED_QUOTED_LINE = re.compile(r'^\s*["\']([^"\']+)["\']\s*,?\s*$')


def _is_forbidden_phrase_list_item(line: str, match_text: str) -> bool:
    """True when the entire line is an isolated quoted string (Python tuple element)."""
    m = _ISOLATED_QUOTED_LINE.match(line)
    if m:
        content = m.group(1).strip()
        return content.lower() == match_text.lower()
    return False


def _is_negated(line: str) -> bool:
    return any(p.search(line) for p in _NEGATION_PATTERNS)


def _should_scan(path: Path) -> bool:
    suffix = path.suffix.lower()
    return suffix in _INCLUDE_EXTENSIONS or path.stem.startswith(".env")


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    violations: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if _is_negated(line):
            continue
        for name, pattern in _VIOLATION_PATTERNS:
            m = pattern.search(line)
            if not m:
                continue
            if _is_label_only(line, m):
                continue
            match_text = m.group(0)
            if _is_forbidden_phrase_list_item(line, match_text):
                continue
            violations.append((lineno, name, line.strip()))
    return violations


def scan_targets(repo_root: Path = REPO_ROOT) -> dict[Path, list[tuple[int, str, str]]]:
    results: dict[Path, list[tuple[int, str, str]]] = {}
    for target_str in _SCAN_TARGETS:
        target = repo_root / target_str
        if target.is_file():
            paths = [target]
        elif target.is_dir():
            paths = [p for p in target.rglob("*") if p.is_file()]
        else:
            continue
        for path in sorted(paths):
            if not _should_scan(path):
                continue
            hits = scan_file(path)
            if hits:
                results[path] = hits
    return results


def main() -> int:
    results = scan_targets()
    if not results:
        print("OK: no trading-safety text violations found.")
        return 0
    print("FAIL: trading-safety text violations found:\n")
    for path, hits in sorted(results.items()):
        rel = path.relative_to(REPO_ROOT)
        for lineno, name, line in hits:
            print(f"  {rel}:{lineno} [{name}]  {line[:120]}")
    print(
        "\nEach flagged line contains positive live/production/order-approval language "
        "not recognized as a negation or UI label."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
