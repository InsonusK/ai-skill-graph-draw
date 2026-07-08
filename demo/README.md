# Demo: diagram-renderer

This folder demonstrates how `diagram-renderer` builds an Obsidian Canvas from markdown files linked via frontmatter, and showcases the main config options from [`docs/configuration.md`](../docs/configuration.md).

All paths in this demo are relative to the `demo/` directory.

## Files

- `skills/**/*.skill.md` — sample skill notes with `depends_on` and `extends` wiki-links.
- `diagrams.yaml` — three render tasks over the *same* source files, each changing exactly one setting so the effect is easy to isolate:

  | Task id | `transitive_reduction` | `layout.engine` | Output |
  |---|---|---|---|
  | `demo-skills-depends-on` | `true` | `layered` | `skills-map.canvas` |
  | `demo-skills-depends-on-no-reduction` | `false` | `layered` | `skills-map-no-reduction.canvas` |
  | `demo-skills-depends-on-igraph-sugiyama` | `true` | `igraph_sugiyama` | `skills-map-igraph-sugiyama.canvas` |

## The sample graph

- `depends_on` chain: `domain-driven-design` -> `entities` -> `value-objects` -> `clean-code` -> `unit-testing`.
- `extends`: `entities` -> `domain-driven-design` and `value-objects` -> `domain-driven-design`.
- `domain-driven-design.skill.md` also declares a **direct** `depends_on` link to `value-objects.skill.md`. That link is redundant — it's already implied by the DDD -> Entities -> Value Objects chain — so `transitive_reduction: true` on the `depends_on` filter hides it from the rendered canvas. Only the 4 non-redundant edges are drawn.
- `entities.skill.md` and `value-objects.skill.md` each also declare an `extends` link back to `domain-driven-design.skill.md`. This is a second, independently styled filter on the same diagram (`docs/configuration.md#несколько-фильтров-на-одной-диаграмме`). It has no `transitive_reduction`, and reduction never borrows chains across filters, so both `extends` edges are always drawn regardless of what `depends_on` looks like.
- `demo-skills-depends-on-igraph-sugiyama` renders the exact same 6-edge graph as `demo-skills-depends-on`, just with `layout.engine: igraph_sugiyama` instead of `layered` (`docs/configuration.md#движки-раскладки`). Open both canvases side by side: `layered` lines every node up on a single row (`y=0.0`), while `igraph_sugiyama` spreads Entities/DDD onto a second row to reduce edge crossings from the `extends` back-edges — same nodes and edges, different coordinates, because `LayoutEngine.place()` is pluggable and swappable per task.

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
2. Open `skills-map-no-reduction.canvas` next to it — same source files, `transitive_reduction: false` — and see the direct DDD -> Value Objects edge reappear.
3. Open `skills-map-igraph-sugiyama.canvas` next to `skills-map.canvas` — same graph, different `layout.engine`. Compare node coordinates: `layered` keeps a single row, `igraph_sugiyama` spreads nodes onto two rows.
4. Compare the colors: `depends_on` edges are color `"4"`, `extends` edges are color `"2"` — two link filters rendered on one canvas.
5. Move a node manually.
6. Re-run the command — the moved node keeps its position if its content did not change, regardless of which layout engine the task uses.
7. Add a new `.skill.md` file and link it from an existing one — the new node appears next to its neighbors.
8. Try `layout.direction: TB` on any task and re-render with `--force` to see the edge-connector sides change (note: only edge sides change, not node coordinates — see `docs/configuration.md`).

## Learn more

- Full config reference: [`docs/configuration.md`](../docs/configuration.md)
- CLI usage: [`docs/usage.md`](../docs/usage.md)
