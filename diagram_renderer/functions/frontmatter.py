"""Parse YAML frontmatter from markdown files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def parse_frontmatter(path: Path, content: str) -> dict[str, Any] | None:
    """Extract YAML frontmatter from markdown content.

    Returns the parsed frontmatter dict, or None if the file has no frontmatter
    or invalid YAML. Warnings are logged for invalid YAML.
    """
    if not content.startswith("---"):
        return None

    # Find the closing '---' on its own line.
    end_index = content.find("\n---", 3)
    if end_index == -1:
        return None

    frontmatter_text = content[3:end_index].strip()
    if not frontmatter_text:
        return {}

    try:
        parsed = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        logger.warning("Invalid YAML frontmatter in '%s': %s", path, exc)
        return None

    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        logger.warning("Frontmatter in '%s' is not a mapping", path)
        return None
    return parsed
