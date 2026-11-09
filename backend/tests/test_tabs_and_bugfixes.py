import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
import database
import tools
from engine import cli_runner

client = TestClient(app)

def test_screenshot_tool_rejects_localhost_3000():
    """TASK 1c: Tool screenshot must reject localhost:3000 (Conduit itself)"""
    res = tools.tool_screenshot("http://localhost:3000")
    assert res.get("success") is False
    assert "Conduit" in res.get("error", "") or "localhost:3000" in res.get("error", "")

def test_screenshot_latest_endpoint():
    """TASK 1b: GET /api/screenshot/latest serves screenshot or 404 cleanly"""
    res = client.get("/api/screenshot/latest")
    # If screenshot exists, returns 200 with image/png, or 404 with detail
    assert res.status_code in [200, 404]
    if res.status_code == 200:
        assert "image" in res.headers.get("content-type", "")

def test_memory_crud_api():
    """TASK 3: GET/POST/PUT/DELETE /api/memory table API"""
    # 1. Create
    res_post = client.post("/api/memory", json={
        "key": "Test Qoida",
        "value": "Test qiymat fakt",
        "source_task": "Test task"
    })
    assert res_post.status_code == 200
    created = res_post.json()
    assert "id" in created
    mem_id = created["id"]

    # 2. Get with search
    res_get = client.get(f"/api/memory?search=Test Qoida")
    assert res_get.status_code == 200
    items = res_get.json()
    assert any(i["id"] == mem_id for i in items)

    # 3. Update
    res_put = client.put(f"/api/memory/{mem_id}", json={
        "key": "Test Qoida Yangilandi",
        "value": "Yangi qiymat"
    })
    assert res_put.status_code == 200
    updated = res_put.json()
    assert updated["key"] == "Test Qoida Yangilandi"

    # 4. Delete
    res_del = client.delete(f"/api/memory/{mem_id}")
    assert res_del.status_code == 200
    assert res_del.json().get("success") is True

def test_apps_toggle_and_create_api():
    """TASK 4: Card grid data, toggle switch, and add custom app"""
    # 1. List apps
    res_apps = client.get("/api/apps")
    assert res_apps.status_code == 200
    apps_list = res_apps.json()
    assert len(apps_list) > 0
    first_app = apps_list[0]
    app_id = first_app["id"]

    # 2. Toggle app
    res_toggle = client.patch(f"/api/apps/{app_id}/toggle", json={"enabled": False})
    assert res_toggle.status_code == 200
    assert res_toggle.json()["enabled"] is False

    # Toggle back to true
    client.patch(f"/api/apps/{app_id}/toggle", json={"enabled": True})

    # 3. Add custom app
    res_add = client.post("/api/apps", json={
        "name": "Unreal Engine 5",
        "exe_path": "C:\\Program Files\\Epic Games\\UE_5.4\\Engine\\Binaries\\Win64\\UnrealEditor.exe",
        "run_template": "{exe} -game",
        "extension": ".uproject",
        "category": "Game Engine"
    })
    assert res_add.status_code == 200
    updated_apps = res_add.json()["apps"]
    assert any(a["name"] == "Unreal Engine 5" for a in updated_apps)

def test_task_retry_api():
    """TASK 1d: Task retry endpoint triggers rerun on FAIL"""
    import uuid
    t_id = f"test_retry_{uuid.uuid4().hex[:6]}"
    database.create_task(t_id, "Test task for retry", "Test prompt", "scout")
    database.update_task_step(t_id, "completed", "FAIL", evidence="FAIL (sabab: Model error 429)")

    res_retry = client.post(f"/api/tasks/{t_id}/retry")
    assert res_retry.status_code == 200
    data = res_retry.json()
    assert data["success"] is True
    assert data["status"] == "retrying"
