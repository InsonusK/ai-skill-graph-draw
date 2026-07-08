"""Default metadata extractor: repo-relative path id + file stem label."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from diagram_renderer.service.graph import MetadataConfig, NodeMetadata


class MetadataExtractor:
    """Extract stable node id, label and subpath from a markdown file."""

    def __init__(self, repo_root: Path, config: MetadataConfig) -> None:
        self.repo_root = repo_root
        self.config = config

    def extract(self, path: Path, frontmatter: dict[str, Any] | None) -> NodeMetadata:
        """Return NodeMetadata for *path*.

        The node id is the repo-relative path (forward slashes). The label is
        the file stem. The subpath is taken from the task configuration.
        """
        node_id = path.relative_to(self.repo_root).as_posix()
        return NodeMetadata(
            id=node_id,
            label=path.stem,
            subpath=self.config.subpath,
        )
