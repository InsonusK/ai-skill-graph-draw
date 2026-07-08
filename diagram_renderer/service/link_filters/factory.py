"""Factory for link filter implementations, selected by `links[].type`."""

from __future__ import annotations

from diagram_renderer.service.graph import LinkFilterConfig
from diagram_renderer.service.link_filters.base import LinkFilter
from diagram_renderer.service.link_filters.frontmatter_field import FrontmatterFieldLinkFilter

_FILTER_TYPES: dict[str, type[FrontmatterFieldLinkFilter]] = {
    "frontmatter_field": FrontmatterFieldLinkFilter,
}


def build_link_filter(config: LinkFilterConfig) -> LinkFilter:
    """Build a LinkFilter instance from config."""
    filter_cls = _FILTER_TYPES.get(config.type)
    if filter_cls is None:
        raise ValueError(f"Unsupported link filter type: {config.type}")
    return filter_cls(
        name=config.name,
        field=config.field,
        style=config.style,
    )
