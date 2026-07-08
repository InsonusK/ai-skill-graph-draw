"""Layered layout delegated to python-igraph's built-in Sugiyama algorithm.

Alternative to `LayeredLayoutEngine` for the same `layered`-style output, but
using a battle-tested crossing-minimization implementation instead of the
hand-rolled barycenter heuristic. Select it via `layout.engine:
igraph_sugiyama` in the task config.
"""

from __future__ import annotations

import logging

from diagram_renderer.service.graph import Graph, Rect
from diagram_renderer.service.layout.base import (
    H_SPACING,
    NODE_HEIGHT,
    NODE_WIDTH,
    V_SPACING,
    LayoutEngine,
)
from diagram_renderer.service.layout.support import place_new_nodes_near_fixed

logger = logging.getLogger(__name__)


class IgraphSugiyamaLayoutEngine(LayoutEngine):
    """Layered layout computed by `igraph.Graph.layout_sugiyama()`.

    igraph computes layers and within-layer order for the *whole* graph in
    one pass; it has no notion of pinned nodes. To honour `fixed_positions`,
    a full igraph layout is only used to seed brand-new diagrams. On
    incremental runs, igraph is used solely to determine which layer each
    node falls into; nodes already in `fixed_positions` keep their
    coordinates, and new nodes are placed near their fixed neighbors — same
    contract as `LayeredLayoutEngine`.
    """

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

        node_ids = [node.id for node in graph.nodes]
        _, layers = self._sugiyama_coords(graph, node_ids)
        layer_by_node = dict(zip(node_ids, layers))
        return place_new_nodes_near_fixed(
            graph=graph,
            fixed_positions=fixed_positions,
            layer_by_node=layer_by_node,
            node_width=self.node_width,
            node_height=self.node_height,
            h_spacing=self.h_spacing,
            v_spacing=self.v_spacing,
        )

    def _full_layout(self, graph: Graph) -> dict[str, Rect]:
        node_ids = [node.id for node in graph.nodes]
        orders, layers = self._sugiyama_coords(graph, node_ids)
        positions: dict[str, Rect] = {}
        for node_id, order, layer in zip(node_ids, orders, layers):
            x = layer * (self.node_width + self.h_spacing)
            y = order * (self.node_height + self.v_spacing)
            positions[node_id] = Rect(x, y, self.node_width, self.node_height)
        return positions

    @staticmethod
    def _sugiyama_coords(
        graph: Graph, node_ids: list[str]
    ) -> tuple[list[float], list[int]]:
        """Return (order-within-layer, layer-index) per node id in *node_ids*."""
        try:
            import igraph
        except ImportError as exc:
            raise RuntimeError(
                "Layout engine 'igraph_sugiyama' requires the 'igraph' package; "
                "install it with 'pip install python-igraph'"
            ) from exc

        index_by_id = {node_id: index for index, node_id in enumerate(node_ids)}
        edges = [
            (index_by_id[edge.from_id], index_by_id[edge.to_id])
            for edge in graph.edges
            if edge.from_id != edge.to_id
        ]

        g = igraph.Graph(n=len(node_ids), edges=edges, directed=True)
        coords = g.layout_sugiyama().coords[: len(node_ids)]
        orders = [order for order, _ in coords]
        layers = [int(round(layer)) for _, layer in coords]
        logger.debug(
            "igraph layout_sugiyama computed %d layer(s) for %d node(s), %d edge(s)",
            max(layers, default=-1) + 1,
            len(node_ids),
            len(edges),
        )
        return orders, layers
