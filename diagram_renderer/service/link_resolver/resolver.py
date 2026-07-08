"""Default link resolver: repo-relative path matching."""

from __future__ import annotations

import logging
from pathlib import Path

from diagram_renderer.service.graph import RawLink

logger = logging.getLogger(__name__)


class LinkResolver:
    """Map RawLink objects to node ids."""

    def __init__(self, repo_root: Path, node_ids: set[str], on_unresolved: str) -> None:
        self.repo_root = repo_root
        self.node_ids = node_ids
        self.on_unresolved = on_unresolved

    def resolve(self, source_path: Path, link: RawLink) -> str | None:
        """Return the node id for *link* or None if unresolved/skipped."""
        target_rel = link.path_part()
        target_path = (self.repo_root / target_rel).resolve()

        if not target_path.exists():
            logger.warning(
                "Link in '%s' points to non-existent file '%s'; skipping",
                source_path,
                target_rel,
            )
            return None

        target_id = target_path.relative_to(self.repo_root).as_posix()
        if target_id in self.node_ids:
            return target_id

        if self.on_unresolved == "stub":
            logger.info(
                "Creating stub node for external link '%s' from '%s'",
                target_rel,
                source_path,
            )
            return target_id

        logger.warning(
            "Link in '%s' points to '%s' which is outside the source set; skipping",
            source_path,
            target_rel,
        )
        return None
