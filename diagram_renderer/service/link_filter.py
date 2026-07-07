"""Pluggable link filters."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from diagram_renderer.functions.wikilinks import extract_wikilinks
from diagram_renderer.service.graph import EdgeStyle, LinkFilterConfig, RawLink

logger = logging.getLogger(__name__)


class LinkFilter(ABC):
    """Interface for extracting raw links from a markdown file."""

    def __init__(self, name: str, style: EdgeStyle) -> None:
        self.name = name
        self.style = style

    @abstractmethod
    def extract(self, path: Path, content: str, frontmatter: dict[str, Any] | None) -> list[RawLink]:
        """Return raw links found in the file."""


class FrontmatterFieldLinkFilter(LinkFilter):
    """Extract wiki-links from a frontmatter list field."""

    def __init__(self, name: str, field: str, style: EdgeStyle) -> None:
        super().__init__(name, style)
        self.field = field

    def extract(self, path: Path, content: str, frontmatter: dict[str, Any] | None) -> list[RawLink]:
        if frontmatter is None:
            return []

        value = frontmatter.get(self.field)
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, (list, tuple)):
            logger.warning(
                "Frontmatter field '%s' in '%s' is not a list; skipping",
                self.field,
                path,
            )
            return []

        links: list[RawLink] = []
        for item in value:
            links.extend(self._extract_from_item(path, item))
        return links

    def _extract_from_item(
        self, path: Path, item: Any
    ) -> list[RawLink]:
        """Extract links from a frontmatter list item.

        YAML parses unquoted `[[foo]]` as a nested list `[['foo']]`. We treat
        a list whose elements are strings as a list of wiki-link targets.
        """
        if isinstance(item, str):
            return extract_wikilinks(item)
        if isinstance(item, (list, tuple)):
            result: list[RawLink] = []
            for sub in item:
                if isinstance(sub, str):
                    result.append(RawLink(sub))
                elif isinstance(sub, (list, tuple)):
                    result.extend(self._extract_from_item(path, sub))
                else:
                    logger.warning(
                        "Non-string nested item in frontmatter field '%s' of '%s'; skipping",
                        self.field,
                        path,
                    )
            return result
        logger.warning(
            "Non-string item in frontmatter field '%s' of '%s'; skipping",
            self.field,
            path,
        )
        return []


def build_link_filter(config: LinkFilterConfig) -> LinkFilter:
    """Build a LinkFilter instance from config."""
    if config.type != "frontmatter_field":
        raise ValueError(f"Unsupported link filter type: {config.type}")
    return FrontmatterFieldLinkFilter(
        name=config.name,
        field=config.field,
        style=config.style,
    )
