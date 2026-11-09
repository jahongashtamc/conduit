import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
import security_guard

client = TestClient(app)

def test_permission_mode_endpoints():
    # 1. Get default mode
    res = client.get("/api/settings/permission-mode")
    assert res.status_code == 200
    assert res.json()["mode"] in ["ask_always", "ask_dangerous_only", "free_in_workspace"]

    # 2. Set to 'ask_always'
    res_set = client.post("/api/settings/permission-mode", json={"mode": "ask_always"})
    assert res_set.status_code == 200
    assert res_set.json()["mode"] == "ask_always"
    assert security_guard.get_permission_mode() == "ask_always"

    # In 'ask_always', even non-dangerous actions require approval
    req_appr, reason = security_guard.should_require_approval("file_read", {"path": "test.txt"})
    assert req_appr is True

    # 3. Set to 'free_in_workspace'
    res_free = client.post("/api/settings/permission-mode", json={"mode": "free_in_workspace"})
    assert res_free.status_code == 200
    assert res_free.json()["mode"] == "free_in_workspace"

    # Inside workspace, safe action doesn't require approval
    req_free, _ = security_guard.should_require_approval("file_read", {"path": "test.txt"}, is_in_workspace=True)
    assert req_free is False

    # But file delete still requires approval
    req_del, _ = security_guard.should_require_approval("file_delete", {"path": "test.txt"}, is_in_workspace=True)
    assert req_del is True

    # 4. Restore 'ask_dangerous_only'
    res_rest = client.post("/api/settings/permission-mode", json={"mode": "ask_dangerous_only"})
    assert res_rest.status_code == 200
    assert security_guard.get_permission_mode() == "ask_dangerous_only"
