---
description: Create the root folder for a CLI application
name: "{App}"
element_kind: project
change_kind: create
---

# Goals
- Provide a home for the CLI application with a layered structure.

# Core Principles
- Separate CLI, Command, Functions, and Service into their own directories.

# Structure

## Project Structure
```
/{App}
  /cli
    __init__.py
    backup.py
  /command
    __init__.py
    backup.py
  /functions
    __init__.py
    helpers.py
  /service
    __init__.py
    backup_service.py
  cli.py
```

## Directory and class skills
| Directory | file | Description |
| --------- | ---- | ----------- |
| /cli | backup.py | Declares one subcommand, parses its arguments, calls the matching Command, prints output. |
| /command | backup.py | Implements the backup operation with typed parameters. |
| /functions | helpers.py | Reusable pure functions. |
| /service | backup_service.py | Reusable service objects. |
| / | cli.py | Entry point: builds parser, configures logging, dispatches to cli modules. |

# Allowed Dependencies
- Standard library only (`argparse`, `logging`, `sys`).

# Rules

## MUST
- Create `/cli`, `/command`, `/functions`, and `/service` directories.

# Anti-patterns
- **Place all code in a single script**
  - Consequence: CLI parsing, business logic, and reusable helpers become tightly coupled.
  - Instead: split code into the four layers.

# Check list
- [ ] `/cli`, `/command`, `/functions`, `/service` directories exist.
- [ ] `cli.py` is at the project root.
