"""Tool katalogi, ruxsat darvozasi va dalil yangiligi regression testlari."""

import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import security_guard
import tools
from engine import cli_runner


def _declared_tools() -> set:
    declared = set()
    for folder in os.listdir(security_guard.SUBAGENTS_DIR):
        declared.update(security_guard.get_allowed_tools(folder))
    return declared


def test_list_tools_covers_every_declared_tool():
    catalog = {t["name"] for t in tools.list_tools()}
    missing = {t for t in _declared_tools() if tools.canonical_tool_name(t) not in catalog}
    assert not missing, f"Role.md'da bor, CLI katalogida yo'q: {sorted(missing)}"


def test_list_tools_has_web_search_and_aliases():
    names = {t["name"] for t in tools.list_tools()}
    assert "web_search" in names
    assert tools.canonical_tool_name("search") == "web_search"
    assert tools.canonical_tool_name("runScript") == "runscript"
    assert tools.canonical_tool_name("bogus_tool") is None


def test_tools_main_enforces_agent_allowlist(monkeypatch, capsys):
    monkeypatch.setenv("CONDUIT_AGENT", "scout")
    monkeypatch.setattr(sys, "argv", ["tools.py", "gen_image", "test"])
    with pytest.raises(SystemExit) as exc:
        tools.main()
    assert exc.value.code == 2
    result = json.loads(capsys.readouterr().out)
    assert result["success"] is False
    assert "RUXSAT" in result["error"].upper() or "ruxsat" in result["error"]


def test_tools_main_allows_declared_tool(monkeypatch, capsys):
    monkeypatch.setenv("CONDUIT_AGENT", "scout")
    monkeypatch.delenv("CONDUIT_TASK_STARTED_AT", raising=False)
    monkeypatch.setattr(sys, "argv", ["tools.py", "get_logs"])
    tools.main()
    result = json.loads(capsys.readouterr().out)
    assert result["success"] is True
    assert result["tool"] == "get_logs"


def test_check_goal_rejects_empty_evidence(monkeypatch):
    monkeypatch.setenv("CONDUIT_TASK_STARTED_AT", str(time.time()))
    res = tools.tool_check_goal("Create a 3D model", "{}")
    assert res["success"] is True
    assert res["verdict"] == "FAIL"
    assert "Dalil taqdim etilmadi" in res["issues"][0]


def test_retry_budget_is_bounded():
    # 1 boshlang'ich + 2 qayta urinish; cheksiz sikl yo'q.
    assert cli_runner.MAX_ARTIFACT_ATTEMPTS == 3


def test_check_goal_rejects_stale_artifact(monkeypatch, tmp_path):
    monkeypatch.setenv("CONDUIT_TASK_STARTED_AT", str(time.time()))
    old = tmp_path / "old.png"
    old.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 4096)
    old_time = time.time() - 3600
    os.utime(old, (old_time, old_time))
    res = tools.tool_check_goal(
        "Create a 3D model",
        json.dumps({"screenshot": str(old), "captured_at": old_time}),
    )
    assert res["verdict"] == "FAIL"
    assert "eski" in res["issues"][0].lower()


def test_evidence_validator_requires_artifact_not_keywords(tmp_path):
    ok, reason = cli_runner.validate_evidence_against_goal(
        "Blender'da 3D kub model yarat", "sculptor", "render model scene", ""
    )
    assert ok is False
    assert "artefakt" in reason.lower()

    # Mavjud bo'lmagan yo'l ham dalil emas.
    fake_ok, _ = cli_runner.validate_evidence_against_goal(
        "Blender'da 3D kub model yarat", "sculptor",
        "render model scene", "workspaces/sculptor/cube.png",
    )
    assert fake_ok is False

    real_png = tmp_path / "cube.png"
    real_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 256)
    ok2, _ = cli_runner.validate_evidence_against_goal(
        "Blender'da 3D kub model yarat", "sculptor",
        f"render model scene {real_png}", str(real_png),
    )
    assert ok2 is True


def test_goal_check_pass_requires_explicit_verdict():
    assert cli_runner.goal_check_passed({"verdict": "PASS"}) is True
    assert cli_runner.goal_check_passed({"verdict": "FAIL", "issues": ["Dalil eski"]}) is False
    # `success` yoki uzun matn PASS emas: bu eski false-PASS yo'li edi.
    assert cli_runner.goal_check_passed(
        {"success": True, "evidence": "ish qilindi " * 50}
    ) is False
