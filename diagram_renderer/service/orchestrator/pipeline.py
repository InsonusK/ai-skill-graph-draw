"""Default pipeline implementation wiring all pipeline stages together."""

from __future__ import annotations

import logging
from pathlib import Path

from diagram_renderer.functions.hashing import hash_file_set
from diagram_renderer.service.cache.manager import CacheManager
from diagram_renderer.service.diff.diff_engine import DiffEngine
from diagram_renderer.service.graph import Graph, Rect, RenderTask
from diagram_renderer.service.graph_builder.builder import GraphBuilder
from diagram_renderer.service.layout.factory import build_layout_engine
from diagram_renderer.service.metadata_extractor.extractor import MetadataExtractor
from diagram_renderer.service.source_collector.collector import SourceCollector
from diagram_renderer.service.writers.factory import build_writer

logger = logging.getLogger(__name__)


class Orchestrator:
    """Run the full render pipeline for one task."""

    def __init__(
        self,
        repo_root: Path,
        cache_manager: CacheManager,
    ) -> None:
        self.repo_root = repo_root
        self.cache_manager = cache_manager
        self.diff_engine = DiffEngine()

    def run(self, task: RenderTask, force: bool = False) -> bool:
        """Execute one render task.

        Returns True if the task produced/updated output, False if skipped due to cache.
        """
        logger.info("Running task '%s'", task.id)

        source_collector = SourceCollector(self.repo_root)
        files, _ = source_collector.collect(task.source)

        if not files:
            logger.warning("Task '%s' has no source files; skipping output", task.id)
            return False

        metadata_extractor = MetadataExtractor(self.repo_root, task.metadata)
        graph_builder = GraphBuilder(
            repo_root=self.repo_root,
            metadata_extractor=metadata_extractor,
            link_configs=task.links,
        )
        files = graph_builder.expand_sources(files)
        file_set_hash = hash_file_set(files, self.repo_root)

        if not force and self.cache_manager.is_file_set_unchanged(task.id, file_set_hash):
            logger.info("Task '%s' file set unchanged; skipping", task.id)
            return False

        graph = graph_builder.build(files)

        if not graph.nodes:
            logger.warning("Task '%s' produced an empty graph; skipping output", task.id)
            return False

        diff = self.diff_engine.diff(graph, task.output.destination)
        cached_positions = self.cache_manager.get_node_positions(task.id, graph)

        # Positions priority: existing canvas file > cache.
        fixed_positions = diff.positions if diff.positions else cached_positions

        # Limit fixed positions to nodes whose content hash has not changed.
        cached_hashes = self.cache_manager.get_node_hashes(task.id)
        stable_positions: dict[str, Rect] = {}
        for node in graph.nodes:
            if node.id in fixed_positions:
                if cached_hashes.get(node.id) == node.content_hash:
                    stable_positions[node.id] = fixed_positions[node.id]
                else:
                    logger.info("Node '%s' content changed; recalculating position", node.id)

        layout_engine = build_layout_engine(
            {"engine": task.layout.engine, "direction": task.layout.direction}
        )
        positions = layout_engine.place(graph, stable_positions)

        # Determine which nodes are truly unchanged for merge purposes.
        unchanged = {
            node.id
            for node in graph.nodes
            if node.id in stable_positions and node.id in positions
        }

        writer = build_writer(
            task.output.format,
            repo_root=self.repo_root,
            direction=task.layout.direction,
        )
        writer.write(
            graph=graph,
            positions=positions,
            destination=task.output.destination,
            unchanged=unchanged,
        )

        self.cache_manager.save(task.id, file_set_hash, graph, positions)
        logger.info("Task '%s' completed successfully", task.id)
        return True
