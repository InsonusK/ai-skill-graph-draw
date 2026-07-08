"""Interface and shared constants for layout engines."""

from __future__ import annotations

from abc import ABC, abstractmethod

from diagram_renderer.service.graph import Graph, Rect

NODE_WIDTH = 400.0
NODE_HEIGHT = 400.0
H_SPACING = 200.0
V_SPACING = 100.0


class LayoutEngine(ABC):
    """Interface for layout engines."""

    @abstractmethod
    def place(self, graph: Graph, fixed_positions: dict[str, Rect]) -> dict[str, Rect]:
        """Return coordinates for all nodes, preserving *fixed_positions*."""
