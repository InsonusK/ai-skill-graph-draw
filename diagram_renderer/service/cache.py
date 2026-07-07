"""Cache manager for render tasks."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from diagram_renderer.service.graph import Graph, Rect

logger = logging.getLogger(__name__)


class CacheManager:
    """Read/write per-task cache and detect unchanged file sets."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir

    def cache_path(self, task_id: str) -> Path:
        return self.cache_dir / f"{task_id}.json"

    def load(self, task_id: str) -> dict[str, Any] | None:
        """Load cached state or None if missing/invalid."""
        path = self.cache_path(task_id)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Cache file '%s' is corrupted: %s; ignoring", path, exc)
            return None

    def is_file_set_unchanged(self, task_id: str, file_set_hash: str) -> bool:
        """Return True if the file set hash matches the cache."""
        cached = self.load(task_id)
        if cached is None:
            return False
        return cached.get("file_set_hash") == file_set_hash

    def get_node_positions(self, task_id: str, graph: Graph) -> dict[str, Rect]:
        """Return cached positions for nodes that still exist in *graph*."""
        cached = self.load(task_id)
        if cached is None:
            return {}
        positions: dict[str, Rect] = {}
        node_ids = {node.id for node in graph.nodes}
        for node_id, rect_data in (cached.get("positions") or {}).items():
            if node_id in node_ids:
                try:
                    positions[node_id] = Rect.from_dict(rect_data)
                except (KeyError, TypeError, ValueError) as exc:
                    logger.warning(
                        "Invalid cached position for node '%s': %s",
                        node_id,
                        exc,
                    )
        return positions

    def get_node_hashes(self, task_id: str) -> dict[str, str]:
        """Return cached per-node content hashes."""
        cached = self.load(task_id)
        if cached is None:
            return {}
        return dict(cached.get("node_hashes") or {})

    def save(
        self,
        task_id: str,
        file_set_hash: str,
        graph: Graph,
        positions: dict[str, Rect],
    ) -> None:
        """Persist cache for a task."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_path(task_id)
        node_hashes = {node.id: node.content_hash for node in graph.nodes}
        data = {
            "file_set_hash": file_set_hash,
            "node_hashes": node_hashes,
            "positions": {node_id: rect.to_dict() for node_id, rect in positions.items()},
        }
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
        logger.info("Cache saved to '%s'", path)
