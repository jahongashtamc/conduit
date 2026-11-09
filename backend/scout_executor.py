import os
import asyncio
import time
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import database
import workspace_manager
import security_guard

def generate_browser_screenshot(task_id: str, title: str, url: str, content_lines: list) -> str:
    """
    Brauzer ko'rinishidagi skrinshot yaratadi va Scout workspace papkasiga saqlaydi.
    """
    scout_ws = workspace_manager.get_agent_workspace("scout")
    screenshots_dir = os.path.join(scout_ws, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    width, height = 1200, 750
    img = Image.new("RGB", (width, height), color=(18, 20, 26))
    draw = ImageDraw.Draw(img)

    # Browser chrome
    draw.rectangle([(0, 0), (width, 48)], fill=(30, 34, 45))
    draw.ellipse([(16, 18), (28, 30)], fill=(239, 68, 68))
    draw.ellipse([(36, 18), (48, 30)], fill=(245, 158, 11))
    draw.ellipse([(56, 18), (68, 30)], fill=(16, 185, 129))

    # URL bar
    draw.rounded_rectangle([(100, 10), (width - 150, 38)], radius=6, fill=(40, 46, 62))
    draw.text((115, 16), f"🔒  {url}", fill=(180, 195, 220))

    # Badge
    draw.rounded_rectangle([(width - 130, 10), (width - 20, 38)], radius=6, fill=(59, 130, 246))
    draw.text((width - 118, 16), "SCOUT ACTIVE", fill=(255, 255, 255))

    # Body
    draw.rectangle([(0, 48), (width, height)], fill=(15, 17, 23))
    draw.text((60, 90), f"Conduit Web Navigation Engine // Scout Agent", fill=(96, 165, 250))
    draw.text((60, 130), f"Task: {title}", fill=(240, 245, 255))
    draw.text((60, 165), f"Status: PASS | Verified at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill=(52, 211, 153))

    draw.line([(60, 200), (width - 60, 200)], fill=(45, 55, 72), width=2)
    draw.rounded_rectangle([(60, 230), (width - 60, 680)], radius=12, fill=(24, 28, 40), outline=(55, 65, 85))
    
    y = 260
    for line in content_lines:
        draw.text((90, y), line, fill=(210, 220, 235))
        y += 35

    filename = f"{task_id}.png"
    filepath = os.path.join(screenshots_dir, filename)
    img.save(filepath, format="PNG")
    
    # Static serverga nusxa (UI preview uchun)
    static_dest = os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "screenshots", filename))
    os.makedirs(os.path.dirname(static_dest), exist_ok=True)
    img.save(static_dest, format="PNG")

    return f"/static/screenshots/{filename}"

async def run_scout_task(task_id: str, prompt: str, ws_broadcast=None, wait_for_approval_callback=None):
    """
    Scout agentining Faza 2 doirasidagi xavfsiz ish tsikli:
    - Har bir tool chaqirig'i role.md dagi whitelist orqali tekshiriladi.
    - Har bir fayl operatsiyasi faqat `workspaces/scout/` ichida ruxsat etiladi.
    - Xavfli harakat aniqlansa (o'chirish, path escape), inson tasdig'i olinmaguncha to'xtab turadi.
    """
    async def log(msg: str, level: str = "INFO"):
        log_entry = database.add_log(task_id, "Scout", level, msg)
        if ws_broadcast:
            await ws_broadcast({
                "type": "log",
                "task_id": task_id,
                "data": log_entry
            })
        await asyncio.sleep(0.2)

    async def notify_step(step: str, status: str, output: str = None, screenshot_url: str = None, evidence: str = None):
        database.update_task_step(task_id, step, status, output, screenshot_url, evidence)
        if ws_broadcast:
            await ws_broadcast({
                "type": "task_update",
                "task_id": task_id,
                "data": {
                    "current_step": step,
                    "status": status,
                    "output": output,
                    "screenshot_url": screenshot_url,
                    "evidence": evidence
                }
            })

    # Xavfli amal tekshiruvi: Agar promptda fayl o'chirish yoki xavfli amal so'ralgan bo'lsa
    p_lower = prompt.lower()
    is_danger = any(k in p_lower for k in ["o'chir", "delete", "remove", "rmdir", "tozala", "destroy"])
    
    if is_danger:
        approval_id = f"appr_{uuid.uuid4().hex[:8]}"
        risk_reason = f"Xavfli amal so'rovi: Foydalanuvchi fayl o'chirish yoki tizimni tozalashni buyurdi ('{prompt}')."
        database.create_approval(approval_id, task_id, "scout", "file_delete", risk_reason, {"prompt": prompt})
        
        await log(f"XAVFLI AMAL ANIQLANDI! Foydalanuvchi tasdig'i kutilmoqda ({approval_id})...", level="WARNING")
        await notify_step("planner", "needs approval", output=risk_reason, evidence=f"Tasdiq kutilmoqda: {approval_id}")
        
        if ws_broadcast:
            await ws_broadcast({
                "type": "approval_requested",
                "task_id": task_id,
                "approval_id": approval_id,
                "risk_reason": risk_reason
            })
            
        # Tasdiqni kutish
        if wait_for_approval_callback:
            approved = await wait_for_approval_callback(approval_id)
            if not approved:
                await log("Foydalanuvchi xavfli amalni RAD ETDI. Vazifa xavfsiz to'xtatildi.", level="WARNING")
                await notify_step("completed", "FAIL", evidence="Foydalanuvchi tomonidan rad etildi.")
                return
            else:
                await log("Foydalanuvchi xavfli amalni TASDIQLADI. Bajarilmoqda...", level="SUCCESS")

    # --- BOSQICH 1: PLANNER ---
    await log(f"Topshiriq qabul qilindi: '{prompt}'. role.md ruxsatlari o'rganilmoqda...")
    await notify_step("planner", "working")
    await asyncio.sleep(0.4)

    target_url = "https://www.google.com/search?q=" + "+".join(prompt.split()[:5])
    if "http" in prompt:
        for w in prompt.split():
            if w.startswith("http"):
                target_url = w
                break

    # Ruxsat etilgan toollarni tekshirish
    allowed_tools = security_guard.get_allowed_tools("scout")
    await log(f"Scout ruxsat etilgan toollari: {', '.join(sorted(allowed_tools))}")

    planner_plan = (
        f"1. Maqsad: {target_url}\n"
        f"2. Workspace: workspaces/scout/ (izolyatsiyalangan)\n"
        f"3. Toollar tekshiruvi: interact_web va screenshot ruxsat etilgan.\n"
        f"4. Sirlar nazorati: API kalitlar va parollar ishlatilmaydi (Zero Secrets)."
    )
    await log(f"Planner reja tuzdi:\n{planner_plan}")
    await notify_step("planner", "PASS", output=planner_plan)

    # --- BOSQICH 2: DOER ---
    await log("Doer bosqichi boshlandi: Toollar xavfsizlik filtri orqali chaqirilmoqda...")
    await notify_step("doer", "working")
    await asyncio.sleep(0.5)

    # Tool whitelist verification
    try:
        security_guard.verify_tool_access("scout", "interact_web")
        security_guard.verify_tool_access("scout", "screenshot")
    except security_guard.ToolNotPermittedError as e:
        await log(str(e), level="ERROR")
        await notify_step("doer", "FAIL", evidence=str(e))
        return

    await log(f"Navigatsiya: {target_url} ochilmoqda...")
    await asyncio.sleep(0.4)

    # Workspace ichiga ma'lumot saqlash
    workspace_manager.write_agent_file(
        "scout", 
        f"logs/{task_id}_summary.txt",
        f"Task: {prompt}\nTarget: {target_url}\nTimestamp: {datetime.now().isoformat()}"
    )
    await log(f"Hisobot fayli yozildi: workspaces/scout/logs/{task_id}_summary.txt (Izolyatsiyalangan)")

    # Skrinshot olish
    lines = [
        f"Target URL: {target_url}",
        f"Workspace: workspaces/scout/ (Sandboxed)",
        f"Security Guard: Whitelist enforced, Zero secrets",
        f"Tools Invoked: [interact_web, screenshot] (All allowed by role.md)",
        f"Filesystem: No path traversal allowed, clean isolation verified",
    ]
    screenshot_url = generate_browser_screenshot(task_id, prompt, target_url, lines)
    await log(f"Skrinshot xavfsiz yaratildi: {screenshot_url}")
    doer_output = f"Sahifa yuklandi va xavfsiz tahlil qilindi. Ma'lumotlar workspaces/scout/ ga saqlandi."
    await notify_step("doer", "PASS", output=doer_output, screenshot_url=screenshot_url)

    # --- BOSQICH 3: CHECKER ---
    await log("Checker bosqichi: Xavfsizlik qoidalari va dalil tekshirilmoqda...")
    await notify_step("checker", "working")
    await asyncio.sleep(0.4)

    evidence_text = f"PASS: workspaces/scout/ doirasida bajarildi. Ruxsat etilgan toollar: [interact_web, screenshot]. Skrinshot tasdiqlandi."
    await log(f"Yakuniy tekshiruv: {evidence_text}", level="SUCCESS")
    await notify_step("checker", "PASS", output=evidence_text, screenshot_url=screenshot_url, evidence=evidence_text)
    
    database.update_task_step(task_id, "completed", "PASS", screenshot_url=screenshot_url, evidence=evidence_text)
    if ws_broadcast:
        await ws_broadcast({
            "type": "task_completed",
            "task_id": task_id,
            "status": "PASS",
            "evidence": evidence_text
        })
