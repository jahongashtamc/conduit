import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))

import database
import tools


def _run_cli(live_backend, *args):
    """CLI'ni test-serverga yo'naltirib ishga tushiradi."""
    env = os.environ.copy()
    env["CONDUIT_API"] = live_backend
    return subprocess.run(
        [sys.executable, "conduit.py", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        encoding="utf-8",
        env=env,
    )


def test_cli_status_json_exposes_top_level_fields(live_backend):
    # Toza bazada (CI) vazifa bo'lmaydi — o'zimiz yaratib, oxirida tozalaymiz.
    # MUHIM: test-server ALOHIDA baza faylida ishlaydi, shuning uchun qatorni
    # aynan o'sha faylga yozamiz (aks holda CLI 404 ko'radi).
    import sqlite3

    task_id = "test_5h_status_contract"
    conn = sqlite3.connect(live_backend.db_path, timeout=30.0)
    try:
        conn.execute(
            "INSERT INTO tasks (task_id, title, prompt, target_agent, execution_mode, "
            "status, current_step, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'standard', 'working', 'planner', ?, ?)",
            (task_id, "5h status sinovi", "status kontrakti", "scout",
             "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
        )
        conn.commit()

        proc = _run_cli(live_backend, "status", task_id, "--json")
        assert proc.returncode == 0, proc.stderr[-400:]
        payload = json.loads(proc.stdout[proc.stdout.find("{"):proc.stdout.rfind("}") + 1])
        assert payload["task_id"] == task_id
        assert payload["status"] == payload["task"]["status"]
        assert "evidence" in payload
        assert "logs" in payload
    finally:
        conn.execute("DELETE FROM logs WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        conn.commit()
        conn.close()


def test_plugin_src_uses_current_user_config_path():
    assert tools.PLUGIN_SRC.endswith(os.path.join("agent-studio-plugin", "src"))
    assert "Users" + os.sep + "user" not in tools.PLUGIN_SRC


def test_cli_json_errors_are_machine_readable(live_backend):
    for command in ("status", "result"):
        proc = _run_cli(live_backend, command, "no-such-task-5h", "--json")
        assert proc.returncode == 1
        payload = json.loads(proc.stdout)
        assert payload["success"] is False
        assert payload["http_status"] == 404
        assert "topilmadi" in payload["error"].lower() or "task not found" in payload["error"].lower()


def test_cli_list_json_has_no_ansi_banner(live_backend):
    proc = _run_cli(live_backend, "list", "--json")
    assert proc.returncode == 0, proc.stderr[-400:]
    assert "\033[" not in proc.stdout
    payload = json.loads(proc.stdout)
    assert "subagents" in payload


def test_api_rejects_unknown_agent():
    from fastapi.testclient import TestClient

    import main

    client = TestClient(main.app)
    resp = client.post(
        "/api/tasks",
        json={"prompt": "5 soatlik sinov", "target_agent": "no_such_agent_5h"},
    )
    assert resp.status_code == 400
    assert "Noma'lum subagent" in resp.json()["detail"]


def test_html_report_escapes_untrusted_task_text():
    import report_generator

    tid = "test_xss_report_5h"
    database.create_task(
        tid,
        "XSS sinovi",
        '<script>alert("xss")</script> va <img src=x onerror=alert(1)>',
        "scout",
    )
    try:
        html_report = report_generator.generate_task_html_report(tid)
        assert "<script>" not in html_report
        assert "<img" not in html_report
        assert "&lt;script&gt;" in html_report
        assert "&lt;img" in html_report
    finally:
        # Faqat shu test yaratgan qatorni tozalaymiz.
        conn = database.get_connection()
        try:
            conn.execute("DELETE FROM tasks WHERE task_id = ?", (tid,))
            conn.commit()
        finally:
            conn.close()
