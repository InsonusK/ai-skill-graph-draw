"""Interface for output format writers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from diagram_renderer.service.graph import Graph, Rect


class FormatWriter(ABC):
    """Interface for writing a Graph to a diagram file, merging with existing content."""

    @abstractmethod
    def write(
        self,
        graph: Graph,
        positions: dict[str, Rect],
        destination: Path,
        unchanged: set[str] | None = None,
    ) -> None:
        """Write *graph* with *positions* to *destination*, preserving *unchanged* nodes."""
