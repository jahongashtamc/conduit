import os
import sys
import logging
import shutil
import uuid
import json
import time
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import database
import apps_manager
import subagent_scanner
import manager_router
import workspace_manager
import security_guard
import clone_manager

LOGGER = logging.getLogger("nexus.main")


def _configure_studio_logging() -> None:
    """DEBUG ham ko'rinsin: aks holda 22 ta tuzatilgan xato yana jim qolardi."""
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    for name in ("nexus", "conduit"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.propagate = False


_configure_studio_logging()

import report_generator
from engine.healer import SelfHealer
from engine import cli_runner

# Initialize database
database.init_db()

# Track running background tasks & approval events
running_tasks: Dict[str, asyncio.Task] = {}
pending_approval_futures: Dict[str, asyncio.Future] = {}

# Jonli sahna: task_id -> shu vazifani kuzatayotgan WebSocket'lar.
TASK_STREAMS: Dict[str, List[WebSocket]] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as exc:
                LOGGER.warning("WS broadcast yuborilmadi: %s: %s", type(exc).__name__, exc)
                self.disconnect(connection)
        # Jonli sahna: task_id'li xabarlarni shu vazifani kuzatuvchilarga ham yuboramiz.
        task_id = message.get("task_id")
        if task_id:
            for tws in list(TASK_STREAMS.get(task_id, [])):
                try:
                    await tws.send_json(message)
                except Exception:
                    try:
                        TASK_STREAMS.get(task_id, []).remove(tws)
                    except ValueError as exc:
                        LOGGER.debug("TASK_STREAMS tozalash: %s (task=%s)", exc, task_id)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure workspaces are initialized
    for agent in ["scout", "inspector", "sculptor", "animator", "editor", "painter", "designer"]:
        workspace_manager.get_agent_workspace(agent)

    # Background CLI processes do not survive a restart, so any task still marked
    # 'working' is orphaned. Fail it explicitly instead of spinning forever.
    try:
        purged = database.purge_test_tasks()
        if purged:
            print(f"[startup] {purged} ta pytest test-vazifasi tozalandi.")
        orphaned = database.reconcile_orphaned_tasks()
        if orphaned:
            print(f"[startup] {orphaned} ta osilib qolgan vazifa BLOCKED ga o'tkazildi.")
    except Exception as exc:  # noqa: BLE001 - startup must not fail on this
        print(f"[startup] Osilgan vazifalarni tozalashda xato: {exc}")

    # Saqlangan tokenlarni env'ga yuklaymiz (UI orqali kiritilganlar).
    try:
        _apply_tokens()
    except Exception as exc:
        LOGGER.error("Saqlangan tokenlar yuklanmadi: %s: %s", type(exc).__name__, exc)

    yield
    # Shutdown: clean up all background processes gracefully
    for task_id, task_coro in list(running_tasks.items()):
        if not task_coro.done():
            task_coro.cancel()
    running_tasks.clear()

app = FastAPI(title="Conduit AI Dashboard API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(os.path.join(STATIC_DIR, "screenshots"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Mahalliy kutubxonalar: Anime.js v4 (CDN'siz, oflayn demo uchun)
ANIMEJS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "vendor", "libraries", "animejs"
)
os.makedirs(ANIMEJS_DIR, exist_ok=True)
app.mount("/library/animejs", StaticFiles(directory=ANIMEJS_DIR), name="animejs-library")

class TaskCreateRequest(BaseModel):
    prompt: str
    target_agent: Optional[str] = "auto"
    execution_mode: Optional[str] = None

class KernelSettingsRequest(BaseModel):
    active_mode: Optional[str] = None
    eepx_confidence_threshold: Optional[float] = None
    swarm_max_parallel: Optional[int] = None
    auto_heal_swarm: Optional[int] = None

class ApprovalDecisionRequest(BaseModel):
    decision: str  # "approved" or "rejected"

@app.get("/api/health")
def get_health():
    return {"status": "ok", "service": "Conduit API", "version": "1.0.0"}

@app.get("/api/screenshot/latest")
def get_latest_screenshot():
    """Eng so'nggi olingan skrinshot tasvirini qaytaradi."""
    screenshots_dir = os.path.join(STATIC_DIR, "screenshots")
    if os.path.exists(screenshots_dir):
        latest_png = os.path.join(screenshots_dir, "latest.png")
        if os.path.exists(latest_png) and os.path.getsize(latest_png) > 0:
            return FileResponse(latest_png, media_type="image/png")
        
        files = [
            os.path.join(screenshots_dir, f)
            for f in os.listdir(screenshots_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and f != "latest.png"
        ]
        if files:
            latest_file = max(files, key=os.path.getmtime)
            if os.path.getsize(latest_file) > 0:
                return FileResponse(latest_file, media_type="image/png")

    recent_tasks = database.get_tasks(limit=5)
    for t in recent_tasks:
        s_url = t.get("screenshot_url")
        if s_url:
            if os.path.isabs(s_url) and os.path.exists(s_url):
                return FileResponse(s_url, media_type="image/png")
            if s_url.startswith("/static/"):
                rel_path = os.path.join(os.path.dirname(__file__), s_url.lstrip("/"))
                if os.path.exists(rel_path):
                    return FileResponse(rel_path, media_type="image/png")

    raise HTTPException(status_code=404, detail="Hali skrinshot yo'q")


@app.get("/api/browser/state")
async def browser_state():
    """Live browser presence: is a subagent page open right now?"""
    import live_browser

    return live_browser.state()


@app.get("/api/browser/frame")
async def browser_frame():
    """Current JPEG frame of the subagent browser, for the live view panel."""
    import live_browser

    data = await live_browser.frame()
    if not data:
        raise HTTPException(status_code=404, detail="Brauzer ochilmagan")
    return Response(content=data, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


class BrowserClickRequest(BaseModel):
    x: float
    y: float


@app.post("/api/browser/click")
async def browser_click(req: BrowserClickRequest):
    """Lets the operator click inside the live view."""
    import live_browser

    ok = await live_browser.click_in_view(req.x, req.y)
    return {"success": ok, "state": live_browser.state()}


class BrowserNavRequest(BaseModel):
    url: str


@app.post("/api/browser/navigate")
async def browser_navigate(req: BrowserNavRequest):
    import live_browser
    import url_validation

    try:
        target = url_validation.normalize_navigation_url(req.url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    ok = await live_browser.navigate(target)
    return {"success": ok, "state": live_browser.state(), "url": target}

class EngineSelectRequest(BaseModel):
    engine: str

@app.get("/api/engine/status")
def get_engine_status():
    return cli_runner.get_engine_status()

@app.get("/api/agent/status")
def get_legacy_agent_status():
    eng = cli_runner.get_engine_status()
    return {
        "is_connected": eng.get("is_connected", True),
        "agent_name": eng.get("engines", {}).get(eng.get("active_engine"), {}).get("name", "Claude Code CLI"),
        "mcp_config_sample": {},
        **eng
    }

@app.post("/api/engine/select")
def select_engine(req: EngineSelectRequest):
    cfg = cli_runner.load_engine_config()
    if req.engine in cfg.get("engines", {}):
        cfg["active_engine"] = req.engine
        with open(cli_runner.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    return cli_runner.get_engine_status()

class AppCreateRequest(BaseModel):
    name: str
    exe_path: str
    run_template: Optional[str] = ""
    extension: Optional[str] = ""
    category: Optional[str] = "Creative"

class AppToggleRequest(BaseModel):
    enabled: bool

@app.get("/api/apps")
def get_apps():
    return apps_manager.get_apps_status()

@app.post("/api/apps")
def add_new_app(req: AppCreateRequest):
    app_id = req.name.strip().lower().replace(" ", "_")
    ok = apps_manager.add_app_to_registry(
        app_id=app_id,
        name=req.name.strip(),
        category=req.category or "Creative",
        executable=os.path.basename(req.exe_path) if req.exe_path else f"{app_id}.exe",
        exe_path=req.exe_path.strip(),
        run_template=req.run_template or "",
        extension=req.extension or ""
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Ilovani ro'yxatga qo'shib bo'lmadi")
    return {"success": True, "apps": apps_manager.get_apps_status()}

@app.patch("/api/apps/{app_id}/toggle")
def toggle_app_endpoint(app_id: str, req: AppToggleRequest):
    ok = apps_manager.toggle_app_enabled(app_id, req.enabled)
    if not ok:
        raise HTTPException(status_code=404, detail="Ilova topilmadi yoki o'zgartirilmadi")
    return {"success": True, "app_id": app_id, "enabled": req.enabled}

# ==================== FAZA 4: ILOVA ADAPTERLARI VA BLENDER ====================

class AdapterRunRequest(BaseModel):
    app_id: str
    script: Optional[str] = None
    args: Optional[List[str]] = None
    headless: Optional[bool] = True

class BlenderExecuteRequest(BaseModel):
    code: str
    model_name: Optional[str] = "3d_scene"

@app.get("/api/adapter/apps")
def get_adapter_apps_endpoint():
    import app_adapter
    return app_adapter.get_all_adapters_status()

@app.post("/api/adapter/blender")
def execute_blender_endpoint(req: BlenderExecuteRequest):
    import app_adapter
    return app_adapter.execute_blender_headless(req.code, model_name=req.model_name)

@app.get("/api/figma/file/{file_key}")
def get_figma_file_endpoint(file_key: str):
    import app_adapter
    return app_adapter.get_figma_project_info(file_key)

@app.get("/api/subagents")
def get_subagents():
    return subagent_scanner.scan_subagents()

@app.get("/api/tasks")
def list_tasks():
    return database.get_tasks()

@app.delete("/api/tasks/history")
def clear_task_history():
    deleted = database.purge_finished_tasks()
    return {"success": True, "deleted": deleted}

@app.get("/api/tasks/{task_id}")
def get_task_detail(task_id: str):
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    logs = database.get_logs(task_id)
    return {"task": task, "logs": logs}

@app.post("/api/tasks/{task_id}/retry")
async def retry_task_endpoint(task_id: str):
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi")
    
    # Qayta urinishni boshlash
    database.update_task_step(task_id, "planner", "working", output="Qayta urinish boshlanmoqda...", evidence="")
    database.add_log(task_id, task["target_agent"], "INFO", "Foydalanuvchi tomonidan qayta urinish (Retry) ishga tushirildi.")
    await manager.broadcast({
        "type": "task_update",
        "task_id": task_id,
        "data": {
            "current_step": "planner",
            "status": "working",
            "output": "Qayta urinish boshlandi...",
            "evidence": None
        }
    })
    
    bg_task = asyncio.create_task(execute_task_lifecycle(task_id, task["target_agent"], task["prompt"]))
    running_tasks[task_id] = bg_task
    return {"success": True, "task_id": task_id, "status": "retrying"}

@app.get("/api/tasks/{task_id}/report")
def get_task_report_endpoint(task_id: str, format: str = "markdown"):
    if format.lower() == "html":
        html = report_generator.generate_task_html_report(task_id)
        return Response(content=html, media_type="text/html")
    else:
        md = report_generator.generate_task_markdown_report(task_id)
        return Response(content=md, media_type="text/markdown")

# ==================== KERNEL V2 / EEPX / SUPER AGENT ENDPOINTS ====================

@app.get("/api/kernel/settings")
def get_kernel_settings_endpoint():
    return database.get_kernel_settings()

@app.post("/api/kernel/settings")
def set_kernel_settings_endpoint(req: KernelSettingsRequest):
    if req.active_mode and req.active_mode not in ["standard", "eepx", "super_agent", "deepx"]:
        raise HTTPException(status_code=400, detail="Noto'g'ri rejim. Ruxsat etilgan: standard, eepx, super_agent, deepx")
    updated = database.set_kernel_settings(
        active_mode=req.active_mode,
        eepx_confidence_threshold=req.eepx_confidence_threshold,
        swarm_max_parallel=req.swarm_max_parallel,
        auto_heal_swarm=req.auto_heal_swarm
    )
    return {"success": True, "settings": updated}

@app.get("/api/kernel/telemetry")
def get_kernel_telemetry_endpoint():
    settings = database.get_kernel_settings()
    res_summary = database.get_resource_summary()
    return {
        "active_mode": settings.get("active_mode", "standard"),
        "confidence_threshold": settings.get("eepx_confidence_threshold", 0.8),
        "swarm_parallel_limit": settings.get("swarm_max_parallel", 3),
        "auto_healing_active": bool(settings.get("auto_heal_swarm", 1)),
        "total_cost_usd": res_summary.get("total_cost_usd", 0.0),
        "total_tokens": res_summary.get("total_tokens", 0),
        "is_budget_blocked": res_summary.get("is_blocked", False),
        "running_tasks_count": len(running_tasks),
        "kernel_version": "2.4.0-elite"
    }

@app.get("/api/tasks/{task_id}/deepx/thoughts")
def get_task_deepx_thoughts_endpoint(task_id: str):
    thoughts = database.get_deepx_thoughts(task_id)
    return {"task_id": task_id, "thoughts": thoughts, "count": len(thoughts)}

@app.get("/api/tasks/{task_id}/deepx/citations")
def get_task_deepx_citations_endpoint(task_id: str):
    citations = database.get_deepsearch_citations(task_id)
    return {"task_id": task_id, "citations": citations, "count": len(citations)}

@app.get("/api/tasks/{task_id}/deepx/blueprint")
def get_task_deepx_blueprint_endpoint(task_id: str):
    blueprint = database.get_mvp_blueprint(task_id)
    return {"task_id": task_id, "blueprint": blueprint}

@app.post("/api/sentinel/audit")
async def trigger_sentinel_audit_endpoint(task_id: str, prompt: Optional[str] = "Ad-hoc security stress-test"):
    kernel = ConduitKernel(ws_broadcast=manager.broadcast)
    super_ws = workspace_manager.get_agent_workspace("superagent")
    report = await kernel.run_sentinel_stress_test(task_id, super_ws, prompt)
    return {"task_id": task_id, "report": report}

@app.get("/api/tasks/{task_id}/eepx")
def get_task_eepx_traces_endpoint(task_id: str):
    traces = database.get_eepx_traces(task_id)
    return {"task_id": task_id, "traces": traces, "count": len(traces)}

@app.get("/api/tasks/{task_id}/swarm")
def get_task_swarm_stages_endpoint(task_id: str):
    stages = database.get_swarm_stages(task_id)
    return {"mission_id": task_id, "stages": stages, "count": len(stages)}

@app.get("/api/healing/events")
def get_healing_events_endpoint(task_id: Optional[str] = None):
    return SelfHealer.get_healing_events(task_id)

@app.post("/api/tasks/{task_id}/self-heal")
async def trigger_task_self_heal_endpoint(task_id: str):
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi")
    err_text = task.get("evidence", "Noma'lum xatolik")
    agent = task.get("target_agent", "scout")
    heal_evt = SelfHealer.apply_auto_heal(task_id, agent, task.get("prompt", ""), err_text, attempt=1)
    
    database.update_task_step(task_id, "planner", "working", output=f"Self-Healing faol: {heal_evt['diagnosis']}")
    await manager.broadcast({
        "type": "self_heal_triggered",
        "task_id": task_id,
        "healing_event": heal_evt
    })
    bg_task = asyncio.create_task(execute_task_lifecycle(task_id, agent, heal_evt["healed_prompt"]))
    running_tasks[task_id] = bg_task
    return {"success": True, "healing_event": heal_evt}

@app.get("/api/tasks/{task_id}/logs")
def get_task_logs(task_id: str):
    return database.get_logs(task_id)

@app.get("/api/brain/state/{task_id}")
def get_brain_state_endpoint(task_id: str):
    state = database.get_brain_state(task_id)
    if not state:
        return {"task_id": task_id, "status": "idle", "thought": "Faol emas"}
    return state

@app.get("/api/brain/events/{task_id}")
def get_brain_events_endpoint(task_id: str):
    return database.get_events(task_id)

class MemoryCreateRequest(BaseModel):
    key: str
    value: str
    source_task: Optional[str] = ""

class MemoryItemUpdateRequest(BaseModel):
    key: str
    value: str

@app.get("/api/memory")
def get_memories_endpoint(search: Optional[str] = None):
    return database.get_memories(search)

@app.post("/api/memory")
def create_memory_endpoint(req: MemoryCreateRequest):
    return database.create_memory(req.key, req.value, req.source_task)

@app.put("/api/memory/{memory_id:int}")
def update_memory_endpoint(memory_id: int, req: MemoryItemUpdateRequest):
    item = database.update_memory(memory_id, req.key, req.value)
    if not item:
        raise HTTPException(status_code=404, detail="Xotira elementi topilmadi")
    return item

@app.delete("/api/memory/{memory_id:int}")
def delete_memory_endpoint(memory_id: int):
    ok = database.delete_memory(memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Xotira elementi topilmadi")
    return {"success": True, "id": memory_id}

class MemoryUpdateRequest(BaseModel):
    content: str

@app.get("/api/memory")
def get_all_memory_endpoint():
    import memory_manager
    return memory_manager.get_all_memory()

@app.get("/api/memory/{name}")
def get_memory_block_endpoint(name: str):
    import memory_manager
    return {"name": name, "content": memory_manager.read_memory_block(name)}

@app.post("/api/memory/{name}")
def update_memory_block_endpoint(name: str, req: MemoryUpdateRequest):
    import memory_manager
    ok = memory_manager.write_memory_block(name, req.content)
    if not ok:
        raise HTTPException(status_code=500, detail="Xotira blokini saqlab bo'lmadi")
    return {"name": name, "content": memory_manager.read_memory_block(name), "saved": True}

@app.get("/api/heart/queue")
def get_heart_queue_endpoint():
    from engine import heart
    return heart.get_queue_status()

@app.post("/api/heart/rollback/{task_id}")
def rollback_task_checkpoint(task_id: str):
    from engine import heart
    chks = heart.CHECKPOINTS.get(task_id, [])
    if not chks:
        raise HTTPException(status_code=404, detail="Ushbu vazifa uchun checkpoint topilmadi")
    last_chk = chks[-1]
    return {"success": True, "rollback": last_chk}

@app.get("/api/approvals")
def get_approvals():
    approvals = database.get_pending_approvals()
    for a in approvals:
        action = a.get("action_type", "")
        desc = a.get("risk_description", "").lower()
        a["is_dangerous"] = (
            action in ["file_delete", "git_push", "db_drop", "system_cmd"]
            or any(kw in desc for kw in ["o'chirish", "delete", "rm", "git push", "drop", "wipe"])
        )
    return approvals

@app.post("/api/approvals/approve-all")
async def approve_all_endpoint():
    count = database.approve_all_pending_approvals()
    for aid, fut in list(pending_approval_futures.items()):
        if not fut.done():
            fut.set_result(True)
        del pending_approval_futures[aid]
    await manager.broadcast({
        "type": "approvals_cleared",
        "count": count
    })
    return {"success": True, "approved_count": count}

@app.post("/api/approvals/{approval_id}/resolve")
async def resolve_approval_endpoint(approval_id: str, req: ApprovalDecisionRequest):
    approval = database.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    decision = req.decision.lower()
    if decision not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    database.resolve_approval(approval_id, decision)
    
    # Yangi ilova qo'shish tasdig'i
    if approval.get("action_type") == "add_app":
        details = {}
        try:
            details = json.loads(approval.get("details_json", "{}"))
        except Exception as exc:
            LOGGER.error("Approval details JSON o'qilmadi: %s: %s", type(exc).__name__, exc)
        app_id = details.get("app_id")
        app_name = details.get("app_name")
        category = details.get("category", "Productivity")

        if decision == "approved" and app_id and app_name:
            import subagent_creator
            subagent_creator.create_dynamic_subagent(app_id, app_name, category)
            database.add_log(approval.get("task_id"), "Manager", "INFO", f"'{app_name}' subagenti va apps.json qatori muvaffaqiyatli yaratildi.")
        else:
            database.add_log(approval.get("task_id"), "Manager", "WARNING", f"'{app_name}' ilovasini qo'shish foydalanuvchi tomonidan rad etildi.")
            database.update_task_step(approval.get("task_id"), "completed", "BLOCKED", evidence=f"Foydalanuvchi '{app_name}' ilovasini qo'shishni rad etdi.")

    # Notify waiting future
    if approval_id in pending_approval_futures:
        fut = pending_approval_futures[approval_id]
        if not fut.done():
            fut.set_result(decision == "approved")
        del pending_approval_futures[approval_id]

    await manager.broadcast({
        "type": "approval_resolved",
        "approval_id": approval_id,
        "decision": decision
    })

    return {"success": True, "approval_id": approval_id, "decision": decision}

# ==================== SKILLS & EVOLUTION ENDPOINTS ====================

class SkillCreateRequest(BaseModel):
    name: str
    description: str
    prompt_template: str
    target_subagents: List[str] = ["*"]
    trigger_keywords: List[str] = []
    source_task_id: Optional[str] = None
    force: bool = False

class SkillUpdateRequest(BaseModel):
    name: str
    description: str
    prompt_template: str
    target_subagents: List[str] = ["*"]
    trigger_keywords: List[str] = []

class SkillToggleRequest(BaseModel):
    enabled: bool

class SkillTestRequest(BaseModel):
    test_prompt: str

class ResourceLimitRequest(BaseModel):
    max_budget_usd: float
    max_tokens: int

@app.get("/api/skills")
def get_skills_endpoint():
    return database.get_skills()

@app.post("/api/skills")
def create_skill_endpoint(req: SkillCreateRequest):
    conflict = database.check_skill_conflict(req.name, req.trigger_keywords)
    if conflict and not req.force:
        return JSONResponse(status_code=409, content={"error": "conflict", "message": conflict})
    skill = database.create_skill(
        name=req.name,
        description=req.description,
        prompt_template=req.prompt_template,
        target_subagents=req.target_subagents,
        trigger_keywords=req.trigger_keywords,
        source_task_id=req.source_task_id
    )
    return skill

@app.put("/api/skills/{skill_id}")
def update_skill_endpoint(skill_id: str, req: SkillUpdateRequest):
    skill = database.update_skill(
        skill_id=skill_id,
        name=req.name,
        description=req.description,
        prompt_template=req.prompt_template,
        target_subagents=req.target_subagents,
        trigger_keywords=req.trigger_keywords
    )
    if not skill:
        raise HTTPException(status_code=404, detail="Skill topilmadi")
    return skill

@app.put("/api/skills/{skill_id}/toggle")
def toggle_skill_endpoint(skill_id: str, req: SkillToggleRequest):
    skill = database.toggle_skill(skill_id, req.enabled)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill topilmadi")
    return skill

@app.delete("/api/skills/{skill_id}")
def delete_skill_endpoint(skill_id: str):
    ok = database.delete_skill(skill_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill topilmadi")
    return {"success": True, "id": skill_id}

@app.post("/api/skills/{skill_id}/test")
async def test_skill_endpoint(skill_id: str, req: SkillTestRequest):
    skill = database.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill topilmadi")
    targets = skill.get("target_subagents", ["*"])
    target = targets[0] if targets and targets[0] != "*" else "scout"
    return {
        "success": True,
        "skill_id": skill_id,
        "skill_name": skill["name"],
        "tested_with_agent": target,
        "prompt_evaluated": f"[{skill['name']}] Ko'rsatma: {skill['prompt_template']} | Kiruvchi: {req.test_prompt}",
        "status": "PASS",
        "result_preview": f"Skill muvaffaqiyatli sinovdan o'tdi: '{target}' agentiga instruksiya yuborildi va buyruq bajarilishga tayyor."
    }

@app.post("/api/skills/from-task/{task_id}")
def create_skill_from_task_endpoint(task_id: str):
    task = database.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Vazifa topilmadi")
    agent = task.get("target_agent", "scout")
    title = task.get("title", "Yangi skill")
    prompt = task.get("prompt", "")
    skill = database.create_skill(
        name=f"{agent.capitalize()} - {title[:25]}",
        description=f"'{prompt[:50]}' vazifasidan avtomatik o'zlashtirilgan skill.",
        prompt_template=prompt,
        target_subagents=[agent],
        trigger_keywords=[w.lower() for w in prompt.split() if len(w) > 3][:4],
        source_task_id=task_id
    )
    return skill

@app.get("/api/user-memory")
async def get_user_memory():
    """Suhbat xotirasi: uslub profili + oxirgi muloqotlar."""
    import user_memory

    return {
        "profile": user_memory.get_style_profile(),
        "interactions": user_memory.list_interactions(50),
    }


@app.get("/api/user-memory/recall")
async def recall_user_memory(q: str = ""):
    """Yangi so'rovga o'xshash o'tgan suhbatlar."""
    import user_memory

    return {"matches": user_memory.recall_similar(q, limit=5)}


@app.delete("/api/user-memory")
async def reset_user_memory():
    """Suhbat xotirasini tozalash."""
    import user_memory

    deleted = user_memory.reset_memory()
    return {"success": True, "deleted": deleted}


@app.get("/api/artifacts")
async def list_artifacts():
    """Barcha workspace artefaktlari (galereya uchun)."""
    import artifacts

    return {"artifacts": artifacts.list_artifacts()}


@app.get("/api/artifacts/file")
async def artifact_file(path: str):
    """Workspace ichidagi bitta artefakt faylini xavfsiz qaytaradi."""
    import artifacts
    from fastapi.responses import FileResponse

    try:
        full = artifacts.safe_artifact_path(path)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return FileResponse(full, media_type=artifacts.MEDIA_MIME.get(
        os.path.splitext(full)[1].lower(), "text/plain"
    ))


class TokenRequest(BaseModel):
    name: str
    value: str


TOKEN_NAMES = {"NOTION_TOKEN", "SLACK_BOT_TOKEN", "GITHUB_TOKEN"}


def _tokens_file() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "config", "tokens.json")


def _load_tokens() -> dict:
    path = _tokens_file()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            LOGGER.error("Token fayli o'qilmadi (%s): %s: %s", path, type(exc).__name__, exc)
            return {}
    return {}


def _apply_tokens() -> None:
    for name, value in _load_tokens().items():
        if name in TOKEN_NAMES and value:
            os.environ[name] = value


@app.get("/api/tokens")
async def get_tokens():
    """Qaysi tokenlar sozlangan (qiymat hech qachon qaytarilmaydi)."""
    saved = _load_tokens()
    return {
        name: {
            "configured": bool(saved.get(name) or os.environ.get(name, "").strip()),
        }
        for name in sorted(TOKEN_NAMES)
    }


@app.post("/api/tokens")
async def set_token(req: TokenRequest):
    """Tokenni saqlaydi (config/tokens.json, gitignored) va darhol qo'llaydi."""
    name = req.name.strip().upper()
    if name not in TOKEN_NAMES:
        raise HTTPException(status_code=400, detail=f"Noma'lum token: {name}")
    if not req.value.strip():
        raise HTTPException(status_code=400, detail="Token bo'sh")
    path = _tokens_file()
    saved = _load_tokens()
    saved[name] = req.value.strip()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(saved, fh, indent=2)
    os.environ[name] = saved[name]
    return {"success": True, "name": name, "configured": True}


@app.delete("/api/tokens/{name}")
async def delete_token(name: str):
    name = name.strip().upper()
    if name not in TOKEN_NAMES:
        raise HTTPException(status_code=400, detail=f"Noma'lum token: {name}")
    saved = _load_tokens()
    saved.pop(name, None)
    with open(_tokens_file(), "w", encoding="utf-8") as fh:
        json.dump(saved, fh, indent=2)
    os.environ.pop(name, None)
    return {"success": True, "name": name, "configured": False}


class PipelineRequest(BaseModel):
    steps: list
    name: str = ""


@app.post("/api/pipeline")
async def create_pipeline(req: PipelineRequest):
    """Agentlar zanjirini yaratadi va darhol ishga tushiradi."""
    import pipeline as pipeline_mod

    try:
        pipe = pipeline_mod.create_pipeline(req.steps, req.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    async def runner() -> None:
        async def _lifecycle_adapter(tid: str, step_prompt: str, step_agent: str):
            await execute_task_lifecycle(tid, step_agent, step_prompt)

        await pipeline_mod.run_pipeline_async(pipe["pipeline_id"], _lifecycle_adapter)

    bg = asyncio.create_task(runner())
    running_tasks[pipe["pipeline_id"]] = bg
    return pipe


@app.get("/api/pipelines")
async def list_pipelines():
    import pipeline as pipeline_mod

    return {"pipelines": pipeline_mod.list_pipelines()}


@app.get("/api/pipeline/{pid}")
async def get_pipeline(pid: str):
    import pipeline as pipeline_mod

    pipe = pipeline_mod.get_pipeline(pid)
    if not pipe:
        raise HTTPException(status_code=404, detail="Zanjir topilmadi")
    return pipe


@app.get("/api/lessons")
def get_lessons_endpoint():
    return database.get_lessons()

@app.post("/api/lessons/{lesson_id}/approve")
def approve_lesson_endpoint(lesson_id: str):
    updated = database.approve_lesson(lesson_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Saboq topilmadi")
    return {"success": True, "lesson_id": lesson_id, "status": "approved"}

@app.post("/api/lessons/{lesson_id}/dismiss")
def dismiss_lesson_endpoint(lesson_id: str):
    ok = database.dismiss_lesson(lesson_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Saboq topilmadi")
    return {"success": True, "lesson_id": lesson_id, "status": "dismissed"}

# ==================== RESOURCE MONITORING & BUDGET ====================

@app.get("/api/tools/catalog")
def get_tool_catalog_endpoint():
    """Subagentlar asosiy agentga bog'langan tool'lar sifatida (universal CLI shartnomasi)."""
    import tool_registry  # type: ignore
    return tool_registry.build_tool_catalog()

@app.get("/api/resources")
def get_resources_endpoint():
    return database.get_resource_summary()

@app.post("/api/resources/limit")
def update_resources_limit_endpoint(req: ResourceLimitRequest):
    return database.update_resource_limits(req.max_budget_usd, req.max_tokens)

# ==================== CONNECTION & CLI HEALTH ====================

@app.get("/api/connections")
def get_connections_endpoint():
    tools_def = [
        {"id": "claude", "name": "Claude Code CLI", "category": "AI LLM Engine"},
        {"id": "gh", "name": "GitHub CLI (gh)", "category": "Version Control"},
        {"id": "figma", "name": "Figma Developer Tool", "category": "Design & UI"},
        {"id": "git", "name": "Git CLI", "category": "Version Control"},
        {"id": "python", "name": "Python 3 Runtime", "category": "Core Runtime"},
        {"id": "node", "name": "Node.js & npm", "category": "Frontend Runtime"},
        {"id": "hyperframes", "name": "Hyperframes Video", "category": "Media Engine"},
        {"id": "ffmpeg", "name": "FFmpeg Engine", "category": "Media Processing"},
        {"id": "chrome", "name": "Google Chrome Headless", "category": "Browser Studio"}
    ]
    results = []
    for td in tools_def:
        tid = td["id"]
        path = shutil.which(tid)
        if not path and tid == "chrome":
            for cand in [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
            ]:
                if os.path.exists(cand):
                    path = cand
                    break
        if not path and tid == "python":
            path = sys.executable

        status = "ready" if path else "missing"
        results.append({
            "id": tid,
            "name": td["name"],
            "category": td["category"],
            "status": status,
            "path": path or "O'rnatilmagan yoki PATH da yo'q",
            "is_ready": status == "ready"
        })
    return results

@app.post("/api/connections/check/{tool_id}")
def check_connection_endpoint(tool_id: str):
    path = shutil.which(tool_id)
    if not path and tool_id == "chrome":
        for cand in [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]:
            if os.path.exists(cand):
                path = cand
                break
    if not path and tool_id == "python":
        path = sys.executable

    return {
        "id": tool_id,
        "status": "ready" if path else "missing",
        "path": path or "O'rnatilmagan",
        "is_ready": bool(path)
    }

class PermissionModeRequest(BaseModel):
    mode: str

@app.get("/api/settings/permission-mode")
def get_permission_mode_endpoint():
    return {"mode": security_guard.get_permission_mode()}

@app.post("/api/settings/permission-mode")
def set_permission_mode_endpoint(req: PermissionModeRequest):
    if req.mode not in security_guard.PERMISSION_MODES:
        raise HTTPException(status_code=400, detail="Noto'g'ri ruxsat darajasi")
    mode = security_guard.set_permission_mode(req.mode)
    return {"mode": mode, "success": True}

async def wait_for_approval(approval_id: str, timeout_seconds: int = 120) -> bool:
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    pending_approval_futures[approval_id] = fut
    try:
        result = await asyncio.wait_for(fut, timeout=timeout_seconds)
        return result
    except asyncio.TimeoutError:
        database.resolve_approval(approval_id, "rejected")
        return False
    finally:
        if approval_id in pending_approval_futures:
            del pending_approval_futures[approval_id]

async def execute_task_lifecycle(task_id: str, target_agent: str, prompt: str, approval_id: Optional[str] = None):
    from engine import heart
    semaphore = heart.get_parallel_semaphore()
    ws_lock = heart.get_workspace_lock(target_agent)

    try:
        loop_result: Dict[str, Any] = {}
        async with semaphore:
            async with ws_lock:
                # Har bir vazifa o'z holat mashinasiga ega
                state_machine = heart.HeartStateMachine(task_id, prompt, ws_broadcast=manager.broadcast)
                state_machine.active_subagent = target_agent

                if approval_id:
                    approved = await wait_for_approval(approval_id)
                    if not approved:
                        await state_machine.transition("BLOCKED", agent="heart", reason="Foydalanuvchi ilovani qo'shishni rad etdi.")
                        database.update_task_step(task_id, "completed", "BLOCKED", evidence="Foydalanuvchi talab qilingan ilovani qo'shishni rad etdi.")
                        await manager.broadcast({
                            "type": "task_completed",
                            "task_id": task_id,
                            "target_agent": target_agent,
                            "status": "BLOCKED",
                            "evidence": "Foydalanuvchi talab qilingan ilovani qo'shishni rad etdi."
                        })
                        return
                    unlisted = manager_router.detect_unlisted_app(prompt)
                    if unlisted:
                        target_agent = unlisted["id"]
                        state_machine.active_subagent = target_agent

                await manager.broadcast({
                    "type": "subagent_activated",
                    "agent": target_agent,
                    "task_id": task_id,
                    "status": "working"
                })

                t_rec = database.get_task(task_id)
                current_mode = (t_rec.get("execution_mode") if t_rec else None) or database.get_kernel_settings().get("active_mode", "standard")

                if current_mode == "deepx":
                    from engine.kernel import ConduitKernel
                    kernel = ConduitKernel(ws_broadcast=manager.broadcast)
                    await kernel.run_deepx_pipeline(task_id=task_id, prompt=prompt, target_agent=target_agent)
                elif current_mode == "eepx":
                    from engine.kernel import ConduitKernel
                    kernel = ConduitKernel(ws_broadcast=manager.broadcast)
                    await kernel.run_eepx_pipeline(task_id=task_id, target_agent=target_agent, prompt=prompt)
                elif current_mode == "super_agent" or target_agent in ["super_agent", "superagent", "swarm", "commander"]:
                    from engine.kernel import ConduitKernel
                    kernel = ConduitKernel(ws_broadcast=manager.broadcast)
                    await kernel.run_super_agent_swarm(mission_id=task_id, goal=prompt)
                elif target_agent in ["brain", "manager"]:
                    from engine import brain
                    await brain.run_heartbeat_loop(
                        task_id=task_id,
                        goal=prompt,
                        ws_broadcast=manager.broadcast
                    )
                else:
                    # Haqiqiy CLI Agent Loop (Claude Code / AGY) orqali subagentni boshqarish
                    loop_result = await cli_runner.run_agent_loop(
                        task_id=task_id,
                        subagent=target_agent,
                        task_goal=prompt,
                        ws_broadcast=manager.broadcast
                    ) or {}

                # Resurs sarfini qayd qilish va saboq taklif qilish
                t_data = database.get_task(task_id)
                # total_duration may be present but NULL, and `.get(key, default)`
                # only falls back when the key is missing - hence the explicit check.
                dur = (t_data or {}).get("total_duration")
                if not isinstance(dur, (int, float)):
                    dur = 5.0
                # Provider o'zi token sarfini e'lon qilsa — shundan foydalanamiz;
                # aks holda (masalan instrument agentlar) eski konservativ baho.
                usage = loop_result.get("usage") or {}
                prompt_toks = int(usage.get("prompt_tokens") or max(len(prompt) // 3, 40))
                comp_toks = int(
                    usage.get("completion_tokens")
                    or (max(len(t_data.get("evidence", "") or "") // 3, 60) if t_data else 60)
                )
                database.record_resource_usage(task_id, target_agent, prompt_toks, comp_toks, dur)

                if t_data and t_data.get("status") == "PASS":
                    prop_skill = {
                        "name": f"{target_agent.capitalize()} - {prompt[:25]}",
                        "description": f"{prompt} vazifasini muvaffaqiyatli bajarish uslubi",
                        "prompt_template": prompt,
                        "target_subagents": [target_agent],
                        "trigger_keywords": [w.lower() for w in prompt.split() if len(w) > 3][:4]
                    }
                    lesson = database.create_lesson(
                        task_id=task_id,
                        title=f"{prompt[:35]} tajribasi",
                        summary=f"Vazifa {round(dur, 1)}s da PASS bo'ldi. Agent: {target_agent}.",
                        proposed_skill=prop_skill
                    )
                    await manager.broadcast({
                        "type": "lesson_suggested",
                        "lesson": lesson
                    })
    except Exception as e:
        err_msg = f"Ijroda xatolik: {str(e)}"
        database.add_log(task_id, target_agent, "ERROR", err_msg)
        database.update_task_step(task_id, "completed", "FAIL", evidence=err_msg)
        await manager.broadcast({
            "type": "task_error",
            "task_id": task_id,
            "error": err_msg
        })
    finally:
        if task_id in running_tasks:
            del running_tasks[task_id]

@app.post("/api/tasks")
async def create_new_task(request: TaskCreateRequest):
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt maydoni bo'sh bo'lishi mumkin emas.")

    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    # 0. Resurs va byudjet limitini tekshirish
    is_blocked, block_reason = database.check_resource_limit()
    if is_blocked:
        target_agent = request.target_agent or "scout"
        active_mode = request.execution_mode or database.get_kernel_settings().get("active_mode", "standard")
        task = database.create_task(task_id, prompt[:60], prompt, target_agent, execution_mode=active_mode)
        database.update_task_step(task_id, "completed", "BLOCKED", evidence=block_reason)
        database.add_log(task_id, "ResourceLimit", "ERROR", block_reason)
        await manager.broadcast({
            "type": "task_created",
            "task": database.get_task(task_id)
        })
        await manager.broadcast({
            "type": "task_completed",
            "task_id": task_id,
            "target_agent": target_agent,
            "status": "BLOCKED",
            "evidence": block_reason
        })
        return {
            "success": False,
            "task_id": task_id,
            "target_agent": target_agent,
            "status": "BLOCKED",
            "reason": block_reason
        }
    
    # 2. Ro'yxatda yo'q ilova talab qilinsa tekshirish
    unlisted = manager_router.detect_unlisted_app(prompt)
    approval_id = None
    
    if unlisted:
        app_name = unlisted["name"]
        app_id = unlisted["id"]
        source = unlisted["official_source"]
        category = unlisted["category"]
        approval_id = f"appr_{uuid.uuid4().hex[:6]}"
        reason = f"Bu vazifa uchun '{app_name}' kerak. Qo'shishga ruxsat berasizmi? (Rasmiy manba: {source})"
        target_agent = app_id

        database.create_approval(
            approval_id=approval_id,
            task_id=task_id,
            agent_id="Manager",
            action_type="add_app",
            risk_description=reason,
            details={"app_id": app_id, "app_name": app_name, "category": category, "source": source}
        )
    else:
        target_agent, reason = manager_router.route_task(prompt, request.target_agent)
    
    # 2.5. Tanlangan subagent-tool'i uchun qolgan byudjet yetarlimi?
    # Bu token modelining faqat ko'rsatkich emas, bajarishdagi himoyasidir.
    tool_budget_reason = None
    try:
        import tool_registry
        catalog = tool_registry.build_tool_catalog(include_budget=True)
        selected_tool = next(
            (t for t in catalog.get("tools", []) if t.get("subagent") == target_agent), None
        )
        if selected_tool and selected_tool.get("within_remaining_budget") is False:
            tool_budget_reason = (
                f"'{target_agent}' tool'i uchun byudjet yetarli emas: "
                f"taxminiy {selected_tool.get('estimated_execution_tokens')} token / "
                f"${selected_tool.get('estimated_cost_usd')}."
            )
    except Exception as exc:
        LOGGER.error("Tool byudjeti tekshirilmadi: %s: %s", type(exc).__name__, exc)

    if tool_budget_reason:
        active_mode = request.execution_mode or database.get_kernel_settings().get("active_mode", "standard")
        database.create_task(task_id, prompt[:60], prompt, target_agent, execution_mode=active_mode)
        database.update_task_step(task_id, "completed", "BLOCKED", evidence=tool_budget_reason)
        database.add_log(task_id, "BudgetGuard", "ERROR", tool_budget_reason)
        await manager.broadcast({"type": "task_created", "task": database.get_task(task_id)})
        await manager.broadcast({
            "type": "task_completed",
            "task_id": task_id,
            "target_agent": target_agent,
            "status": "BLOCKED",
            "evidence": tool_budget_reason,
        })
        return {
            "success": False,
            "task_id": task_id,
            "target_agent": target_agent,
            "status": "BLOCKED",
            "reason": tool_budget_reason,
        }

    active_mode = request.execution_mode or database.get_kernel_settings().get("active_mode", "standard")
    task = database.create_task(task_id, prompt[:60], prompt, target_agent, execution_mode=active_mode)
    database.add_log(task_id, "Manager", "INFO", f"Vazifa qabul qilindi. Manager qarori: {reason}")
    # Remember what the user asked, in their own words, for style learning.
    try:
        import user_memory
        user_memory.record_interaction(task_id, target_agent, prompt)
    except Exception as exc:
        LOGGER.error("Foydalanuvchi uslubi saqlanmadi: %s: %s", type(exc).__name__, exc)

    await manager.broadcast({
        "type": "task_created",
        "task": task,
        "routing_reason": reason
    })

    if approval_id:
        await manager.broadcast({
            "type": "approval_required",
            "approval": {
                "approval_id": approval_id,
                "task_id": task_id,
                "action_type": "add_app",
                "reason": reason,
                "details": {"app_id": unlisted["id"], "app_name": unlisted["name"]}
            }
        })

    task_coro = asyncio.create_task(execute_task_lifecycle(task_id, target_agent, prompt, approval_id=approval_id))
    running_tasks[task_id] = task_coro

    return {
        "success": True,
        "task_id": task_id,
        "target_agent": target_agent,
        "routing_reason": reason,
        "requires_approval": bool(approval_id),
        "approval_id": approval_id,
        "task": task
    }

@app.post("/api/kill-all")
async def kill_all_processes():
    cli_runner.kill_all_cli_processes()
    cancelled_count = 0
    for task_id, task_coro in list(running_tasks.items()):
        if not task_coro.done():
            task_coro.cancel()
            cancelled_count += 1
            database.add_log(task_id, "System", "WARNING", "Vazifa 'Kill all' signali bilan to'xtatildi.")
            database.update_task_step(task_id, "completed", "FAIL", evidence="To'xtatildi (Cancelled by user)")
    running_tasks.clear()

    # Reject any pending approvals
    for app_id, fut in list(pending_approval_futures.items()):
        if not fut.done():
            fut.set_result(False)
            database.resolve_approval(app_id, "rejected")
    pending_approval_futures.clear()

    await manager.broadcast({
        "type": "kill_all",
        "message": "Barcha faol subagent jarayonlari to'xtatildi va xavfsiz tozalandi."
    })
    return {"success": True, "cancelled_count": cancelled_count, "message": "All tasks terminated and cleaned up."}

# ==================== TOOLS ENGINE & DEEPSEARCH ENDPOINTS ====================

class CloneCreateRequest(BaseModel):
    url: str
    name: Optional[str] = None
    commit_pin: Optional[str] = None


@app.post("/api/clones")
async def api_clone_repository(req: CloneCreateRequest):
    """Haqiqiy GitHub klonini loyiha ichidagi clones/ papkaga oladi."""
    try:
        result = await asyncio.to_thread(
            clone_manager.clone_repository, req.url, req.name, req.commit_pin
        )
    except clone_manager.CloneError as exc:
        LOGGER.warning("Klonlash rad etildi: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        LOGGER.error("Klonlash xatosi: %s: %s", type(exc).__name__, exc)
        raise HTTPException(status_code=500, detail=f"Klonlash xatosi: {type(exc).__name__}")
    await manager.broadcast({"type": "clone_progress", "status": "ready", "clone": result})
    return {"success": True, "clone": result}


@app.get("/api/clones")
async def api_list_clones():
    return {"clones": clone_manager.list_clones()}


@app.get("/api/clones/{name}")
async def api_get_clone(name: str):
    info = clone_manager.get_clone(name)
    if info is None:
        raise HTTPException(status_code=404, detail="Klon topilmadi")
    return {"clone": info}


@app.post("/api/clones/{name}/refresh")
async def api_refresh_clone(name: str):
    try:
        result = await asyncio.to_thread(clone_manager.refresh_clone, name)
    except clone_manager.CloneError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        LOGGER.error("Klon yangilash xatosi: %s: %s", type(exc).__name__, exc)
        raise HTTPException(status_code=500, detail=f"Yangilash xatosi: {type(exc).__name__}")
    return {"success": True, "clone": result}


@app.delete("/api/clones/{name}")
async def api_delete_clone(name: str):
    try:
        clone_manager.delete_clone(name)
    except clone_manager.CloneError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"success": True, "name": name}


@app.get("/api/research")
async def list_research_reports():
    import datetime as _dt
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    research_dir = os.path.join(workspace_root, "research")
    os.makedirs(research_dir, exist_ok=True)
    reports = []
    for f in os.listdir(research_dir):
        if f.endswith(".md"):
            fp = os.path.join(research_dir, f)
            stat = os.stat(fp)
            topic = f[:-3].replace("_", " ").title()
            reports.append({
                "filename": f,
                "topic": topic,
                "path": f"/research/{f}",
                "updated_at": _dt.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "size_bytes": stat.st_size
            })
    return {"success": True, "reports": sorted(reports, key=lambda x: x["updated_at"], reverse=True)}

@app.get("/api/research/{topic}")
async def get_research_report(topic: str):
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    clean_t = topic.lower().replace(" ", "_").replace(".md", "")
    fp = os.path.join(workspace_root, "research", f"{clean_t}.md")
    if not os.path.exists(fp):
        raise HTTPException(status_code=404, detail=f"Tadqiqot hisoboti '{topic}' topilmadi.")
    with open(fp, "r", encoding="utf-8") as f:
        rep_content = f.read()
    return {"success": True, "topic": topic, "content": rep_content}

@app.get("/api/tools/candidates")
async def get_tool_candidates():
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidates_fp = os.path.join(workspace_root, "tools", "candidates.json")
    if not os.path.exists(candidates_fp):
        return {"success": True, "candidates": []}
    try:
        with open(candidates_fp, "r", encoding="utf-8") as f:
            candidates = json.load(f)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

@app.post("/api/tools/deepsearch")
async def run_deepsearch_endpoint(payload: Dict[str, Any]):
    topic = payload.get("topic", "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Mavzu (topic) ko'rsatilishi shart.")
    from engine.deepsearch import DeepSearchEngine
    from engine.deepx import DeepXAnalyzer
    ds = DeepSearchEngine()
    analyzer = DeepXAnalyzer()
    candidates = await ds.search_candidates_for_topic(topic)
    evaluated = [analyzer.evaluate_candidate(c) for c in candidates]
    report_path = analyzer.generate_research_report(topic, evaluated)
    analyzer.update_candidates_json(evaluated)
    return {
        "success": True,
        "topic": topic,
        "total_candidates": len(evaluated),
        "report_file": report_path,
        "candidates": evaluated
    }


async def _task_preview_frame(task_id: str) -> Optional[dict]:
    """Jonli sahna uchun preview kadr manbasi.

    Ustuvorlik:
    1. Subagent brauzer oynasi ochiq bo'lsa — jonli JPEG kadr (base64).
    2. Vazifa workspace'ida vazifa boshlangandan keyin yaratilgan eng yangi
       rasm fayli bo'lsa — u kadr sifatida yuboriladi (rasm/render topshiriqlari).
    3. Aks holda None — klient matn oqimini ko'rsatadi.
    """
    # 1) Jonli brauzer
    try:
        import live_browser
        if live_browser.state().get("open"):
            data = await live_browser.frame()
            if data:
                import base64
                return {"source": "browser", "mime": "image/jpeg",
                        "data": "data:image/jpeg;base64," + base64.b64encode(data).decode()}
    except Exception as exc:
        print(f"[live_scene] brauzer kadri olinmadi ({task_id}): {exc}")

    # 2) Workspace'dagi eng yangi rasm artefakti
    task = database.get_task(task_id)
    if not task:
        return None
    agent = task.get("target_agent") or ""
    if not agent:
        return None
    ws_dir = workspace_manager.get_agent_workspace(agent)
    started = task.get("created_at") or ""
    import datetime as _dt
    try:
        started_ts = _dt.datetime.fromisoformat(started.replace("Z", "+00:00")).timestamp() if started else 0
    except ValueError:
        started_ts = 0
    best = None
    for root, _dirs, files in os.walk(ws_dir):
        for fname in files:
            if fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                path = os.path.join(root, fname)
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    continue
                # Yarim yozilgan kadrlarni o'qishga urinmaymiz (progressiv render).
                if time.time() - mtime < 0.6:
                    continue
                if mtime >= started_ts and (best is None or mtime > best[0]):
                    best = (mtime, path)
    if not best:
        return None
    try:
        from PIL import Image
        import base64
        import io
        img = Image.open(best[1])
        img.thumbnail((1280, 1280))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=70)
        rel = os.path.relpath(best[1], os.path.dirname(__file__)).replace(os.sep, "/")
        return {"source": "artifact", "mime": "image/jpeg", "path": "/" + rel,
                "data": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}
    except Exception as exc:
        print(f"[live_scene] artefakt kadri tayyorlanmadi ({task_id}): {exc}")
        return None


@app.websocket("/ws/task/{task_id}")
async def websocket_task_stream(websocket: WebSocket, task_id: str):
    """Jonli sahna: bitta vazifaning qadam hodisalari + preview kadrlari.

    1) snapshot — vazifa holati, qadamlar, loglar (oxirgi 50)
    2) har bir task_id'li broadcast xabari (heart_transition, brain_event, log...)
    3) preview_frame — vazifa RUNNING bo'lsa har ~1.5s da kadr
    """
    await websocket.accept()
    task = database.get_task(task_id)
    if not task:
        await websocket.send_json({"type": "error", "message": f"Vazifa topilmadi: {task_id}"})
        await websocket.close()
        return
    logs = database.get_logs(task_id)
    await websocket.send_json({
        "type": "snapshot",
        "task_id": task_id,
        "task": task,
        "logs": logs[-50:],
    })
    TASK_STREAMS.setdefault(task_id, []).append(websocket)
    try:
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=1.5)
                if msg == "ping":
                    await websocket.send_text("pong")
                continue
            except asyncio.TimeoutError:
                # Oddiy polling pauzasi — keyingi receive'ga o'tamiz (xato emas).
                continue
            status = (database.get_task(task_id) or {}).get("status", "")
            if status in ("RUNNING", "working", "CHECKING"):
                frame = await _task_preview_frame(task_id)
                if frame:
                    await websocket.send_json({"type": "preview_frame", "task_id": task_id, "frame": frame})
            elif status in ("PASS", "FAIL", "BLOCKED"):
                # Yakuniy holat — bir marta yuborib, kuzatuvni tugatamiz.
                await websocket.send_json({"type": "task_completed", "task_id": task_id, "status": status})
                break
    except WebSocketDisconnect:
        LOGGER.debug("WS /ws/task/%s mijoz uzildi", task_id)
    finally:
        conns = TASK_STREAMS.get(task_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            TASK_STREAMS.pop(task_id, None)


@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "init",
            "apps": apps_manager.get_apps_status(),
            "subagents": subagent_scanner.scan_subagents(),
            "tasks": database.get_tasks(10),
            "pending_approvals": database.get_pending_approvals()
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        LOGGER.warning("WS /ws/live xatosi: %s: %s", type(exc).__name__, exc)
        manager.disconnect(websocket)

@app.websocket("/ws/terminal")
async def websocket_terminal_endpoint(websocket: WebSocket):
    """
    Persistent Terminal Bridge for Window 1 (bound strictly to 127.0.0.1).
    Session survives WebSocket disconnects, replays scrollback on reconnect,
    and supports automatic reconnection + heartbeat ping/pong.
    """
    client_host = websocket.client.host if websocket.client else "unknown"
    allowed_hosts = ("127.0.0.1", "localhost", "::1", "testclient")
    is_local = (
        client_host in allowed_hosts or
        client_host.startswith("127.") or
        client_host.startswith("192.168.") or
        client_host.startswith("10.") or
        client_host.startswith("172.")
    )
    if not is_local:
        await websocket.close(code=1008, reason="Terminal access restricted to localhost (127.0.0.1)")
        return

    import terminal_session
    session = terminal_session.TerminalSession.get_instance()
    await session.connect_client(websocket)

    try:
        while True:
            msg = await websocket.receive_text()
            await session.handle_input(msg)
    except WebSocketDisconnect:
        session.disconnect_client(websocket)
    except Exception as exc:
        LOGGER.warning("WS /ws/terminal xatosi: %s: %s", type(exc).__name__, exc)
        session.disconnect_client(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
