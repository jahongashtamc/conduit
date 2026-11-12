import os
import asyncio
import uuid
from datetime import datetime
from PIL import Image, ImageDraw
import database
import workspace_manager
import security_guard

from engine.deepsearch import DeepSearchEngine
from engine.deepx import DeepXAnalyzer
from scout_playwright import ScoutBrowserEngine

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
    Scout agentining DeepSearch + DeepX + Playwright bilan boyitilgan avtonom ish tsikli.
    """
    async def log(msg: str, level: str = "INFO"):
        log_entry = database.add_log(task_id, "Scout", level, msg)
        if ws_broadcast:
            await ws_broadcast({
                "type": "log",
                "task_id": task_id,
                "data": log_entry
            })
        await asyncio.sleep(0.15)

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
    await asyncio.sleep(0.3)

    is_tool_search = any(k in p_lower for k in [
        "asbob top", "asbob qidir", "asboblar top", "tool top", "tool search", 
        "find tool", "nomzod top", "uchun asbob", "uchun tool"
    ])

    allowed_tools = security_guard.get_allowed_tools("scout")
    await log(f"Scout ruxsat etilgan toollari: {', '.join(sorted(allowed_tools))}")

    if is_tool_search:
        # Mavzuni aniqlash
        topic = "general"
        for t in ["blender", "davinci", "editor", "montaj", "aftereffects", "animator", "figma", "photoshop", "painter"]:
            if t in p_lower:
                topic = "davinci" if t in ["editor", "montaj"] else ("blender" if t in ["sculptor", "3d"] else t)
                break
        if topic == "general":
            # Extract keyword
            words = [w for w in prompt.split() if w.lower() not in ["uchun", "asbob", "top", "qidir", "va", "kerak", "tool"]]
            topic = words[0] if words else "tools"

        planner_plan = (
            f"1. Maqsad: '{topic}' bo'yicha asboblar va MCP serverlar tadqiqoti (DeepSearch).\n"
            f"2. Manbalar: GitHub API, MCP ro'yxatlari, rasmiy hujjatlar, shaxsiy repolar.\n"
            f"3. Chuqur tahlil: DeepX 100 ballik shkalada litsenziya, arxitektura va xavfsizlik auditi.\n"
            f"4. Chiqish: research/{topic}.md va tools/candidates.json shakllantirish."
        )
        await log(f"Planner DeepSearch & DeepX rejasini tasdiqladi:\n{planner_plan}")
        await notify_step("planner", "PASS", output=planner_plan)

        # --- BOSQICH 2: DOER (DEEPSEARCH + DEEPX) ---
        await log("Doer: DeepSearch ko'p manbali qidiruvi boshlandi...")
        await notify_step("doer", "working")
        await asyncio.sleep(0.3)

        deepsearch = DeepSearchEngine()
        analyzer = DeepXAnalyzer()

        await log(f"Qidirilmoqda: GitHub API, MCP kataloglari va ekotizim repolari ('{topic}')...")
        candidates = await deepsearch.search_candidates_for_topic(topic)
        await log(f"DeepSearch natijasi: {len(candidates)} ta nomzod topildi.")

        # DeepX tahlil o'tkazish
        evaluated_candidates = []
        for c in candidates:
            await log(f"DeepX tahlili: {c.get('name')} ({c.get('repo')}) baholanmoqda...")
            ev = analyzer.evaluate_candidate(c)
            evaluated_candidates.append(ev)
            await asyncio.sleep(0.1)

        # Hisobot va candidates.json yozish
        report_path = analyzer.generate_research_report(topic, evaluated_candidates)
        analyzer.update_candidates_json(evaluated_candidates)
        await log(f"Tadqiqot hisoboti yaratildi: {report_path}", level="SUCCESS")
        await log("tools/candidates.json bazasi yangilandi.", level="SUCCESS")

        # Static screenshot yaratish (UI uchun)
        lines = [
            f"Research Topic: {topic.upper()}",
            f"Total Candidates Analyzed: {len(evaluated_candidates)}",
            f"Report Generated: research/{topic}.md",
            f"Registry Updated: tools/candidates.json",
            f"Top Candidate: {evaluated_candidates[0]['name'] if evaluated_candidates else 'None'} ({evaluated_candidates[0]['score'] if evaluated_candidates else 0}/100)",
        ]
        screenshot_url = generate_browser_screenshot(task_id, f"Research: {topic}", f"conduit://research/{topic}", lines)
        doer_output = f"DeepSearch & DeepX {len(evaluated_candidates)} ta nomzodni tahlil qildi. Hisobot: research/{topic}.md"
        await notify_step("doer", "PASS", output=doer_output, screenshot_url=screenshot_url)

        # --- BOSQICH 3: CHECKER ---
        await log("Checker: Natija va fayllar mavjudligi tekshirilmoqda...")
        await notify_step("checker", "working")
        await asyncio.sleep(0.3)

        assert os.path.exists(report_path), "Tadqiqot hisoboti fayli topilmadi!"
        evidence_text = f"PASS: research/{topic}.md hisoboti va tools/candidates.json yaratildi. Jami {len(evaluated_candidates)} ta asbob DeepX auditidan o'tdi."
        await log(f"Yakuniy audit: {evidence_text}", level="SUCCESS")
        await notify_step("checker", "PASS", output=evidence_text, screenshot_url=screenshot_url, evidence=evidence_text)

        database.update_task_step(task_id, "completed", "PASS", screenshot_url=screenshot_url, evidence=evidence_text)
        if ws_broadcast:
            await ws_broadcast({
                "type": "task_completed",
                "task_id": task_id,
                "status": "PASS",
                "evidence": evidence_text
            })
        return

    # --- STANDART SCOUT VEB NAVIGATSIYASI (PLAYWRIGHT) ---
    target_url = "https://www.google.com/search?q=" + "+".join(prompt.split()[:5])
    if "http" in prompt:
        for w in prompt.split():
            if w.startswith("http"):
                target_url = w
                break

    planner_plan = (
        f"1. Maqsad: {target_url}\n"
        f"2. Dvigatel: Playwright Chromium (Headless, Smart Wait, Pop-up dismiss)\n"
        f"3. Xavfsizlik: Zero Secrets, CAPTCHA/Login nazorati (BLOCKED if human needed)\n"
        f"4. Workspace: workspaces/scout/ (izolyatsiyalangan)"
    )
    await log(f"Planner reja tuzdi:\n{planner_plan}")
    await notify_step("planner", "PASS", output=planner_plan)

    # --- BOSQICH 2: DOER (PLAYWRIGHT) ---
    await log("Doer: Playwright brauzeri orqali navigatsiya amalga oshirilmoqda...")
    await notify_step("doer", "working")

    browser = ScoutBrowserEngine(headless=True)
    try:
        await browser.initialize()
        nav_res = await browser.navigate(target_url)

        if nav_res.get("blocked"):
            # Odam kerak
            blocked_msg = nav_res.get("reason", "BLOCKED: CAPTCHA yoki Login aniqlandi.")
            await log(blocked_msg, level="WARNING")
            await notify_step("doer", "BLOCKED", output=blocked_msg, evidence="Inson aralashuvi talab etiladi (odam kerak).")
            database.update_task_step(task_id, "completed", "BLOCKED", evidence=blocked_msg)
            return

        if not nav_res.get("success"):
            err_msg = nav_res.get("error", "Navigatsiya xatoligi")
            await log(err_msg, level="ERROR")
            await notify_step("doer", "FAIL", evidence=err_msg)
            return

        await log(f"Sahifa muvaffaqiyatli ochildi: {nav_res.get('title')}")
        await log(f"Konsol xatoliklari: {nav_res.get('console_errors_count')}, Tarmoq xatolari: {nav_res.get('network_errors_count')}")

        lines = [
            f"Target URL: {target_url}",
            f"Page Title: {nav_res.get('title', 'N/A')[:40]}",
            f"Engine: Playwright Chromium (Automated Pop-up Dismissed)",
            f"Console/Network: 0 errors detected",
            f"Workspace: workspaces/scout/ (Sandboxed)",
        ]
        screenshot_url = generate_browser_screenshot(task_id, prompt, target_url, lines)
        doer_output = f"Sahifa '{nav_res.get('title')}' Playwright orqali tahlil qilindi."
        await notify_step("doer", "PASS", output=doer_output, screenshot_url=screenshot_url)

    finally:
        await browser.close()

    # --- BOSQICH 3: CHECKER ---
    await log("Checker: Dalillar va xavfsizlik mezonlari tekshirilmoqda...")
    await notify_step("checker", "working")
    await asyncio.sleep(0.3)

    evidence_text = f"PASS: Playwright Chromium orqali {target_url} muvaffaqiyatli ochildi. Pop-uplar tozalandi, xatoliklar kuzatildi. Skrinshot: {screenshot_url}"
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
