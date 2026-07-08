"""YAML config file and CLI-argument loader for render tasks."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from diagram_renderer.service.graph import (
    EdgeStyle,
    LayoutConfig,
    LinkFilterConfig,
    MetadataConfig,
    OutputConfig,
    RenderTask,
    SourceConfig,
)

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = Path(".cache/diagram-renderer")


class ConfigValidationError(Exception):
    """Raised when a task configuration is invalid."""


class ConfigLoader:
    """Load render tasks from YAML config or CLI arguments."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def load_from_file(self, path: Path) -> list[RenderTask]:
        """Load and validate all tasks from a YAML config file."""
        logger.info("Loading config from '%s'", path)
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except Exception as exc:
            raise ConfigValidationError(f"Cannot read config '{path}': {exc}") from exc

        if not isinstance(data, dict):
            raise ConfigValidationError("Config root must be a mapping")

        raw_tasks = data.get("tasks")
        if not isinstance(raw_tasks, list):
            raise ConfigValidationError("Config must contain a 'tasks' list")

        tasks: list[RenderTask] = []
        for raw in raw_tasks:
            try:
                tasks.append(self._parse_task(raw))
            except ConfigValidationError as exc:
                logger.warning("Skipping invalid task: %s", exc)
        return tasks

    def load_single(
        self,
        task_id: str,
        include: list[str],
        link_field: str,
        output: Path,
        subpath: str | None = None,
        exclude: list[str] | None = None,
        on_unresolved: str = "skip",
        layout_engine: str = "igraph_sugiyama",
        layout_direction: str = "LR",
        output_format: str = "obsidian_canvas",
        edge_color: str | None = None,
        edge_label: str | None = None,
        transitive_reduction: bool = False,
    ) -> RenderTask:
        """Build a single task from explicit CLI arguments."""
        return RenderTask(
            id=task_id,
            source=SourceConfig(
                include=tuple(include),
                exclude=tuple(exclude or []),
            ),
            metadata=MetadataConfig(subpath=subpath),
            links=(
                LinkFilterConfig(
                    name=link_field,
                    type="frontmatter_field",
                    field=link_field,
                    on_unresolved=on_unresolved,
                    style=EdgeStyle(color=edge_color, label=edge_label),
                    transitive_reduction=transitive_reduction,
                ),
            ),
            layout=LayoutConfig(engine=layout_engine, direction=layout_direction),
            output=OutputConfig(format=output_format, destination=output),
        )

    def _parse_task(self, data: Any) -> RenderTask:
        if not isinstance(data, dict):
            raise ConfigValidationError("Task must be a mapping")

        task_id = self._require_str(data, "id")
        source = self._parse_source(data.get("source", {}))
        metadata = self._parse_metadata(data.get("metadata", {}))
        links = self._parse_links(data.get("links", []))
        layout = self._parse_layout(data.get("layout", {}))
        output = self._parse_output(data.get("output", {}))

        if not links:
            raise ConfigValidationError(f"Task '{task_id}' has no link filters")

        return RenderTask(
            id=task_id,
            source=source,
            metadata=metadata,
            links=links,
            layout=layout,
            output=output,
        )

    def _parse_source(self, data: Any) -> SourceConfig:
        if not isinstance(data, dict):
            raise ConfigValidationError("'source' must be a mapping")
        include = self._require_str_list(data, "include")
        exclude = self._optional_str_list(data.get("exclude"))
        return SourceConfig(include=tuple(include), exclude=tuple(exclude or []))

    def _parse_metadata(self, data: Any) -> MetadataConfig:
        if not isinstance(data, dict):
            return MetadataConfig()
        return MetadataConfig(
            subpath=data.get("subpath"),
        )

    def _parse_links(self, data: Any) -> tuple[LinkFilterConfig, ...]:
        if not isinstance(data, list):
            raise ConfigValidationError("'links' must be a list")

        configs: list[LinkFilterConfig] = []
        for item in data:
            if not isinstance(item, dict):
                raise ConfigValidationError("Each link filter must be a mapping")
            name = self._require_str(item, "name")
            filter_type = item.get("type", "frontmatter_field")
            if filter_type != "frontmatter_field":
                raise ConfigValidationError(
                    f"Link filter type '{filter_type}' is not supported in v1"
                )
            field = self._require_str(item, "field")
            on_unresolved = item.get("on_unresolved", "skip")
            if on_unresolved not in ("skip", "stub"):
                raise ConfigValidationError(
                    f"Invalid on_unresolved value '{on_unresolved}'"
                )
            style_data = item.get("style", {}) or {}
            style = EdgeStyle(
                color=style_data.get("color"),
                label=style_data.get("label"),
            )
            transitive_reduction = item.get("transitive_reduction", False)
            if not isinstance(transitive_reduction, bool):
                raise ConfigValidationError(
                    f"Field 'transitive_reduction' of link filter '{name}' must be a boolean"
                )
            configs.append(
                LinkFilterConfig(
                    name=name,
                    type=filter_type,
                    field=field,
                    on_unresolved=on_unresolved,
                    style=style,
                    transitive_reduction=transitive_reduction,
                )
            )
        return tuple(configs)

    def _parse_layout(self, data: Any) -> LayoutConfig:
        if not isinstance(data, dict):
            return LayoutConfig()
        return LayoutConfig(
            engine=data.get("engine", "igraph_sugiyama"),
            direction=data.get("direction", "LR"),
        )

    def _parse_output(self, data: Any) -> OutputConfig:
        if not isinstance(data, dict):
            raise ConfigValidationError("'output' must be a mapping")
        fmt = data.get("format", "obsidian_canvas")
        dest_str = self._require_str(data, "destination")
        return OutputConfig(format=fmt, destination=self.repo_root / dest_str)

    @staticmethod
    def _require_str(data: dict[str, Any], key: str) -> str:
        value = data.get(key)
        if not isinstance(value, str) or not value:
            raise ConfigValidationError(f"Missing or invalid required field '{key}'")
        return value

    @staticmethod
    def _require_str_list(data: dict[str, Any], key: str) -> list[str]:
        value = data.get(key)
        if not isinstance(value, list):
            raise ConfigValidationError(f"Field '{key}' must be a list of strings")
        return [str(item) for item in value]

    @staticmethod
    def _optional_str_list(value: Any) -> list[str] | None:
        if value is None:
            return None
        if not isinstance(value, list):
            raise ConfigValidationError("List field must contain strings")
        return [str(item) for item in value]
