"""Link filter that reads wiki-links from a frontmatter list field."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from diagram_renderer.functions.wikilinks import extract_wikilinks
from diagram_renderer.service.graph import EdgeStyle, RawLink
from diagram_renderer.service.link_filters.base import LinkFilter

logger = logging.getLogger(__name__)


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
