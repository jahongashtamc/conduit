"""Subagentlarning agy/Claude Code ga native tool sifatida bog'lanishi testlari."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import native_subagents  # noqa: E402


def test_sync_creates_local_definitions(tmp_path):
    result = native_subagents.sync_native_subagents(str(tmp_path))
    assert result["count"] >= 10
    assert result["directory"] == os.path.join(str(tmp_path), ".agents", "agents")
    assert all(os.path.isfile(p) for p in result["files"])

    scout_path = os.path.join(result["directory"], "conduit_scout.md")
    with open(scout_path, encoding="utf-8") as fh:
        content = fh.read()
    assert content.startswith("---\n")
    assert "name: conduit_scout" in content
    assert "description: >-" in content
    assert "subagent: true" in content
    assert "mainAgent: false" in content
    assert "commandExecutionPolicy: sandbox" in content
    assert "conduit run scout" in content
    assert "conduit result" in content
    assert "# System Prompt" in content


def test_only_verified_agy_tools_are_listed(tmp_path):
    native_subagents.sync_native_subagents(str(tmp_path))
    agents_dir = os.path.join(str(tmp_path), ".agents", "agents")
    for name in os.listdir(agents_dir):
        with open(os.path.join(agents_dir, name), encoding="utf-8") as fh:
            head = fh.read().split("---", 2)[1]
        for line in head.splitlines():
            line = line.strip()
            if line.startswith("- "):
                assert line[2:] in native_subagents.AGY_VERIFIED_TOOLS
