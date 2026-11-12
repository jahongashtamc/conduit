import uuid
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
import database

client = TestClient(app)

def test_skills_crud_and_conflict_detection():
    # 1. Create skill
    skill_name = f"Test Skill {uuid.uuid4().hex[:6]}"
    res = client.post("/api/skills", json={
        "name": skill_name,
        "description": "Avtomatlashtirilgan sinov skilli",
        "prompt_template": "Ushbu test buyrug'ini bajar: {input}",
        "target_subagents": ["scout"],
        "trigger_keywords": ["sinov_kw1", "sinov_kw2"]
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["name"] == skill_name
    skill_id = data["id"]
    assert "scout" in data["target_subagents"]

    # 2. Conflict check with identical name
    res_conflict = client.post("/api/skills", json={
        "name": skill_name,
        "description": "Ziddiyatli nom",
        "prompt_template": "test",
        "target_subagents": ["inspector"],
        "trigger_keywords": ["boshqa"]
    })
    assert res_conflict.status_code == 409
    assert "Ziddiyat aniqlandi" in res_conflict.json()["message"]

    # 3. Test skill execution ("Sinab ko'r")
    res_test = client.post(f"/api/skills/{skill_id}/test", json={
        "test_prompt": "Salom dunyo sinov tekshiruvi"
    })
    assert res_test.status_code == 200
    test_out = res_test.json()
    assert test_out["status"] == "PASS"
    assert test_out["tested_with_agent"] == "scout"

    # 4. Toggle skill
    res_toggle = client.put(f"/api/skills/{skill_id}/toggle", json={"enabled": False})
    assert res_toggle.status_code == 200
    assert res_toggle.json()["enabled"] is False

    # 5. Clean up
    del_res = client.delete(f"/api/skills/{skill_id}")
    assert del_res.status_code == 200

def test_lessons_evolution():
    task_id = f"test_task_{uuid.uuid4().hex[:6]}"
    prop_skill = {
        "name": f"Auto Learned Skill {uuid.uuid4().hex[:4]}",
        "description": "Saboqdan o'zlashtirilgan skill",
        "prompt_template": "Doer uslubi",
        "target_subagents": ["inspector"],
        "trigger_keywords": ["audit_auto"]
    }
    lesson = database.create_lesson(
        task_id=task_id,
        title="Muvaffaqiyatli xavfsizlik auditi sabog'i",
        summary="Inspector 4.2 soniyada barcha xatolarni tuzatdi.",
        proposed_skill=prop_skill
    )
    assert lesson["id"].startswith("lesson_")

    # Approve lesson -> turns into an active skill
    res = client.post(f"/api/lessons/{lesson['id']}/approve")
    assert res.status_code == 200

    skills = database.get_skills()
    skill_names = [s["name"] for s in skills]
    assert prop_skill["name"] in skill_names

def test_resource_limits_and_budget_enforcement():
    # Set limit to tiny fraction ($0.00001)
    client.post("/api/resources/limit", json={
        "max_budget_usd": 0.00001,
        "max_tokens": 100
    })

    # Record some usage
    database.record_resource_usage("tid_res_1", "scout", 2000, 1000, 5.0)

    # Check summary
    res_sum = client.get("/api/resources").json()
    assert res_sum["is_blocked"] is True
    assert "Byudjet limiti tugadi" in res_sum["block_reason"]

    # Try creating task -> should return BLOCKED
    task_res = client.post("/api/tasks", json={
        "prompt": "Resurs cheklovi ostida bajarilmaydigan vazifa",
        "target_agent": "scout"
    })
    assert task_res.status_code == 200
    task_data = task_res.json()
    assert task_data["status"] == "BLOCKED"
    assert "Byudjet limiti tugadi" in task_data["reason"]

    # Restore safe limits
    client.post("/api/resources/limit", json={
        "max_budget_usd": 10.0,
        "max_tokens": 500000
    })
    res_restored = client.get("/api/resources").json()
    assert res_restored["is_blocked"] is False

def test_approvals_queue_dangerous_and_approve_all():
    appr_id1 = f"appr_dang_{uuid.uuid4().hex[:6]}"
    appr_id2 = f"appr_safe_{uuid.uuid4().hex[:6]}"

    database.create_approval(
        approval_id=appr_id1,
        task_id="task_test_1",
        agent_id="inspector",
        action_type="file_delete",
        risk_description="Eski log fayllarini o'chirish (rm -rf /logs)",
        details={"path": "/logs"}
    )

    database.create_approval(
        approval_id=appr_id2,
        task_id="task_test_2",
        agent_id="scout",
        action_type="add_app",
        risk_description="Yangi ilova qo'shish",
        details={"app_id": "slack"}
    )

    approvals = client.get("/api/approvals").json()
    dang_item = next((a for a in approvals if a["approval_id"] == appr_id1), None)
    assert dang_item is not None
    assert dang_item["is_dangerous"] is True

    # One-click approve all
    res_all = client.post("/api/approvals/approve-all")
    assert res_all.status_code == 200
    assert res_all.json()["approved_count"] >= 2

    # Verify queue is now empty
    empty_apprs = client.get("/api/approvals").json()
    assert not any(a["approval_id"] in [appr_id1, appr_id2] for a in empty_apprs)

def test_connections_endpoint():
    res = client.get("/api/connections")
    assert res.status_code == 200
    tools = res.json()
    tool_ids = [t["id"] for t in tools]
    assert "claude" in tool_ids
    assert "python" in tool_ids
    assert "git" in tool_ids
