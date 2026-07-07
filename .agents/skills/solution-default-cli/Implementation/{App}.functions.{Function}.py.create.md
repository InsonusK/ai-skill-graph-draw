---
description: Create reusable helper functions
project_name: "{App}"
name: "functions/{Function}.py"
element_kind: class
change_kind: create
---

# Goals
- Provide pure, reusable helper functions used by Commands.

# Implementation changes
```python
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def list_files(directory: Path) -> list[Path]:
    logger.debug("Listing files in %s", directory)
    if not directory.is_dir():
        logger.warning("Directory does not exist or is not a directory: %s", directory)
        return []
    return [path for path in directory.rglob("*") if path.is_file()]
```

# Rules

## MUST
- Functions must be reusable and stateless where possible.
- Use logging instead of `print`.

# Check list
- [ ] Functions are stateless and reusable.
