"""Tests for helper functions."""

from __future__ import annotations

from pathlib import Path

import pytest

from diagram_renderer.functions.files import collect_files
from diagram_renderer.functions.frontmatter import parse_frontmatter
from diagram_renderer.functions.graph_algorithms import transitive_reduction_indices
from diagram_renderer.functions.hashing import hash_file_set, hash_node_content, hash_text
from diagram_renderer.functions.wikilinks import extract_wikilinks


class TestFrontmatter:
    def test_parses_valid_frontmatter(self, tmp_path: Path) -> None:
        path = tmp_path / "file.md"
        path.write_text("---\nname: Foo\ndepends_on:\n  - [[bar]]\n---\nBody\n")
        result = parse_frontmatter(path, path.read_text())
        # YAML parses `- [[bar]]` as a list containing a nested list.
        assert result == {"name": "Foo", "depends_on": [[["bar"]]]}

    def test_returns_none_without_frontmatter(self, tmp_path: Path) -> None:
        path = tmp_path / "file.md"
        path.write_text("# Heading\n")
        assert parse_frontmatter(path, path.read_text()) is None

    def test_returns_empty_dict_for_empty_frontmatter(self, tmp_path: Path) -> None:
        path = tmp_path / "file.md"
        path.write_text("---\n---\nBody\n")
        assert parse_frontmatter(path, path.read_text()) == {}

    def test_returns_none_for_invalid_yaml(self, tmp_path: Path) -> None:
        path = tmp_path / "file.md"
        path.write_text("---\nname: : bad\n---\nBody\n")
        assert parse_frontmatter(path, path.read_text()) is None

    def test_returns_none_for_non_mapping_frontmatter(self, tmp_path: Path) -> None:
        path = tmp_path / "file.md"
        path.write_text("---\n- one\n- two\n---\nBody\n")
        assert parse_frontmatter(path, path.read_text()) is None


class TestWikilinks:
    def test_extracts_simple_links(self) -> None:
        assert extract_wikilinks("See [[foo]] and [[bar|Bar Label]]") == [
            extract_wikilinks("[[foo]]")[0],
            extract_wikilinks("[[bar|Bar Label]]")[0],
        ]

    def test_path_and_alias(self) -> None:
        link = extract_wikilinks("[[path/to/file|Alias]]")[0]
        assert link.path_part() == "path/to/file"
        assert link.alias() == "Alias"

    def test_no_alias(self) -> None:
        link = extract_wikilinks("[[path/to/file]]")[0]
        assert link.alias() is None


class TestHashing:
    def test_hash_text_deterministic(self) -> None:
        assert hash_text("hello") == hash_text("hello")
        assert hash_text("hello") != hash_text("world")

    def test_hash_file_set_uses_mtime(self, tmp_path: Path) -> None:
        file = tmp_path / "a.md"
        file.write_text("content")
        h1 = hash_file_set([file], tmp_path)
        # mtime change -> hash change
        file.write_text("changed")
        import os
        os.utime(file, (file.stat().st_atime + 1, file.stat().st_mtime + 1))
        h2 = hash_file_set([file], tmp_path)
        assert h1 != h2

    def test_hash_node_content_deterministic(self) -> None:
        frontmatter = {"name": "Foo"}
        links = [("depends_on", "[[bar]]")]
        assert hash_node_content(frontmatter, links) == hash_node_content(
            frontmatter, list(links)
        )


class TestTransitiveReduction:
    def test_drops_direct_edge_implied_by_chain(self) -> None:
        pairs = [("A", "B"), ("B", "C"), ("A", "C")]
        assert transitive_reduction_indices(pairs) == [0, 1]

    def test_keeps_edges_without_alternate_path(self) -> None:
        pairs = [("A", "B"), ("B", "C")]
        assert transitive_reduction_indices(pairs) == [0, 1]

    def test_diamond_drops_only_the_shortcut(self) -> None:
        # A -> B -> D and A -> C -> D both reach D, so the direct A -> D
        # edge is redundant; B -> D and C -> D are each the only path to D
        # from their source and must be kept.
        pairs = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("A", "D")]
        assert transitive_reduction_indices(pairs) == [0, 1, 2, 3]

    def test_unrelated_pairs_are_all_kept(self) -> None:
        pairs = [("A", "B"), ("C", "D")]
        assert transitive_reduction_indices(pairs) == [0, 1]

    def test_cycle_does_not_hang_and_keeps_edges(self) -> None:
        pairs = [("A", "B"), ("B", "A")]
        assert transitive_reduction_indices(pairs) == [0, 1]


class TestCollectFiles:
    def test_collects_by_include(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("a")
        (tmp_path / "b.md").write_text("b")
        (tmp_path / "c.txt").write_text("c")
        result = collect_files(["*.md"], [], tmp_path)
        assert result == [tmp_path / "a.md", tmp_path / "b.md"]

    def test_respects_exclude(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("a")
        (tmp_path / "skip.md").write_text("skip")
        result = collect_files(["*.md"], ["skip.md"], tmp_path)
        assert result == [tmp_path / "a.md"]

    def test_result_sorted(self, tmp_path: Path) -> None:
        (tmp_path / "z.md").write_text("z")
        (tmp_path / "a.md").write_text("a")
        result = collect_files(["*.md"], [], tmp_path)
        assert result == [tmp_path / "a.md", tmp_path / "z.md"]
