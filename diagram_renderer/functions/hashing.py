"""Deterministic hashing helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def hash_text(text: str) -> str:
    """Return SHA-256 hex digest of *text*."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_file_set(files: list[Path], repo_root: Path) -> str:
    """Return a deterministic hash of a file set based on relative paths and mtimes.

    Args:
        files: Sorted list of absolute file paths.
        repo_root: Root used to compute relative paths.
    """
    entries: list[dict[str, Any]] = []
    for file in files:
        rel = file.relative_to(repo_root).as_posix()
        mtime = file.stat().st_mtime
        entries.append({"path": rel, "mtime": mtime})

    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return hash_text(canonical)


def hash_node_content(frontmatter: dict[str, Any], raw_links: list[tuple[str, str]]) -> str:
    """Return a deterministic hash of node-relevant content.

    Args:
        frontmatter: Parsed frontmatter dict.
        raw_links: List of (filter_name, link_text) tuples, already sorted.
    """
    canonical = json.dumps(
        {"frontmatter": frontmatter, "raw_links": raw_links},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hash_text(canonical)
