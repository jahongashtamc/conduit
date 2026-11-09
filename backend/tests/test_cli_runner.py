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

def test_tools_py_direct_check_goal():
    res = tools.tool_check_goal("Verify system", '{"screenshot": "test.png", "logs": "clean"}')
    assert res.get("success") is True
    assert res.get("verdict") == "PASS"

def test_engine_selection_api():
    res = client.get("/api/engine/status")
    assert res.status_code == 200
    data = res.json()
    assert data["active_engine"] in ["claude_code", "agy"]

    # Select claude_code
    res_select = client.post("/api/engine/select", json={"engine": "claude_code"})
    assert res_select.status_code == 200
    assert res_select.json()["active_engine"] == "claude_code"

def test_unauthorized_tool_rejection():
    # Test that security_guard blocks unauthorized tools
    import security_guard
    allowed = security_guard.get_allowed_tools("scout")
    assert "screenshot" in allowed
    assert "interact_web" in allowed
    
    # Unauthorized tool should raise ToolNotPermittedError
    with pytest.raises(security_guard.ToolNotPermittedError):
        security_guard.verify_tool_access("scout", "unauthorized_secret_bypass")
