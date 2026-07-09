"""Argument parser for the `scan` subcommand."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from diagram_renderer.command import scan as scan_command
from diagram_renderer.service.config.loader import DEFAULT_CACHE_DIR

logger = logging.getLogger(__name__)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "scan",
        help="Find diagrams.yaml files and render each one.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--filename",
        default="diagrams.yaml",
        help="Name of the config file to look for (default: diagrams.yaml).",
    )
    parser.add_argument(
        "--task-id",
        action="append",
        dest="task_ids",
        help="Run only specific task ids from each config (can be repeated).",
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

    parser.set_defaults(run=run)


def run(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    directory = Path(args.directory)
    if not directory.is_absolute():
        directory = repo_root / directory

    result = scan_command.run(
        repo_root=repo_root,
        directory=directory,
        filename=args.filename,
        task_ids=args.task_ids,
        force=args.force,
        cache_dir=args.cache_dir,
    )

    print(
        f"Found configs: {result.found}, "
        f"Rendered: {result.rendered}, Skipped: {result.skipped}, Failed: {result.failed}"
    )
    return 1 if result.failed else 0
