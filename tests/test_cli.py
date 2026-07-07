"""Tests for CLI entry point and render command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from diagram_renderer.__main__ import main


class TestCli:
    def test_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_render_single_task(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "a.md").write_text(
            "---\nname: A\ndepends_on:\n  - [[b.md]]\n---\n"
        )
        (tmp_path / "b.md").write_text("---\nname: B\n---\n")
        output = tmp_path / "out.canvas"

        code = main(
            [
                "render",
                "--include",
                "*.md",
                "--link-field",
                "depends_on",
                "--label-field",
                "name",
                "--output",
                str(output),
                "--cache-dir",
                str(tmp_path / "cache"),
            ]
        )
        assert code == 0
        assert output.exists()
        data = json.loads(output.read_text())
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_render_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "a.md").write_text(
            "---\nname: A\ndepends_on:\n  - [[b.md]]\n---\n"
        )
        (tmp_path / "b.md").write_text("---\nname: B\n---\n")
        config = tmp_path / "config.yaml"
        config.write_text(
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
        code = main(
            [
                "render",
                "--config",
                str(config),
                "--cache-dir",
                str(tmp_path / "cache"),
            ]
        )
        assert code == 0
        assert (tmp_path / "out.canvas").exists()

    def test_render_config_task_filter(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config = tmp_path / "config.yaml"
        config.write_text(
            "tasks:\n"
            "  - id: run-me\n"
            "    source:\n"
            "      include:\n"
            "        - '*.md'\n"
            "    links:\n"
            "      - name: depends_on\n"
            "        field: depends_on\n"
            "    output:\n"
            "      destination: run.canvas\n"
            "  - id: skip-me\n"
            "    source:\n"
            "      include:\n"
            "        - '*.md'\n"
            "    links:\n"
            "      - name: depends_on\n"
            "        field: depends_on\n"
            "    output:\n"
            "      destination: skip.canvas\n"
        )
        (tmp_path / "x.md").write_text("---\n---\n")
        code = main(
            [
                "render",
                "--config",
                str(config),
                "--task-id",
                "run-me",
                "--cache-dir",
                str(tmp_path / "cache"),
            ]
        )
        assert code == 0
        assert (tmp_path / "run.canvas").exists()
        assert not (tmp_path / "skip.canvas").exists()

    def test_missing_arguments(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["render"])
        assert code == 2
