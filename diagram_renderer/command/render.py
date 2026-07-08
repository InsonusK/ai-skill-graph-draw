"""Business logic for the `render` command."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from diagram_renderer.service.cache.manager import CacheManager
from diagram_renderer.service.config.loader import ConfigLoader
from diagram_renderer.service.graph import RenderTask
from diagram_renderer.service.orchestrator.pipeline import Orchestrator

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RenderCommandResult:
    """Result of the render command."""

    rendered: int
    skipped: int
    failed: int


def run(
    repo_root: Path,
    cache_dir: Path,
    config_path: Path | None,
    task_ids: list[str] | None,
    force: bool,
    single_task: RenderTask | None,
) -> RenderCommandResult:
    """Run render tasks.

    Args:
        repo_root: Repository root used for relative paths.
        cache_dir: Directory for per-task cache files.
        config_path: Path to YAML config, or None for single-task mode.
        task_ids: Optional filter to run only specific task ids from config.
        force: Ignore cache and re-render.
        single_task: Task built from CLI arguments when --config is not used.

    Returns:
        RenderCommandResult with rendered/skipped/failed counts.
    """
    cache_manager = CacheManager(cache_dir)
    orchestrator = Orchestrator(repo_root=repo_root, cache_manager=cache_manager)

    if config_path is not None:
        loader = ConfigLoader(repo_root)
        try:
            tasks = loader.load_from_file(config_path)
        except Exception as exc:
            logger.error("Failed to load config '%s': %s", config_path, exc)
            return RenderCommandResult(rendered=0, skipped=0, failed=1)
    elif single_task is not None:
        tasks = [single_task]
    else:
        logger.error("Either --config or single-task arguments must be provided")
        return RenderCommandResult(rendered=0, skipped=0, failed=1)

    if task_ids:
        allowed = set(task_ids)
        tasks = [task for task in tasks if task.id in allowed]
        if not tasks:
            logger.warning("No tasks matched the requested ids: %s", task_ids)

    rendered = skipped = failed = 0
    for task in tasks:
        try:
            produced = orchestrator.run(task, force=force)
            if produced:
                rendered += 1
            else:
                skipped += 1
        except Exception as exc:
            logger.critical("Task '%s' failed: %s", task.id, exc, exc_info=True)
            failed += 1

    logger.info(
        "Render command finished: %d rendered, %d skipped, %d failed",
        rendered,
        skipped,
        failed,
    )
    return RenderCommandResult(rendered=rendered, skipped=skipped, failed=failed)
