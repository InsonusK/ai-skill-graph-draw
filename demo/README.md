# Demo: diagram-renderer

This folder demonstrates how `diagram-renderer` builds an Obsidian Canvas from markdown files linked via frontmatter, and showcases the main config options from [`docs/configuration.md`](../docs/configuration.md).

All paths in this demo are relative to the `demo/` directory.

## Files

- `skills/**/*.skill.md` — sample skill notes with `depends_on` and `extends` wiki-links.
- `diagrams.yaml` — render task configuration.
- `skills-map.canvas` — generated Obsidian Canvas diagram.

## The sample graph

- `depends_on` chain: `domain-driven-design` -> `entities` -> `value-objects` -> `clean-code` -> `unit-testing`.
- `extends`: `entities` -> `domain-driven-design` and `value-objects` -> `domain-driven-design`.
- `domain-driven-design.skill.md` also declares a **direct** `depends_on` link to `value-objects.skill.md`. That link is redundant — it's already implied by the DDD -> Entities -> Value Objects chain — so `transitive_reduction: true` on the `depends_on` filter hides it from the rendered canvas. Only the 4 non-redundant edges are drawn.
- `entities.skill.md` and `value-objects.skill.md` each also declare an `extends` link back to `domain-driven-design.skill.md`. This is a second, independently styled filter on the same diagram (`docs/configuration.md#несколько-фильтров-на-одной-диаграмме`). It has no `transitive_reduction`, and reduction never borrows chains across filters, so both `extends` edges are always drawn regardless of what `depends_on` looks like.

## Run

From this directory (`demo/`):

```bash
cd demo
PYTHONPATH=.. ../.venv/bin/python -m diagram_renderer render --config diagrams.yaml
```

Or, if `diagram_renderer` is installed in the active Python environment:

```bash
cd demo
python -m diagram_renderer render --config diagrams.yaml
```

To force a full re-render:

```bash
cd demo
PYTHONPATH=.. ../.venv/bin/python -m diagram_renderer render --config diagrams.yaml --force
```

## What to try

1. Open `skills-map.canvas` in Obsidian (or any JSON Canvas viewer). Note there is no direct arrow from Domain-Driven Design to Value Objects, even though `domain-driven-design.skill.md` lists it in `depends_on` — it's hidden by `transitive_reduction`.
2. Set `transitive_reduction: false` (or delete the line) on the `depends_on` filter in `diagrams.yaml`, re-render with `--force`, and see the direct DDD -> Value Objects edge reappear.
3. Compare the colors: `depends_on` edges are color `"4"`, `extends` edges are color `"2"` — two link filters rendered on one canvas.
4. Move a node manually.
5. Re-run the command — the moved node keeps its position if its content did not change.
6. Add a new `.skill.md` file and link it from an existing one — the new node appears next to its neighbors.

## Learn more

- Full config reference: [`docs/configuration.md`](../docs/configuration.md)
- CLI usage: [`docs/usage.md`](../docs/usage.md)
