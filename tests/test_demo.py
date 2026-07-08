"""Tests that the bundled demo project renders correctly."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from diagram_renderer.__main__ import main


class TestDemo:
    def test_demo_config_renders_all_tasks(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project_root = Path(__file__).resolve().parent.parent
        demo_source = project_root / "demo"

        demo_tmp = tmp_path / "demo"
        demo_tmp.mkdir()
        shutil.copytree(demo_source / "skills", demo_tmp / "skills")
        shutil.copy(demo_source / "diagrams.yaml", demo_tmp / "diagrams.yaml")

        monkeypatch.chdir(demo_tmp)
        cache_dir = demo_tmp / "cache"

        code = main(
            [
                "render",
                "--config",
                "diagrams.yaml",
                "--force",
                "--cache-dir",
                str(cache_dir),
            ]
        )
        assert code == 0

        reduced = json.loads((demo_tmp / "skills-map.canvas").read_text())
        no_reduction = json.loads(
            (demo_tmp / "skills-map-no-reduction.canvas").read_text()
        )
        sugiyama = json.loads(
            (demo_tmp / "skills-map-igraph-sugiyama.canvas").read_text()
        )

        for canvas in (reduced, no_reduction, sugiyama):
            assert len(canvas["nodes"]) == 5
            assert all(node.get("subpath") == "#Summary" for node in canvas["nodes"])

        # With transitive reduction the redundant DDD -> Value Objects edge is hidden.
        assert len(reduced["edges"]) == 6
        # Without reduction the redundant edge is kept: 5 depends_on + 2 extends.
        assert len(no_reduction["edges"]) == 7
        # Same reduced graph rendered with a different layout engine.
        assert len(sugiyama["edges"]) == 6

        for canvas in (reduced, no_reduction, sugiyama):
            labels = {edge.get("label") for edge in canvas["edges"]}
            assert labels == {"depends on", "extends"}
            colors = {edge.get("color") for edge in canvas["edges"]}
            assert colors == {"4", "2"}
