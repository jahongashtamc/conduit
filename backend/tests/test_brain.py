import os
import sys
import uuid
import pytest
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from engine import brain

@pytest.fixture(autouse=True)
def setup_db():
    database.init_db()

@pytest.mark.anyio
async def test_brain_command_protocol():
    task_id = f"test_proto_{uuid.uuid4().hex[:8]}"
    
    # 1. Miya subagentga buyruq yuboradi
    cmd = brain.BrainCommand(
        id="cmd_test_01",
        to="scout",
        task="Test veb qidiruv",
        expected_evidence="screenshot"
    )
    ev_cmd = database.log_event(
        task_id=task_id,
        direction="command",
        from_agent="brain",
        to_agent=cmd.to,
        payload={"to": cmd.to, "task": cmd.task, "expected_evidence": cmd.expected_evidence},
        status="dispatched"
    )
    assert ev_cmd["direction"] == "command"
    assert ev_cmd["from_agent"] == "brain"
    assert ev_cmd["to_agent"] == "scout"
    assert ev_cmd["payload"]["expected_evidence"] == "screenshot"

    # 2. Subagent hisobot qaytaradi
    report = brain.AgentReport(
        id="rep_test_01",
        from_agent="scout",
        status="PASS",
        evidence="/static/screenshots/test.png",
        notes="Skrinshot muvaffaqiyatli olindi"
    )
    ev_rep = database.log_event(
        task_id=task_id,
        direction="report",
        from_agent=report.from_agent,
        to_agent="brain",
        payload={
            "from": report.from_agent,
            "status": report.status,
            "evidence": report.evidence,
            "notes": report.notes
        },
        status=report.status
    )
    assert ev_rep["direction"] == "report"
    assert ev_rep["from_agent"] == "scout"
    assert ev_rep["status"] == "PASS"

    # 3. Events ro'yxatini olish
    events = database.get_events(task_id)
    assert len(events) >= 2
    assert events[0]["direction"] == "command"
    assert events[1]["direction"] == "report"

@pytest.mark.anyio
async def test_brain_decision_engine_lifecycle():
    engine = brain.RuleBasedBrainEngine()
    task_id = f"test_life_{uuid.uuid4().hex[:8]}"
    goal = "Google'dan Conduit haqida qidir, skrinshot ol va tekshir"

    state = {
        "task_id": task_id,
        "goal": goal,
        "plan": [],
        "attempt": 1
    }

    # Step 1: Dastlabki reja va Scout'ga buyruq
    cmd1 = await engine.decide(state)
    assert cmd1 is not None
    assert cmd1.to == "scout"
    assert "Google" in cmd1.task
    assert len(state["plan"]) == 2
    assert "Miya" in state["thought"]

    # Scout PASS hisoboti kiritiladi
    state["last_report"] = {
        "from_agent": "scout",
        "status": "PASS",
        "evidence": "C:/path/screenshot.png",
        "screenshot_url": "/static/test.png",
        "notes": "OK"
    }

    # Step 2: Scout natijasi qabul qilinib, Inspector'ga buyruq beriladi
    cmd2 = await engine.decide(state)
    assert cmd2 is not None
    assert cmd2.to == "inspector"
    assert state["plan"][0]["status"] == "PASS"

    # Inspector PASS hisoboti kiritiladi
    state["last_report"] = {
        "from_agent": "inspector",
        "status": "PASS",
        "evidence": "Inspector audit PASS",
        "notes": "Hammasi me'yorda"
    }

    # Step 3: Yakuniy tasdiq va finish
    cmd3 = await engine.decide(state)
    assert cmd3 is None
    assert state["status"] == "PASS"
    assert state["plan"][1]["status"] == "PASS"

@pytest.mark.anyio
async def test_brain_memory_persistence():
    task_id = f"test_mem_{uuid.uuid4().hex[:8]}"
    database.save_brain_state(
        task_id=task_id,
        goal="Test Memory Goal",
        thought="Fikrlayapman...",
        plan=[{"step": 1, "title": "Sinov"}],
        status="executing"
    )

    database.append_brain_memory(
        task_id=task_id,
        decision="1-qaror qabul qilindi",
        error=None,
        result="Muvaffaqiyatli"
    )

    saved = database.get_brain_state(task_id)
    assert saved is not None
    assert saved["goal"] == "Test Memory Goal"
    assert saved["thought"] == "Fikrlayapman..."
    assert len(saved["plan"]) == 1
    assert len(saved["short_memory"]) == 1
    assert saved["short_memory"][0]["decision"] == "1-qaror qabul qilindi"
