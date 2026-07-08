"""Interface for link filter implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from diagram_renderer.service.graph import EdgeStyle, RawLink


class LinkFilter(ABC):
    """Interface for extracting raw links from a markdown file."""

    def __init__(self, name: str, style: EdgeStyle) -> None:
        self.name = name
        self.style = style

    @abstractmethod
    def extract(self, path: Path, content: str, frontmatter: dict[str, Any] | None) -> list[RawLink]:
        """Return raw links found in the file."""
