"""Factory for layout engine implementations, selected by `layout.engine`."""

from __future__ import annotations

from typing import Any

from diagram_renderer.service.layout.base import LayoutEngine
from diagram_renderer.service.layout.layered import LayeredLayoutEngine
from diagram_renderer.service.layout.sugiyama_igraph import IgraphSugiyamaLayoutEngine

_ENGINES: dict[str, type[LayoutEngine]] = {
    "layered": LayeredLayoutEngine,
    "igraph_sugiyama": IgraphSugiyamaLayoutEngine,
}


def build_layout_engine(config: dict[str, Any]) -> LayoutEngine:
    """Factory for layout engines."""
    engine = config.get("engine", "layered")
    engine_cls = _ENGINES.get(engine)
    if engine_cls is None:
        raise ValueError(f"Unsupported layout engine: {engine}")
    return engine_cls(direction=config.get("direction", "LR"))
