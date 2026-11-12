"""Vazifa zanjiri (Pipeline).

Bir nechta agentni ketma-ket ishga tushiradi: har bir oldingi vazifaning
natijasi (evidence) keyingisiga kontekst bo'lib beriladi. Oldingi qadam
FAIL/BLOCKED bo'lsa zanjir to'xtaydi.

    POST /api/pipeline {"steps": [{"agent": "scout", "prompt": "..."}, ...]}
    GET  /api/pipeline/{id}
    GET  /api/pipelines

Ishga tushirish FastAPI event loop'ida bo'ladi: main.py
`run_pipeline_async(pid, execute_task_lifecycle)` ni asyncio.create_task bilan
chaqiradi — shunda WebSocket broadcast va semaphore'lar ishlaydi.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional

import database


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(database.DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    return con


def init_pipeline_db() -> None:
    with _connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS pipelines (
                pipeline_id TEXT PRIMARY KEY,
                name TEXT,
                steps_json TEXT NOT NULL,
                current_step INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                task_ids TEXT DEFAULT '[]',
                created_at REAL,
                updated_at REAL
            )
            """
        )


def validate_steps(steps: Any) -> List[Dict[str, Any]]:
    if not isinstance(steps, list) or not steps:
        raise ValueError("Kamida bitta qadam kerak")
    clean: List[Dict[str, Any]] = []
    for s in steps:
        if not isinstance(s, dict) or not s.get("agent") or not s.get("prompt"):
            raise ValueError("Har qadamda 'agent' va 'prompt' bo'lishi shart")
        clean.append({"agent": str(s["agent"]).lower(), "prompt": str(s["prompt"])})
    return clean


def create_pipeline(steps: List[Dict[str, Any]], name: str = "") -> Dict[str, Any]:
    steps = validate_steps(steps)
    pid = f"pipe_{uuid.uuid4().hex[:8]}"
    init_pipeline_db()
    with _connect() as con:
        con.execute(
            "INSERT INTO pipelines (pipeline_id, name, steps_json, current_step, status, task_ids, created_at, updated_at) "
            "VALUES (?, ?, ?, 0, 'running', '[]', ?, ?)",
            (pid, name or f"{len(steps)} qadamli zanjir", json.dumps(steps, ensure_ascii=False), time.time(), time.time()),
        )
    return get_pipeline(pid)


def get_pipeline(pid: str) -> Optional[Dict[str, Any]]:
    init_pipeline_db()
    with _connect() as con:
        row = con.execute("SELECT * FROM pipelines WHERE pipeline_id = ?", (pid,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["steps"] = json.loads(d.pop("steps_json") or "[]")
    d["task_ids"] = json.loads(d.pop("task_ids") or "[]")
    return d


def list_pipelines(limit: int = 20) -> List[Dict[str, Any]]:
    init_pipeline_db()
    with _connect() as con:
        rows = [dict(r) for r in con.execute(
            "SELECT * FROM pipelines ORDER BY created_at DESC LIMIT ?", (limit,)
        )]
    for d in rows:
        d["steps"] = json.loads(d.pop("steps_json") or "[]")
        d["task_ids"] = json.loads(d.pop("task_ids") or "[]")
    return rows


def _update(pid: str, **fields: Any) -> None:
    fields["updated_at"] = time.time()
    sets = ", ".join(f"{k} = ?" for k in fields)
    with _connect() as con:
        con.execute(f"UPDATE pipelines SET {sets} WHERE pipeline_id = ?", (*fields.values(), pid))


async def run_pipeline_async(
    pid: str,
    execute_task_lifecycle: Callable[[str, str, str], Awaitable[Any]],
    stop_event: Optional[Any] = None,
) -> Dict[str, Any]:
    """Zanjirni event loop ichida ketma-ket bajaradi.

    execute_task_lifecycle — main.py'dagi async funksiya (task_id, prompt, agent).
    """
    import asyncio

    pipe = get_pipeline(pid)
    if not pipe:
        raise ValueError("Zanjir topilmadi")
    steps = pipe["steps"]
    task_ids: List[str] = []

    for idx, step in enumerate(steps):
        _update(pid, current_step=idx)
        agent = step["agent"]
        prompt = step["prompt"]

        # Oldingi qadam natijasi keyingisiga kontekst bo'ladi.
        if task_ids:
            prev = database.get_task(task_ids[-1]) or {}
            if (prev.get("status") or "").upper() in ("FAIL", "BLOCKED"):
                _update(pid, status=f"stopped_at_step_{idx}", task_ids=json.dumps(task_ids))
                return get_pipeline(pid)  # type: ignore[return-value]
            prev_ev = (prev.get("evidence") or "").strip()
            if prev_ev:
                prompt = f"{prompt}\n\nOldingi qadam natijasi ({prev.get('target_agent')}): {prev_ev[:400]}"

        task_id = f"task_{uuid.uuid4().hex[:8]}"
        database.create_task(task_id, prompt[:60], prompt, agent, execution_mode="standard")
        database.add_log(task_id, "Pipeline", "INFO", f"Zanjir {pid}, qadam {idx + 1}/{len(steps)} ({agent})")

        try:
            await execute_task_lifecycle(task_id, prompt, agent)
        except Exception as exc:  # noqa: BLE001 - one failed step stops the chain
            database.add_log(task_id, "Pipeline", "ERROR", f"Qadam xatosi: {str(exc)[:200]}")
            _update(pid, status=f"error_at_step_{idx}", task_ids=json.dumps(task_ids + [task_id]))
            return get_pipeline(pid)  # type: ignore[return-value]

        task_ids.append(task_id)
        _update(pid, task_ids=json.dumps(task_ids))

    _update(pid, status="completed", task_ids=json.dumps(task_ids))
    return get_pipeline(pid)  # type: ignore[return-value]
