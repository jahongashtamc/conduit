import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from engine import cli_runner
import tools

client = TestClient(app)

def test_engine_config_and_status():
    status = cli_runner.get_engine_status()
    assert "active_engine" in status
    assert "claude_code" in status["engines"]
    assert "agy" in status["engines"]
    # Claude code is installed
    assert status["engines"]["claude_code"]["available"] is True

def test_tools_py_direct_screenshot():
    # Use target site (never localhost:3000 Conduit itself)
    res = tools.tool_screenshot("https://www.google.com")
    assert res.get("success") is True
    assert "screenshot_path" in res
    assert os.path.exists(res["screenshot_path"])

def test_tools_py_direct_check_goal(tmp_path):
    """check_goal dalilsiz PASS bermasligi + haqiqiy fayl bilan PASS berishi."""
    # 1) Mavjud bo'lmagan fayl = PASS bo'lmasligi SHART (dalilsiz PASS qoidasi)
    missing = tools.tool_check_goal("Verify system", '{"screenshot": "test.png", "logs": "clean"}')
    assert missing.get("success") is True
    assert missing.get("verdict") == "FAIL", "Mavjud bo'lmagan dalil PASS bo'lmasligi kerak"

    # 2) Haqiqiy skrinshot fayli bilan PASS
    shot = tmp_path / "evidence.png"
    shot.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 4096)
    evidence = os.path.join(str(tmp_path), "evidence.png").replace("\\", "/")
    res = tools.tool_check_goal("Verify system", '{"screenshot": "%s", "logs": "clean"}' % evidence)
    assert res.get("success") is True
    assert res.get("verdict") == "PASS", res

def test_engine_selection_api():
    """Engine selection must round-trip without destroying the real config."""
    res = client.get("/api/engine/status")
    assert res.status_code == 200
    data = res.json()
    assert data["active_engine"] in ["claude_code", "agy"]

    # Remember what the machine is actually configured to use, switch it, then
    # put it back: this endpoint writes config/engine.json for real, and leaving
    # it on claude_code silently broke every later subagent run on this box.
    original = data["active_engine"]
    other = "agy" if original == "claude_code" else "claude_code"
    try:
        res_select = client.post("/api/engine/select", json={"engine": other})
        assert res_select.status_code == 200
        assert res_select.json()["active_engine"] == other
    finally:
        client.post("/api/engine/select", json={"engine": original})

    assert cli_runner.load_engine_config().get("active_engine") == original

def test_unauthorized_tool_rejection():
    # Test that security_guard blocks unauthorized tools
    import security_guard
    allowed = security_guard.get_allowed_tools("scout")
    assert "screenshot" in allowed
    assert "interact_web" in allowed
    
    # Unauthorized tool should raise ToolNotPermittedError
    with pytest.raises(security_guard.ToolNotPermittedError):
        security_guard.verify_tool_access("scout", "unauthorized_secret_bypass")
