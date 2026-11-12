"""
Conduit Yurak Qatlami (engine/heart.py) — AI EMAS!

Oddiy, ishonchli va qat'iy holat mashinasi:
1. Holat mashinasi: PLANNED -> RUNNING -> CHECKING -> PASS / FAIL / BLOCKED
2. Har bir holat o'tishi SQLite `events` jadvaliga yoziladi.
3. Navbat (Queue): vazifalar ketma-ketligi, joriy vazifa ko'rsatkichi.
4. Cheklovlar: har subagentga max 8 qadam, har vazifaga max 3 aylanish.
   Chegara buzilsa darhol BLOCKED.
5. Checkpoint: har muvaffaqiyatli qadamda holat saqlanadi, "rollback_to_checkpoint" mavjud.
6. Protokol nazorati: Buyruq va hisobotlar `protocol.py` (Pydantic) orqali tekshiriladi.
   Mavjud bo'lmagan yoki faol bo'lmagan subagentga buyruq berilsa darhol rad etiladi.
   Dalilsiz PASS qat'iyan rad etiladi.
"""

import os
import sys
import asyncio
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database
import memory_manager
from engine.protocol import Command, Report, validate_command, validate_report

# Ruxsat etilgan holatlar
VALID_STATES = ["PLANNED", "RUNNING", "CHECKING", "PASS", "FAIL", "BLOCKED"]

# Checkpoint ombori {task_id: [snapshots]}
CHECKPOINTS: Dict[str, List[Dict[str, Any]]] = {}

# Navbat va parallel boshqaruv
TASK_QUEUE: List[str] = []
CURRENT_TASK_ID: Optional[str] = None
WORKSPACE_LOCKS: Dict[str, asyncio.Lock] = {}
ACTIVE_HEART_INSTANCES: Dict[str, 'HeartStateMachine'] = {}
PARALLEL_SEMAPHORE: Optional[asyncio.Semaphore] = None

def get_workspace_lock(subagent: str) -> asyncio.Lock:
    """Bitta workspace'da bir vaqtda faqat bitta vazifa bajarilishini ta'minlaydi."""
    sub = subagent.lower().strip()
    if sub not in WORKSPACE_LOCKS:
        WORKSPACE_LOCKS[sub] = asyncio.Lock()
    return WORKSPACE_LOCKS[sub]

def get_parallel_semaphore() -> asyncio.Semaphore:
    """Tizim bo'yicha bir vaqtda eng ko'pi N vazifa parallel bajarilishini ta'minlaydi."""
    global PARALLEL_SEMAPHORE
    if PARALLEL_SEMAPHORE is None:
        try:
            from engine.cli_runner import load_engine_config
            cfg = load_engine_config()
            limit = int(cfg.get("max_parallel_tasks", 3))
        except Exception:
            limit = 3
        PARALLEL_SEMAPHORE = asyncio.Semaphore(limit)
    return PARALLEL_SEMAPHORE

def get_active_parallel_tasks() -> List[Dict[str, Any]]:
    """Hozirda parallel ishlayotgan barcha vazifalar holatini qaytaradi."""
    result = []
    for tid, instance in list(ACTIVE_HEART_INSTANCES.items()):
        result.append({
            "task_id": tid,
            "goal": instance.goal,
            "active_subagent": instance.active_subagent,
            "current_state": instance.current_state,
            "step": instance.step_count,
            "loop": instance.loop_count,
        })
    return result

def get_active_subagents() -> set:
    try:
        from subagent_scanner import scan_subagents
        active = {s["id"].lower() for s in scan_subagents() if s.get("status") == "active"}
        return active if active else {"scout", "inspector"}
    except Exception:
        return {"scout", "inspector"}

ACTIVE_SUBAGENTS = {"scout", "inspector", "designer"}

class HeartStateMachine:
    def __init__(self, task_id: str, goal: str, ws_broadcast: Optional[Callable] = None):
        self.task_id = task_id
        self.goal = goal
        self.ws_broadcast = ws_broadcast
        self.current_state = "PLANNED"
        self.step_count = 0
        self.loop_count = 1
        self.max_steps_per_agent = 8
        self.max_loops = 3
        self.active_subagent: Optional[str] = None
        self.active_command: Optional[Command] = None
        self.last_report: Optional[Report] = None
        self.blocked_reason: Optional[str] = None
        ACTIVE_HEART_INSTANCES[task_id] = self

    async def transition(self, new_state: str, agent: str = "heart", reason: str = "") -> bool:
        """Holat o'tishini amalga oshiradi va SQLite events jadvaliga yozadi."""
        if new_state not in VALID_STATES:
            err = f"Noma'lum holat: {new_state}"
            database.add_log(self.task_id, "Heart", "ERROR", err)
            return False

        old_state = self.current_state
        self.current_state = new_state
        now = datetime.now().isoformat()

        # SQLite events jadvaliga yozish
        database.log_event(
            task_id=self.task_id,
            direction="state_transition",
            from_agent=agent,
            to_agent="heart",
            payload={
                "old_state": old_state,
                "new_state": new_state,
                "step": self.step_count,
                "loop": self.loop_count,
                "reason": reason
            },
            status=new_state
        )

        database.add_log(
            self.task_id,
            "Heart",
            "INFO",
            f"Holat o'tishi: {old_state} -> {new_state} [Aylanish: {self.loop_count}/3, Qadam: {self.step_count}/8] {reason}"
        )

        # Dashboardga uzatish
        if self.ws_broadcast:
            await self.ws_broadcast({
                "type": "heart_transition",
                "task_id": self.task_id,
                "data": {
                    "old_state": old_state,
                    "new_state": new_state,
                    "step": self.step_count,
                    "loop": self.loop_count,
                    "active_subagent": self.active_subagent,
                    "reason": reason,
                    "timestamp": now
                }
            })

        if new_state in ("PASS", "FAIL", "BLOCKED"):
            ACTIVE_HEART_INSTANCES.pop(self.task_id, None)

        return True

    def create_checkpoint(self, step_name: str, payload: Dict[str, Any]):
        """Muvaffaqiyatli qadam holatini xotirada saqlaydi."""
        if self.task_id not in CHECKPOINTS:
            CHECKPOINTS[self.task_id] = []

        snapshot = {
            "checkpoint_id": f"chk_{len(CHECKPOINTS[self.task_id]) + 1}",
            "step_name": step_name,
            "state": self.current_state,
            "step_count": self.step_count,
            "loop_count": self.loop_count,
            "active_subagent": self.active_subagent,
            "payload": payload,
            "timestamp": datetime.now().isoformat()
        }
        CHECKPOINTS[self.task_id].append(snapshot)
        database.add_log(self.task_id, "Heart", "INFO", f"Checkpoint yaratildi: {step_name} (#{snapshot['checkpoint_id']})")

    def rollback_to_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Oxirgi yaxshi checkpoint holatiga qaytaradi."""
        chks = CHECKPOINTS.get(self.task_id, [])
        if not chks:
            database.add_log(self.task_id, "Heart", "WARNING", "Qaytish uchun hech qanday checkpoint topilmadi.")
            return None

        last_good = chks[-1]
        self.current_state = last_good["state"]
        self.step_count = last_good["step_count"]
        self.active_subagent = last_good["active_subagent"]
        database.add_log(self.task_id, "Heart", "WARNING", f"Checkpointga qaytildi: {last_good['checkpoint_id']} ({last_good['step_name']})")
        return last_good

    async def verify_and_dispatch_command(self, raw_cmd: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Command]]:
        """
        Yurak buyruqni tekshiradi:
        1. Format to'g'rimi (protocol.py Command)?
        2. Subagent mavjudmi va faolmi?
        3. Cheklovlar buzilmaganmi?
        """
        cmd, err = validate_command(raw_cmd)
        if err or not cmd:
            database.add_log(self.task_id, "Heart", "ERROR", f"Qoidabuzarlik: Buyruq formati xato! {err}")
            return False, err, None

        sub = cmd.to.lower().strip()
        
        # Subagent mavjudligi va faolligi
        active_pool = get_active_subagents()
        if sub not in active_pool:
            err = f"Rad etildi: Subagent '{sub}' mavjud emas yoki hozirda faol emas (faqat: {list(active_pool)})"
            database.add_log(self.task_id, "Heart", "ERROR", err)
            memory_manager.append_error(self.task_id, err, "Nofaol subagentga murojaat")
            return False, err, None

        # Cheklovlar: max 8 qadam
        if self.step_count >= self.max_steps_per_agent:
            self.blocked_reason = f"Subagent {sub} uchun maksimal 8 qadam cheklovi oshib ketdi."
            await self.transition("BLOCKED", reason=self.blocked_reason)
            return False, self.blocked_reason, None

        # Cheklovlar: max 3 aylanish
        if self.loop_count > self.max_loops:
            self.blocked_reason = f"Vazifa uchun maksimal 3 aylanish cheklovi oshib ketdi."
            await self.transition("BLOCKED", reason=self.blocked_reason)
            return False, self.blocked_reason, None

        self.step_count += 1
        self.active_subagent = sub
        self.active_command = cmd

        # Holat RUNNING ga o'tadi
        await self.transition("RUNNING", agent="heart", reason=f"Buyruq {sub} agentiga yuborildi: {cmd.task[:60]}")

        # Protokol hodisasini SQLite'ga yozish
        database.log_event(
            task_id=self.task_id,
            direction="command",
            from_agent="brain",
            to_agent=sub,
            payload=cmd.model_dump(),
            status="dispatched"
        )

        if self.ws_broadcast:
            await self.ws_broadcast({
                "type": "brain_event",
                "task_id": self.task_id,
                "event": {
                    "direction": "command",
                    "from_agent": "brain",
                    "to_agent": sub,
                    "payload": cmd.model_dump(),
                    "status": "dispatched",
                    "timestamp": datetime.now().isoformat()
                }
            })

        return True, None, cmd

    async def verify_and_accept_report(self, raw_report: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Report]]:
        """
        Yurak subagent hisobotini tekshiradi:
        1. Format to'g'rimi (protocol.py Report)?
        2. Dalilsiz PASS qat'iyan rad etiladi.
        """
        await self.transition("CHECKING", agent="heart", reason="Subagent hisoboti tekshirilmoqda")

        rep, err = validate_report(raw_report)
        if err or not rep:
            database.add_log(self.task_id, "Heart", "ERROR", f"Qoidabuzarlik: Hisobot rad etildi! {err}")
            memory_manager.append_error(self.task_id, err, "Yaroqsiz hisobot yoki dalil yo'qligi")
            return False, err, None

        self.last_report = rep

        # Protokol hisobotini SQLite'ga yozish
        database.log_event(
            task_id=self.task_id,
            direction="report",
            from_agent=rep.from_agent,
            to_agent="heart",
            payload=rep.model_dump(),
            status=rep.status
        )

        if self.ws_broadcast:
            await self.ws_broadcast({
                "type": "brain_event",
                "task_id": self.task_id,
                "event": {
                    "direction": "report",
                    "from_agent": rep.from_agent,
                    "to_agent": "heart",
                    "payload": rep.dict(),
                    "status": rep.status,
                    "timestamp": datetime.now().isoformat()
                }
            })

        if rep.status == "PASS":
            # Checkpoint yaratish
            self.create_checkpoint(step_name=f"{rep.from_agent}_completed", payload=rep.dict())
            memory_manager.append_decision(self.task_id, f"{rep.from_agent} vazifani muvaffaqiyatli bajardi (PASS): {rep.evidence[:80]}")
        else:
            memory_manager.append_error(self.task_id, f"{rep.from_agent} FAIL: {rep.notes}")

        return True, None, rep

# Global navbat boshqaruvi
def enqueue_task(task_id: str):
    global TASK_QUEUE
    if task_id not in TASK_QUEUE:
        TASK_QUEUE.append(task_id)

def get_queue_status() -> Dict[str, Any]:
    global CURRENT_TASK_ID, TASK_QUEUE
    return {
        "current_task_id": CURRENT_TASK_ID,
        "queue": TASK_QUEUE,
        "total_queued": len(TASK_QUEUE)
    }

def finish_task_in_queue(task_id: str):
    global CURRENT_TASK_ID, TASK_QUEUE
    if task_id in TASK_QUEUE:
        TASK_QUEUE.remove(task_id)
    if CURRENT_TASK_ID == task_id:
        CURRENT_TASK_ID = TASK_QUEUE[0] if TASK_QUEUE else None
