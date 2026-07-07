---
name: solution-default-cli
description: Define the base structure for Python CLI applications with clear separation between CLI, commands, and reusable services/functions
domain: python
type: architecture
version: 
tags:
  - skill/architecture/solution
  - python
  - cli
  - architecture
triggers:
  - Create a new Python CLI application
  - Add a new CLI command to an existing Python application
  - Refactor a script-like CLI into a layered structure
creates:
  - "{App}/cli.py"
  - "{App}/cli/{Command}.py"
  - "{App}/command/{Command}.py"
  - "{App}/functions/{Function}.py"
  - "{App}/service/{Service}.py"
extends:
depends_on:
  - "[logging-principle](.agents/skills/logging-principle/SKILL.md)"
adr:
---

# Goal
- Define the base structure for Python CLI applications.
- Separate terminal integration, business operations, and reusable code into distinct layers.
- Make CLI applications readable, testable, and easy to extend.

# Capabilities
- Clear separation of concerns: CLI parses arguments, Commands run business logic, Functions/Services provide reusable behavior.
- Easy to add new commands without changing existing CLI wiring.
- Business logic can be unit-tested independently of argument parsing.
- Consistent logging behavior across all CLI applications.

# Core Principles
- **CLI layer is thin**: it declares command names and arguments, converts `argparse`/`sys.argv` into typed Python values, configures logging, invokes the matching Command, and prints the result.
- **Commands are capabilities**: each Command represents one thing the application can do. It receives typed parameters, validates them, orchestrates Functions/Services, and returns a result.
- **Functions and Services are reusable**: pure helper functions live in `functions/`, stateful or dependency-heavy objects live in `service/`.
- **Logging is mandatory**: every CLI application must set up logging and support a `--debug` flag disabled by default, following [logging-principle](.agents/skills/logging-principle/SKILL.md).

# Requirements
SOLUTION:
- [logging-principle](.agents/skills/logging-principle/SKILL.md)
  - All CLI entry points must configure logging and expose `--debug`.
  - Logs must use specific messages and correct levels.

PYTHON STANDARD LIBRARY:
- `argparse`
  - CLI layer uses `argparse.ArgumentParser` to declare commands and arguments.
- `logging`
  - CLI layer configures the standard `logging` module.
- `sys`
  - `cli.py` uses `sys.exit` to return non-zero exit codes on failures.

# Template Skill Mutations
PROJECT:
- [{App} project](.agents/skills/solution-default-cli/Implementation/{App}.create.md) - create - root folder for the CLI application
  - [cli.py](.agents/skills/solution-default-cli/Implementation/{App}.cli.py.create.md) - create - entry point that wires subcommands and logging
  - [cli/__init__.py](.agents/skills/solution-default-cli/Implementation/{App}.cli.__init__.py.create.md) - create - make cli a package
  - [cli/{Command}.py](.agents/skills/solution-default-cli/Implementation/{App}.cli.{Command}.py.create.md) - create - argparse wiring for one command
  - [command/__init__.py](.agents/skills/solution-default-cli/Implementation/{App}.command.__init__.py.create.md) - create - make command a package
  - [command/{Command}.py](.agents/skills/solution-default-cli/Implementation/{App}.command.{Command}.py.create.md) - create - business logic for one command
  - [functions/__init__.py](.agents/skills/solution-default-cli/Implementation/{App}.functions.__init__.py.create.md) - create - make functions a package
  - [functions/{Function}.py](.agents/skills/solution-default-cli/Implementation/{App}.functions.{Function}.py.create.md) - create - reusable helper function example
  - [service/__init__.py](.agents/skills/solution-default-cli/Implementation/{App}.service.__init__.py.create.md) - create - make service a package
  - [service/{Service}.py](.agents/skills/solution-default-cli/Implementation/{App}.service.{Service}.py.create.md) - create - reusable service example

# Workflow
## Run CLI command (happy path)
1. User runs `python {App}/cli.py {command} --arg value` from the project root.
2. `cli.py` builds the argument parser and configures logging.
3. The matched `cli/{command}.py` subparser converts raw arguments into typed Python values.
4. `cli/{command}.py` calls the corresponding `command/{command}.py` function with typed parameters.
5. The Command validates parameters and orchestrates Functions and Services.
6. The Command returns a result object or value.
7. `cli/{command}.py` prints the result to the terminal.
8. `cli.py` exits with code `0`.

See [run-cli-command](.agents/skills/solution-default-cli/diagrams/run-cli-command.mmd)

## Validation failure
1. User provides invalid or missing arguments.
2. `argparse` prints usage and exits with code `2`.
3. If the Command detects a business validation failure, it logs an error and returns a non-zero exit code.

## Debug logging enabled
1. User adds `--debug`.
2. `cli.py` sets the root logger level to `DEBUG`.
3. Commands, Functions, and Services emit debug logs with specific context.

# Rules
## MUST
- [cli.py.create](.agents/skills/solution-default-cli/Implementation/{App}.cli.py.create.md#MUST)
- [cli/{Command}.py.create](.agents/skills/solution-default-cli/Implementation/{App}.cli.{Command}.py.create.md#MUST)
- [command/{Command}.py.create](.agents/skills/solution-default-cli/Implementation/{App}.command.{Command}.py.create.md#MUST)
- Every CLI entry point must accept a `--debug` flag and configure logging before any business logic runs.
- Commands must receive typed parameters, not raw argument namespaces.

## SHOULD
- Keep each `cli/{command}.py` file focused on a single command.
- Name the command module in `command/` the same as the CLI subcommand.

## SHOULD NOT
- [cli/{Command}.py.create](.agents/skills/solution-default-cli/Implementation/{App}.cli.{Command}.py.create.md#SHOULD NOT)
- Put business logic directly in the CLI layer.

## MUST NOT
- Use `print` for logging or operational messages (see [logging-principle](.agents/skills/logging-principle/SKILL.md)).
- Mix argument parsing and business logic in the same function or module.

# Anti-patterns
- **Mix CLI and Commands**
  - Consequence: code becomes hard to test, responsibilities blur, and adding new commands requires touching business logic.
  - Instead: keep CLI modules dedicated to argument parsing and output formatting; delegate work to Commands.
- **Use `print` instead of logging**
  - Consequence: logs cannot be aggregated, levels cannot be controlled, and `--debug` becomes impossible to implement consistently.
  - Instead: use the `logging` module and follow [logging-principle](.agents/skills/logging-principle/SKILL.md).
- **Pass raw `argparse.Namespace` into Commands**
  - Consequence: Commands become coupled to CLI wiring and cannot be reused or unit-tested.
  - Instead: convert `Namespace` attributes into typed variables or dataclasses before calling the Command.

# Check list
- [ ] `cli.py` exists at the project root and configures logging.
- [ ] `--debug` flag is available and disabled by default.
- [ ] `cli/` folder contains one module per subcommand with argument parsing only.
- [ ] `command/` folder contains one module per operation with business logic only.
- [ ] `functions/` folder exists for reusable helper functions.
- [ ] `service/` folder exists for reusable services.
- [ ] No `print` statements are used for logging or operational output.
- [ ] Commands receive typed parameters, not raw argument namespaces.
