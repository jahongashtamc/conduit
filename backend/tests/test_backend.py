import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
import database
import apps_manager
import subagent_scanner
import manager_router

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_apps_manager_status():
    apps = apps_manager.get_apps_status()
    assert isinstance(apps, list)
    assert len(apps) >= 6
    app_ids = [a["id"] for a in apps]
    for required in ["blender", "after_effects", "davinci", "premiere", "maya", "figma"]:
        assert required in app_ids
    for a in apps:
        assert a["status"] in ["ready", "not installed", "running"]

def test_subagent_scanner_dynamic_discovery():
    subagents = subagent_scanner.scan_subagents()
    assert len(subagents) >= 7
    ids = [s["id"] for s in subagents]
    for expected in ["scout", "inspector", "sculptor", "animator", "editor", "painter", "designer"]:
        assert expected in ids
    
    # Scout and Inspector should be active
    scout = next(s for s in subagents if s["id"] == "scout")
    inspector = next(s for s in subagents if s["id"] == "inspector")
    assert scout["status"] == "active"
    assert inspector["status"] == "active"
    assert scout["has_planner"] is True
    assert scout["has_doer"] is True
    assert scout["has_checker"] is True

def test_manager_task_routing():
    # Browser/Web keywords -> scout
    agent, reason = manager_router.route_task("Google qidiruvidan Conduit haqida ma'lumot top")
    assert agent == "scout"

    # Test/Audit keywords -> inspector
    agent, reason = manager_router.route_task("Tizim testlarini ishga tushir va audit qil")
    assert agent == "inspector"

    # 3D/Blender -> sculptor
    agent, reason = manager_router.route_task("Blenderda 3D kub modelini yarat")
    assert agent == "sculptor"

    # Motion graphics -> animator
    agent, reason = manager_router.route_task("After Effects da kinetik matn animatsiyasini tayyorla")
    assert agent == "animator"

def test_api_task_lifecycle_endpoints():
    # 1. Create a task via API
    res = client.post("/api/tasks", json={
        "prompt": "Test veb-saytini tekshir va skrinshot ol",
        "target_agent": "auto"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["target_agent"] == "scout"
    task_id = data["task_id"]

    # 2. Get task list
    list_res = client.get("/api/tasks")
    assert list_res.status_code == 200
    tasks = list_res.json()
    assert any(t["task_id"] == task_id for t in tasks)

    # 3. Kill all endpoint
    kill_res = client.post("/api/kill-all")
    assert kill_res.status_code == 200
    assert kill_res.json()["success"] is True
