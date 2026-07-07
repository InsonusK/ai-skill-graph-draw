"""Layout engines for assigning node coordinates."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from diagram_renderer.service.graph import Graph, Rect

logger = logging.getLogger(__name__)

NODE_WIDTH = 400.0
NODE_HEIGHT = 400.0
H_SPACING = 200.0
V_SPACING = 100.0


class LayoutEngine(ABC):
    """Interface for layout engines."""

    @abstractmethod
    def place(self, graph: Graph, fixed_positions: dict[str, Rect]) -> dict[str, Rect]:
        """Return coordinates for all nodes, preserving *fixed_positions*."""


class LayeredLayoutEngine(LayoutEngine):
    """Sugiyama-like layered layout implemented in pure Python."""

    def __init__(
        self,
        direction: str = "LR",
        node_width: float = NODE_WIDTH,
        node_height: float = NODE_HEIGHT,
        h_spacing: float = H_SPACING,
        v_spacing: float = V_SPACING,
    ) -> None:
        self.direction = direction
        self.node_width = node_width
        self.node_height = node_height
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing

    def place(self, graph: Graph, fixed_positions: dict[str, Rect]) -> dict[str, Rect]:
        if not graph.nodes:
            return {}

        if not fixed_positions:
            return self._full_layout(graph)

        return self._incremental_layout(graph, fixed_positions)

    def _full_layout(self, graph: Graph) -> dict[str, Rect]:
        layers = self._compute_layers(graph)
        ordered_layers = self._order_layers(graph, layers)
        positions: dict[str, Rect] = {}
        for layer_index, layer in enumerate(ordered_layers):
            x = layer_index * (self.node_width + self.h_spacing)
            for node_index, node_id in enumerate(layer):
                y = node_index * (self.node_height + self.v_spacing)
                positions[node_id] = Rect(x, y, self.node_width, self.node_height)
        return positions

    def _incremental_layout(
        self, graph: Graph, fixed_positions: dict[str, Rect]
    ) -> dict[str, Rect]:
        layers = self._compute_layers(graph)
        node_to_layer = {node_id: idx for idx, layer in enumerate(layers) for node_id in layer}

        positions = dict(fixed_positions)
        added = [node.id for node in graph.nodes if node.id not in fixed_positions]
        added.sort()

        # Place each new node near the average position of its fixed neighbors.
        adjacency = self._adjacency(graph)
        for node_id in added:
            layer = node_to_layer[node_id]
            x = layer * (self.node_width + self.h_spacing)

            neighbor_positions = [
                positions[neighbor]
                for neighbor in adjacency.get(node_id, set())
                if neighbor in positions
            ]
            if neighbor_positions:
                y = sum(p.y for p in neighbor_positions) / len(neighbor_positions)
            else:
                y = 0.0

            # Avoid overlapping with existing nodes in the same horizontal band.
            y = self._resolve_overlap(node_id, x, y, positions)
            positions[node_id] = Rect(x, y, self.node_width, self.node_height)

        return positions

    def _resolve_overlap(
        self, node_id: str, x: float, y: float, positions: dict[str, Rect]
    ) -> float:
        """Shift *y* vertically so the new node does not overlap existing ones."""
        step = self.node_height + self.v_spacing
        existing = [rect for nid, rect in positions.items() if nid != node_id]
        candidate_y = y
        for _ in range(1000):
            new_rect = Rect(x, candidate_y, self.node_width, self.node_height)
            if not any(self._rects_overlap(new_rect, rect) for rect in existing):
                return candidate_y
            candidate_y += step
        logger.warning("Could not resolve overlap for node '%s' after 1000 attempts", node_id)
        return candidate_y

    @staticmethod
    def _rects_overlap(a: Rect, b: Rect) -> bool:
        """Return True if two rectangles overlap (excluding borders)."""
        return (
            a.x < b.x + b.width
            and a.x + a.width > b.x
            and a.y < b.y + b.height
            and a.y + a.height > b.y
        )

    def _compute_layers(self, graph: Graph) -> list[list[str]]:
        """Assign each node to a layer based on a DAG of the graph.

        Cycles are broken by ignoring back edges during layer calculation; the
        edges themselves remain in the graph for rendering.
        """
        edges = [(e.from_id, e.to_id) for e in graph.edges]
        node_ids = [node.id for node in graph.nodes]
        dag_edges = self._break_cycles(node_ids, edges)

        # Longest path layering from sources.
        in_degree: dict[str, int] = {node_id: 0 for node_id in node_ids}
        outgoing: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        for src, dst in dag_edges:
            outgoing[src].append(dst)
            in_degree[dst] += 1

        layer_by_node: dict[str, int] = {node_id: 0 for node_id in node_ids}
        queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
        # Deterministic processing.
        queue.sort()
        visited = set(queue)

        while queue:
            current = queue.pop(0)
            for neighbor in sorted(outgoing[current]):
                layer_by_node[neighbor] = max(
                    layer_by_node[neighbor], layer_by_node[current] + 1
                )
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    queue.sort()

        max_layer = max(layer_by_node.values()) if layer_by_node else 0
        layers: list[list[str]] = [[] for _ in range(max_layer + 1)]
        for node_id in node_ids:
            layers[layer_by_node[node_id]].append(node_id)
        for layer in layers:
            layer.sort()
        return layers

    def _order_layers(self, graph: Graph, layers: list[list[str]]) -> list[list[str]]:
        """Reorder nodes within layers using a simple barycenter heuristic."""
        adjacency = self._adjacency(graph)
        ordered = [list(layer) for layer in layers]

        for _ in range(3):
            # Top-down pass.
            for i in range(1, len(ordered)):
                ordered[i] = self._barycenter_sort(ordered[i], ordered[i - 1], adjacency)
            # Bottom-up pass.
            for i in range(len(ordered) - 2, -1, -1):
                ordered[i] = self._barycenter_sort(ordered[i], ordered[i + 1], adjacency)

        return ordered

    @staticmethod
    def _barycenter_sort(
        layer: list[str], reference_layer: list[str], adjacency: dict[str, set[str]]
    ) -> list[str]:
        """Sort nodes in *layer* by average index of their neighbors in *reference_layer*."""
        reference_index = {node_id: idx for idx, node_id in enumerate(reference_layer)}

        def score(node_id: str) -> float:
            neighbors = [
                reference_index[neighbor]
                for neighbor in adjacency.get(node_id, set())
                if neighbor in reference_index
            ]
            if not neighbors:
                return float("inf")
            return sum(neighbors) / len(neighbors)

        return sorted(layer, key=lambda node_id: (score(node_id), node_id))

    @staticmethod
    def _adjacency(graph: Graph) -> dict[str, set[str]]:
        """Return undirected adjacency for layout ordering."""
        adjacency: dict[str, set[str]] = {node.id: set() for node in graph.nodes}
        for edge in graph.edges:
            adjacency[edge.from_id].add(edge.to_id)
            adjacency[edge.to_id].add(edge.from_id)
        return adjacency

    @staticmethod
    def _break_cycles(nodes: list[str], edges: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """Return a DAG edge list by removing back edges detected via DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {node: WHITE for node in nodes}
        adjacency: dict[str, list[str]] = {node: [] for node in nodes}
        for src, dst in edges:
            adjacency[src].append(dst)

        back_edges: set[tuple[str, str]] = set()

        def dfs(node: str) -> None:
            color[node] = GRAY
            for neighbor in sorted(adjacency[node]):
                if color[neighbor] == GRAY:
                    back_edges.add((node, neighbor))
                elif color[neighbor] == WHITE:
                    dfs(neighbor)
            color[node] = BLACK

        for node in sorted(nodes):
            if color[node] == WHITE:
                dfs(node)

        dag_edges = [edge for edge in edges if edge not in back_edges]
        if back_edges:
            logger.warning(
                "Cycle(s) detected; %d edge(s) excluded from layer calculation",
                len(back_edges),
            )
        return dag_edges


def build_layout_engine(config: dict[str, Any]) -> LayoutEngine:
    """Factory for layout engines."""
    engine = config.get("engine", "layered")
    if engine == "layered":
        return LayeredLayoutEngine(direction=config.get("direction", "LR"))
    raise ValueError(f"Unsupported layout engine: {engine}")
