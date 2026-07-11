"""Tests for service-layer components."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from diagram_renderer.service.cache.manager import CacheManager
from diagram_renderer.service.config.loader import ConfigLoader, ConfigValidationError
from diagram_renderer.service.diff.diff_engine import DiffEngine
from diagram_renderer.service.graph import (
    Edge,
    EdgeStyle,
    Graph,
    LayoutConfig,
    LinkFilterConfig,
    MetadataConfig,
    Node,
    OutputConfig,
    Rect,
    RenderTask,
    SourceConfig,
)
from diagram_renderer.service.graph_builder.builder import GraphBuilder
from diagram_renderer.service.layout.factory import build_layout_engine
from diagram_renderer.service.layout.layered import LayeredLayoutEngine
from diagram_renderer.service.layout.sugiyama_igraph import IgraphSugiyamaLayoutEngine
from diagram_renderer.service.link_filters.factory import build_link_filter
from diagram_renderer.service.link_filters.frontmatter_field import FrontmatterFieldLinkFilter
from diagram_renderer.service.link_resolver.resolver import LinkResolver
from diagram_renderer.service.metadata_extractor.extractor import MetadataExtractor
from diagram_renderer.service.orchestrator.pipeline import Orchestrator
from diagram_renderer.service.source_collector.collector import SourceCollector
from diagram_renderer.service.writers.factory import build_writer
from diagram_renderer.service.writers.obsidian_canvas import ObsidianCanvasWriter


class TestConfigLoader:
    def test_loads_valid_config(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "cache_dir: .cache\n"
            "tasks:\n"
            "  - id: test-task\n"
            "    source:\n"
            "      include:\n"
            "        - '*.md'\n"
            "    metadata:\n"
            "      label_field: name\n"
            "      subpath: '#Foo'\n"
            "    links:\n"
            "      - name: depends_on\n"
            "        type: frontmatter_field\n"
            "        field: depends_on\n"
            "        style:\n"
            "          color: '4'\n"
            "          label: depends on\n"
            "    layout:\n"
            "      engine: layered\n"
            "      direction: LR\n"
            "    output:\n"
            "      format: obsidian_canvas\n"
            "      destination: out.canvas\n"
        )
        loader = ConfigLoader(tmp_path)
        tasks = loader.load_from_file(config_path)
        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "test-task"
        assert task.source.include == ("*.md",)
        assert task.metadata.subpath == "#Foo"
        assert task.output.destination == tmp_path / "out.canvas"

    def test_skips_invalid_task(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "tasks:\n"
            "  - id: bad\n"
            "  - id: good\n"
            "    source:\n"
            "      include:\n"
            "        - '*.md'\n"
            "    links:\n"
            "      - name: depends_on\n"
            "        field: depends_on\n"
            "    output:\n"
            "      destination: out.canvas\n"
        )
        loader = ConfigLoader(tmp_path)
        tasks = loader.load_from_file(config_path)
        assert len(tasks) == 1
        assert tasks[0].id == "good"

    def test_invalid_on_unresolved(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "tasks:\n"
            "  - id: bad\n"
            "    source:\n"
            "      include:\n"
            "        - '*.md'\n"
            "    links:\n"
            "      - name: depends_on\n"
            "        field: depends_on\n"
            "        on_unresolved: invalid\n"
            "    output:\n"
            "      destination: out.canvas\n"
        )
        loader = ConfigLoader(tmp_path)
        tasks = loader.load_from_file(config_path)
        assert tasks == []

    def test_parses_transitive_reduction(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "tasks:\n"
            "  - id: t\n"
            "    source:\n"
            "      include:\n"
            "        - '*.md'\n"
            "    links:\n"
            "      - name: depends_on\n"
            "        field: depends_on\n"
            "        transitive_reduction: true\n"
            "    output:\n"
            "      destination: out.canvas\n"
        )
        loader = ConfigLoader(tmp_path)
        tasks = loader.load_from_file(config_path)
        assert len(tasks) == 1
        assert tasks[0].links[0].transitive_reduction is True

    def test_transitive_reduction_defaults_to_false(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "tasks:\n"
            "  - id: t\n"
            "    source:\n"
            "      include:\n"
            "        - '*.md'\n"
            "    links:\n"
            "      - name: depends_on\n"
            "        field: depends_on\n"
            "    output:\n"
            "      destination: out.canvas\n"
        )
        loader = ConfigLoader(tmp_path)
        tasks = loader.load_from_file(config_path)
        assert tasks[0].links[0].transitive_reduction is False

    def test_invalid_transitive_reduction_type(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "tasks:\n"
            "  - id: bad\n"
            "    source:\n"
            "      include:\n"
            "        - '*.md'\n"
            "    links:\n"
            "      - name: depends_on\n"
            "        field: depends_on\n"
            "        transitive_reduction: not-a-bool\n"
            "    output:\n"
            "      destination: out.canvas\n"
        )
        loader = ConfigLoader(tmp_path)
        tasks = loader.load_from_file(config_path)
        assert tasks == []


class TestSourceCollector:
    def test_collects_and_hashes(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("a")
        (tmp_path / "b.md").write_text("b")
        collector = SourceCollector(tmp_path)
        files, file_hash = collector.collect(
            SourceConfig(include=("*.md",), exclude=())
        )
        assert files == [tmp_path / "a.md", tmp_path / "b.md"]
        assert isinstance(file_hash, str)


class TestFrontmatterFieldLinkFilter:
    def test_extracts_links(self, tmp_path: Path) -> None:
        filter_ = FrontmatterFieldLinkFilter(
            "depends_on", "depends_on", EdgeStyle()
        )
        links = filter_.extract(
            tmp_path / "a.md",
            "",
            {"depends_on": ["[[b]]", "[[c|C]]"]},
        )
        assert [link.text for link in links] == ["b", "c|C"]

    def test_extracts_links_from_yaml_nested_lists(self, tmp_path: Path) -> None:
        filter_ = FrontmatterFieldLinkFilter(
            "depends_on", "depends_on", EdgeStyle()
        )
        links = filter_.extract(
            tmp_path / "a.md",
            "",
            {"depends_on": [["b"], ["c|C"]]},
        )
        assert [link.text for link in links] == ["b", "c|C"]

    def test_missing_field_returns_empty(self, tmp_path: Path) -> None:
        filter_ = FrontmatterFieldLinkFilter(
            "depends_on", "depends_on", EdgeStyle()
        )
        assert filter_.extract(tmp_path / "a.md", "", {}) == []


class TestLinkFilterFactory:
    def test_builds_frontmatter_field_filter(self) -> None:
        config = LinkFilterConfig("depends_on", "frontmatter_field", "depends_on")
        filter_ = build_link_filter(config)
        assert isinstance(filter_, FrontmatterFieldLinkFilter)

    def test_unsupported_type_raises(self) -> None:
        config = LinkFilterConfig("depends_on", "regex", "depends_on")
        with pytest.raises(ValueError):
            build_link_filter(config)


class TestMetadataExtractor:
    def test_extracts_id_and_stem_label(self, tmp_path: Path) -> None:
        file = tmp_path / "skills" / "a.md"
        file.parent.mkdir()
        file.write_text("")
        extractor = MetadataExtractor(tmp_path, MetadataConfig())
        meta = extractor.extract(file, {"name": "Nice Name"})
        assert meta.id == "skills/a.md"
        assert meta.label == "a"

    def test_fallback_to_stem(self, tmp_path: Path) -> None:
        file = tmp_path / "a.md"
        file.write_text("")
        extractor = MetadataExtractor(tmp_path, MetadataConfig())
        meta = extractor.extract(file, {})
        assert meta.label == "a"


class TestLinkResolver:
    def test_resolves_internal_link(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("")
        resolver = LinkResolver(tmp_path, {"target.md"}, "skip")
        link = type("Link", (), {"path_part": lambda self: "target.md"})()
        assert resolver.resolve(tmp_path / "source.md", link) == "target.md"

    def test_skips_nonexistent_file(self, tmp_path: Path) -> None:
        resolver = LinkResolver(tmp_path, set(), "skip")
        link = type("Link", (), {"path_part": lambda self: "missing.md"})()
        assert resolver.resolve(tmp_path / "source.md", link) is None

    def test_on_unresolved_stub(self, tmp_path: Path) -> None:
        target = tmp_path / "external.md"
        target.write_text("")
        resolver = LinkResolver(tmp_path, set(), "stub")
        link = type("Link", (), {"path_part": lambda self: "external.md"})()
        assert resolver.resolve(tmp_path / "source.md", link) == "external.md"


class TestGraphBuilder:
    def test_builds_simple_graph(self, tmp_path: Path) -> None:
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("---\ndepends_on:\n  - [[b.md]]\n---\n")
        b.write_text("---\nname: B\n---\n")

        extractor = MetadataExtractor(tmp_path, MetadataConfig())
        builder = GraphBuilder(
            tmp_path,
            extractor,
            (LinkFilterConfig("depends_on", "frontmatter_field", "depends_on"),),
        )
        graph = builder.build([a, b])
        assert {node.id for node in graph.nodes} == {"a.md", "b.md"}
        assert len(graph.edges) == 1
        assert graph.edges[0].from_id == "a.md"
        assert graph.edges[0].to_id == "b.md"

    def test_transitive_reduction_drops_redundant_edge(self, tmp_path: Path) -> None:
        # A -> B -> C and a direct A -> C: the direct edge is implied by the
        # chain and should be hidden when transitive_reduction is enabled.
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        c = tmp_path / "c.md"
        a.write_text("---\ndepends_on:\n  - [[b.md]]\n  - [[c.md]]\n---\n")
        b.write_text("---\ndepends_on:\n  - [[c.md]]\n---\n")
        c.write_text("---\nname: C\n---\n")

        extractor = MetadataExtractor(tmp_path, MetadataConfig())
        builder = GraphBuilder(
            tmp_path,
            extractor,
            (
                LinkFilterConfig(
                    "depends_on",
                    "frontmatter_field",
                    "depends_on",
                    transitive_reduction=True,
                ),
            ),
        )
        graph = builder.build([a, b, c])
        pairs = {(edge.from_id, edge.to_id) for edge in graph.edges}
        assert pairs == {("a.md", "b.md"), ("b.md", "c.md")}

    def test_transitive_reduction_disabled_keeps_redundant_edge(self, tmp_path: Path) -> None:
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        c = tmp_path / "c.md"
        a.write_text("---\ndepends_on:\n  - [[b.md]]\n  - [[c.md]]\n---\n")
        b.write_text("---\ndepends_on:\n  - [[c.md]]\n---\n")
        c.write_text("---\nname: C\n---\n")

        extractor = MetadataExtractor(tmp_path, MetadataConfig())
        builder = GraphBuilder(
            tmp_path,
            extractor,
            (LinkFilterConfig("depends_on", "frontmatter_field", "depends_on"),),
        )
        graph = builder.build([a, b, c])
        pairs = {(edge.from_id, edge.to_id) for edge in graph.edges}
        assert pairs == {("a.md", "b.md"), ("b.md", "c.md"), ("a.md", "c.md")}

    def test_transitive_reduction_scoped_per_filter(self, tmp_path: Path) -> None:
        # depends_on forms A -> B -> C plus a redundant A -> C, but the
        # extends filter only has a single A -> C edge and must survive
        # even though depends_on has a matching (u, v) chain.
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        c = tmp_path / "c.md"
        a.write_text(
            "---\n"
            "depends_on:\n"
            "  - [[b.md]]\n"
            "  - [[c.md]]\n"
            "extends:\n"
            "  - [[c.md]]\n"
            "---\n"
        )
        b.write_text("---\ndepends_on:\n  - [[c.md]]\n---\n")
        c.write_text("---\nname: C\n---\n")

        extractor = MetadataExtractor(tmp_path, MetadataConfig())
        builder = GraphBuilder(
            tmp_path,
            extractor,
            (
                LinkFilterConfig(
                    "depends_on",
                    "frontmatter_field",
                    "depends_on",
                    transitive_reduction=True,
                ),
                LinkFilterConfig("extends", "frontmatter_field", "extends"),
            ),
        )
        graph = builder.build([a, b, c])
        triples = {(edge.from_id, edge.to_id, edge.filter_name) for edge in graph.edges}
        assert triples == {
            ("a.md", "b.md", "depends_on"),
            ("b.md", "c.md", "depends_on"),
            ("a.md", "c.md", "extends"),
        }

    def test_expand_sources_includes_linked_target_files(self, tmp_path: Path) -> None:
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("---\ndepends_on:\n  - [[b.md]]\n---\n")
        b.write_text("---\nname: B\n---\n")

        extractor = MetadataExtractor(tmp_path, MetadataConfig())
        builder = GraphBuilder(
            tmp_path,
            extractor,
            (LinkFilterConfig("depends_on", "frontmatter_field", "depends_on"),),
        )
        expanded = builder.expand_sources([a])
        assert expanded == [a, b]

    def test_expand_sources_ignores_missing_targets(self, tmp_path: Path) -> None:
        a = tmp_path / "a.md"
        a.write_text("---\ndepends_on:\n  - [[missing.md]]\n---\n")

        extractor = MetadataExtractor(tmp_path, MetadataConfig())
        builder = GraphBuilder(
            tmp_path,
            extractor,
            (LinkFilterConfig("depends_on", "frontmatter_field", "depends_on"),),
        )
        expanded = builder.expand_sources([a])
        assert expanded == [a]

    def test_expand_sources_follows_link_chains(self, tmp_path: Path) -> None:
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        c = tmp_path / "c.md"
        a.write_text("---\ndepends_on:\n  - [[b.md]]\n---\n")
        b.write_text("---\ndepends_on:\n  - [[c.md]]\n---\n")
        c.write_text("---\nname: C\n---\n")

        extractor = MetadataExtractor(tmp_path, MetadataConfig())
        builder = GraphBuilder(
            tmp_path,
            extractor,
            (LinkFilterConfig("depends_on", "frontmatter_field", "depends_on"),),
        )
        expanded = builder.expand_sources([a])
        assert expanded == [a, b, c]

    def test_build_with_expanded_sources_creates_edges(self, tmp_path: Path) -> None:
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("---\ndepends_on:\n  - [[b.md]]\n---\n")
        b.write_text("---\nname: B\n---\n")

        extractor = MetadataExtractor(tmp_path, MetadataConfig())
        builder = GraphBuilder(
            tmp_path,
            extractor,
            (LinkFilterConfig("depends_on", "frontmatter_field", "depends_on"),),
        )
        graph = builder.build(builder.expand_sources([a]))
        assert {node.id for node in graph.nodes} == {"a.md", "b.md"}
        assert len(graph.edges) == 1
        assert graph.edges[0].from_id == "a.md"
        assert graph.edges[0].to_id == "b.md"


class TestCacheManager:
    def test_save_and_load(self, tmp_path: Path) -> None:
        cache = CacheManager(tmp_path)
        node = Node(
            id="a.md",
            label="A",
            subpath=None,
            source_file=tmp_path / "a.md",
            content_hash="abc",
        )
        graph = Graph(nodes=(node,), edges=())
        positions = {"a.md": Rect(10.0, 20.0, 100.0, 100.0)}
        cache.save("task", "filehash", graph, positions)

        assert cache.is_file_set_unchanged("task", "filehash") is True
        assert cache.is_file_set_unchanged("task", "other") is False
        assert cache.get_node_positions("task", graph) == positions
        assert cache.get_node_hashes("task") == {"a.md": "abc"}


class TestDiffEngine:
    def test_empty_destination(self) -> None:
        diff = DiffEngine()
        node = Node(
            id="a.md",
            label="A",
            subpath=None,
            source_file=Path("/a.md"),
            content_hash="abc",
        )
        graph = Graph(nodes=(node,), edges=())
        result = diff.diff(graph, Path("/nonexistent.canvas"))
        assert result.added == {"a.md"}
        assert result.removed == set()
        assert result.unchanged == set()

    def test_reads_existing_positions(self, tmp_path: Path) -> None:
        canvas = tmp_path / "out.canvas"
        canvas.write_text(
            json.dumps(
                {
                    "nodes": [
                        {
                            "id": "a.md",
                            "type": "file",
                            "file": "a.md",
                            "x": 100,
                            "y": 200,
                            "width": 300,
                            "height": 400,
                        }
                    ],
                    "edges": [],
                }
            )
        )
        diff = DiffEngine()
        node = Node(
            id="a.md",
            label="A",
            subpath=None,
            source_file=tmp_path / "a.md",
            content_hash="abc",
        )
        graph = Graph(nodes=(node,), edges=())
        result = diff.diff(graph, canvas)
        assert result.unchanged == {"a.md"}
        assert result.positions["a.md"] == Rect(100.0, 200.0, 300.0, 400.0)

    def test_invalid_canvas_raises(self, tmp_path: Path) -> None:
        canvas = tmp_path / "out.canvas"
        canvas.write_text("not json")
        diff = DiffEngine()
        with pytest.raises(ValueError):
            diff.diff(Graph(nodes=(), edges=()), canvas)


class TestLayeredLayoutEngine:
    def test_full_layout(self) -> None:
        nodes = (
            Node("a.md", "A", None, Path("/a.md"), "h1"),
            Node("b.md", "B", None, Path("/b.md"), "h2"),
        )
        edges = (Edge("a.md", "b.md", "depends_on"),)
        graph = Graph(nodes=nodes, edges=edges)
        engine = LayeredLayoutEngine()
        positions = engine.place(graph, {})
        assert "a.md" in positions
        assert "b.md" in positions
        assert positions["a.md"].x < positions["b.md"].x

    def test_preserves_fixed_positions(self) -> None:
        nodes = (
            Node("a.md", "A", None, Path("/a.md"), "h1"),
            Node("b.md", "B", None, Path("/b.md"), "h2"),
        )
        edges = (Edge("a.md", "b.md", "depends_on"),)
        graph = Graph(nodes=nodes, edges=edges)
        engine = LayeredLayoutEngine()
        fixed = {"a.md": Rect(50.0, 60.0, 100.0, 100.0)}
        positions = engine.place(graph, fixed)
        assert positions["a.md"] == Rect(50.0, 60.0, 100.0, 100.0)
        assert "b.md" in positions

    def test_cycle_breaking(self) -> None:
        nodes = (
            Node("a.md", "A", None, Path("/a.md"), "h1"),
            Node("b.md", "B", None, Path("/b.md"), "h2"),
        )
        edges = (Edge("a.md", "b.md", "x"), Edge("b.md", "a.md", "x"))
        graph = Graph(nodes=nodes, edges=edges)
        engine = LayeredLayoutEngine()
        positions = engine.place(graph, {})
        assert len(positions) == 2


class TestIgraphSugiyamaLayoutEngine:
    def test_empty_graph(self) -> None:
        engine = IgraphSugiyamaLayoutEngine()
        assert engine.place(Graph(nodes=(), edges=()), {}) == {}

    def test_full_layout(self) -> None:
        nodes = (
            Node("a.md", "A", None, Path("/a.md"), "h1"),
            Node("b.md", "B", None, Path("/b.md"), "h2"),
        )
        edges = (Edge("a.md", "b.md", "depends_on"),)
        graph = Graph(nodes=nodes, edges=edges)
        engine = IgraphSugiyamaLayoutEngine()
        positions = engine.place(graph, {})
        assert "a.md" in positions
        assert "b.md" in positions
        assert positions["a.md"].x < positions["b.md"].x

    def test_preserves_fixed_positions(self) -> None:
        nodes = (
            Node("a.md", "A", None, Path("/a.md"), "h1"),
            Node("b.md", "B", None, Path("/b.md"), "h2"),
            Node("c.md", "C", None, Path("/c.md"), "h3"),
        )
        edges = (Edge("a.md", "b.md", "depends_on"), Edge("b.md", "c.md", "depends_on"))
        graph = Graph(nodes=nodes, edges=edges)
        engine = IgraphSugiyamaLayoutEngine()
        fixed = {
            "a.md": Rect(50.0, 60.0, 100.0, 100.0),
            "b.md": Rect(700.0, 60.0, 100.0, 100.0),
        }
        positions = engine.place(graph, fixed)
        assert positions["a.md"] == Rect(50.0, 60.0, 100.0, 100.0)
        assert positions["b.md"] == Rect(700.0, 60.0, 100.0, 100.0)
        assert "c.md" in positions

    def test_cycle_does_not_raise(self) -> None:
        nodes = (
            Node("a.md", "A", None, Path("/a.md"), "h1"),
            Node("b.md", "B", None, Path("/b.md"), "h2"),
        )
        edges = (Edge("a.md", "b.md", "x"), Edge("b.md", "a.md", "x"))
        graph = Graph(nodes=nodes, edges=edges)
        engine = IgraphSugiyamaLayoutEngine()
        positions = engine.place(graph, {})
        assert len(positions) == 2


class TestLayoutFactory:
    def test_builds_igraph_sugiyama_by_default(self) -> None:
        engine = build_layout_engine({})
        assert isinstance(engine, IgraphSugiyamaLayoutEngine)

    def test_builds_layered_explicitly(self) -> None:
        engine = build_layout_engine({"engine": "layered", "direction": "TB"})
        assert isinstance(engine, LayeredLayoutEngine)
        assert engine.direction == "TB"

    def test_unsupported_engine_raises(self) -> None:
        with pytest.raises(ValueError):
            build_layout_engine({"engine": "does-not-exist"})


class TestObsidianCanvasWriter:
    def test_writes_new_canvas(self, tmp_path: Path) -> None:
        a = tmp_path / "a.md"
        a.write_text("")
        node = Node("a.md", "A", None, a, "h")
        graph = Graph(nodes=(node,), edges=())
        writer = ObsidianCanvasWriter(tmp_path)
        writer.write(graph, {"a.md": Rect(0.0, 0.0, 100.0, 100.0)}, tmp_path / "out.canvas")

        data = json.loads((tmp_path / "out.canvas").read_text())
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["id"] == "a.md"
        assert data["nodes"][0]["file"] == "a.md"

    def test_preserves_unchanged_size(self, tmp_path: Path) -> None:
        a = tmp_path / "a.md"
        a.write_text("")
        canvas = tmp_path / "out.canvas"
        canvas.write_text(
            json.dumps(
                {
                    "nodes": [
                        {
                            "id": "a.md",
                            "type": "file",
                            "file": "a.md",
                            "x": 10,
                            "y": 20,
                            "width": 999,
                            "height": 888,
                        }
                    ],
                    "edges": [],
                }
            )
        )
        node = Node("a.md", "A", None, a, "h")
        graph = Graph(nodes=(node,), edges=())
        writer = ObsidianCanvasWriter(tmp_path)
        writer.write(
            graph,
            {"a.md": Rect(10.0, 20.0, 400.0, 400.0)},
            canvas,
            unchanged={"a.md"},
        )
        data = json.loads(canvas.read_text())
        assert data["nodes"][0]["width"] == 999
        assert data["nodes"][0]["height"] == 888

    def _write_edge(
        self, tmp_path: Path, from_rect: Rect, to_rect: Rect
    ) -> dict[str, Any]:
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("")
        b.write_text("")
        nodes = (Node("a.md", "A", None, a, "h1"), Node("b.md", "B", None, b, "h2"))
        graph = Graph(nodes=nodes, edges=(Edge("a.md", "b.md", "depends_on"),))
        writer = ObsidianCanvasWriter(tmp_path)
        destination = tmp_path / "out.canvas"
        writer.write(graph, {"a.md": from_rect, "b.md": to_rect}, destination)
        data = json.loads(destination.read_text())
        return data["edges"][0]

    def test_side_right_when_target_is_to_the_right(self, tmp_path: Path) -> None:
        # dx=600 > dy=0: dominant axis is X, target is to the right.
        edge = self._write_edge(
            tmp_path,
            Rect(0.0, 0.0, 400.0, 400.0),
            Rect(600.0, 0.0, 400.0, 400.0),
        )
        assert edge["fromSide"] == "right"
        assert edge["toSide"] == "left"

    def test_side_left_when_target_is_to_the_left(self, tmp_path: Path) -> None:
        edge = self._write_edge(
            tmp_path,
            Rect(600.0, 0.0, 400.0, 400.0),
            Rect(0.0, 0.0, 400.0, 400.0),
        )
        assert edge["fromSide"] == "left"
        assert edge["toSide"] == "right"

    def test_side_bottom_when_target_is_below(self, tmp_path: Path) -> None:
        # dx=0, dy=600: dominant axis is Y, target is below (canvas y grows down).
        edge = self._write_edge(
            tmp_path,
            Rect(0.0, 0.0, 400.0, 400.0),
            Rect(0.0, 600.0, 400.0, 400.0),
        )
        assert edge["fromSide"] == "bottom"
        assert edge["toSide"] == "top"

    def test_side_top_when_target_is_above(self, tmp_path: Path) -> None:
        edge = self._write_edge(
            tmp_path,
            Rect(0.0, 600.0, 400.0, 400.0),
            Rect(0.0, 0.0, 400.0, 400.0),
        )
        assert edge["fromSide"] == "top"
        assert edge["toSide"] == "bottom"

    def test_diagonal_prefers_dominant_horizontal_axis(self, tmp_path: Path) -> None:
        # dx=600, dy=100: target is below and to the right, but dx > dy so
        # the horizontal axis wins.
        edge = self._write_edge(
            tmp_path,
            Rect(0.0, 0.0, 400.0, 400.0),
            Rect(600.0, 100.0, 400.0, 400.0),
        )
        assert edge["fromSide"] == "right"
        assert edge["toSide"] == "left"

    def test_diagonal_prefers_dominant_vertical_axis(self, tmp_path: Path) -> None:
        # dx=100, dy=600: target is below and to the right, but dy > dx so
        # the vertical axis wins.
        edge = self._write_edge(
            tmp_path,
            Rect(0.0, 0.0, 400.0, 400.0),
            Rect(100.0, 600.0, 400.0, 400.0),
        )
        assert edge["fromSide"] == "bottom"
        assert edge["toSide"] == "top"


class TestWriterFactory:
    def test_builds_obsidian_canvas_writer(self, tmp_path: Path) -> None:
        writer = build_writer("obsidian_canvas", repo_root=tmp_path, direction="LR")
        assert isinstance(writer, ObsidianCanvasWriter)

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            build_writer("svg", repo_root=tmp_path, direction="LR")


class TestOrchestrator:
    def test_full_pipeline(self, tmp_path: Path) -> None:
        cache = CacheManager(tmp_path / "cache")
        orchestrator = Orchestrator(tmp_path, cache)

        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        a = skill_dir / "a.skill.md"
        b = skill_dir / "b.skill.md"
        a.write_text("---\nname: A\ndepends_on:\n  - [[skills/b.skill.md]]\n---\n")
        b.write_text("---\nname: B\n---\n")

        task = RenderTask(
            id="test",
            source=SourceConfig(include=("skills/*.skill.md",)),
            metadata=MetadataConfig(),
            links=(LinkFilterConfig("depends_on", "frontmatter_field", "depends_on"),),
            layout=LayoutConfig(),
            output=OutputConfig(
                format="obsidian_canvas",
                destination=tmp_path / "out.canvas",
            ),
        )
        assert orchestrator.run(task) is True
        assert (tmp_path / "out.canvas").exists()

        # Second run should be skipped.
        assert orchestrator.run(task) is False

        # Force run should update.
        assert orchestrator.run(task, force=True) is True

    def test_pipeline_auto_includes_linked_targets(self, tmp_path: Path) -> None:
        cache = CacheManager(tmp_path / "cache")
        orchestrator = Orchestrator(tmp_path, cache)

        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("---\nname: A\ndepends_on:\n  - [[b.md]]\n---\n")
        b.write_text("---\nname: B\n---\n")

        task = RenderTask(
            id="test",
            source=SourceConfig(include=("a.md",)),
            metadata=MetadataConfig(),
            links=(LinkFilterConfig("depends_on", "frontmatter_field", "depends_on"),),
            layout=LayoutConfig(),
            output=OutputConfig(
                format="obsidian_canvas",
                destination=tmp_path / "out.canvas",
            ),
        )
        assert orchestrator.run(task) is True
        data = json.loads((tmp_path / "out.canvas").read_text())
        assert {node["id"] for node in data["nodes"]} == {"a.md", "b.md"}
        assert len(data["edges"]) == 1
