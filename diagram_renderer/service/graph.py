"""Data models for diagram rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class RawLink:
    """A raw wiki-style link before resolution."""

    text: str

    def path_part(self) -> str:
        """Return the path portion of `[[path|alias]]`."""
        return self.text.split("|", 1)[0].strip()

    def alias(self) -> str | None:
        """Return the alias portion of `[[path|alias]]` if present."""
        if "|" in self.text:
            return self.text.split("|", 1)[1].strip() or None
        return None


@dataclass(frozen=True, slots=True)
class EdgeStyle:
    """Visual style for edges produced by a link filter."""

    color: str | None = None
    label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.color is not None:
            result["color"] = self.color
        if self.label is not None:
            result["label"] = self.label
        return result


@dataclass(frozen=True, slots=True)
class NodeMetadata:
    """Extracted metadata for a markdown file."""

    id: str
    label: str
    subpath: str | None = None


@dataclass(frozen=True, slots=True)
class Rect:
    """Rectangle with position and size."""

    x: float
    y: float
    width: float
    height: float

    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> Rect:
        return cls(
            x=float(data["x"]),
            y=float(data["y"]),
            width=float(data["width"]),
            height=float(data["height"]),
        )


@dataclass(frozen=True, slots=True)
class Node:
    """A node in the rendered graph."""

    id: str
    label: str
    subpath: str | None
    source_file: Path
    content_hash: str


@dataclass(frozen=True, slots=True)
class Edge:
    """A directed edge between two nodes."""

    from_id: str
    to_id: str
    filter_name: str
    style: EdgeStyle = field(default_factory=EdgeStyle)


@dataclass(frozen=True, slots=True)
class Graph:
    """Graph produced for one render task."""

    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]

    def node_by_id(self) -> dict[str, Node]:
        return {node.id: node for node in self.nodes}


@dataclass(frozen=True, slots=True)
class LinkFilterConfig:
    """Configuration for one link filter."""

    name: str
    type: str
    field: str
    on_unresolved: str = "skip"
    style: EdgeStyle = field(default_factory=EdgeStyle)
    transitive_reduction: bool = False
    reverse: bool = False


@dataclass(frozen=True, slots=True)
class SourceConfig:
    """Source file selection configuration."""

    include: tuple[str, ...]
    exclude: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MetadataConfig:
    """Node metadata extraction configuration."""

    subpath: str | None = None


@dataclass(frozen=True, slots=True)
class LayoutConfig:
    """Layout engine configuration."""

    engine: str = "igraph_sugiyama"
    direction: str = "LR"


@dataclass(frozen=True, slots=True)
class OutputConfig:
    """Output writer configuration."""

    format: str
    destination: Path


@dataclass(frozen=True, slots=True)
class RenderTask:
    """One diagram render task."""

    id: str
    source: SourceConfig
    metadata: MetadataConfig
    links: tuple[LinkFilterConfig, ...]
    layout: LayoutConfig
    output: OutputConfig
