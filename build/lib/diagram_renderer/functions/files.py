"""File-system helpers."""

from __future__ import annotations

import fnmatch
from pathlib import Path


def collect_files(include: list[str], exclude: list[str], repo_root: Path) -> list[Path]:
    """Collect markdown files matching *include* glob patterns, excluding *exclude*.

    Returns a sorted list of absolute paths.
    """
    seen: set[Path] = set()
    result: list[Path] = []

    for pattern in include:
        for path in repo_root.glob(pattern):
            if not path.is_file():
                continue
            abs_path = path.resolve()
            if abs_path in seen:
                continue
            if _is_excluded(abs_path, exclude, repo_root):
                continue
            seen.add(abs_path)
            result.append(abs_path)

    result.sort()
    return result


def _is_excluded(path: Path, exclude_patterns: list[str], repo_root: Path) -> bool:
    rel = path.relative_to(repo_root).as_posix()
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(path.name, pattern):
            return True
    return False
