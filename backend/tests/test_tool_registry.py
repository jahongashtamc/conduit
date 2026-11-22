"""Subagentlar agentga bog'langan tool'lar sifatida ishlashi testlari."""

import os
import sys
import subprocess

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tool_registry  # noqa: E402
import terminal_session  # noqa: E402
from engine import cli_runner  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)


def test_catalog_shape_and_content():
    catalog = tool_registry.build_tool_catalog(include_budget=False)
    assert catalog["version"] == "1.0"
    assert catalog["protocol"] == "conduit-cli"
    assert catalog["tools"], "faol subagentlardan tool'lar yaratilishi kerak"

    by_name = {t["name"]: t for t in catalog["tools"]}
    assert "conduit_run_scout" in by_name
    assert "conduit_run_sculptor" in by_name

    scout = by_name["conduit_run_scout"]
    assert scout["subagent"] == "scout"
    assert scout["description"]
    assert scout["input_schema"]["required"] == ["task"]
    assert "screenshot" in scout["allowed_tools"]
    assert scout["invocation"] == 'conduit run scout "<task>"'
    assert scout["context_tokens"] > 0
    assert scout["estimated_execution_tokens"] >= 15_000
    assert scout["estimated_execution_tokens"] > scout["context_tokens"]
    assert scout["estimated_cost_usd"] > 0
    assert isinstance(scout["within_remaining_budget"], bool)


def test_description_budget_within_limit():
    catalog = tool_registry.build_tool_catalog(include_budget=False)
    assert catalog["description_budget_ok"] is True
    assert 0 < catalog["total_description_tokens"] < catalog["description_limit_tokens"]
    assert catalog["description_limit_tokens"] == 15_000


def test_compact_lines_are_agent_facing_tools():
    lines = tool_registry.compact_tool_lines()
    assert "- `conduit_run_scout` (scout):" in lines
    assert len(lines.splitlines()) >= 10


def test_guide_documents_tools_and_budget():
    guide = terminal_session._studio_guide_md()
    assert terminal_session.DOC_MARKER in guide
    assert "conduit tools" in guide
    assert "conduit budget" in guide
    assert "conduit_run_scout" in guide
    assert "Asosiy kontekstga faqat" in guide
    assert "umumiy token/narx limitiga" in guide


def test_catalog_endpoint():
    resp = client.get("/api/tools/catalog")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.0"
    assert any(t["subagent"] == "scout" for t in data["tools"])
    # Byudjet bo'limi mavjud (DB ishga tushgan bo'lsa available=True).
    assert "budget" in data


def test_token_usage_extraction_is_provider_agnostic():
    assert cli_runner.extract_token_usage(
        {"type": "result", "message": {"usage": {"input_tokens": 120, "output_tokens": 45}}}
    ) == {"prompt_tokens": 120, "completion_tokens": 45}
    assert cli_runner.extract_token_usage(
        {"event": "usage", "usage": {"prompt_token_count": 7, "generated_token_count": 3}}
    ) == {"prompt_tokens": 7, "completion_tokens": 3}
    assert cli_runner.extract_token_usage({"event": "step_update"}) == {}


def test_cumulative_usage_is_not_double_counted():
    snapshot = {"prompt_tokens": 0, "completion_tokens": 0}
    cli_runner.merge_usage_snapshot(
        snapshot,
        {"event": "step_update", "step_update": {"usage": {"input_tokens": 500, "output_tokens": 10}}},
    )
    cli_runner.merge_usage_snapshot(
        snapshot,
        {"event": "result", "result": {"usage": {"input_tokens": 900, "output_tokens": 25}}},
    )
    assert snapshot == {"prompt_tokens": 900, "completion_tokens": 25}


def test_task_blocked_when_tool_budget_insufficient(monkeypatch):
    import tool_registry

    catalog = tool_registry.build_tool_catalog(include_budget=False)
    for tool in catalog["tools"]:
        tool["within_remaining_budget"] = tool["subagent"] != "scout"
    monkeypatch.setattr(tool_registry, "build_tool_catalog", lambda include_budget=True: catalog)

    resp = client.post("/api/tasks", json={"prompt": "budget guard test", "target_agent": "scout"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "BLOCKED"
    assert "byudjet yetarli emas" in data["reason"]


def test_cli_exposes_tools_and_budget():
    cli = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "conduit.py"))
    out = subprocess.run(
        [sys.executable, cli, "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    assert out.returncode == 0
    assert "tools" in out.stdout
    assert "budget" in out.stdout
