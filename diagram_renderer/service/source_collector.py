"""Collect markdown source files for a render task."""

from __future__ import annotations

import logging
from pathlib import Path

from diagram_renderer.functions.files import collect_files
from diagram_renderer.functions.hashing import hash_file_set
from diagram_renderer.service.graph import SourceConfig

logger = logging.getLogger(__name__)


class SourceCollector:
    """Collect and hash source files."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def collect(self, config: SourceConfig) -> tuple[list[Path], str]:
        """Return sorted absolute paths and a deterministic hash of the file set."""
        files = collect_files(
            include=list(config.include),
            exclude=list(config.exclude),
            repo_root=self.repo_root,
        )
        logger.info("Collected %d source files", len(files))
        if not files:
            logger.warning("No source files matched the include/exclude patterns")
        file_set_hash = hash_file_set(files, self.repo_root)
        return files, file_set_hash
