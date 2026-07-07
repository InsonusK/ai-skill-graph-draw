---
description: Create the CLI entry point
project_name: "{App}"
name: "cli.py"
element_kind: class
change_kind: create
---

# Goals
- Build the argument parser and register subcommands.
- Configure logging before any command runs.
- Dispatch to the correct CLI subcommand module.

# Core Principles
- `cli.py` is the only file aware of all available subcommands.
- Logging configuration belongs here, not in individual commands.

# Naming convention
| use case | class name pattern | class name | file name pattern | file name |
| -------- | ------------------ | ---------- | ----------------- | --------- |
| Entry point | - | - | cli.py | cli.py |

# Implementation changes
`cli.py` must:
1. Import `argparse`, `logging`, and `sys`.
2. Import each `cli.{command}` module.
3. Add a `--debug` argument to the top-level parser.
4. Configure the root logger level to `DEBUG` if `--debug` is set, otherwise `INFO`.
5. Create subparsers for each command.
6. Delegate argument parsing to the matching `cli/{command}.py`.
   - Each `cli/{command}.py` registers its own `run` function via `parser.set_defaults(run=run)`.
   - `args.run(args)` dispatches to that function without `cli.py` knowing command names.
7. Exit with the return code provided by the command.

```python
import argparse
import logging
import sys

import cli.backup as backup_cli


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="{App}")
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    backup_cli.register(subparsers)

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # `args.run` was set by the active subcommand (`parser.set_defaults(run=run)`).
    # This keeps cli.py free of per-command `if` branches.
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
```

# Rule changes

## MUST
- Accept `--debug` and configure logging before invoking any command.
- Register every subcommand in `cli.py`.
- Use `sys.exit` to return the command's exit code.

## SHOULD NOT
- Contain business logic.

## MUST NOT
- Use `print` for output.

# Check list
- [ ] `--debug` flag is defined.
- [ ] Logging is configured before `args.run(args)`.
- [ ] All subcommands are registered.
