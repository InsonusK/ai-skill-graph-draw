# Demo: diagram-renderer

This folder demonstrates how `diagram-renderer` builds an Obsidian Canvas from markdown files linked via frontmatter.

## Files

- `skills/**/*.skill.md` — sample skill notes with `depends_on` wiki-links.
- `diagrams.yaml` — render task configuration.
- `skills-map.canvas` — generated Obsidian Canvas diagram.

## Run

From the repository root:

```bash
python -m diagram_renderer render --config demo/diagrams.yaml
```

To force a full re-render:

```bash
python -m diagram_renderer render --config demo/diagrams.yaml --force
```

## What to try

1. Open `demo/skills-map.canvas` in Obsidian (or any JSON Canvas viewer).
2. Move a node manually.
3. Re-run the command — the moved node keeps its position if its content did not change.
4. Add a new `.skill.md` file and link it from an existing one — the new node appears next to its neighbors.
