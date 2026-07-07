"""Build a Graph from collected files, metadata and resolved links."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from diagram_renderer.functions.frontmatter import parse_frontmatter
from diagram_renderer.functions.hashing import hash_node_content
from diagram_renderer.service.graph import Edge, Graph, LinkFilterConfig, Node, RawLink
from diagram_renderer.service.link_filter import LinkFilter, build_link_filter
from diagram_renderer.service.link_resolver import LinkResolver
from diagram_renderer.service.metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Assemble the task graph."""

    def __init__(
        self,
        repo_root: Path,
        metadata_extractor: MetadataExtractor,
        link_configs: tuple[LinkFilterConfig, ...],
    ) -> None:
        self.repo_root = repo_root
        self.metadata_extractor = metadata_extractor
        self.link_configs = link_configs

    def build(self, files: list[Path]) -> Graph:
        """Build Graph from *files*."""
        # First pass: parse frontmatter and metadata for every file.
        file_data: list[tuple[Path, str, dict[str, Any] | None, Node]] = []
        for path in files:
            content = path.read_text(encoding="utf-8")
            frontmatter = parse_frontmatter(path, content)
            metadata = self.metadata_extractor.extract(path, frontmatter)
            file_data.append((path, content, frontmatter, metadata))

        node_by_id = {node.id: node for _, _, _, node in file_data}
        node_ids = set(node_by_id.keys())

        # Second pass: extract and resolve links, compute per-node content hash.
        nodes: list[Node] = []
        edges: list[Edge] = []

        filters = [build_link_filter(config) for config in self.link_configs]

        for path, content, frontmatter, metadata in file_data:
            node_id = metadata.id
            raw_links: list[tuple[str, str]] = []

            for config, filter_ in zip(self.link_configs, filters):
                resolver = LinkResolver(
                    repo_root=self.repo_root,
                    node_ids=node_ids,
                    on_unresolved=config.on_unresolved,
                )
                found = filter_.extract(path, content, frontmatter)
                for link in found:
                    raw_links.append((config.name, link.text))
                    target_id = resolver.resolve(path, link)
                    if target_id is None:
                        continue
                    if target_id == node_id:
                        logger.warning("Self-loop detected for node '%s'; skipping", node_id)
                        continue
                    edges.append(
                        Edge(
                            from_id=node_id,
                            to_id=target_id,
                            filter_name=config.name,
                            style=config.style,
                        )
                    )

            raw_links.sort()
            content_hash = hash_node_content(frontmatter or {}, raw_links)
            nodes.append(
                Node(
                    id=node_id,
                    label=metadata.label,
                    subpath=metadata.subpath,
                    source_file=path,
                    content_hash=content_hash,
                )
            )

        nodes.sort(key=lambda n: n.id)
        edges.sort(key=lambda e: (e.from_id, e.to_id, e.filter_name))
        logger.info("Built graph with %d nodes and %d edges", len(nodes), len(edges))
        return Graph(nodes=tuple(nodes), edges=tuple(edges))
