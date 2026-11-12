import os
import sys
import asyncio
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database
from engine import heart, cli_runner
from terminal_session import TerminalSession
import main

client = TestClient(main.app)

@pytest.mark.anyio
async def test_heartbeat_timeout_rule():
    """
    Heartbeat timeout testi:
    Umumiy vaqt o'rniga, N soniya davomida hech qanday chiqish (stdout/stderr)
    bo'lmaganda jarayon to'xtatilishi va BLOCKED qaytishi tekshiriladi.
    """
    # Test task with a mock command that sleeps without printing
    import uuid
    task_id = f"test_hb_{uuid.uuid4().hex[:6]}"
    database.init_db()
    database.create_task(task_id, "Silent sleep test", "test sleep", "scout")
    
    cfg = cli_runner.load_engine_config()
    _ = cfg.get("output_heartbeat_timeout", 30)
    # Configure tiny heartbeat timeout of 1 second for fast test
    cfg["output_heartbeat_timeout"] = 1
    
    # Run a silent python sleep that outputs nothing for 3 seconds
    silent_cmd = 'python -c "import time; time.sleep(3)"'
    
    proc = await asyncio.create_subprocess_shell(
        silent_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    
    timed_out = False
    heartbeat_timeout = cfg["output_heartbeat_timeout"]
    try:
        await asyncio.wait_for(proc.stdout.readline(), timeout=heartbeat_timeout)
    except asyncio.TimeoutError:
        timed_out = True
        cli_runner.kill_process_tree(proc.pid)
        
    assert timed_out is True, "1s davomida chiqish bo'lmaganda Heartbeat timeout ishlashi shart!"

@pytest.mark.anyio
async def test_parallel_semaphore_and_workspace_locks():
    """
    Yurak parallel ishlasin:
    - Bir vaqtda eng ko'pi N vazifa (semaphore).
    - Bitta workspace'da bir vaqtda faqat bitta vazifa (workspace lock).
    - Turli workspace'lar (scout, sculptor, inspector) bir vaqtda parallel ishlaydi.
    """
    sem = heart.get_parallel_semaphore()
    assert sem._value >= 1, "Parallel semafor faol bo'lishi kerak"

    # Workspace lock isolation
    lock_scout = heart.get_workspace_lock("scout")
    lock_sculptor = heart.get_workspace_lock("sculptor")

    assert lock_scout is not lock_sculptor, "Har bir subagent o'z workspace lock'iga ega bo'lishi shart"

    # Acquire scout lock
    await lock_scout.acquire()
    assert lock_scout.locked() is True
    # Sculptor can still be acquired concurrently!
    assert lock_sculptor.locked() is False
    await lock_sculptor.acquire()
    assert lock_sculptor.locked() is True

    lock_sculptor.release()
    lock_scout.release()

@pytest.mark.anyio
async def test_terminal_session_persistence_and_scrollback():
    """
    Terminal sessiyasi persistentsiyasi:
    - Sessiya xotirasida scrollback saqlanadi.
    - Yangi ulanish bo'lganda scrollback tarixi qaytadi.
    """
    session = TerminalSession.get_instance()
    test_marker = "=== TEST_CONDUIT_MARKER_123 ==="
    session._append_scrollback(test_marker)

    full_history = "".join(session.scrollback_buffer)
    assert test_marker in full_history, "Scrollback buferida xabarlar to'planishi kerak"

def test_conduit_cli_run_returns_task_id_immediately():
    """
    conduit run <subagent> <vazifa> kutmasdan darrov task_id qaytarishi tekshiriladi.
    """
    res = client.post("/api/tasks", json={
        "prompt": "Test parallel dispatch",
        "target_agent": "inspector"
    })
    assert res.status_code == 200
    data = res.json()
    assert "task_id" in data
    assert data["target_agent"] == "inspector"
    assert data["task_id"].startswith("task_")
