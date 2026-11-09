import os
import sys
import json
import asyncio
import uuid
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

import database
import subagent_scanner
import security_guard
import scout_executor
import inspector_executor
from providers.base import MCPAgentProvider

# Initialize database
database.init_db()

# Global default MCP provider
mcp_provider = MCPAgentProvider(agent_name="Antigravity Sovereign Agent")

def list_subagents() -> List[Dict[str, Any]]:
    """
    Conduit subagentlar ro'yxati va ularning joriy holatini qaytaradi.
    """
    subagents = subagent_scanner.scan_subagents()
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "target_app": s["target_app"],
            "status": s["status"],
            "role_summary": s.get("role_summary", ""),
            "allowed_tools": list(security_guard.get_allowed_tools(s["id"]))
        }
        for s in subagents
    ]

def get_subagent_role(name: str) -> Dict[str, Any]:
    """
    Ko'rsatilgan subagentning role.md instruksiyasi va ruxsat berilgan toollarini qaytaradi.
    """
    clean_name = name.strip().lower()
    role_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "subagents", clean_name, "role.md"))
    
    if not os.path.exists(role_path):
        return {
            "error": f"Subagent '{clean_name}' topilmadi.",
            "subagent": clean_name,
            "allowed_tools": []
        }

    with open(role_path, "r", encoding="utf-8") as f:
        role_content = f.read()

    allowed = list(security_guard.get_allowed_tools(clean_name))

    return {
        "subagent": clean_name,
        "role_md": role_content,
        "allowed_tools": allowed
    }

async def execute_mcp_task(task_id: str, subagent: str, prompt: str):
    """Subagent vazifasini ishga tushirish va WebSocket orqali efirga uzatish."""
    try:
        # Import main manager to broadcast over active WebSockets
        import main
        broadcast_func = main.manager.broadcast
    except Exception:
        broadcast_func = None

    if subagent == "scout":
        await scout_executor.run_scout_task(task_id, prompt, ws_broadcast=broadcast_func)
    elif subagent == "inspector":
        await inspector_executor.run_inspector_task(task_id, prompt, ws_broadcast=broadcast_func)
    else:
        database.add_log(task_id, subagent, "INFO", f"Subagent '{subagent}' hozirda 'keyinroq' holatida.")
        database.update_task_step(task_id, "planner", "needs approval", 
                                 output=f"'{subagent}' subagenti Faza 4 doirasida ulanadi.", 
                                 evidence="Holat: Keyinroq")

def run_task(subagent: str, task: str) -> Dict[str, Any]:
    """
    Vazifani ko'rsatilgan subagentga (masalan: scout, inspector) topshiradi.
    Yangi task_id yaratadi va dashboard jonli yangilanishi uchun fon rejimida ishga tushiradi.
    """
    clean_agent = subagent.strip().lower()
    prompt = task.strip()
    task_id = f"task_{uuid.uuid4().hex[:8]}"

    # Save to SQLite
    db_task = database.create_task(task_id, prompt[:60], prompt, clean_agent)
    database.add_log(task_id, "MCP_Server", "INFO", f"MCP mijozidan vazifa qabul qilindi -> Ijrochi: {clean_agent}")

    # Asinxron fonda ishga tushirish
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(execute_mcp_task(task_id, clean_agent, prompt))
    except RuntimeError:
        # Agar running loop bo'lmasa (masalan yangi potokda chaqirilsa)
        asyncio.run(execute_mcp_task(task_id, clean_agent, prompt))

    return {
        "task_id": task_id,
        "status": "working",
        "subagent": clean_agent,
        "prompt": prompt,
        "created_at": db_task.get("created_at")
    }

def get_task(task_id: str) -> Dict[str, Any]:
    """
    Vazifaning joriy holati, qadamlari, skrinshot yo'li, loglari va PASS/FAIL xulosasini qaytaradi.
    """
    task = database.get_task(task_id)
    if not task:
        return {"error": f"Vazifa topilmadi: {task_id}"}
    
    logs = database.get_logs(task_id)
    return {
        "task_id": task.get("task_id"),
        "title": task.get("title"),
        "subagent": task.get("target_agent"),
        "status": task.get("status"),
        "current_step": task.get("current_step"),
        "steps": {
            "planner": task.get("planner_output"),
            "doer": task.get("doer_output"),
            "checker": task.get("checker_output"),
        },
        "screenshot_url": task.get("screenshot_url"),
        "evidence": task.get("evidence"),
        "logs": logs
    }

# ==================== MCP 2.x SERVER DEFINITION ====================
from mcp.server.fastmcp import FastMCP as MCPServer

mcp = MCPServer("conduit-mcp-server")

@mcp.tool()
def mcp_list_subagents() -> str:
    """Subagentlar ro'yxati va ularning holatini qaytaradi."""
    return json.dumps(list_subagents(), indent=2)

@mcp.tool()
def mcp_run_task(subagent: str, task: str) -> str:
    """Vazifani subagentga topshirish va task_id olish."""
    res = run_task(subagent, task)
    return json.dumps(res, indent=2)

@mcp.tool()
def mcp_get_task(task_id: str) -> str:
    """Vazifaning to'liq holati, qadamlari, skrinshot yo'li va natijasini olish."""
    res = get_task(task_id)
    return json.dumps(res, indent=2)

@mcp.tool()
def mcp_get_subagent_role(name: str) -> str:
    """Subagentning role.md va ruxsat berilgan toollarini olish."""
    res = get_subagent_role(name)
    return json.dumps(res, indent=2)

if __name__ == "__main__":
    # Standard MCP server runner via stdio
    mcp.run()
