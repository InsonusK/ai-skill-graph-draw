"""Entry point for `python -m diagram_renderer`."""

from __future__ import annotations

import argparse
import logging
import sys

from diagram_renderer.cli import render as render_cli
from diagram_renderer.cli import scan as scan_cli


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="diagram-renderer")
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    render_cli.register(subparsers)
    scan_cli.register(subparsers)

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
