"""Default graph builder: assembles Graph from files, metadata and links."""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from diagram_renderer.functions.frontmatter import parse_frontmatter
from diagram_renderer.functions.graph_algorithms import transitive_reduction_indices
from diagram_renderer.functions.hashing import hash_node_content
from diagram_renderer.service.graph import Edge, Graph, LinkFilterConfig, Node, RawLink
from diagram_renderer.service.link_filters.factory import build_link_filter
from diagram_renderer.service.link_resolver.resolver import LinkResolver
from diagram_renderer.service.metadata_extractor.extractor import MetadataExtractor

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
                    from_id, to_id = (
                        (target_id, node_id) if config.reverse else (node_id, target_id)
                    )
                    edges.append(
                        Edge(
                            from_id=from_id,
                            to_id=to_id,
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

        reduce_filters = {config.name for config in self.link_configs if config.transitive_reduction}
        if reduce_filters:
            edges = self._reduce_transitive_edges(edges, reduce_filters)

        nodes.sort(key=lambda n: n.id)
        edges.sort(key=lambda e: (e.from_id, e.to_id, e.filter_name))
        logger.info("Built graph with %d nodes and %d edges", len(nodes), len(edges))
        return Graph(nodes=tuple(nodes), edges=tuple(edges))

    def _reduce_transitive_edges(self, edges: list[Edge], filter_names: set[str]) -> list[Edge]:
        """Drop edges implied by a longer path within the same link filter.

        Each filter is reduced independently: a chain built from `depends_on`
        edges must not be used to justify dropping an `extends` edge, since
        the two relations are not interchangeable.
        """
        by_filter: dict[str, list[Edge]] = defaultdict(list)
        passthrough: list[Edge] = []
        for edge in edges:
            if edge.filter_name in filter_names:
                by_filter[edge.filter_name].append(edge)
            else:
                passthrough.append(edge)

        kept = list(passthrough)
        for filter_name, group in by_filter.items():
            pairs = [(edge.from_id, edge.to_id) for edge in group]
            keep_indices = transitive_reduction_indices(pairs)
            removed = len(group) - len(keep_indices)
            if removed:
                logger.info(
                    "Filter '%s': dropped %d transitively redundant edge(s)",
                    filter_name,
                    removed,
                )
            kept.extend(group[i] for i in keep_indices)
        return kept
