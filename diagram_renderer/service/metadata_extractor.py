"""Extract node metadata from markdown files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from diagram_renderer.service.graph import MetadataConfig, NodeMetadata

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract stable node id, label and subpath from a markdown file."""

    def __init__(self, repo_root: Path, config: MetadataConfig) -> None:
        self.repo_root = repo_root
        self.config = config

    def extract(self, path: Path, frontmatter: dict[str, Any] | None) -> NodeMetadata:
        """Return NodeMetadata for *path*.

        The node id is the repo-relative path (forward slashes). The label is
        taken from *frontmatter* using the configured label field; if missing,
        the file stem is used.
        """
        node_id = path.relative_to(self.repo_root).as_posix()
        label = self._extract_label(path, frontmatter)
        return NodeMetadata(id=node_id, label=label, subpath=self.config.subpath)

    def _extract_label(self, path: Path, frontmatter: dict[str, Any] | None) -> str:
        if frontmatter and isinstance(frontmatter, dict):
            label = frontmatter.get(self.config.label_field)
            if isinstance(label, str) and label:
                return label
        logger.debug(
            "Label field '%s' missing in '%s'; using file stem",
            self.config.label_field,
            path,
        )
        return path.stem
