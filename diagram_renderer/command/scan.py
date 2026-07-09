"""Business logic for the `scan` command."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from diagram_renderer.command import render as render_command

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ScanCommandResult:
    """Result of the scan command."""

    found: int
    rendered: int
    skipped: int
    failed: int


def run(
    repo_root: Path,
    directory: Path,
    filename: str,
    task_ids: list[str] | None,
    force: bool,
    cache_dir: Path,
) -> ScanCommandResult:
    """Find config files and render each one.

    Args:
        repo_root: Repository root used for relative paths.
        directory: Directory to scan recursively.
        filename: Name of the config file to look for.
        task_ids: Optional filter passed to each config render.
        force: Ignore cache and re-render.
        cache_dir: Directory for per-task cache files.

    Returns:
        ScanCommandResult with found/rendered/skipped/failed counts.
    """
    if not directory.exists():
        logger.error("Scan directory '%s' does not exist", directory)
        return ScanCommandResult(found=0, rendered=0, skipped=0, failed=1)

    if not directory.is_dir():
        logger.error("Scan path '%s' is not a directory", directory)
        return ScanCommandResult(found=0, rendered=0, skipped=0, failed=1)

    config_paths = sorted(directory.rglob(filename))
    found = len(config_paths)
    if found == 0:
        logger.warning(
            "No '%s' files found under '%s'", filename, directory
        )
        return ScanCommandResult(found=0, rendered=0, skipped=0, failed=0)

    logger.info(
        "Found %d config file(s) matching '%s' under '%s'",
        found,
        filename,
        directory,
    )

    rendered = skipped = failed = 0
    for config_path in config_paths:
        logger.info("Rendering config '%s'", config_path)
        render_result = render_command.run(
            repo_root=repo_root,
            cache_dir=cache_dir,
            config_path=config_path,
            task_ids=task_ids,
            force=force,
            single_task=None,
        )
        rendered += render_result.rendered
        skipped += render_result.skipped
        failed += render_result.failed

    logger.info(
        "Scan command finished: %d found, %d rendered, %d skipped, %d failed",
        found,
        rendered,
        skipped,
        failed,
    )
    return ScanCommandResult(found=found, rendered=rendered, skipped=skipped, failed=failed)
