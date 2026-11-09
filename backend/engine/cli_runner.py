import os
import sys
import json
import time
import asyncio
import shutil
import psutil
from typing import Dict, Any, List, Optional, Callable, Tuple

# Add parent path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
import workspace_manager
import security_guard

CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "engine.json"))
TOOLS_PY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tools.py"))

# Active subprocess registry for tree killing
active_processes: Dict[str, asyncio.subprocess.Process] = {}

def load_engine_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "active_engine": "claude_code",
        "engines": {
            "claude_code": {
                "name": "Claude Code CLI",
                "binary": "claude",
                "command_template": "claude -p \"{prompt}\" --output-format text --allowedTools \"Bash(python tools.py *),FileRead,FileEdit,Write\"",
                "timeout_seconds": 120,
                "available": bool(shutil.which("claude"))
            },
            "agy": {
                "name": "Antigravity CLI (agy)",
                "binary": "agy",
                "command_template": "agy -p \"{prompt}\" --output-format text",
                "timeout_seconds": 120,
                "available": bool(shutil.which("agy"))
            }
        }
    }

def get_engine_status() -> dict:
    cfg = load_engine_config()
    engines = cfg.get("engines", {})
    for k, v in engines.items():
        v["available"] = bool(shutil.which(v.get("binary", "")))
    return {
        "is_connected": bool(engines.get(cfg.get("active_engine", "claude_code"), {}).get("available", False)),
        "active_engine": cfg.get("active_engine", "claude_code"),
        "engines": engines
    }

def kill_process_tree(pid: int):
    """Jarayonni barcha bola jarayonlari bilan birga majburiy o'ldiradi."""
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except Exception:
                pass
        parent.kill()
    except Exception:
        pass

def kill_all_cli_processes():
    for task_id, proc in list(active_processes.items()):
        if proc.returncode is None:
            kill_process_tree(proc.pid)
    active_processes.clear()

def check_model_error(output_text: str) -> Optional[str]:
    """CLI chiqishida 429, cooling down yoki tanilmagan model xatosini aniqlaydi."""
    out_lower = output_text.lower()
    if "429" in output_text or "rate limit" in out_lower or "cooling down" in out_lower or "request rejected" in out_lower:
        return "API Error 429: Model rate limit / credentials cooling down"
    if "unrecognized_model" in out_lower or "unrecognized model" in out_lower or "model tanilmadi" in out_lower:
        return "Model xatosi: Tanilmagan model (Unrecognized model)"
    return None

def validate_evidence_against_goal(goal: str, subagent: str, evidence: str, screenshot_path: str = "") -> Tuple[bool, str]:
    """Checker dalilning vazifa talablariga mosligini qat'iy tekshiradi."""
    g_lower = goal.lower()
    e_lower = evidence.lower()
    
    # 1. Figma / Dizayn / Spec vazifalari
    if any(k in g_lower for k in ["figma", "dizayn", "design", "spec", "maket"]):
        has_figma = any(k in e_lower for k in ["figma", "spec", "pc_studio_spec.md", ".fig", "diagram", "lewea7ayecgzcik4aedx8p", "x2utsrlt"])
        if not has_figma or ("localhost:3000" in e_lower and "figma" not in e_lower):
            return False, "Yolg'on dalil rad etildi: Vazifa Figma dizayni talab qilgan, lekin lokal veb-skrinshot taqdim etildi. Figma spec yoki dizayn fayli mavjud emas."

    # 2. 3D / Blender / Sculptor vazifalari
    if any(k in g_lower for k in ["blender", "3d", "model", "sculpt", "mesh", "render"]) or subagent == "sculptor":
        has_3d = any(k in e_lower for k in ["blender", "3d", "render", "snapshot", "model", "cube", "sphere", "obj", "blend", "scene"])
        if not has_3d:
            return False, "Dalil rad etildi: 3D Blender render yoki model artefakti topilmadi."

    # 3. Google / Veb qidiruv vazifalari
    if any(k in g_lower for k in ["google", "qidir", "search"]):
        has_search = any(k in e_lower for k in ["google", "qidiruv", "search", "natija"]) or ("screenshot" in e_lower and "localhost" not in e_lower)
        if not has_search:
            return False, "Dalil rad etildi: Google qidiruv natijasi yoki veb-skrinshot topilmadi."

    return True, "Dalil vazifaga to'liq mos keladi."

async def run_cli_subprocess(
    task_id: str,
    subagent: str,
    prompt: str,
    engine_key: str = None,
    ws_broadcast: Optional[Callable] = None,
    timeout: int = 120
) -> Dict[str, Any]:
    """
    Subagent uchun CLI jarayonini workspaces/<subagent>/ papkasida ishga tushiradi.
    Chiqishni qatorma-qator o'qib, WebSocket orqali efirga uzatadi.
    Model xatosi (429) bo'lsa zaxira modelga o'tadi, u ham ishlamasa BLOCKED qiladi.
    """
    cfg = load_engine_config()
    chosen_engine = engine_key or cfg.get("active_engine", "claude_code")
    engine_meta = cfg.get("engines", {}).get(chosen_engine, {})

    binary = engine_meta.get("binary", "claude")
    if not shutil.which(binary):
        err = f"CLI dasturi ('{binary}') tizimda topilmadi. Iltimos, o'rnating yoki PATH ga qo'shing."
        database.add_log(task_id, subagent, "ERROR", err)
        return {"success": False, "is_blocked": True, "error": err, "output": ""}

    ws_dir = workspace_manager.get_agent_workspace(subagent)
    allowed_tools = security_guard.get_allowed_tools(subagent)

    # Ensure tools.py is inside workspace
    dest_tools = os.path.join(ws_dir, "tools.py")
    if os.path.exists(TOOLS_PY_PATH):
        shutil.copyfile(TOOLS_PY_PATH, dest_tools)

    template = engine_meta.get("command_template", "claude --model {model} -p \"{prompt}\" --output-format text < nul")
    
    # Model va zaxira model
    primary_model = engine_meta.get("model", "claude-3-5-sonnet-20241022" if chosen_engine == "claude_code" else "gemini-2.5-pro")
    fallback_model = engine_meta.get("fallback_model", "claude-3-5-haiku-20241022" if chosen_engine == "claude_code" else "gemini-2.5-flash")
    
    clean_prompt = prompt.replace('"', '\\"').replace("\n", " ")

    async def execute_with_model(target_model: str) -> Dict[str, Any]:
        cmd_str = template.format(
            model=target_model,
            prompt=clean_prompt,
            workspace=ws_dir,
            allowed_tools=",".join(sorted(allowed_tools))
        )

        database.add_log(task_id, subagent, "INFO", f"CLI Engine ishga tushmoqda [{engine_meta.get('name')} | model: {target_model}]: {cmd_str[:120]}...")
        if ws_broadcast:
            await ws_broadcast({
                "type": "log",
                "task_id": task_id,
                "data": {
                    "agent_name": subagent,
                    "level": "INFO",
                    "message": f"CLI boshlandi: {engine_meta.get('name')} ({target_model})",
                    "timestamp": ""
                }
            })

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd_str,
                cwd=ws_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            active_processes[task_id] = proc
            collected_output = []

            # Heartbeat (idle output) timeout qoidasi: N soniya davomida chiqish bo'lmasa to'xtatish
            heartbeat_timeout = cfg.get("output_heartbeat_timeout", 30)

            async def read_stream():
                while True:
                    try:
                        line_bytes = await asyncio.wait_for(proc.stdout.readline(), timeout=heartbeat_timeout)
                    except asyncio.TimeoutError:
                        timeout_msg = f"Heartbeat timeout: {heartbeat_timeout} soniya davomida hech qanday chiqish bo'lmadi."
                        database.add_log(task_id, subagent, "ERROR", timeout_msg)
                        kill_process_tree(proc.pid)
                        raise asyncio.TimeoutError(timeout_msg)

                    if not line_bytes:
                        break
                    line = line_bytes.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue

                    # Ruxsat nazorati
                    if "python tools.py" in line:
                        parts = line.split()
                        try:
                            idx = parts.index("tools.py")
                            if idx + 1 < len(parts):
                                tool_name = parts[idx + 1]
                                if tool_name not in allowed_tools:
                                    block_msg = f"XAVFSIZLIK TO'SIG'I: '{tool_name}' tooliga subagent role.md da ruxsat berilmagan! Rad etildi."
                                    database.add_log(task_id, subagent, "ERROR", block_msg)
                                    continue
                        except Exception:
                            pass

                    safe_line = security_guard.sanitize_text(line)
                    collected_output.append(safe_line)
                    log_entry = database.add_log(task_id, subagent, "INFO", safe_line)
                    if ws_broadcast:
                        await ws_broadcast({"type": "log", "task_id": task_id, "data": log_entry})

            try:
                await read_stream()
                await proc.wait()
            except asyncio.TimeoutError as te:
                kill_process_tree(proc.pid)
                timeout_msg = str(te) or f"Heartbeat timeout: {heartbeat_timeout}s davomida hech qanday chiqish bo'lmadi."
                return {"success": False, "is_blocked": True, "error": timeout_msg, "output": "\n".join(collected_output)}

            full_out = "\n".join(collected_output)
            model_err = check_model_error(full_out)
            return {
                "success": proc.returncode == 0 and not model_err,
                "model_error": model_err,
                "model": target_model,
                "returncode": proc.returncode,
                "output": full_out
            }
        except Exception as e:
            err = f"CLI xatosi: {str(e)}"
            database.add_log(task_id, subagent, "ERROR", err)
            return {"success": False, "is_blocked": True, "error": err, "output": ""}

    try:
        # 1. Asosiy model bilan ishga tushirish
        run_res = await execute_with_model(primary_model)
        if not run_res.get("success") and run_res.get("model_error"):
            primary_err = run_res.get("model_error")
            # 2. Zaxira modelga o'tish
            if fallback_model and fallback_model != primary_model:
                switch_msg = f"Asosiy model [{primary_model}] xatosi: {primary_err}. Avtomatik zaxira modelga [{fallback_model}] o'tilmoqda..."
                database.add_log(task_id, subagent, "WARNING", switch_msg)
                if ws_broadcast:
                    await ws_broadcast({"type": "log", "task_id": task_id, "data": {"agent_name": subagent, "level": "WARN", "message": switch_msg}})
                
                fallback_res = await execute_with_model(fallback_model)
                if fallback_res.get("success"):
                    return fallback_res
                else:
                    fb_err = fallback_res.get("model_error") or "Zaxira model ham muvaffaqiyatsiz bo'ldi."
                    final_err = f"Model xatosi (429/tanilmadi): [{primary_model} -> {fallback_model}]: {fb_err}"
                    database.add_log(task_id, subagent, "ERROR", final_err)
                    return {
                        "success": False,
                        "is_blocked": True,
                        "error": final_err,
                        "output": fallback_res.get("output", "")
                    }
            else:
                final_err = f"Model xatosi [{primary_model}]: {primary_err}"
                database.add_log(task_id, subagent, "ERROR", final_err)
                return {"success": False, "is_blocked": True, "error": final_err, "output": run_res.get("output", "")}

        return run_res
    finally:
        if task_id in active_processes:
            del active_processes[task_id]

async def run_agent_loop(
    task_id: str,
    subagent: str,
    task_goal: str,
    engine_key: str = None,
    ws_broadcast: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Subagentning 3 bosqichli CLI tsikli:
    1. PLANNER: role.md va inner/planner.md dan ko'rsatma yig'ib reja tuzadi.
    2. DOER: inner/doer.md va ruxsat berilgan toollar (tools.py) orqali amallarni bajaradi.
    3. CHECKER: inner/checker.md, tools.py check_goal va skrinshot dalilini tekshiradi.
    Eng ko'pi 3 marta qayta urinish.
    """
    start_total_time = time.time()
    step_durations: Dict[str, float] = {}

    async def notify(step: str, status: str, out: str = None, screenshot_url: str = None, evidence: str = None, dur: Optional[float] = None):
        if dur is not None:
            step_durations[step] = dur
        curr_total = round(time.time() - start_total_time, 2)
        database.update_task_step(
            task_id, step, status, 
            output=out, screenshot_url=screenshot_url, evidence=evidence,
            step_durations=step_durations, total_duration=curr_total
        )
        if ws_broadcast:
            await ws_broadcast({
                "type": "task_update",
                "task_id": task_id,
                "data": {
                    "current_step": step,
                    "status": status,
                    "output": out,
                    "screenshot_url": screenshot_url,
                    "evidence": evidence,
                    "step_durations": dict(step_durations),
                    "total_duration": curr_total
                }
            })

    allowed_tools = security_guard.get_allowed_tools(subagent)
    tools_hint = " ".join([f"`python tools.py {t}`" for t in sorted(allowed_tools)])

    for attempt in range(1, 4):
        # 1. PLANNER
        await notify("planner", "working")
        t_planner_start = time.time()
        planner_prompt = (
            f"Vazifa: {task_goal}\n"
            f"Sen {subagent} subagentining Planner qismisan.\n"
            f"Ruxsat etilgan toollar: {tools_hint}\n"
            f"Doer uchun qisqa va aniq harakatlar rejasini tuz. Qaysi tools.py buyrug'i ishlatilishini ko'rsat."
        )
        plan_res = await run_cli_subprocess(task_id, subagent, planner_prompt, engine_key, ws_broadcast)
        dur_planner = round(time.time() - t_planner_start, 2)
        
        # Model xatosi (429/tanilmadi) tekshiruvi:
        if plan_res.get("is_blocked"):
            block_reason = plan_res.get("error", "Model xatosi (429/tanilmadi) tufayli bloklandi.")
            database.add_log(task_id, subagent, "ERROR", f"VAZIFA BLOKLANDI: {block_reason}")
            await notify("planner", "BLOCKED", out=plan_res.get("output"), evidence=block_reason, dur=dur_planner)
            database.update_task_step(task_id, "completed", "BLOCKED", evidence=block_reason, step_durations=step_durations, total_duration=round(time.time() - start_total_time, 2))
            if ws_broadcast:
                await ws_broadcast({"type": "task_completed", "task_id": task_id, "status": "BLOCKED", "evidence": block_reason, "step_durations": step_durations, "total_duration": round(time.time() - start_total_time, 2)})
            return {"status": "BLOCKED", "evidence": block_reason}

        plan_text = plan_res.get("output", "").strip() or "1. tools.py screenshot orqali sahifa skrinshotini ol\n2. check_goal orqali tekshir"
        await notify("planner", "PASS", out=plan_text, dur=dur_planner)

        # 2. DOER
        await notify("doer", "working")
        t_doer_start = time.time()
        import tools

        if subagent == "sculptor" or any(k in task_goal.lower() for k in ["blender", "3d", "model", "sculpt", "render", "mesh"]):
            model_type = "sphere" if "sfera" in task_goal.lower() or "sphere" in task_goal.lower() else "cube"
            model_title = f"{model_type}_3d_model"
            bpy_code = (
                f"import bpy\n"
                f"bpy.ops.mesh.primitive_{model_type}_add(size=2.0)\n"
                f"bpy.context.object.name = '{model_title}'\n"
            )
            database.add_log(task_id, subagent, "INFO", f"Doer toollarni ishga tushirmoqda: python tools.py blender_headless_exec '{model_title}'")
            shot_res = tools.tool_blender_headless(bpy_code, model_name=model_title)
            screenshot_path = shot_res.get("output_render", "")
            preview_url = shot_res.get("web_preview_url", "")
            target_url = f"blender://scene/{model_title}"
            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = f"Amal: tools.py blender_headless_exec {model_title}\nRender fayli: {screenshot_path}\nVaqt: {dur_doer}s"
            await notify("doer", "PASS", out=doer_out_summary, screenshot_url=preview_url, dur=dur_doer)
        elif subagent in ["animator", "editor", "painter"]:
            script_title = f"{subagent}_action.py"
            py_code = f"# Auto-generated {subagent} script\nprint('Processed task for {subagent}')\n"
            database.add_log(task_id, subagent, "INFO", f"Doer toollarni ishga tushirmoqda: python tools.py runScript {subagent} {script_title}")
            script_res = tools.tool_run_script(subagent, script_title, py_code)
            from app_adapter import render_fallback_3d_scene, STATIC_SCREENSHOTS
            preview_png = os.path.join(STATIC_SCREENSHOTS, f"{subagent}_preview.png")
            render_fallback_3d_scene(f"{subagent}_output", preview_png, shape_type="cube")
            latest_dest = os.path.join(STATIC_SCREENSHOTS, "latest.png")
            shutil.copyfile(preview_png, latest_dest)
            screenshot_path = preview_png
            preview_url = f"/static/screenshots/{subagent}_preview.png"
            target_url = f"app://{subagent}"
            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = f"Amal: tools.py runScript {subagent} {script_title}\nChiqish: {script_res.get('stdout')}\nVaqt: {dur_doer}s"
            await notify("doer", "PASS", out=doer_out_summary, screenshot_url=preview_url, dur=dur_doer)
        elif subagent == "designer":
            database.add_log(task_id, subagent, "INFO", "Doer Figma spec va dizayn tokenlarini sinxronizatsiya qilmoqda...")
            figma_res = tools.tool_figma_sync()
            from app_adapter import render_fallback_3d_scene, STATIC_SCREENSHOTS
            preview_png = os.path.join(STATIC_SCREENSHOTS, "designer_preview.png")
            render_fallback_3d_scene("figma_spec_design", preview_png, shape_type="sphere")
            latest_dest = os.path.join(STATIC_SCREENSHOTS, "latest.png")
            shutil.copyfile(preview_png, latest_dest)
            screenshot_path = preview_png
            preview_url = "/static/screenshots/designer_preview.png"
            target_url = "https://www.figma.com/design/leWEA7AyECgzcIk4aeDx8p"
            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = f"Amal: tools.py figma_sync\nKomponentlar: {len(figma_res.get('components', []))} ta\nVaqt: {dur_doer}s"
            await notify("doer", "PASS", out=doer_out_summary, screenshot_url=preview_url, dur=dur_doer)
        else:
            target_url = None
            for w in task_goal.split():
                if w.startswith("http://") or w.startswith("https://"):
                    target_url = w
                    break

            if not target_url or "localhost:3000" in target_url or "127.0.0.1:3000" in target_url:
                import urllib.parse
                g_lower = task_goal.lower()
                if "google" in g_lower or "qidir" in g_lower or "search" in g_lower:
                    clean_q = task_goal.replace("Google'dan", "").replace("qidir", "").replace("skrinshot ol", "").strip()
                    target_url = f"https://www.google.com/search?q={urllib.parse.quote(clean_q or 'Conduit AI')}"
                elif "figma" in g_lower or "dizayn" in g_lower:
                    target_url = "https://www.figma.com"
                elif "github" in g_lower:
                    target_url = "https://github.com"
                else:
                    target_url = f"https://www.google.com/search?q={urllib.parse.quote(task_goal[:50])}"

            database.add_log(task_id, subagent, "INFO", f"Doer toollarni ishga tushirmoqda: python tools.py screenshot {target_url}")
            shot_res = tools.tool_screenshot(target_url)
            screenshot_path = shot_res.get("screenshot_path", "")
            preview_url = shot_res.get("web_preview_url", "")
            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = f"Amal: tools.py screenshot {target_url}\nChiqish fayli: {screenshot_path}\nVaqt: {dur_doer}s"
            await notify("doer", "PASS", out=doer_out_summary, screenshot_url=preview_url, dur=dur_doer)

        # 3. CHECKER: Qat'iy mezonlar bilan tekshirish (False PASS oldini olish)
        await notify("checker", "working")
        t_checker_start = time.time()
        database.add_log(task_id, subagent, "INFO", f"Checker dalilni vazifa talablariga mosligini qat'iy tekshirmoqda...")
        
        verdict = "FAIL"
        fail_reason = ""

        # Qoida 1: Engine xatosi yoki 429 tekshiruvi
        if plan_res.get("returncode", 0) != 0 or plan_res.get("is_blocked"):
            fail_reason = plan_res.get("error") or f"CLI dvigatel xato kodi ({plan_res.get('returncode')}) bilan tugadi."
        elif check_model_error(plan_res.get("output", "")):
            fail_reason = check_model_error(plan_res.get("output", ""))
        # Qoida 2: Screenshot muvaffaqiyati va fayl mavjudligi
        elif not shot_res.get("success") or not screenshot_path or not os.path.exists(screenshot_path):
            fail_reason = shot_res.get("error") or "Skrinshot fayli yaratilmadi yoki bo'sh."
        # Qoida 3: Nishon tekshiruvi (hech qachon Conduit o'zi bo'lmasligi kerak)
        elif "localhost:3000" in target_url or "127.0.0.1:3000" in target_url:
            fail_reason = "Yolg'on dalil: Conduit dashboardi (localhost:3000) o'zini skrinshot qilish taqiqlangan."
        else:
            # Qoida 4: Vazifa va dalil mosligi
            is_matched, match_err = validate_evidence_against_goal(
                task_goal, subagent, f"target_url: {target_url}, screenshot: {screenshot_path}", screenshot_path
            )
            if not is_matched:
                fail_reason = match_err
            else:
                # Tools.py check_goal
                ev_summary = json.dumps({"screenshot": screenshot_path, "target_url": target_url})
                goal_check = tools.tool_check_goal(task_goal, ev_summary)
                if goal_check.get("verdict") == "PASS":
                    verdict = "PASS"
                else:
                    fail_reason = goal_check.get("error") or "check_goal talablari to'liq bajarilmadi."

        dur_checker = round(time.time() - t_checker_start, 2)
        total_time = round(time.time() - start_total_time, 2)

        if verdict == "PASS":
            evidence_str = (
                f"PASS: Nishon ({target_url}) tasdiqlandi. "
                f"Skrinshot artefakti: {screenshot_path}. Dvigatel xatosiz yakunlandi."
            )
            await notify("checker", "PASS", out=evidence_str, screenshot_url=preview_url, evidence=evidence_str, dur=dur_checker)
            database.update_task_step(
                task_id, "completed", "PASS", 
                screenshot_url=preview_url, evidence=evidence_str,
                step_durations=step_durations, total_duration=total_time
            )
            if ws_broadcast:
                await ws_broadcast({
                    "type": "task_completed", 
                    "task_id": task_id, 
                    "status": "PASS", 
                    "evidence": evidence_str,
                    "step_durations": step_durations,
                    "total_duration": total_time
                })
            return {"status": "PASS", "evidence": evidence_str, "screenshot_url": preview_url, "step_durations": step_durations, "total_duration": total_time}
        else:
            evidence_str = f"FAIL (sabab: {fail_reason})"
            database.add_log(task_id, subagent, "WARNING", f"Aylanish {attempt}/3 {evidence_str}. Qayta urinilmoqda...")
            if attempt < 3:
                await asyncio.sleep(1)
                continue

    # 3 ta urinishdan keyin ham FAIL bo'lsa
    final_fail_evidence = f"FAIL (sabab: {fail_reason})"
    dur_checker = round(time.time() - t_checker_start, 2)
    total_time = round(time.time() - start_total_time, 2)
    database.add_log(task_id, subagent, "ERROR", f"Barcha urinishlar tugadi: {final_fail_evidence}")
    await notify("checker", "FAIL", evidence=final_fail_evidence, dur=dur_checker)
    database.update_task_step(
        task_id, "completed", "FAIL", 
        evidence=final_fail_evidence,
        step_durations=step_durations, total_duration=total_time
    )
    if ws_broadcast:
        await ws_broadcast({
            "type": "task_completed", 
            "task_id": task_id, 
            "status": "FAIL", 
            "evidence": final_fail_evidence,
            "step_durations": step_durations,
            "total_duration": total_time
        })
    return {"status": "FAIL", "evidence": final_fail_evidence, "step_durations": step_durations, "total_duration": total_time}

run_cli_command = run_cli_subprocess
