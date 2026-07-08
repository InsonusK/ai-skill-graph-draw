"""Placement helpers shared by multiple layout engine implementations.

Any layered layout engine can compute a full topology (which layer each node
belongs to) differently, but placing *new* nodes without disturbing
`fixed_positions` is the same problem regardless of how layers were derived:
put the node in its layer's column, near its already-placed neighbors, and
nudge it clear of collisions. This module implements that part once so
engines only need to supply a `layer_by_node` mapping.
"""

from __future__ import annotations

import logging

from diagram_renderer.service.graph import Graph, Rect

logger = logging.getLogger(__name__)


def place_new_nodes_near_fixed(
    graph: Graph,
    fixed_positions: dict[str, Rect],
    layer_by_node: dict[str, int],
    node_width: float,
    node_height: float,
    h_spacing: float,
    v_spacing: float,
) -> dict[str, Rect]:
    """Return positions for all nodes without moving any node already fixed.

    New nodes are placed in their assigned layer's column, at the average y
    of their already-positioned neighbors (or y=0 if none), then nudged
    vertically to avoid overlapping any node already placed in that column.
    """
    positions = dict(fixed_positions)
    added = sorted(node.id for node in graph.nodes if node.id not in fixed_positions)
    adjacency = _undirected_adjacency(graph)

    for node_id in added:
        x = layer_by_node[node_id] * (node_width + h_spacing)

        neighbor_positions = [
            positions[neighbor]
            for neighbor in adjacency.get(node_id, ())
            if neighbor in positions
        ]
        y = (
            sum(p.y for p in neighbor_positions) / len(neighbor_positions)
            if neighbor_positions
            else 0.0
        )

        y = _resolve_overlap(node_id, x, y, positions, node_width, node_height, v_spacing)
        positions[node_id] = Rect(x, y, node_width, node_height)

    return positions


def _resolve_overlap(
    node_id: str,
    x: float,
    y: float,
    positions: dict[str, Rect],
    node_width: float,
    node_height: float,
    v_spacing: float,
) -> float:
    """Shift *y* vertically so the new node does not overlap existing ones."""
    step = node_height + v_spacing
    existing = [rect for nid, rect in positions.items() if nid != node_id]
    candidate_y = y
    for _ in range(1000):
        new_rect = Rect(x, candidate_y, node_width, node_height)
        if not any(_rects_overlap(new_rect, rect) for rect in existing):
            return candidate_y
        candidate_y += step
    logger.warning("Could not resolve overlap for node '%s' after 1000 attempts", node_id)
    return candidate_y


def _rects_overlap(a: Rect, b: Rect) -> bool:
    """Return True if two rectangles overlap (excluding borders)."""
    return (
        a.x < b.x + b.width
        and a.x + a.width > b.x
        and a.y < b.y + b.height
        and a.y + a.height > b.y
    )


def _undirected_adjacency(graph: Graph) -> dict[str, set[str]]:
    """Return undirected adjacency for neighbor-based placement."""
    adjacency: dict[str, set[str]] = {node.id: set() for node in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.from_id].add(edge.to_id)
        adjacency[edge.to_id].add(edge.from_id)
    return adjacency
