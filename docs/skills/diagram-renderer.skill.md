---
name: diagram-renderer
description: How to invoke the diagram-renderer CLI to generate or update Obsidian Canvas diagrams from markdown files with frontmatter wiki-links
whenToUse: when you need to render or update one or more .canvas diagrams from markdown files that declare relationships via frontmatter wiki-links, when you need to scan a directory tree for diagrams.yaml configs and render each one, or when you need to call the diagram-renderer CLI inside this repository
tags:
  - python
  - cli
  - obsidian
  - canvas
  - diagram
  - markdown
---

# Goal
- Generate or update an Obsidian Canvas (`.canvas`) file from a set of markdown files.
- Use the relationships declared in YAML frontmatter wiki-links to build the graph.
- Call the CLI correctly from another agent or script with the right parameters and exit-code handling.

# Core Principle
- The CLI is the primary interface. Do not import internal modules directly unless you are extending the tool.
- Always tell the CLI where to read from (`--config` or `--include`) and where to write (`--output` or config `output.destination`).
- The tool caches task results by default; use `--force` when you want a full re-render.

# Rule

## MUST
- Install the package before use:
  - From GitHub: `pip install git+https://github.com/InsonusK/ai-skill-graph-draw.git`
  - Locally for development: `pip install -e ".[dev]"`
- Invoke the CLI through one of the supported entry points:
  - `diagram-renderer ...`
  - `python -m diagram_renderer ...`
- Choose the right command:
  - `render` for a single config file or a single CLI-defined task.
  - `scan` to discover config files recursively and render each one.
- Provide either `--config PATH` with a YAML file **or** single-task arguments (`--include` and `--output`) to `render`. Never provide both.
- Set `--link-field NAME` when using single-task mode. Default is `depends_on`.
- Specify the output destination. In single-task mode use `--output PATH`. In config mode set `output.destination` for every task.
- Handle exit codes:
  - `0` — success; all requested tasks rendered or skipped.
  - `1` — one or more tasks failed.
  - `2` — CLI argument error (e.g. missing `--include` or combining `--config` with single-task args).
- Use `scan DIRECTORY` to find all `diagrams.yaml` files under `DIRECTORY`. Default directory is the current working directory.
- Use `scan --filename NAME` when the config files have a name other than `diagrams.yaml`.
- Use `--force` when the cache may be stale or when you need a deterministic full re-render.
- Ensure markdown frontmatter wiki-links are valid YAML. Quote links to avoid parsing ambiguity:
  ```yaml
  depends_on:
    - "[[skills/other.skill.md]]"
    - "[[skills/another.skill.md|Alias]]"
  ```

## SHOULD
- Use a YAML config file when rendering more than one diagram or when the task has non-default options.
- Use `--task-id ID` to run only selected tasks from a config file (repeatable). Works with both `render` and `scan`.
- Use `scan` when a repository contains multiple diagrams.yaml files in different folders.
- Use `--cache-dir PATH` to keep cache files outside the default `.cache/diagram-renderer` when needed.
- Prefer `igraph_sugiyama` (default) for complex graphs to reduce edge crossings.
- Add `--transitive-reduction` in single-task mode to hide redundant edges.
- Use `scan --cache-dir PATH` to keep all discovered tasks' cache in one place.
- Set `--on-unresolved stub` only when external links should produce placeholder nodes.

## MAY
- Use `--edge-color VALUE` and `--edge-label TEXT` in single-task mode to style edges.
- Use `--subpath ANCHOR` to append an anchor (e.g. `#Capabilities`) to every node link in the Canvas.
- Use `--layout-engine layered` when you want a pure-Python layout without the `python-igraph` dependency.

## SHOULD NOT
- Combine `--config` with single-task arguments such as `--include`, `--exclude`, or `--output`.
- Treat `layout.direction` (`LR`, `RL`, `TB`, `BT`) as a guarantee of Canvas `fromSide`/`toSide`; the writer computes sides from actual node coordinates, not from this setting.
- Rely on the default cache when files were deleted or renamed; use `--force` instead.

## MUST NOT
- Use any `output.format` other than `obsidian_canvas` in v1.
- Use any link filter `type` other than `frontmatter_field` in v1.
- Call internal service modules directly from outside the package unless the task explicitly requires extending the tool.

# Anti-patterns

- **Calling the CLI without specifying input and output**
  - Example: `diagram-renderer render`
  - Consequence: the command exits with code `2` because neither `--config` nor `--include/--output` is provided.
  - Instead: run `diagram-renderer render --config diagrams.yaml` or `diagram-renderer render --include "skills/**/*.skill.md" --output skills-map.canvas`.

- **Mixing config mode and single-task mode**
  - Example: `diagram-renderer render --config diagrams.yaml --include "docs/**/*.md"`
  - Consequence: the command exits with code `2`.
  - Instead: put all includes, excludes, and output in the YAML config or omit `--config` and pass all options as CLI flags.

- **Leaving wiki-links unquoted in YAML frontmatter**
  - Example: `depends_on:\n  - [[skills/other.skill.md]]`
  - Consequence: YAML may parse `[[...]]` as nested lists and the link is lost or malformed.
  - Instead: quote every wiki-link: `"[[skills/other.skill.md]]"`.

- **Expecting `layout.direction` to control Canvas edge sides**
  - Example: setting `layout.direction: TB` and assuming all edges attach to `bottom`/`top`.
  - Consequence: the writer derives `fromSide`/`toSide` from computed node centers, so the visual result depends on layout, not on this option.
  - Instead: use `layout.direction` only as a hint to the layout engine; inspect the resulting `.canvas` file if exact sides matter.

- **Ignoring exit code `1` and assuming the diagram was produced**
  - Example: running the tool in a script without checking `$?`.
  - Consequence: downstream steps may use a missing or stale `.canvas` file.
  - Instead: capture the exit code and fail the agent step if it is non-zero.

# Example

## Install and run with a YAML config

```bash
pip install git+https://github.com/InsonusK/ai-skill-graph-draw.git
cat > diagrams.yaml <<'YAML'
cache_dir: .cache/diagram-renderer

tasks:
  - id: skills-map
    source:
      include:
        - "skills/**/*.skill.md"
    links:
      - name: depends_on
        type: frontmatter_field
        field: depends_on
    output:
      format: obsidian_canvas
      destination: "skills-map.canvas"
YAML

diagram-renderer render --config diagrams.yaml
```

## Run a single task from CLI flags

```bash
diagram-renderer render \
  --include "skills/**/*.skill.md" \
  --link-field depends_on \
  --output "skills-map.canvas"
```

## Run only one task from a config

```bash
diagram-renderer render --config diagrams.yaml --task-id skills-map
```

## Force re-render

```bash
diagram-renderer render --config diagrams.yaml --force
```

## Force re-render during scan

```bash
diagram-renderer scan . --force
```

# Check list
- [ ] The package is installed or the local editable install is available.
- [ ] The chosen entry point (`diagram-renderer` or `python -m diagram_renderer`) works in the environment.
- [ ] The correct command is chosen: `render` for one config/task, `scan` for multiple config files.
- [ ] Input is provided through `--config` or through `--include` plus `--output`, but not both (for `render`).
- [ ] The frontmatter field used for links matches `--link-field` (default `depends_on`).
- [ ] The output destination is specified and writable.
- [ ] Wiki-links in frontmatter are quoted to avoid YAML parsing issues.
- [ ] Exit code `0`, `1`, or `2` is checked and handled by the caller.
- [ ] For `scan`, the directory and `--filename` match the intended config files.
- [ ] `--force` is used when the cache may be stale.
