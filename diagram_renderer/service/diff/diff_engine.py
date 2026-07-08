"""Default diff engine comparing the graph against the on-disk canvas file."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from diagram_renderer.service.graph import Graph, Rect

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DiffResult:
    """Result of comparing a new graph with the existing canvas."""

    added: set[str]
    removed: set[str]
    unchanged: set[str]
    positions: dict[str, Rect]


class DiffEngine:
    """Compare the new graph with the destination canvas on disk."""

    def diff(self, graph: Graph, destination: Path) -> DiffResult:
        """Return added/removed/unchanged node ids and known positions.

        Positions are taken from the existing destination file when it is valid
        and the node is unchanged. The cache is used only for fast path
        detection; this method always trusts the actual file on disk.
        """
        new_ids = {node.id for node in graph.nodes}
        existing_positions = self._read_existing_positions(destination)
        existing_ids = set(existing_positions.keys())

        added = new_ids - existing_ids
        removed = existing_ids - new_ids
        unchanged = new_ids & existing_ids

        positions = {node_id: existing_positions[node_id] for node_id in unchanged}

        logger.info(
            "Diff result: %d added, %d removed, %d unchanged",
            len(added),
            len(removed),
            len(unchanged),
        )
        return DiffResult(
            added=added,
            removed=removed,
            unchanged=unchanged,
            positions=positions,
        )

    def _read_existing_positions(self, destination: Path) -> dict[str, Rect]:
        """Read node positions from an existing .canvas file.

        If the file does not exist, return an empty dict. If it is corrupted or
        has an unexpected schema, raise ValueError to avoid overwriting user edits.
        """
        if not destination.exists():
            return {}

        try:
            with destination.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Destination file '{destination}' contains invalid JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(f"Destination file '{destination}' is not a JSON object")

        nodes = data.get("nodes")
        if nodes is None:
            raise ValueError(f"Destination file '{destination}' has no 'nodes' key")
        if not isinstance(nodes, list):
            raise ValueError(f"Destination file '{destination}' 'nodes' must be a list")

        positions: dict[str, Rect] = {}
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_id = node.get("id")
            if not isinstance(node_id, str):
                continue
            try:
                rect = Rect(
                    x=float(node["x"]),
                    y=float(node["y"]),
                    width=float(node["width"]),
                    height=float(node["height"]),
                )
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning(
                    "Skipping malformed node '%s' in destination: %s",
                    node_id,
                    exc,
                )
                continue
            positions[node_id] = rect

        return positions
