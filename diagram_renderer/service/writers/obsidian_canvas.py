"""Obsidian Canvas (.canvas) format writer."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from diagram_renderer.service.graph import Edge, Graph, Node, Rect
from diagram_renderer.service.writers.base import FormatWriter

logger = logging.getLogger(__name__)

_DEFAULT_WIDTH = 400.0
_DEFAULT_HEIGHT = 400.0


class ObsidianCanvasWriter(FormatWriter):
    """Write a Graph to an Obsidian Canvas JSON file, merging with existing content."""

    def __init__(self, repo_root: Path, direction: str = "LR") -> None:
        self.repo_root = repo_root
        # Kept for FormatWriter construction symmetry with layout engines;
        # edge sides are derived from actual node positions, not this hint.
        self.direction = direction

    def write(
        self,
        graph: Graph,
        positions: dict[str, Rect],
        destination: Path,
        unchanged: set[str] | None = None,
    ) -> None:
        """Write the graph to *destination* preserving positions for unchanged nodes."""
        unchanged = unchanged or set()
        existing = self._read_existing(destination)

        nodes_data: list[dict[str, Any]] = []
        for node in graph.nodes:
            rect = positions.get(node.id)
            if rect is None:
                rect = Rect(0.0, 0.0, _DEFAULT_WIDTH, _DEFAULT_HEIGHT)
            node_data = self._node_to_canvas(node, rect)

            # Preserve width/height from existing canvas for unchanged nodes if present.
            if node.id in unchanged and node.id in existing.get("node_positions", {}):
                existing_rect = existing["node_positions"][node.id]
                node_data["width"] = existing_rect.width
                node_data["height"] = existing_rect.height

            nodes_data.append(node_data)

        edges_data: list[dict[str, Any]] = []
        for edge in graph.edges:
            edges_data.append(self._edge_to_canvas(edge, positions))

        output = {"nodes": nodes_data, "edges": edges_data}
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2, sort_keys=True)
        logger.info("Canvas written to '%s'", destination)

    def _node_to_canvas(self, node: Node, rect: Rect) -> dict[str, Any]:
        rel_path = node.source_file.relative_to(self.repo_root).as_posix()
        data: dict[str, Any] = {
            "id": node.id,
            "type": "file",
            "file": rel_path,
            "x": rect.x,
            "y": rect.y,
            "width": rect.width,
            "height": rect.height,
        }
        if node.subpath:
            data["subpath"] = node.subpath
        return data

    def _edge_to_canvas(self, edge: Edge, positions: dict[str, Rect]) -> dict[str, Any]:
        from_side, to_side = self._sides_for_edge(edge, positions)
        edge_id = self._edge_id(edge)
        data: dict[str, Any] = {
            "id": edge_id,
            "fromNode": edge.from_id,
            "fromSide": from_side,
            "toNode": edge.to_id,
            "toSide": to_side,
        }
        style_dict = edge.style.to_dict()
        if "color" in style_dict:
            data["color"] = style_dict["color"]
        if "label" in style_dict:
            data["label"] = style_dict["label"]
        return data

    def _sides_for_edge(self, edge: Edge, positions: dict[str, Rect]) -> tuple[str, str]:
        """Return (fromSide, toSide) based on where the two nodes actually sit.

        Canvas coordinates have (0, 0) at the top-left, x growing right and y
        growing down. `fromSide` is the side of `fromNode` facing `toNode`
        (and vice versa for `toSide`), picked from the dominant axis of the
        vector between their centers.
        """
        default_rect = Rect(0.0, 0.0, _DEFAULT_WIDTH, _DEFAULT_HEIGHT)
        from_center = self._center(positions.get(edge.from_id, default_rect))
        to_center = self._center(positions.get(edge.to_id, default_rect))
        dx = to_center[0] - from_center[0]
        dy = to_center[1] - from_center[1]
        return self._side_for_delta(dx, dy), self._side_for_delta(-dx, -dy)

    @staticmethod
    def _center(rect: Rect) -> tuple[float, float]:
        return (rect.x + rect.width / 2, rect.y + rect.height / 2)

    @staticmethod
    def _side_for_delta(dx: float, dy: float) -> str:
        """Return which side of a node an edge exits from, given the vector
        (dx, dy) from that node's center towards the other node's center."""
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        return "bottom" if dy > 0 else "top"

    @staticmethod
    def _edge_id(edge: Edge) -> str:
        raw = f"{edge.from_id}|{edge.to_id}|{edge.filter_name}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _read_existing(self, destination: Path) -> dict[str, Any]:
        """Read existing canvas file and return {node_positions: {id: Rect}}."""
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

        positions: dict[str, Rect] = {}
        for node in data.get("nodes", []):
            if not isinstance(node, dict):
                continue
            node_id = node.get("id")
            if not isinstance(node_id, str):
                continue
            try:
                positions[node_id] = Rect(
                    x=float(node["x"]),
                    y=float(node["y"]),
                    width=float(node["width"]),
                    height=float(node["height"]),
                )
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning("Malformed existing node '%s': %s", node_id, exc)
        return {"node_positions": positions}
