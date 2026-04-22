from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import zipfile


ARCHIVEIGNORE = ".archiveignore"


@dataclass(frozen=True)
class ArchiveRuleSet:
    patterns: tuple[str, ...]

    def matches(self, relative_path: str) -> bool:
        normalized = relative_path.strip("/")
        if not normalized:
            return False
        path = PurePosixPath(normalized)
        for pattern in self.patterns:
            candidate = pattern.strip()
            if not candidate:
                continue
            if path.match(candidate):
                return True
            if "/" not in candidate and not any(char in candidate for char in "*?[]"):
                if path.name == candidate:
                    return True
        return False


def load_archive_rules(source_dir: Path) -> ArchiveRuleSet:
    archiveignore = source_dir / ARCHIVEIGNORE
    if not archiveignore.exists():
        raise FileNotFoundError(f"Missing {ARCHIVEIGNORE} in {source_dir}")
    patterns: list[str] = []
    for raw_line in archiveignore.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return ArchiveRuleSet(patterns=tuple(patterns))


def iter_bundle_paths(source_dir: Path, rules: ArchiveRuleSet) -> list[Path]:
    included: list[Path] = []
    for root, dirnames, filenames in os.walk(source_dir, topdown=True):
        root_path = Path(root)
        kept_dirnames: list[str] = []
        for dirname in sorted(dirnames):
            rel_dir = (root_path / dirname).relative_to(source_dir).as_posix()
            if rules.matches(rel_dir) or rules.matches(f"{rel_dir}/"):
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        for filename in sorted(filenames):
            path = root_path / filename
            relative = path.relative_to(source_dir).as_posix()
            if rules.matches(relative):
                continue
            included.append(path)
    return included


def create_review_bundle(*, source_dir: Path, output_path: Path) -> Path:
    source_dir = source_dir.resolve()
    output_path = output_path.resolve()
    rules = load_archive_rules(source_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_relative: str | None = None
    try:
        output_relative = output_path.relative_to(source_dir).as_posix()
    except ValueError:
        output_relative = None

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in iter_bundle_paths(source_dir, rules):
            if output_relative is not None and path.relative_to(source_dir).as_posix() == output_relative:
                continue
            archive.write(path, arcname=path.relative_to(source_dir).as_posix())
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a clean review bundle using .archiveignore.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path.cwd(),
        help="Repository root to bundle. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination .zip path for the review bundle.",
    )
    args = parser.parse_args()
    create_review_bundle(source_dir=args.source, output_path=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
