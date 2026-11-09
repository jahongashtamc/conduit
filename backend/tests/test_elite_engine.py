import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from engine.healer import SelfHealer

client = TestClient(app)

def test_self_healer_taxonomy_diagnosis():
    # 1. Kod / sintaksis xatosi
    d1 = SelfHealer.diagnose("SyntaxError: unexpected EOF while parsing", "sculptor")
    assert d1["category"] == "SYNTAX_CODE_ERROR"
    assert "sintaksis" in d1["diagnosis"].lower()

    # 2. Resurs / Network xatosi
    d2 = SelfHealer.diagnose("ConnectionRefusedError: [Errno 111] Connection refused", "scout")
    assert d2["category"] == "NETWORK_RESOURCE_UNAVAILABLE"
    assert "ulanish" in d2["diagnosis"].lower()

    # 3. API Rate limit / 429
    d3 = SelfHealer.diagnose("anthropic.RateLimitError: 429 Too Many Requests: tokens per minute exceeded", "scout")
    assert d3["category"] == "API_RATE_LIMIT"
    assert "cheklov" in d3["diagnosis"].lower() or "model" in d3["diagnosis"].lower()

    # 4. Fayl yo'li topilmadi
    d4 = SelfHealer.diagnose("FileNotFoundError: [Errno 2] No such file or directory: 'src/config.json'", "sculptor")
    assert d4["category"] == "MISSING_FILE_PATH"
    assert "fayl" in d4["diagnosis"].lower()

    # 5. Standart xatolik
    d5 = SelfHealer.diagnose("Process failed with exit code 1", "scout")
    assert d5["category"] == "GENERIC_EXECUTION_FAILURE"


def test_self_healer_apply_auto_heal():
    res = SelfHealer.apply_auto_heal(
        task_id="task-test-heal-99",
        subagent="sculptor",
        original_prompt="Build static landing page",
        error_text="SyntaxError: invalid syntax in index.js on line 4",
        attempt=1
    )
    assert res["status"] == "remedied"
    assert "XATOLIK TUZATILDI" in res["healed_prompt"]
    assert res["category"] == "SYNTAX_CODE_ERROR"

    # Verify event stored in DB
    events = SelfHealer.get_healing_events(task_id="task-test-heal-99")
    assert len(events) >= 1
    assert events[0]["task_id"] == "task-test-heal-99"


def test_permission_mode_api():
    # 1. GET permission mode
    get_res = client.get("/api/settings/permission-mode")
    assert get_res.status_code == 200
    assert "mode" in get_res.json()

    # 2. POST update permission mode
    modes = ["ask_always", "ask_dangerous_only", "free_in_workspace"]
    for m in modes:
        post_res = client.post("/api/settings/permission-mode", json={"mode": m})
        assert post_res.status_code == 200
        assert post_res.json()["mode"] == m

    # Verify invalid mode is rejected
    bad_res = client.post("/api/settings/permission-mode", json={"mode": "unrestricted_chaos"})
    assert bad_res.status_code == 400


def test_audit_report_generation():
    # Create a task
    create_res = client.post("/api/tasks", json={
        "prompt": "Test elite audit report creation",
        "target_agent": "scout"
    })
    assert create_res.status_code == 200
    task_id = create_res.json()["task_id"]

    # 1. Fetch Markdown report
    md_res = client.get(f"/api/tasks/{task_id}/report?format=markdown")
    assert md_res.status_code == 200
    assert "CONDUIT MISSIYA AUDIT HISOBOTI" in md_res.text
    assert task_id in md_res.text

    # 2. Fetch HTML report
    html_res = client.get(f"/api/tasks/{task_id}/report?format=html")
    assert html_res.status_code == 200
    assert "<!DOCTYPE html>" in html_res.text
    assert "Conduit Audit Report" in html_res.text
    assert task_id in html_res.text


def test_self_heal_endpoint():
    # Create task
    create_res = client.post("/api/tasks", json={
        "prompt": "Compile typescript module",
        "target_agent": "sculptor"
    })
    task_id = create_res.json()["task_id"]

    # Trigger self heal endpoint
    heal_res = client.post(f"/api/tasks/{task_id}/self-heal")
    assert heal_res.status_code == 200
    data = heal_res.json()
    assert data["success"] is True
    assert "healing_event" in data

    # Query healing events
    events_res = client.get(f"/api/healing/events?task_id={task_id}")
    assert events_res.status_code == 200
    assert isinstance(events_res.json(), list)
