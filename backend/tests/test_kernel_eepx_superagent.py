import sys
import os
import uuid
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
import database
from engine.kernel import ConduitKernel, KernelMode

client = TestClient(app)

def test_kernel_mode_and_settings():
    # 1. Database level settings
    init_settings = database.get_kernel_settings()
    assert "active_mode" in init_settings

    # Update to eepx
    updated = database.set_kernel_settings(active_mode="eepx", eepx_confidence_threshold=0.85)
    assert updated["active_mode"] == "eepx"
    assert updated["eepx_confidence_threshold"] == 0.85

    # 2. REST API endpoint GET
    res_get = client.get("/api/kernel/settings")
    assert res_get.status_code == 200
    assert res_get.json()["active_mode"] == "eepx"

    # 3. REST API endpoint POST
    res_post = client.post("/api/kernel/settings", json={"active_mode": "super_agent", "swarm_max_parallel": 5})
    assert res_post.status_code == 200
    assert res_post.json()["settings"]["active_mode"] == "super_agent"

    # Reset back to standard
    client.post("/api/kernel/settings", json={"active_mode": "standard"})

    # 4. Reject invalid mode
    res_bad = client.post("/api/kernel/settings", json={"active_mode": "quantum_hyper_mode"})
    assert res_bad.status_code == 400


@pytest.mark.anyio
async def test_eepx_pipeline_execution():
    kernel = ConduitKernel()
    task_id = f"test_eepx_task_{uuid.uuid4().hex[:6]}"

    database.create_task(
        task_id=task_id,
        title="Test EEPX Deep Cognitive Run",
        prompt="Veb qidiruv orqali AI dashboard arxitekturasini top",
        target_agent="scout",
        execution_mode="eepx"
    )

    with patch("engine.cli_runner.run_agent_loop") as mock_loop:
        mock_loop.return_value = {
            "status": "PASS",
            "evidence": "Google qidiruv natijasi va skrinshot: workspaces/scout/screenshot.png",
            "step_durations": {"planner": 0.5, "doer": 1.0, "checker": 0.5}
        }
        result = await kernel.run_eepx_pipeline(
            task_id=task_id,
            target_agent="scout",
            prompt="Veb qidiruv orqali AI dashboard arxitekturasini top"
        )

    assert result["mode"] == "eepx"
    assert result["status"] == "PASS"
    assert "dual_verify" in result

    # Verify traces in DB
    traces = database.get_eepx_traces(task_id)
    phases = [t["phase"] for t in traces]
    assert "E1_EXPLORATION" in phases
    assert "E2_EVALUATION" in phases
    assert "P_PLANNING" in phases
    assert "DUAL_VERIFY" in phases

    # Check REST endpoint
    res_api = client.get(f"/api/tasks/{task_id}/eepx")
    assert res_api.status_code == 200
    data = res_api.json()
    assert data["task_id"] == task_id
    assert data["count"] >= 4


@pytest.mark.anyio
async def test_super_agent_swarm_decomposition_and_execution():
    kernel = ConduitKernel()
    mission_id = f"test_swarm_mission_{uuid.uuid4().hex[:6]}"
    goal = "Figma dizayn spec yarat, 3D model render qil va brauzerda skrinshot ol"

    database.create_task(
        task_id=mission_id,
        title="Super Agent Swarm Mission",
        prompt=goal,
        target_agent="super_agent",
        execution_mode="super_agent"
    )

    # Verify decomposition logic
    stages_def = kernel._decompose_mission_into_stages(goal)
    agents = [s["agent"] for s in stages_def]
    assert "designer" in agents
    assert "sculptor" in agents
    assert "scout" in agents
    assert "inspector" in agents

    with patch("engine.cli_runner.run_agent_loop") as mock_loop:
        mock_loop.return_value = {
            "status": "PASS",
            "evidence": "Artefakt muvaffaqiyatli saqlandi va tekshirildi",
            "step_durations": {"planner": 0.3, "doer": 0.5, "checker": 0.3}
        }
        res = await kernel.run_super_agent_swarm(mission_id=mission_id, goal=goal)

    assert res["mission_id"] == mission_id
    assert res["status"] == "PASS"
    assert len(res["stages"]) >= 4

    # Verify all stages are recorded in DB
    db_stages = database.get_swarm_stages(mission_id)
    assert len(db_stages) >= 4
    for stg in db_stages:
        assert stg["status"] == "passed"

    # Check REST endpoint
    res_api = client.get(f"/api/tasks/{mission_id}/swarm")
    assert res_api.status_code == 200
    assert res_api.json()["count"] >= 4


@pytest.mark.anyio
async def test_super_agent_swarm_self_healing_recovery():
    kernel = ConduitKernel()
    mission_id = f"test_heal_mission_{uuid.uuid4().hex[:6]}"
    goal = "Veb qidiruv va skrinshot"

    database.create_task(
        task_id=mission_id,
        title="Healing Swarm Mission",
        prompt=goal,
        target_agent="super_agent",
        execution_mode="super_agent"
    )

    # First attempt fails with SyntaxError, second attempt passes (healed)
    call_count = 0
    async def mock_agent_loop(task_id, subagent, task_goal, ws_broadcast=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"status": "FAIL", "evidence": "SyntaxError: invalid token on line 3"}
        return {"status": "PASS", "evidence": "Healed execution success"}

    with patch("engine.cli_runner.run_agent_loop", side_effect=mock_agent_loop):
        res = await kernel.run_super_agent_swarm(mission_id=mission_id, goal=goal)

    assert res["status"] == "PASS"
    stages = database.get_swarm_stages(mission_id)
    assert len(stages) >= 1
    assert stages[0]["status"] == "passed"


def test_kernel_telemetry_endpoint():
    res = client.get("/api/kernel/telemetry")
    assert res.status_code == 200
    data = res.json()
    assert "active_mode" in data
    assert "kernel_version" in data
    assert "auto_healing_active" in data
    assert data["kernel_version"] == "2.4.0-elite"
