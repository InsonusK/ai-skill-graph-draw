---
description: Create a reusable service
project_name: "{App}"
name: "service/{Service}.py"
element_kind: class
change_kind: create
---

# Goals
- Encapsulate stateful or dependency-heavy behavior used by Commands.

# Implementation changes
```python
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupService:
    def __init__(self, destination: Path) -> None:
        self.destination = destination

    def backup(self, files: list[Path]) -> None:
        logger.info("Backing up %d files to %s", len(files), self.destination)
        self.destination.mkdir(parents=True, exist_ok=True)
        for file in files:
            target = self.destination / file.name
            logger.debug("Copying %s to %s", file, target)
            shutil.copy2(file, target)
```

# Rules

## MUST
- Services should encapsulate a single responsibility.
- Use logging.

# Check list
- [ ] Service has a single responsibility.
