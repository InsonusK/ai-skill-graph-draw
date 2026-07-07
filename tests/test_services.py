"""Tests for service-layer components."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from diagram_renderer.service.cache import CacheManager
from diagram_renderer.service.canvas_writer import ObsidianCanvasWriter
from diagram_renderer.service.config import ConfigLoader, ConfigValidationError
from diagram_renderer.service.diff import DiffEngine
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
from diagram_renderer.service.graph_builder import GraphBuilder
from diagram_renderer.service.layout import LayeredLayoutEngine
from diagram_renderer.service.link_filter import FrontmatterFieldLinkFilter
from diagram_renderer.service.link_resolver import LinkResolver
from diagram_renderer.service.metadata_extractor import MetadataExtractor
from diagram_renderer.service.orchestrator import Orchestrator
from diagram_renderer.service.source_collector import SourceCollector


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
        assert task.metadata.label_field == "name"
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


class TestMetadataExtractor:
    def test_extracts_label_and_id(self, tmp_path: Path) -> None:
        file = tmp_path / "skills" / "a.md"
        file.parent.mkdir()
        file.write_text("")
        extractor = MetadataExtractor(tmp_path, MetadataConfig(label_field="name"))
        meta = extractor.extract(file, {"name": "Nice Name"})
        assert meta.id == "skills/a.md"
        assert meta.label == "Nice Name"

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
            metadata=MetadataConfig(label_field="name"),
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
