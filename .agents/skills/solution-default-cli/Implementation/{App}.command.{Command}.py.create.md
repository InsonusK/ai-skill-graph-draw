---
description: Create one business operation
project_name: "{App}"
name: "command/{Command}.py"
element_kind: class
change_kind: create
---

# Goals
- Implement one operation using typed parameters.
- Validate input, orchestrate services/functions, and return a result.

# Core Principles
- Commands are the application's capabilities. They contain the key business logic.

# Naming convention
| use case | class name pattern | class name | file name pattern | file name |
| -------- | ------------------ | ---------- | ----------------- | --------- |
| Operation | - | - | command/{command}.py | command/backup.py |

# Implementation changes
```python
import logging
from dataclasses import dataclass
from pathlib import Path

import functions.helpers as helpers
import service.backup_service as backup_service

logger = logging.getLogger(__name__)


@dataclass
class BackupResult:
    message: str
    exit_code: int


def run(source: str, destination: str) -> BackupResult:
    logger.info("Backup command invoked for source '%s'", source)
    source_path = Path(source)
    destination_path = Path(destination)

    if not source_path.exists():
        logger.error("Source path does not exist: %s", source)
        return BackupResult(message=f"Source not found: {source}", exit_code=1)

    files = helpers.list_files(source_path)
    logger.info("Found %d files to back up", len(files))

    service = backup_service.BackupService(destination_path)
    try:
        service.backup(files)
    except Exception as exc:
        logger.critical("Backup failed: %s", exc, exc_info=True)
        return BackupResult(message=f"Backup failed: {exc}", exit_code=1)

    return BackupResult(message=f"Backup completed: {len(files)} files", exit_code=0)
```

# Rule changes

## MUST
- Accept typed parameters.
- Validate business preconditions.
- Log workflow milestones, warnings, errors, and caught exceptions.
- Return a result object with an exit code.

## SHOULD NOT
- Parse command-line arguments.

## MUST NOT
- Use `print`.

# Anti-patterns
- **Put CLI parsing here**
  - Consequence: the command cannot be unit-tested without `argparse`.
  - Instead: receive plain Python types.

# Check list
- [ ] Parameters are typed.
- [ ] Preconditions are validated.
- [ ] Result includes an exit code.
