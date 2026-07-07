"""Extract wiki-style links from text."""

from __future__ import annotations

import re

from diagram_renderer.service.graph import RawLink

_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def extract_wikilinks(text: str) -> list[RawLink]:
    """Return all `[[path|alias]]` links found in *text*."""
    return [RawLink(match.group(1)) for match in _WIKILINK_RE.finditer(text)]
