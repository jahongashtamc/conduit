import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
import workspace_manager
import security_guard
import database

client = TestClient(app)

def test_workspace_isolation_and_path_traversal():
    agent_id = "scout"
    ws = workspace_manager.get_agent_workspace(agent_id)
    assert os.path.exists(ws)
    assert "workspaces" in ws.lower()

    # 1. Normal safe write & read
    file_path = workspace_manager.write_agent_file(agent_id, "notes/test.txt", "Salom Conduit")
    assert os.path.exists(file_path)
    content = workspace_manager.read_agent_file(agent_id, "notes/test.txt")
    assert content == "Salom Conduit"

    # 2. Path Traversal relative escape attempt
    with pytest.raises(workspace_manager.SecurityViolation):
        workspace_manager.resolve_safe_path(agent_id, "../../outside_file.txt")

    # 3. Path Traversal absolute escape attempt
    with pytest.raises(workspace_manager.SecurityViolation):
        workspace_manager.resolve_safe_path(agent_id, "C:\\Windows\\System32\\calc.exe")

def test_tool_whitelist_enforcement():
    # Scout has interact_web, screenshot in role.md
    allowed = security_guard.get_allowed_tools("scout")
    assert "screenshot" in allowed
    assert "interact_web" in allowed

    # Valid tool check
    assert security_guard.verify_tool_access("scout", "screenshot") is True

    # Unauthorized tool check
    with pytest.raises(security_guard.ToolNotPermittedError):
        security_guard.verify_tool_access("scout", "unauthorized_backdoor_tool")

def test_zero_secrets_sanitization():
    raw_log = "Error connecting to db: api_key=sk-proj998877665544332211 and password=SuperSecretPassword123"
    clean_log = security_guard.sanitize_text(raw_log)
    assert "sk-proj998877665544332211" not in clean_log
    assert "SuperSecretPassword123" not in clean_log
    assert "[REDACTED_SECRET]" in clean_log

def test_dangerous_action_detection():
    # File delete
    is_danger, reason = security_guard.inspect_danger_level("delete_file", {"file_path": "data.json"})
    assert is_danger is True
    assert "o'chirish" in reason.lower() or "delete" in reason.lower()

    # System command
    is_danger, reason = security_guard.inspect_danger_level("exec_command", {"command": "rm -rf /"})
    assert is_danger is True

    # Safe read
    is_danger, reason = security_guard.inspect_danger_level("read_file", {"file_path": "data.json"})
    assert is_danger is False

import uuid

def test_approval_flow_endpoints():
    approval_id = f"test_appr_{uuid.uuid4().hex[:8]}"
    database.create_approval(
        approval_id=approval_id,
        task_id="test_task_01",
        agent_id="scout",
        action_type="file_delete",
        risk_description="Fayl o'chirish amali uchun tasdiq talab etiladi",
        details={"path": "temp.txt"}
    )

    # 1. List approvals
    res = client.get("/api/approvals")
    assert res.status_code == 200
    approvals = res.json()
    assert any(a["approval_id"] == approval_id for a in approvals)

    # 2. Resolve approval
    res_resolve = client.post(f"/api/approvals/{approval_id}/resolve", json={"decision": "approved"})
    assert res_resolve.status_code == 200
    assert res_resolve.json()["decision"] == "approved"

    # 3. Verified resolved
    appr = database.get_approval(approval_id)
    assert appr["status"] == "approved"
