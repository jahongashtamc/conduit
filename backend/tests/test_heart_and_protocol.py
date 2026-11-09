import os
import sys
import uuid
import pytest
import asyncio
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
import database
import memory_manager
from engine import protocol, heart, brain

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    database.init_db()

def test_protocol_command_validation_success():
    raw = {
        "id": "cmd_123",
        "to": "scout",
        "task": "Sahifani och va skrinshot ol",
        "expected_evidence": "screenshot"
    }
    cmd, err = protocol.validate_command(raw)
    assert err is None
    assert cmd is not None
    assert cmd.to == "scout"

def test_protocol_command_validation_failure():
    # Bo'sh yoki yetishmayotgan maydonlar
    raw_bad = {
        "id": "cmd_bad",
        "to": "s",  # too short
        "task": ""  # empty
    }
    cmd, err = protocol.validate_command(raw_bad)
    assert cmd is None
    assert err is not None
    assert "Noto'g'ri buyruq formati" in err

def test_protocol_report_evidence_requirement():
    # 1. Dalilsiz PASS -> Rad etiladi!
    raw_pass_no_ev = {
        "id": "rep_01",
        "from_agent": "scout",
        "status": "PASS",
        "evidence": "",  # bo'sh dalil!
        "notes": "Hammasi yaxshi"
    }
    rep, err = protocol.validate_report(raw_pass_no_ev)
    assert rep is None
    assert "Dalilsiz" in err

    # 2. To'g'ri dalilli PASS -> Qabul qilinadi
    raw_pass_ok = {
        "id": "rep_02",
        "from_agent": "scout",
        "status": "PASS",
        "evidence": "/static/screenshots/proof.png",
        "notes": "Skrinshot olindi"
    }
    rep_ok, err_ok = protocol.validate_report(raw_pass_ok)
    assert err_ok is None
    assert rep_ok is not None
    assert rep_ok.status == "PASS"

@pytest.mark.anyio
async def test_heart_rejects_nonexistent_subagent():
    task_id = f"test_heart_{uuid.uuid4().hex[:6]}"
    sm = heart.HeartStateMachine(task_id=task_id, goal="Test Subagent Rejection")

    # Mavjud bo'lmagan subagent
    raw_cmd = {
        "id": "cmd_inv",
        "to": "non_existent_hacker_agent",
        "task": "Buzib kir",
        "expected_evidence": "root_shell"
    }
    ok, err, cmd = await sm.verify_and_dispatch_command(raw_cmd)
    assert ok is False
    assert cmd is None
    assert "mavjud emas yoki hozirda faol emas" in err

@pytest.mark.anyio
async def test_heart_rejects_inactive_subagent():
    task_id = f"test_heart_{uuid.uuid4().hex[:6]}"
    sm = heart.HeartStateMachine(task_id=task_id, goal="Test Inactive Subagent")

    # Nofaol yoki ro'yxatda yo'q agent rad etilishi kerak
    raw_cmd = {
        "id": "cmd_super",
        "to": "inactive_subagent",
        "task": "Murakkab sintez",
        "expected_evidence": "synthesis_report"
    }
    ok, err, cmd = await sm.verify_and_dispatch_command(raw_cmd)
    assert ok is False
    assert "faol emas" in err

@pytest.mark.anyio
async def test_heart_impossible_task_blocked_after_3_loops():
    """
    Ataylab bajarib bo'lmaydigan vazifa 3 aylanishdan keyin BLOCKED bo'lishini isbotlash.
    """
    task_id = f"test_block_{uuid.uuid4().hex[:6]}"
    goal = "Mavjud bo'lmagan xato_vazifa buzib kir"

    result = await brain.run_heartbeat_loop(task_id=task_id, goal=goal)
    assert result["status"] == "BLOCKED"

    # SQLite holati BLOCKED bo'lishi kerak
    state = database.get_brain_state(task_id)
    assert state is not None
    assert state["status"] == "BLOCKED"
    assert state["attempt"] >= 3

@pytest.mark.anyio
async def test_heart_checkpoint_and_rollback():
    task_id = f"test_chk_{uuid.uuid4().hex[:6]}"
    sm = heart.HeartStateMachine(task_id=task_id, goal="Test Checkpoint")
    await sm.transition("RUNNING")

    # Checkpoint yaratish
    sm.create_checkpoint("step1_success", {"file": "shot.png"})
    assert len(heart.CHECKPOINTS[task_id]) == 1

    # Holat o'zgardi
    await sm.transition("CHECKING")
    assert sm.current_state == "CHECKING"

    # Rollback qilish
    rolled = sm.rollback_to_checkpoint()
    assert rolled is not None
    assert rolled["step_name"] == "step1_success"
    assert sm.current_state == "RUNNING"

def test_memory_blocks_api_read_write():
    # 1. Read
    res = client.get("/api/memory/project")
    assert res.status_code == 200
    assert "Conduit" in res.json()["content"]

    # 2. Write update
    test_content = "# Conduit Test Update\nYangi test xotirasi"
    res_post = client.post("/api/memory/project", json={"content": test_content})
    assert res_post.status_code == 200
    assert res_post.json()["saved"] is True

    # 3. Verify updated
    res_get = client.get("/api/memory/project")
    assert test_content in res_get.json()["content"]

    # Restore original content
    client.post("/api/memory/project", json={
        "content": "# Conduit Loyihasi Xotirasi\n\n## Maqsad\nConduit — AI agentlar boshqaruv dashboardi."
    })
