"""Lightweight secret hygiene scan of committed files.

Fails on obvious key material: PEM private key blocks, bearer token values,
signing keys with non-empty non-placeholder values in env examples.

This is NOT a substitute for professional secret scanning (e.g. truffleHog,
gitleaks). It catches the most obvious patterns only. See KNOWN_ISSUES.md K-029.

Usage:
    python scripts/check_secret_hygiene.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Excluded from all scanning to prevent self-matching on regex patterns / test fixtures.
_SKIP_PATHS: frozenset[Path] = frozenset(
    {
        Path(__file__).resolve(),
        Path(__file__).resolve().parent.parent / "tests" / "test_secret_hygiene.py",
    }
)

# Directories (relative to repo root) where _KEY_VALUE_PATTERNS are not applied.
# Test fixtures reference key names in function calls and variable bindings — not real secrets.
_KV_SKIP_DIRS: frozenset[str] = frozenset({"tests"})

# Files / dirs to scan
_SCAN_TARGETS = [
    ".env.example",
    "apps",
    "core",
    "services",
    "scripts",
    "configs",
    "docs",
    "tests",
    "CURRENT_TRUTH.md",
    "AGENTS.md",
    "README.md",
]

_INCLUDE_EXTENSIONS = {
    ".py",
    ".js",
    ".html",
    ".md",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".example",
    "",
}

# Placeholder markers accepted for key fields (not real secrets)
_PLACEHOLDER_MARKERS = (
    "",  # empty / blank
    "replace_me",
    "your_key_here",
    "your_secret_here",
    "<your",
    "CHANGE_ME",
    "PLACEHOLDER",
    "TODO",
    "example",
    "test",
    "fake",
    "dummy",
)

_PEM_BLOCK = re.compile(r"-----BEGIN\s+[A-Z ]+PRIVATE KEY-----", re.IGNORECASE)
# Require first segment to start with an alphanumeric char so `Bearer ...` (redaction marker)
# and similar documentation placeholders do not match.
_BEARER_TOKEN = re.compile(
    r"[Aa]uthorization:\s*Bearer\s+[A-Za-z0-9][A-Za-z0-9\-_\.]*\.[A-Za-z0-9\-_\.]+"
)

# Key-value patterns where the VALUE must not be non-empty and non-placeholder
_KEY_VALUE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("signing_private_key", re.compile(r"EXCHANGE_SIGNING_PRIVATE_KEY=(.+)", re.IGNORECASE)),
    (
        "jwt_private_key_pem",
        re.compile(r"COINBASE_ADVANCED_JWT_PRIVATE_KEY_PEM=(.+)", re.IGNORECASE),
    ),
    (
        "hyperliquid_uat_private_key",
        re.compile(r"HYPERLIQUID_UAT_SANDBOX_PRIVATE_KEY=(.+)", re.IGNORECASE),
    ),
]


def _looks_like_placeholder(value: str) -> bool:
    v = value.strip()
    if not v:
        return True
    v_lower = v.lower()
    return any(marker.lower() in v_lower for marker in _PLACEHOLDER_MARKERS if marker)


def _should_scan(path: Path) -> bool:
    suffix = path.suffix.lower()
    name = path.name.lower()
    return suffix in _INCLUDE_EXTENSIONS or name.startswith(".env")


def scan_file(path: Path, *, skip_kv_patterns: bool = False) -> list[tuple[int, str, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    violations: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        # PEM private key block
        if _PEM_BLOCK.search(line):
            violations.append((lineno, "pem_private_key_block", line.strip()[:100]))
        # Bearer token with a non-trivial value
        if _BEARER_TOKEN.search(line):
            violations.append((lineno, "bearer_token_value", line.strip()[:100]))
        # Key-value patterns with non-placeholder values (skipped for test dirs)
        if not skip_kv_patterns:
            for name, pattern in _KEY_VALUE_PATTERNS:
                m = pattern.search(line)
                if m:
                    value = m.group(1).strip()
                    if not _looks_like_placeholder(value):
                        violations.append((lineno, name, "<value present — not shown>"))
    return violations


def scan_targets(repo_root: Path = REPO_ROOT) -> dict[Path, list[tuple[int, str, str]]]:
    results: dict[Path, list[tuple[int, str, str]]] = {}
    for target_str in _SCAN_TARGETS:
        target = repo_root / target_str
        skip_kv = target_str in _KV_SKIP_DIRS or target_str.split("/")[0] in _KV_SKIP_DIRS
        if target.is_file():
            paths = [target]
        elif target.is_dir():
            paths = [p for p in target.rglob("*") if p.is_file()]
        else:
            continue
        for path in sorted(paths):
            if not _should_scan(path):
                continue
            if path in _SKIP_PATHS:
                continue
            hits = scan_file(path, skip_kv_patterns=skip_kv)
            if hits:
                results[path] = hits
    return results


def main() -> int:
    results = scan_targets()
    if not results:
        print("OK: no obvious secret material found.")
        print(
            "NOTE: This is a lightweight check only — not a substitute for professional scanning."
        )
        return 0
    print("FAIL: possible secret material found:\n")
    for path, hits in sorted(results.items()):
        rel = path.relative_to(REPO_ROOT)
        for lineno, name, line in hits:
            print(f"  {rel}:{lineno} [{name}]  {line}")
    print(
        "\nThis is a lightweight check. Replace any real secret with a placeholder "
        "such as 'replace_me_do_not_commit_real_key' and re-run."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
