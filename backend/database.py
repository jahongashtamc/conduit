import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "conduit.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        prompt TEXT NOT NULL,
        target_agent TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'idle',
        current_step TEXT NOT NULL DEFAULT 'idle',
        planner_output TEXT,
        doer_output TEXT,
        checker_output TEXT,
        screenshot_url TEXT,
        evidence TEXT,
        step_durations_json TEXT,
        total_duration REAL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Try altering tasks table if it already exists without new columns
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN step_durations_json TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN total_duration REAL")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN execution_mode TEXT DEFAULT 'standard'")
    except Exception:
        pass
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        level TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        approval_id TEXT UNIQUE NOT NULL,
        task_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        action_type TEXT NOT NULL,
        risk_description TEXT NOT NULL,
        details_json TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        resolved_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        direction TEXT NOT NULL,
        from_agent TEXT NOT NULL,
        to_agent TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        status TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS brain_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE NOT NULL,
        goal TEXT NOT NULL,
        thought TEXT,
        plan_json TEXT,
        active_subagent TEXT,
        active_command_json TEXT,
        last_report_json TEXT,
        short_memory_json TEXT,
        status TEXT NOT NULL DEFAULT 'planning',
        attempt INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        source_task TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id TEXT PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT NOT NULL,
        prompt_template TEXT NOT NULL,
        target_subagents_json TEXT NOT NULL DEFAULT '["*"]',
        enabled INTEGER NOT NULL DEFAULT 1,
        trigger_keywords_json TEXT DEFAULT '[]',
        source_task_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lessons (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        proposed_skill_json TEXT,
        status TEXT NOT NULL DEFAULT 'suggested',
        created_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resource_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        prompt_tokens INTEGER DEFAULT 0,
        completion_tokens INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        duration_seconds REAL DEFAULT 0,
        cost_usd REAL DEFAULT 0,
        timestamp TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resource_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        max_budget_usd REAL DEFAULT 5.0,
        max_tokens INTEGER DEFAULT 200000,
        is_blocked INTEGER DEFAULT 0,
        block_reason TEXT
    );
    """)
    cursor.execute("INSERT OR IGNORE INTO resource_settings (id, max_budget_usd, max_tokens, is_blocked, block_reason) VALUES (1, 5.0, 200000, 0, NULL);")

    # ==================== KERNEL V2 SETTINGS & MODES ====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kernel_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        active_mode TEXT DEFAULT 'standard',
        eepx_confidence_threshold REAL DEFAULT 0.8,
        swarm_max_parallel INTEGER DEFAULT 3,
        auto_heal_swarm INTEGER DEFAULT 1,
        updated_at TEXT
    );
    """)
    cursor.execute("INSERT OR IGNORE INTO kernel_settings (id, active_mode, eepx_confidence_threshold, swarm_max_parallel, auto_heal_swarm, updated_at) VALUES (1, 'standard', 0.8, 3, 1, CURRENT_TIMESTAMP);")

    # ==================== EEPX COGNITIVE TRACES ====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eepx_traces (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        phase TEXT NOT NULL,
        confidence_score REAL DEFAULT 1.0,
        details_json TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    # ==================== SUPER AGENT SWARM STAGES ====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS swarm_stages (
        id TEXT PRIMARY KEY,
        mission_id TEXT NOT NULL,
        stage_index INTEGER NOT NULL,
        stage_title TEXT NOT NULL,
        target_agent TEXT NOT NULL,
        action_prompt TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        input_artifact TEXT,
        output_artifact TEXT,
        evidence TEXT,
        created_at TEXT NOT NULL,
        completed_at TEXT
    );
    """)

    # ==================== DEEPX THOUGHT STEPS ====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deepx_thought_steps (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        step_number INTEGER NOT NULL,
        thought_title TEXT NOT NULL,
        thought_content TEXT NOT NULL,
        perspective TEXT NOT NULL,
        confidence REAL DEFAULT 0.9,
        created_at TEXT NOT NULL
    );
    """)

    # ==================== DEEPSEARCH CITATIONS ====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deepsearch_citations (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        query TEXT NOT NULL,
        source_title TEXT NOT NULL,
        source_uri TEXT NOT NULL,
        summary TEXT NOT NULL,
        relevance_score REAL DEFAULT 0.95,
        created_at TEXT NOT NULL
    );
    """)

    # ==================== MVP BLUEPRINTS ====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mvp_blueprints (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        project_name TEXT NOT NULL,
        frontend_spec_json TEXT,
        backend_spec_json TEXT,
        database_spec_json TEXT,
        security_spec_json TEXT,
        scaffold_status TEXT DEFAULT 'ready',
        created_at TEXT NOT NULL
    );
    """)
    conn.commit()

    # Seed initial memories if empty
    cursor.execute("SELECT COUNT(*) FROM memory")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        seeds = [
            ("Loyiha Maqsadi", "Conduit — AI subagentlar va studio ilovalarini avtomatlashtirish ekotizimi", "Tizim o'rnatilishi"),
            ("Arxitektura Qarori", "Bosh agent Miya (qaror) va Yurak (holat mashinasi) ga ajratilgan, subagentlar mustaqil CLI orqali ishlaydi", "Arxitektura"),
            ("Xavfsizlik Qoidasi", "Har bir subagent faqat ruxsat berilgan toollarni va o'z workspace papkasini ishlatishi mumkin", "Xavfsizlik"),
            ("Dalil Standarti", "Yolg'on dalillar rad etiladi. PASS faqat real artefakt va maqsad tasdiqlanganda beriladi", "Dalil tekshiruvi")
        ]
        for k, v, st in seeds:
            cursor.execute(
                "INSERT INTO memory (key, value, source_task, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (k, v, st, now, now)
            )
        conn.commit()

    # Seed initial skills if empty
    cursor.execute("SELECT COUNT(*) FROM skills")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        initial_skills = [
            (
                "skill_search",
                "Veb qidiruv va ma'lumot tahlili",
                "Google orqali berilgan mavzuni qidirib, topilgan natijalardan eng muhim faktlarni ajratadi va skrinshot oladi.",
                "Foydalanuvchi so'rovini qidirish parametriga aylantir va brauzer orqali ochib skrinshot ol.",
                json.dumps(["scout"]),
                1,
                json.dumps(["qidir", "search", "google", "veb"]),
                None,
                now,
                now
            ),
            (
                "skill_3d_render",
                "3D Model geometriyasi va render",
                "Blender headless Python skripti yordamida procedural 3D sahna va obyekt yaratib render qiladi.",
                "Blender bpy moduli orqali mesh va kamera o'rnatib render_image() chaqir.",
                json.dumps(["sculptor"]),
                1,
                json.dumps(["3d", "blender", "render", "mesh", "model"]),
                None,
                now,
                now
            ),
            (
                "skill_code_audit",
                "Xavfsizlik va kod auditi",
                "Kod bazasini OWASP zaifliklari, ruxsatsiz chaqiruvlar va sintaksis bo'yicha tekshiradi.",
                "Manba kodini tahlil qilib, xavfsizlik zaifliklarini ro'yxatga ol va tavsiyalar ber.",
                json.dumps(["inspector"]),
                1,
                json.dumps(["audit", "xavfsizlik", "kod", "security", "tekshir"]),
                None,
                now,
                now
            )
        ]
        for sk in initial_skills:
            cursor.execute("""
            INSERT INTO skills (id, name, description, prompt_template, target_subagents_json, enabled, trigger_keywords_json, source_task_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sk)
        conn.commit()

    conn.close()

def create_approval(approval_id: str, task_id: str, agent_id: str, 
                    action_type: str, risk_description: str, details: dict) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO approvals (approval_id, task_id, agent_id, action_type, risk_description, details_json, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (approval_id, task_id, agent_id, action_type, risk_description, json.dumps(details), now))
    conn.commit()
    conn.close()
    return get_approval(approval_id)

def get_approval(approval_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approvals WHERE approval_id = ?", (approval_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_pending_approvals() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approvals WHERE status = 'pending' ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def resolve_approval(approval_id: str, decision: str) -> Optional[Dict[str, Any]]:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE approvals SET status = ?, resolved_at = ? WHERE approval_id = ?
    """, (decision, now, approval_id))
    conn.commit()
    conn.close()
    return get_approval(approval_id)

def create_task(task_id: str, title: str, prompt: str, target_agent: str, execution_mode: str = "standard") -> Dict[str, Any]:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tasks (task_id, title, prompt, target_agent, execution_mode, status, current_step, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, 'working', 'planner', ?, ?)
    """, (task_id, title, prompt, target_agent, execution_mode, now, now))
    conn.commit()
    conn.close()
    return get_task(task_id)

def update_task_step(task_id: str, step: str, status: str, output: Optional[str] = None, 
                     screenshot_url: Optional[str] = None, evidence: Optional[str] = None,
                     step_durations: Optional[dict] = None, total_duration: Optional[float] = None):
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = ["current_step = ?", "status = ?", "updated_at = ?"]
    params = [step, status, now]
    
    if step == "planner" and output:
        fields.append("planner_output = ?")
        params.append(output)
    elif step == "doer" and output:
        fields.append("doer_output = ?")
        params.append(output)
    elif step == "checker" and output:
        fields.append("checker_output = ?")
        params.append(output)
        
    if screenshot_url:
        fields.append("screenshot_url = ?")
        params.append(screenshot_url)
    if evidence:
        fields.append("evidence = ?")
        params.append(evidence)
    if step_durations is not None:
        fields.append("step_durations_json = ?")
        params.append(json.dumps(step_durations))
    if total_duration is not None:
        fields.append("total_duration = ?")
        params.append(total_duration)
        
    params.append(task_id)
    query = f"UPDATE tasks SET {', '.join(fields)} WHERE task_id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def _format_task_row(row) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    d = dict(row)
    if "step_durations_json" in d and d["step_durations_json"]:
        try:
            d["step_durations"] = json.loads(d["step_durations_json"])
        except Exception:
            d["step_durations"] = {}
    else:
        d["step_durations"] = {}
    return d

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return _format_task_row(row)

def get_tasks(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [_format_task_row(r) for r in rows if r]

def add_log(task_id: str, agent_name: str, level: str, message: str) -> Dict[str, Any]:
    import security_guard
    clean_message = security_guard.sanitize_text(message)
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO logs (task_id, agent_name, level, message, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (task_id, agent_name, level, clean_message, now))
    conn.commit()
    conn.close()
    return {
        "task_id": task_id,
        "agent_name": agent_name,
        "level": level,
        "message": clean_message,
        "timestamp": now
    }

def get_logs(task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if task_id:
        cursor.execute("SELECT * FROM logs WHERE task_id = ? ORDER BY id ASC LIMIT ?", (task_id, limit))
    else:
        cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ==================== PROTOCOL & BRAIN EVENTS ====================

def log_event(
    task_id: str,
    direction: str,
    from_agent: str,
    to_agent: str,
    payload: dict,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Buyruq yoki hisobot hodisasini SQLite bazasiga saqlaydi.
    - direction: 'command' (Miya -> Subagent) yoki 'report' (Subagent -> Miya)
    - payload: {to, task, expected_evidence} yoki {from, status, evidence, notes}
    """
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO events (task_id, direction, from_agent, to_agent, payload_json, status, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (task_id, direction, from_agent, to_agent, json.dumps(payload), status, now))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": event_id,
        "task_id": task_id,
        "direction": direction,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "payload": payload,
        "status": status,
        "timestamp": now
    }

def get_events(task_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Vazifa bo'yicha barcha hodisalarni qaytaradi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM events WHERE task_id = ? ORDER BY id ASC LIMIT ?
    """, (task_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    events = []
    for r in rows:
        d = dict(r)
        try:
            d["payload"] = json.loads(d.get("payload_json", "{}"))
        except Exception:
            d["payload"] = {}
        events.append(d)
    return events

# ==================== BRAIN STATE & MEMORY ====================

def save_brain_state(
    task_id: str,
    goal: str,
    thought: Optional[str] = None,
    plan: Optional[List[Any]] = None,
    active_subagent: Optional[str] = None,
    active_command: Optional[dict] = None,
    last_report: Optional[dict] = None,
    short_memory: Optional[List[dict]] = None,
    status: Optional[str] = None,
    attempt: Optional[int] = None
) -> Dict[str, Any]:
    """Bosh agent holati va xotirasini yangilaydi yoki yaratadi."""
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()

    existing = get_brain_state(task_id)
    thought_val = thought if thought is not None else (existing.get("thought", "") if existing else "")
    status_val = status if status is not None else (existing.get("status", "planning") if existing else "planning")
    attempt_val = attempt if attempt is not None else (existing.get("attempt", 1) if existing else 1)
    plan_json = json.dumps(plan) if plan is not None else (existing.get("plan_json", "[]") if existing else "[]")
    cmd_json = json.dumps(active_command) if active_command is not None else (existing.get("active_command_json") if existing else None)
    rep_json = json.dumps(last_report) if last_report is not None else (existing.get("last_report_json") if existing else None)
    mem_json = json.dumps(short_memory) if short_memory is not None else (existing.get("short_memory_json", "[]") if existing else "[]")

    if existing:
        cursor.execute("""
        UPDATE brain_memory SET
            thought = ?,
            plan_json = ?,
            active_subagent = ?,
            active_command_json = ?,
            last_report_json = ?,
            short_memory_json = ?,
            status = ?,
            attempt = ?,
            updated_at = ?
        WHERE task_id = ?
        """, (thought_val, plan_json, active_subagent, cmd_json, rep_json, mem_json, status_val, attempt_val, now, task_id))
    else:
        cursor.execute("""
        INSERT INTO brain_memory (
            task_id, goal, thought, plan_json, active_subagent, active_command_json,
            last_report_json, short_memory_json, status, attempt, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (task_id, goal, thought_val, plan_json, active_subagent, cmd_json, rep_json, mem_json, status_val, attempt_val, now, now))

    conn.commit()
    conn.close()
    return get_brain_state(task_id)

def append_brain_memory(task_id: str, decision: str, error: Optional[str] = None, result: Optional[str] = None):
    """Qisqa xotiraga (qaror, xato, natija) yangi element qo'shadi."""
    state = get_brain_state(task_id)
    if not state:
        return
    mem = state.get("short_memory", [])
    mem.append({
        "timestamp": datetime.now().isoformat(),
        "decision": decision,
        "error": error,
        "result": result
    })
    save_brain_state(
        task_id=task_id,
        goal=state.get("goal", ""),
        short_memory=mem
    )

def get_brain_state(task_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM brain_memory WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d["plan"] = json.loads(d.get("plan_json", "[]"))
    except Exception:
        d["plan"] = []
    try:
        d["active_command"] = json.loads(d.get("active_command_json")) if d.get("active_command_json") else None
    except Exception:
        d["active_command"] = None
    try:
        d["last_report"] = json.loads(d.get("last_report_json")) if d.get("last_report_json") else None
    except Exception:
        d["last_report"] = None
    try:
        d["short_memory"] = json.loads(d.get("short_memory_json", "[]"))
    except Exception:
        d["short_memory"] = []
    return d

# ==================== GENERAL SYSTEM MEMORY ====================

def get_memories(search: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        s = f"%{search.strip().lower()}%"
        cursor.execute(
            "SELECT * FROM memory WHERE LOWER(key) LIKE ? OR LOWER(value) LIKE ? OR LOWER(source_task) LIKE ? ORDER BY id DESC",
            (s, s, s)
        )
    else:
        cursor.execute("SELECT * FROM memory ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_memory(key: str, value: str, source_task: Optional[str] = None) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO memory (key, value, source_task, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (key.strip(), value.strip(), (source_task or "").strip(), now, now)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "key": key.strip(),
        "value": value.strip(),
        "source_task": source_task or "",
        "created_at": now,
        "updated_at": now
    }

def update_memory(memory_id: int, key: str, value: str) -> Optional[Dict[str, Any]]:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE memory SET key = ?, value = ?, updated_at = ? WHERE id = ?",
        (key.strip(), value.strip(), now, memory_id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM memory WHERE id = ?", (memory_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_memory(memory_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memory WHERE id = ?", (memory_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# ==================== SKILLS & EVOLUTION ====================

def _parse_skill_row(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    try:
        d["target_subagents"] = json.loads(d.get("target_subagents_json", '["*"]'))
    except Exception:
        d["target_subagents"] = ["*"]
    try:
        d["trigger_keywords"] = json.loads(d.get("trigger_keywords_json", '[]'))
    except Exception:
        d["trigger_keywords"] = []
    d["enabled"] = bool(d.get("enabled", 1))
    return d

def get_skills() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM skills ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [_parse_skill_row(r) for r in rows]

def get_skill(skill_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM skills WHERE id = ?", (skill_id,))
    row = cursor.fetchone()
    conn.close()
    return _parse_skill_row(row) if row else None

def check_skill_conflict(name: str, trigger_keywords: List[str], exclude_id: Optional[str] = None) -> Optional[str]:
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_id:
        cursor.execute("SELECT * FROM skills WHERE id != ?", (exclude_id,))
    else:
        cursor.execute("SELECT * FROM skills")
    existing_skills = [_parse_skill_row(r) for r in cursor.fetchall()]
    conn.close()

    name_clean = name.strip().lower()
    kw_set = {k.strip().lower() for k in trigger_keywords if k.strip()}

    for sk in existing_skills:
        ex_name = sk["name"].strip().lower()
        if ex_name == name_clean:
            return f"DIQQAT: '{sk['name']}' nomli skill tizimda allaqachon mavjud! Ziddiyat aniqlandi."
        ex_kws = {k.strip().lower() for k in sk.get("trigger_keywords", []) if k.strip()}
        common = kw_set.intersection(ex_kws)
        if len(common) >= 2:
            return f"DIQQAT: '{sk['name']}' skilli bilan bir xil kalit so'zlar to'qnashuvi ({', '.join(common)}) aniqlandi!"
    return None

def create_skill(name: str, description: str, prompt_template: str, 
                 target_subagents: List[str], trigger_keywords: List[str], 
                 source_task_id: Optional[str] = None, skill_id: Optional[str] = None) -> Dict[str, Any]:
    import uuid
    sid = skill_id or f"skill_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO skills (id, name, description, prompt_template, target_subagents_json, enabled, trigger_keywords_json, source_task_id, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
    """, (
        sid,
        name.strip(),
        description.strip(),
        prompt_template.strip(),
        json.dumps(target_subagents),
        json.dumps(trigger_keywords),
        source_task_id,
        now,
        now
    ))
    conn.commit()
    conn.close()
    return get_skill(sid)

def update_skill(skill_id: str, name: str, description: str, prompt_template: str, 
                 target_subagents: List[str], trigger_keywords: List[str]) -> Optional[Dict[str, Any]]:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE skills 
    SET name = ?, description = ?, prompt_template = ?, target_subagents_json = ?, trigger_keywords_json = ?, updated_at = ?
    WHERE id = ?
    """, (
        name.strip(),
        description.strip(),
        prompt_template.strip(),
        json.dumps(target_subagents),
        json.dumps(trigger_keywords),
        now,
        skill_id
    ))
    conn.commit()
    conn.close()
    return get_skill(skill_id)

def toggle_skill(skill_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE skills SET enabled = ?, updated_at = ? WHERE id = ?", (1 if enabled else 0, now, skill_id))
    conn.commit()
    conn.close()
    return get_skill(skill_id)

def delete_skill(skill_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# ==================== LESSONS / SABOQLAR ====================

def _parse_lesson_row(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    try:
        d["proposed_skill"] = json.loads(d.get("proposed_skill_json", "{}"))
    except Exception:
        d["proposed_skill"] = {}
    return d

def get_lessons() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [_parse_lesson_row(r) for r in rows]

def create_lesson(task_id: str, title: str, summary: str, proposed_skill: Dict[str, Any]) -> Dict[str, Any]:
    import uuid
    lid = f"lesson_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO lessons (id, task_id, title, summary, proposed_skill_json, status, created_at)
    VALUES (?, ?, ?, ?, ?, 'suggested', ?)
    """, (lid, task_id, title.strip(), summary.strip(), json.dumps(proposed_skill), now))
    conn.commit()
    cursor.execute("SELECT * FROM lessons WHERE id = ?", (lid,))
    row = cursor.fetchone()
    conn.close()
    return _parse_lesson_row(row)

def approve_lesson(lesson_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    lesson = _parse_lesson_row(row)
    cursor.execute("UPDATE lessons SET status = 'approved' WHERE id = ?", (lesson_id,))
    conn.commit()
    conn.close()

    # Automatically create skill if proposed
    prop = lesson.get("proposed_skill", {})
    if prop and prop.get("name"):
        try:
            create_skill(
                name=prop.get("name"),
                description=prop.get("description", lesson.get("summary")),
                prompt_template=prop.get("prompt_template", ""),
                target_subagents=prop.get("target_subagents", ["*"]),
                trigger_keywords=prop.get("trigger_keywords", []),
                source_task_id=lesson.get("task_id")
            )
        except Exception:
            pass

    return get_lessons()

def dismiss_lesson(lesson_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE lessons SET status = 'dismissed' WHERE id = ?", (lesson_id,))
    conn.commit()
    ok = cursor.rowcount > 0
    conn.close()
    return ok

# ==================== BULK APPROVALS ====================

def approve_all_pending_approvals() -> int:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE approvals SET status = 'approved', resolved_at = ? WHERE status = 'pending'", (now,))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# ==================== RESOURCE MANAGEMENT & BUDGET ====================

def record_resource_usage(task_id: str, agent_id: str, prompt_tokens: int, completion_tokens: int, duration_seconds: float) -> Dict[str, Any]:
    total_tokens = prompt_tokens + completion_tokens
    # Claude 3.5 Sonnet benchmark cost: $3/M in, $15/M out
    cost_usd = round((prompt_tokens * 3.0 / 1_000_000) + (completion_tokens * 15.0 / 1_000_000), 6)
    now = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO resource_ledger (task_id, agent_id, prompt_tokens, completion_tokens, total_tokens, duration_seconds, cost_usd, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (task_id, agent_id, prompt_tokens, completion_tokens, total_tokens, duration_seconds, cost_usd, now))
    conn.commit()
    conn.close()

    check_resource_limit()
    return {
        "task_id": task_id,
        "agent_id": agent_id,
        "total_tokens": total_tokens,
        "cost_usd": cost_usd,
        "duration_seconds": duration_seconds
    }

def get_resource_summary() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    # Totals
    cursor.execute("""
    SELECT 
        COALESCE(SUM(prompt_tokens), 0) as total_prompt,
        COALESCE(SUM(completion_tokens), 0) as total_comp,
        COALESCE(SUM(total_tokens), 0) as total_tok,
        COALESCE(SUM(duration_seconds), 0) as total_dur,
        COALESCE(SUM(cost_usd), 0) as total_cost
    FROM resource_ledger
    """)
    totals_row = cursor.fetchone()

    # Per agent breakdown
    cursor.execute("""
    SELECT 
        agent_id,
        COALESCE(SUM(total_tokens), 0) as tokens,
        COALESCE(SUM(duration_seconds), 0) as duration,
        COALESCE(SUM(cost_usd), 0) as cost
    FROM resource_ledger
    GROUP BY agent_id
    """)
    agent_rows = cursor.fetchall()
    by_agent = {}
    for r in agent_rows:
        by_agent[r["agent_id"]] = {
            "tokens": r["tokens"],
            "duration_seconds": round(r["duration"], 2),
            "cost_usd": round(r["cost"], 5)
        }

    # Settings
    cursor.execute("SELECT max_budget_usd, max_tokens, is_blocked, block_reason FROM resource_settings WHERE id = 1")
    setting = cursor.fetchone()
    conn.close()

    max_budget = setting["max_budget_usd"] if setting else 5.0
    max_tokens = setting["max_tokens"] if setting else 200000
    is_blocked = bool(setting["is_blocked"]) if setting else False
    block_reason = setting["block_reason"] if setting else None

    return {
        "total_prompt_tokens": totals_row["total_prompt"],
        "total_completion_tokens": totals_row["total_comp"],
        "total_tokens": totals_row["total_tok"],
        "total_duration_seconds": round(totals_row["total_dur"], 2),
        "total_cost_usd": round(totals_row["total_cost"], 5),
        "max_budget_usd": max_budget,
        "max_tokens": max_tokens,
        "is_blocked": is_blocked,
        "block_reason": block_reason,
        "by_agent": by_agent
    }

def update_resource_limits(max_budget_usd: float, max_tokens: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE resource_settings
    SET max_budget_usd = ?, max_tokens = ?
    WHERE id = 1
    """, (max_budget_usd, max_tokens))
    conn.commit()
    conn.close()
    check_resource_limit()
    return get_resource_summary()

def check_resource_limit() -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        COALESCE(SUM(total_tokens), 0) as total_tok,
        COALESCE(SUM(cost_usd), 0) as total_cost
    FROM resource_ledger
    """)
    totals = cursor.fetchone()
    cursor.execute("SELECT max_budget_usd, max_tokens FROM resource_settings WHERE id = 1")
    setting = cursor.fetchone()

    total_cost = totals["total_cost"] if totals else 0.0
    total_tokens = totals["total_tok"] if totals else 0
    max_budget = setting["max_budget_usd"] if setting else 5.0
    max_tokens = setting["max_tokens"] if setting else 200000

    is_blocked = False
    block_reason = None

    if total_cost >= max_budget:
        is_blocked = True
        block_reason = f"Byudjet limiti tugadi! Sarflangan: ${round(total_cost, 4)} / Limit: ${round(max_budget, 2)}. Agent to'xtatildi."
    elif total_tokens >= max_tokens:
        is_blocked = True
        block_reason = f"Token limiti tugadi! Sarflangan: {total_tokens:,} / Limit: {max_tokens:,} token. Agent to'xtatildi."

    cursor.execute("""
    UPDATE resource_settings
    SET is_blocked = ?, block_reason = ?
    WHERE id = 1
    """, (1 if is_blocked else 0, block_reason))
    conn.commit()
    conn.close()

    return is_blocked, block_reason

# ==================== KERNEL V2 / EEPX / SUPER AGENT HELPERS ====================

def get_kernel_settings() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kernel_settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "active_mode": "standard",
        "eepx_confidence_threshold": 0.8,
        "swarm_max_parallel": 3,
        "auto_heal_swarm": 1
    }

def set_kernel_settings(
    active_mode: Optional[str] = None,
    eepx_confidence_threshold: Optional[float] = None,
    swarm_max_parallel: Optional[int] = None,
    auto_heal_swarm: Optional[int] = None
) -> Dict[str, Any]:
    current = get_kernel_settings()
    mode = active_mode if active_mode is not None else current.get("active_mode", "standard")
    thresh = eepx_confidence_threshold if eepx_confidence_threshold is not None else current.get("eepx_confidence_threshold", 0.8)
    parallel = swarm_max_parallel if swarm_max_parallel is not None else current.get("swarm_max_parallel", 3)
    heal = auto_heal_swarm if auto_heal_swarm is not None else current.get("auto_heal_swarm", 1)

    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE kernel_settings
    SET active_mode = ?, eepx_confidence_threshold = ?, swarm_max_parallel = ?, auto_heal_swarm = ?, updated_at = ?
    WHERE id = 1
    """, (mode, thresh, parallel, heal, now))
    conn.commit()
    conn.close()
    return get_kernel_settings()

def record_eepx_trace(
    task_id: str,
    phase: str,
    confidence_score: float,
    details: Dict[str, Any]
) -> Dict[str, Any]:
    import uuid
    trace_id = f"trace_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO eepx_traces (id, task_id, phase, confidence_score, details_json, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (trace_id, task_id, phase, confidence_score, json.dumps(details), now))
    conn.commit()
    conn.close()
    return {
        "id": trace_id,
        "task_id": task_id,
        "phase": phase,
        "confidence_score": confidence_score,
        "details": details,
        "timestamp": now
    }

def get_eepx_traces(task_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM eepx_traces WHERE task_id = ? ORDER BY timestamp ASC", (task_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        try:
            d["details"] = json.loads(d["details_json"])
        except Exception:
            d["details"] = {}
        res.append(d)
    return res

def create_swarm_stage(
    stage_id: str,
    mission_id: str,
    stage_index: int,
    stage_title: str,
    target_agent: str,
    action_prompt: str,
    input_artifact: Optional[str] = None
) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO swarm_stages (id, mission_id, stage_index, stage_title, target_agent, action_prompt, status, input_artifact, created_at)
    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
    """, (stage_id, mission_id, stage_index, stage_title, target_agent, action_prompt, input_artifact, now))
    conn.commit()
    conn.close()
    return {
        "id": stage_id,
        "mission_id": mission_id,
        "stage_index": stage_index,
        "stage_title": stage_title,
        "target_agent": target_agent,
        "action_prompt": action_prompt,
        "status": "pending",
        "input_artifact": input_artifact,
        "created_at": now
    }

def update_swarm_stage(
    stage_id: str,
    status: str,
    output_artifact: Optional[str] = None,
    evidence: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE swarm_stages
    SET status = ?, output_artifact = ?, evidence = ?, completed_at = ?
    WHERE id = ?
    """, (status, output_artifact, evidence, now, stage_id))
    conn.commit()
    cursor.execute("SELECT * FROM swarm_stages WHERE id = ?", (stage_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_swarm_stages(mission_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM swarm_stages WHERE mission_id = ? ORDER BY stage_index ASC", (mission_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

get_all_lessons = get_lessons

def append_task_log(task_id: str, agent_name: str, message: str, level: str = "INFO"):
    return add_log(task_id, agent_name, level.upper(), message)

def update_task_status(
    task_id: str,
    status: str,
    step: str = "working",
    planner_output: Optional[str] = None,
    doer_output: Optional[str] = None,
    checker_output: Optional[str] = None,
    screenshot_url: Optional[str] = None,
    evidence: Optional[str] = None
):
    out = checker_output or doer_output or planner_output
    return update_task_step(task_id, step, status, output=out, screenshot_url=screenshot_url, evidence=evidence)

# ==================== DEEPX & DEEPSEARCH HELPERS ====================

def record_deepx_thought(
    task_id: str,
    step_number: int,
    thought_title: str,
    thought_content: str,
    perspective: str,
    confidence: float = 0.95
) -> Dict[str, Any]:
    thought_id = f"th_{datetime.now().strftime('%M%S%f')[:8]}"
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO deepx_thought_steps (id, task_id, step_number, thought_title, thought_content, perspective, confidence, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (thought_id, task_id, step_number, thought_title, thought_content, perspective, confidence, now))
    conn.commit()
    conn.close()
    return {
        "id": thought_id,
        "task_id": task_id,
        "step_number": step_number,
        "thought_title": thought_title,
        "thought_content": thought_content,
        "perspective": perspective,
        "confidence": confidence,
        "created_at": now
    }

def get_deepx_thoughts(task_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deepx_thought_steps WHERE task_id = ? ORDER BY step_number ASC", (task_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def record_deepsearch_citation(
    task_id: str,
    query: str,
    source_title: str,
    source_uri: str,
    summary: str,
    relevance_score: float = 0.95
) -> Dict[str, Any]:
    cit_id = f"cit_{datetime.now().strftime('%M%S%f')[:8]}"
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO deepsearch_citations (id, task_id, query, source_title, source_uri, summary, relevance_score, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (cit_id, task_id, query, source_title, source_uri, summary, relevance_score, now))
    conn.commit()
    conn.close()
    return {
        "id": cit_id,
        "task_id": task_id,
        "query": query,
        "source_title": source_title,
        "source_uri": source_uri,
        "summary": summary,
        "relevance_score": relevance_score,
        "created_at": now
    }

def get_deepsearch_citations(task_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deepsearch_citations WHERE task_id = ? ORDER BY relevance_score DESC", (task_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_mvp_blueprint(
    task_id: str,
    project_name: str,
    frontend_spec: Dict[str, Any],
    backend_spec: Dict[str, Any],
    database_spec: Dict[str, Any],
    security_spec: Dict[str, Any]
) -> Dict[str, Any]:
    bp_id = f"bp_{datetime.now().strftime('%M%S%f')[:8]}"
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO mvp_blueprints (id, task_id, project_name, frontend_spec_json, backend_spec_json, database_spec_json, security_spec_json, scaffold_status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'ready', ?)
    """, (
        bp_id,
        task_id,
        project_name,
        json.dumps(frontend_spec, ensure_ascii=False),
        json.dumps(backend_spec, ensure_ascii=False),
        json.dumps(database_spec, ensure_ascii=False),
        json.dumps(security_spec, ensure_ascii=False),
        now
    ))
    conn.commit()
    conn.close()
    return {
        "id": bp_id,
        "task_id": task_id,
        "project_name": project_name,
        "frontend_spec": frontend_spec,
        "backend_spec": backend_spec,
        "database_spec": database_spec,
        "security_spec": security_spec,
        "scaffold_status": "ready",
        "created_at": now
    }

def get_mvp_blueprint(task_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mvp_blueprints WHERE task_id = ? ORDER BY created_at DESC LIMIT 1", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for k in ["frontend_spec", "backend_spec", "database_spec", "security_spec"]:
        json_key = f"{k}_json"
        try:
            d[k] = json.loads(d[json_key])
        except Exception:
            d[k] = {}
    return d





def reconcile_orphaned_tasks(reason: str = "Server qayta ishga tushdi, jarayon uzildi.") -> int:
    """Marks tasks left in 'working' as BLOCKED after a restart.

    A background CLI process cannot survive a backend restart, so any task still
    marked 'working' at startup is orphaned: it would otherwise stay "working"
    forever and keep the UI spinning. Returns how many rows were fixed.
    """
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT task_id FROM tasks WHERE status = 'working'"
    )
    orphans = [row[0] for row in cursor.fetchall()]
    for task_id in orphans:
        cursor.execute(
            "UPDATE tasks SET status = ?, current_step = ?, evidence = ?, updated_at = ? "
            "WHERE task_id = ?",
            ("BLOCKED", "completed", reason, now, task_id),
        )
    conn.commit()
    return len(orphans)


def purge_test_tasks(prefixes: tuple = ("test_",)) -> int:
    """Deletes rows created by the pytest suite so they never reach the UI.

    The tests write real rows into the shared database; without this the
    dashboard fills up with fake 'test_*' tasks that stay 'working' forever.
    """
    conn = get_connection()
    cursor = conn.cursor()
    deleted = 0
    for prefix in prefixes:
        cursor.execute("SELECT task_id FROM tasks WHERE task_id LIKE ?", (prefix + "%",))
        ids = [row[0] for row in cursor.fetchall()]
        for task_id in ids:
            cursor.execute("DELETE FROM logs WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            deleted += 1
    conn.commit()
    return deleted
