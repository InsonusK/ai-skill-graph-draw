"""Argument parser for the `render` subcommand."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from diagram_renderer.command import render as render_command
from diagram_renderer.service.config.loader import ConfigLoader, DEFAULT_CACHE_DIR
from diagram_renderer.service.graph import RenderTask

logger = logging.getLogger(__name__)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "render",
        help="Render or update diagram files from markdown links.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to YAML config file with one or more tasks.",
    )
    parser.add_argument(
        "--task-id",
        action="append",
        dest="task_ids",
        help="Run only specific task ids from config (can be repeated).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore cache and re-render everything.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help="Directory for per-task cache files.",
    )

    # Arguments for a single-task CLI invocation.
    parser.add_argument(
        "--include",
        action="append",
        dest="includes",
        help="Glob pattern for source files (repeatable).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        dest="excludes",
        help="Glob pattern to exclude source files (repeatable).",
    )
    parser.add_argument(
        "--link-field",
        default="depends_on",
        help="Frontmatter field containing wiki-links.",
    )
    parser.add_argument(
        "--subpath",
        help="Optional subpath added to file links in Canvas.",
    )
    parser.add_argument(
        "--on-unresolved",
        choices=("skip", "stub"),
        default="skip",
        help="Behavior for links pointing outside the source set.",
    )
    parser.add_argument(
        "--layout-engine",
        default="igraph_sugiyama",
        help="Layout engine name.",
    )
    parser.add_argument(
        "--layout-direction",
        default="LR",
        help="Layout direction (LR, RL, TB, BT).",
    )
    parser.add_argument(
        "--output-format",
        default="obsidian_canvas",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output destination path.",
    )
    parser.add_argument(
        "--edge-color",
        help="Edge color for single-task mode.",
    )
    parser.add_argument(
        "--edge-label",
        help="Edge label for single-task mode.",
    )
    parser.add_argument(
        "--transitive-reduction",
        action="store_true",
        help="Hide edges implied by a longer path between the same nodes.",
    )

    parser.set_defaults(run=run)


def run(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    single_task = _build_single_task(args, repo_root)

    if args.config is None and single_task is None:
        logger.error(
            "Either --config with a YAML file or single-task arguments "
            "(--include, --output) are required"
        )
        return 2

    if args.config is not None and single_task is not None:
        logger.error("Cannot combine --config with single-task arguments")
        return 2

    result = render_command.run(
        repo_root=repo_root,
        cache_dir=args.cache_dir,
        config_path=args.config,
        task_ids=args.task_ids,
        force=args.force,
        single_task=single_task,
    )

    print(
        f"Rendered: {result.rendered}, Skipped: {result.skipped}, Failed: {result.failed}"
    )
    return 1 if result.failed else 0


def _build_single_task(args: argparse.Namespace, repo_root: Path) -> RenderTask | None:
    if args.config is not None:
        return None

    if not args.includes or not args.output:
        return None

    loader = ConfigLoader(repo_root)
    return loader.load_single(
        task_id="cli-task",
        include=args.includes,
        exclude=args.excludes or [],
        link_field=args.link_field,
        subpath=args.subpath,
        output=args.output,
        on_unresolved=args.on_unresolved,
        layout_engine=args.layout_engine,
        layout_direction=args.layout_direction,
        output_format=args.output_format,
        edge_color=args.edge_color,
        edge_label=args.edge_label,
        transitive_reduction=args.transitive_reduction,
    )
