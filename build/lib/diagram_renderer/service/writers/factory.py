"""Factory for output format writers, selected by `output.format`."""

from __future__ import annotations

from pathlib import Path

from diagram_renderer.service.writers.base import FormatWriter
from diagram_renderer.service.writers.obsidian_canvas import ObsidianCanvasWriter

_WRITERS: dict[str, type[FormatWriter]] = {
    "obsidian_canvas": ObsidianCanvasWriter,
}


def build_writer(format_name: str, *, repo_root: Path, direction: str) -> FormatWriter:
    """Factory for format writers."""
    writer_cls = _WRITERS.get(format_name)
    if writer_cls is None:
        raise ValueError(f"Unsupported output format: {format_name}")
    return writer_cls(repo_root=repo_root, direction=direction)
