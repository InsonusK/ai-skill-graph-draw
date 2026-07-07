---
description: Create argparse wiring for one command
project_name: "{App}"
name: "cli/{Command}.py"
element_kind: class
change_kind: create
---

# Goals
- Declare one subcommand and its arguments.
- Convert parsed arguments into typed Python values.
- Call `command/{command}.py` and print the result.

# Core Principles
- This module knows nothing about the business logic; it only translates terminal input to Python types.

# Naming convention
| use case | class name pattern | class name | file name pattern | file name |
| -------- | ------------------ | ---------- | ----------------- | --------- |
| Subcommand wiring | - | - | cli/{command}.py | cli/backup.py |

# Implementation changes
```python
import argparse
import logging

import command.backup as backup_command

logger = logging.getLogger(__name__)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("backup", help="Create a backup.")
    parser.add_argument("--source", required=True, help="Path to back up.")
    parser.add_argument("--destination", required=True, help="Backup destination.")
    # Store this module's `run` in the parsed args so cli.py can dispatch to it.
    parser.set_defaults(run=run)


def run(args: argparse.Namespace) -> int:
    logger.info("Starting backup from '%s' to '%s'", args.source, args.destination)
    result = backup_command.run(source=args.source, destination=args.destination)
    print(result.message)
    return result.exit_code
```

# Rule changes

## MUST
- Convert raw `Namespace` attributes into named/typed arguments before calling the Command.
- Return an integer exit code.

## SHOULD NOT
- Validate business rules.

## MUST NOT
- Call `print` for logging.
- Perform business logic directly.

# Anti-patterns
- **Parse arguments inside the Command**
  - Consequence: the Command becomes tied to `argparse` and cannot be reused.
  - Instead: do all parsing here and pass typed values to the Command.

# Check list
- [ ] `register` adds the subcommand to the parent parser.
- [ ] `run` extracts typed values and calls the Command.
- [ ] Result is printed to the terminal.
