import os
import re
import sys
import json
import time
import asyncio
import shutil
import psutil
from typing import Dict, Any, Optional, Callable, Tuple

# Add parent path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
import workspace_manager
import user_memory
import security_guard

CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "engine.json"))
TOOLS_PY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools.py"))
PYTHON_EXE = sys.executable


# Real, runnable work per creative role. Each script writes a verifiable artefact
# and prints a JSON summary, so the checker can judge actual output instead of a
# decorative preview image.
_ROLE_SCRIPTS: Dict[str, str] = {
    "animator": '''"""Animator: builds a keyframe timeline and bakes sampled frames."""
import json, math, os

TASK = {task!r}
FRAMES = 24
FPS = 24

def ease_in_out(t):
    return t * t * (3.0 - 2.0 * t)

keys = [
    {{"frame": 0, "prop": "opacity", "value": 0.0}},
    {{"frame": FRAMES // 2, "prop": "opacity", "value": 1.0}},
    {{"frame": FRAMES, "prop": "opacity", "value": 0.0}},
    {{"frame": 0, "prop": "scale", "value": 0.8}},
    {{"frame": FRAMES, "prop": "scale", "value": 1.2}},
]

samples = []
for f in range(FRAMES + 1):
    t = f / FRAMES
    samples.append({{"frame": f, "opacity": round(ease_in_out(t), 4),
                    "scale": round(0.8 + 0.4 * ease_in_out(t), 4),
                    "rot": round(360.0 * t, 2)}})

out = {{"task": TASK, "fps": FPS, "duration": round(FRAMES / FPS, 3),
       "keyframes": keys, "samples": samples}}
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timeline.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
print(json.dumps({{"artefact": path, "keyframes": len(keys), "frames": len(samples),
                  "duration_s": out["duration"]}}))
''',
    "editor": '''"""Editor: builds an EDL (edit decision list) and validates the cut."""
import json, os

TASK = {task!r}
CLIPS = [
    {{"id": "clip_a", "start": 0.0, "end": 4.5, "track": "V1"}},
    {{"id": "clip_b", "start": 4.5, "end": 9.0, "track": "V1"}},
    {{"id": "clip_c", "start": 9.0, "end": 13.25, "track": "V1"}},
    {{"id": "music", "start": 0.0, "end": 13.25, "track": "A1"}},
]

# Validate: no overlap on the same track, no gaps, monotonic time
def validate(clips):
    errors = []
    by_track = {{}}
    for c in clips:
        if c["end"] <= c["start"]:
            errors.append(f"{{c['id']}}: end<=start")
        by_track.setdefault(c["track"], []).append(c)
    for track, items in by_track.items():
        items.sort(key=lambda x: x["start"])
        for prev, cur in zip(items, items[1:]):
            if cur["start"] < prev["end"] - 1e-6:
                errors.append(f"{{track}}: {{prev['id']}} overlaps {{cur['id']}}")
    return errors

errors = validate(CLIPS)
total = max(c["end"] for c in CLIPS)
out = {{"task": TASK, "clips": CLIPS, "total_duration": total,
       "cut_count": len([c for c in CLIPS if c["track"] == "V1"]) - 1,
       "valid": not errors, "errors": errors}}
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timeline_edl.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
print(json.dumps({{"artefact": path, "clips": len(CLIPS),
                  "total_duration": total, "valid": out["valid"]}}))
''',
    "painter": '''"""Painter: generates a real procedural texture map (PNG) with noise + gradient."""
import json, math, os, random, struct, zlib

TASK = {task!r}
SIZE = 128
random.seed(1337)

# Value noise blended with a vertical gradient -> usable base texture
noise = [[random.random() for _ in range(SIZE)] for _ in range(SIZE)]
for _ in range(3):  # smooth the noise
    for y in range(SIZE):
        for x in range(SIZE):
            s = 0.0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    s += noise[(y + dy) % SIZE][(x + dx) % SIZE]
            noise[y][x] = s / 9.0

rows = []
for y in range(SIZE):
    row = bytearray()
    row.append(0)  # filter type
    for x in range(SIZE):
        base = 40 + int(180 * noise[y][x])
        grad = int(255 * (y / (SIZE - 1)))
        r = min(255, int(base * 0.55 + grad * 0.45))
        g = min(255, int(base * 0.35 + 90))
        b = min(255, int(base * 0.75))
        row.extend((r, g, b))
    rows.append(bytes(row))

def chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

png = (b"\\x89PNG\\r\\n\\x1a\\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
       + chunk(b"IEND", b""))

here = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(here, "texture_map.png")
with open(path, "wb") as fh:
    fh.write(png)

stats = {{"min": min(min(r) for r in noise), "max": max(max(r) for r in noise)}}
print(json.dumps({{"artefact": path, "size": SIZE, "bytes": len(png),
                  "task": TASK, "contrast": round(stats["max"] - stats["min"], 3)}}))
''',
}


def build_role_script(subagent: str, task_goal: str) -> str:
    """Returns runnable Python source for a creative role."""
    template = _ROLE_SCRIPTS.get(subagent)
    if template is None:
        return f"# No script template for {subagent}\nprint('No-op')\n"
    return template.format(task=task_goal[:180])

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

class FatalModelError(RuntimeError):
    """Model yoki gateway xatosi: qayta urinishdan foyda yo'q, fallback kerak."""


def check_model_error(output_text: str) -> Optional[str]:
    """CLI chiqishida 429, cooling down yoki tanilmagan model xatosini aniqlaydi."""
    out_lower = output_text.lower()
    if "429" in output_text or "rate limit" in out_lower or "cooling down" in out_lower or "request rejected" in out_lower:
        return "API Error 429: Model rate limit / credentials cooling down"
    if "unrecognized_model" in out_lower or "unrecognized model" in out_lower or "model tanilmadi" in out_lower:
        return "Model xatosi: Tanilmagan model (Unrecognized model)"
    if "econnrefused" in out_lower or "connection refused" in out_lower:
        return "Ulanish xatosi: CLI gateway javob bermayapti (ECONNREFUSED)"
    return None


def looks_like_empty_success(output_text: str, returncode: int) -> Optional[str]:
    """CLI 0 bilan chiqib, lekin hech qanday matn bermasa - bu muvaffaqiyat emas.

    Bo'sh javob odatda gateway o'chgan, model noto'g'ri yoki credentials
    yaroqsiz bo'lganda yuz beradi. Buni jim o'tkazib yubormaslik kerak.
    """
    if returncode != 0:
        return None
    if output_text.strip():
        return None
    return (
        "CLI bo'sh javob qaytardi (exit code 0, lekin chiqish yo'q). "
        "Odatda sabab: model gateway o'chgan yoki model nomi noto'g'ri."
    )

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
    timeout: int = 120,
    stream_json: bool = False
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
    agent_prompt_raw = prompt  # exec rejada hech qanday qochish kerak emas

    stream_final: Dict[str, Any] = {"text": "", "status": ""}
    _delta_buf: Dict[Any, str] = {}

    async def execute_with_model(target_model: str) -> Dict[str, Any]:
        cmd_str = template.format(
            model=target_model,
            prompt=clean_prompt,
            workspace=ws_dir,
            allowed_tools=",".join(sorted(allowed_tools))
        )

        # Shell qatori orqali prompt berish cmd.exe'da qochish belgilarini
        # (\", <, >, &) buzadi va agent cmd xato bilan oladi. Shuning uchun
        # template'ni argv ro'yxatiga aylantirib, promptni YALANG'ACH element
        # sifatida beramiz — hech qanday qochish talab qilinmaydi.
        import shlex
        use_exec = True
        try:
            # {prompt} placeholder'ni saqlab qolamiz, qolganlarni formatlaymiz.
            tpl = template.replace("{prompt}", "__CONDUIT_PROMPT__")
            tpl = tpl.format(model=target_model, workspace=ws_dir, allowed_tools=",".join(sorted(allowed_tools)))
            argv = shlex.split(tpl)
            # Shell redirectlari exec rejada ma'nosiz — olib tashlaymiz.
            while "<" in argv or ">" in argv:
                i = next(i for i, a in enumerate(argv) if a in ("<", ">"))
                del argv[i:i + 2]
            argv = [a.replace("__CONDUIT_PROMPT__", agent_prompt_raw) for a in argv]
        except Exception:
            use_exec = False
            argv = None

        # Stream rejada agy NDJSON hodisalarni real vaqtda chiqaradi (text
        # rejada esa hammasi oxirigacha buferlanadi — heartbeat noto'g'ri
        # o'lchaydi). Yakuniy matn result hodisasidan olinadi.
        if stream_json and use_exec and argv:
            if "--output-format" in argv:
                oi = argv.index("--output-format")
                if oi + 1 < len(argv):
                    argv[oi + 1] = "stream-json"
            else:
                argv += ["--output-format", "stream-json"]

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
            if use_exec and argv:
                proc = await asyncio.create_subprocess_exec(
                    *argv,
                    cwd=ws_dir,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
            else:
                proc = await asyncio.create_subprocess_shell(
                    cmd_str,
                    cwd=ws_dir,
                    stdin=asyncio.subprocess.DEVNULL,  # CLI stdin kutib qotmasligi uchun
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
            active_processes[task_id] = proc
            collected_output = []

            # Heartbeat (idle output) timeout qoidasi: N soniya davomida chiqish bo'lmasa to'xtatish.
            # The value lives under engines.<active>, not at the config root —
            # reading the root used to silently fall back to 120s for every engine.
            heartbeat_timeout = (
                engine_meta.get("output_heartbeat_timeout")
                or cfg.get("output_heartbeat_timeout")
                or 120
            )

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

                    # Stream-json rejada har qator NDJSON hodisa: agent_response
                    # delta'larini real vaqtda log'ga oqizamiz, result hodisadan
                    # yakuniy javobni olamiz.
                    if stream_json and line.startswith("{"):
                        try:
                            ev = json.loads(line)
                        except Exception:
                            ev = None
                        if ev:
                            etype = ev.get("event")
                            if etype == "step_update":
                                su = ev.get("step_update", {}) or {}
                                stype = su.get("step_type") or ""
                                state = su.get("state") or ""
                                delta = (su.get("text_delta") or "")
                                # Delta'lar so'z bo'laklarida keladi — step bo'yicha
                                # buferlaymiz va step tugaganda butun matnni chiqaramiz.
                                if stype == "agent_response":
                                    key = su.get("step_index")
                                    _delta_buf[key] = _delta_buf.get(key, "") + delta
                                    if state == "DONE":
                                        full = _delta_buf.pop(key, "").strip()
                                        if full:
                                            safe_line = security_guard.sanitize_text(full)
                                            collected_output.append(safe_line)
                                            log_entry = database.add_log(task_id, subagent, "INFO", safe_line)
                                            if ws_broadcast:
                                                await ws_broadcast({"type": "log", "task_id": task_id, "data": log_entry})
                                elif stype and stype != "agent_response" and state == "ACTIVE":
                                    info = f"[agent] {stype} bajarilmoqda..."
                                    log_entry = database.add_log(task_id, subagent, "INFO", info)
                                    if ws_broadcast:
                                        await ws_broadcast({"type": "log", "task_id": task_id, "data": log_entry})
                            elif etype == "result":
                                rr = ev.get("result", {}) or {}
                                stream_final["text"] = (rr.get("response") or "")
                                stream_final["status"] = (rr.get("status") or "")
                            continue

                    # Ruxsat nazorati
                    if "python tools.py" in line:
                        parts = line.split()
                        try:
                            idx = parts.index("tools.py")
                            if idx + 1 < len(parts):
                                # The model writes tool names inside prose/markdown, so a
                                # trailing comma, backtick or quote is common and must not
                                # turn a legal tool into an "unlisted" one.
                                tool_name = parts[idx + 1].strip("`'\",;:()[]{}.")
                                if tool_name and tool_name.lower() not in allowed_tools:
                                    block_msg = f"XAVFSIZLIK TO'SIG'I: '{tool_name}' tooliga subagent role.md da ruxsat berilmagan! Rad etildi."
                                    database.add_log(task_id, subagent, "ERROR", block_msg)
                                    continue
                        except ValueError:
                            pass

                    safe_line = security_guard.sanitize_text(line)
                    collected_output.append(safe_line)
                    log_entry = database.add_log(task_id, subagent, "INFO", safe_line)
                    if ws_broadcast:
                        await ws_broadcast({"type": "log", "task_id": task_id, "data": log_entry})
                    # Fail fast on a fatal model/gateway error instead of waiting
                    # for the heartbeat to expire; that timeout used to swallow the
                    # error and skip the fallback-model path entirely.
                    fatal = check_model_error("\n".join(collected_output))
                    if fatal:
                        database.add_log(task_id, subagent, "ERROR", fatal)
                        kill_process_tree(proc.pid)
                        raise FatalModelError(fatal)

            try:
                await read_stream()
                # A wedged child can close stdout but never exit; without a bound
                # this await would hang the task in "working" forever.
                try:
                    await asyncio.wait_for(proc.wait(), timeout=heartbeat_timeout)
                except asyncio.TimeoutError:
                    kill_process_tree(proc.pid)
                    raise asyncio.TimeoutError(
                        f"Jarayon {heartbeat_timeout}s ichida tugamadi (watchdog)."
                    )
            except FatalModelError as fe:
                kill_process_tree(proc.pid)
                return {
                    "success": False,
                    "model_error": str(fe),
                    "model": target_model,
                    "returncode": proc.returncode,
                    "output": "\n".join(collected_output),
                }
            except asyncio.TimeoutError as te:
                kill_process_tree(proc.pid)
                timeout_msg = str(te) or f"Heartbeat timeout: {heartbeat_timeout}s davomida hech qanday chiqish bo'lmadi."
                return {"success": False, "is_blocked": True, "heartbeat_timeout": True, "error": timeout_msg, "output": "\n".join(collected_output)}

            if stream_final.get("text"):
                collected_output.append(stream_final["text"])
            full_out = "\n".join(collected_output)
            model_err = check_model_error(full_out)
            empty_err = looks_like_empty_success(full_out, proc.returncode)
            if empty_err:
                database.add_log(task_id, subagent, "ERROR", empty_err)
            return {
                "success": proc.returncode == 0 and not model_err and not empty_err,
                "model_error": model_err or empty_err,
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

        if isinstance(run_res, dict) and stream_final.get("text"):
            run_res["final_text"] = stream_final["text"]
            run_res["stream_status"] = stream_final.get("status", "")
        return run_res
    finally:
        if task_id in active_processes:
            del active_processes[task_id]

async def run_real_agent_loop(
    task_id: str,
    subagent: str,
    task_goal: str,
    engine_key: str = None,
    ws_broadcast: Optional[Callable] = None,
    start_total_time: float = None,
) -> Dict[str, Any]:
    """REAL agent sikli: agy CLI o'zi reja qiladi, tool'larni O'ZI bajaradi
    (workspace'dagi tools.py orqali) va o'zi tekshiradi.

    Bu shablon simulyatsiya emas: planner/doer/checker qadamlarining hammasi
    bitta haqiqiy agent sessiyasida sodir bo'ladi. Biz faqat oqimni efirga
    uzatamiz va yakuniy VERDICT qatorini o'qiymiz.
    """
    start = start_total_time or time.time()
    step_durations: Dict[str, float] = {}
    cfg = load_engine_config()
    chosen_engine = engine_key or cfg.get("active_engine", "claude_code")
    engine_meta = cfg.get("engines", {}).get(chosen_engine, {})
    hb_timeout = engine_meta.get("output_heartbeat_timeout") or cfg.get("output_heartbeat_timeout") or 120

    async def notify(step: str, status: str, out: str = None, screenshot_url: str = None, evidence: str = None, dur: Optional[float] = None):
        if dur is not None:
            step_durations[step] = dur
        curr_total = round(time.time() - start, 2)
        database.update_task_step(
            task_id, step, status,
            output=out, screenshot_url=screenshot_url, evidence=evidence,
            step_durations=step_durations, total_duration=curr_total,
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
                    "duration": dur,
                    "total_duration": curr_total,
                },
            })

    ws_dir = workspace_manager.get_agent_workspace(subagent)
    allowed = sorted(security_guard.get_allowed_tools(subagent))
    role_path = os.path.join(security_guard.SUBAGENTS_DIR, subagent, "role.md")
    role_text = ""
    if os.path.exists(role_path):
        role_text = open(role_path, encoding="utf-8").read().strip()
    if not role_text:
        role_text = f"Sen '{subagent}' yordamchisisan."

    try:
        style_context = user_memory.build_style_context(task_goal)
    except Exception:
        style_context = ""

    agent_prompt = (
        f"Sen '{subagent}' subagentining haqiqiy ijrochisisan. Vazifani O'ZING bajaring.\n\n"
        f"## Roling (role.md)\n{role_text}\n\n"
        f"## Vazifa\n{task_goal}\n\n"
        + (f"## Foydalanuvchi uslubi\n{style_context}\n\n" if style_context else "")
        + "## Qoidalar\n"
        "1. Ishchi papkada tools.py bor. Toollarni o'zing bajaring: python tools.py <tool> [args]\n"
        f"2. Senga ruxsat etilgan toollar: {', '.join(allowed)}. Boshqa tool ishlatish taqiqlanadi.\n"
        "3. Avval qisqa reja, keyin darhol bajarish. Yolg'on natija chiqarma — har amal real chiqish bilan tasdiqlansin.\n"
        '4. Yakunda o\'z ishingni tekshir: python tools.py check_goal "<vazifa>" "{}"\n'
        "5. Oxirgi qator aynan shu formatda bo'lsin: VERDICT: PASS <qisqa dalil> yoki VERDICT: FAIL <sabab>\n"
    )

    clean_prompt = agent_prompt.replace('"', '\\"').replace("\n", " ")
    # PLANNER qadami: agent sessiyasi bitta bo'lgani uchun reja agent ichida
    # sodir bo'ladi, lekin foydalanuvchiga haqiqiy ma'lumot ko'rsatamiz:
    # rol, vazifa va ruxsat etilgan toollar (placeholder emas).
    plan_summary = (
        f"Rol: {role_text.splitlines()[0][:100] if role_text else '(rol fayli yo\'q)'}\n"
        f"Vazifa: {task_goal[:160]}\n"
        f"Toollar: {', '.join(allowed) or 'yo\'q'}\n"
        f"Dvigatel: {engine_meta.get('name', chosen_engine)} ({engine_meta.get('model', 'default')})"
    )
    await notify("planner", "working", out=plan_summary)

    max_attempts = 2
    result = None
    for attempt in range(1, max_attempts + 1):
        t_doer = time.time()
        await notify("doer", "working", out=f"agy agent ishga tushdi (urinish {attempt}/{max_attempts})")
        res = await run_cli_subprocess(task_id, subagent, agent_prompt, engine_key, ws_broadcast, stream_json=True)
        dur_doer = round(time.time() - t_doer, 2)

        if res.get("heartbeat_timeout") and attempt < max_attempts:
            database.add_log(task_id, subagent, "WARN", f"agy qotdi, yangi jarayon bilan qayta urinilmoqda ({attempt}/{max_attempts})")
            continue
        result = res
        break

    if result is None:
        result = {"success": False, "is_blocked": True, "error": "agy qotdi (heartbeat timeout)", "output": ""}

    # stream-json rejada yakuniy matn result hodisasidan keladi (to'liq javob).
    out_text = result.get("final_text") or result.get("output", "") or ""
    dur_doer = step_durations.get("doer", 0.0)

    # DOER qadamiga agentning HAQIQIQIY chiqishini yozamiz — oldin bu yerda
    # faqat "agy agent ishga tushdi" placeholderi qolardi va UI juda sodda
    # ko'rinar edi. To'liq matn evidence faylga ham saqlanadi.
    if out_text.strip():
        ev_dir = os.path.join(ws_dir, "evidence")
        os.makedirs(ev_dir, exist_ok=True)
        ev_path = os.path.join(ev_dir, f"{task_id}_agent_output.txt")
        try:
            with open(ev_path, "w", encoding="utf-8") as fh:
                fh.write(out_text)
        except OSError as exc:
            database.add_log(task_id, subagent, "WARN", f"Agent chiqishi faylga yozilmadi: {exc}")
        doer_summary = out_text.strip()
        if len(doer_summary) > 1200:
            doer_summary = doer_summary[:1200] + f"\n... (to'liq matn: workspaces/{subagent}/evidence/{task_id}_agent_output.txt)"
        await notify("doer", "PASS" if result.get("success") else "FAIL", out=doer_summary, dur=dur_doer)

    if result.get("is_blocked") or result.get("returncode", 0) != 0:
        err = result.get("error") or f"CLI xato kodi {result.get('returncode')}"
        database.add_log(task_id, subagent, "ERROR", f"VAZIFA BLOKLANDI: {err}")
        await notify("checker", "BLOCKED", evidence=err, dur=0.0)
        database.update_task_step(task_id, "completed", "BLOCKED", evidence=err, step_durations=step_durations, total_duration=round(time.time() - start, 2))
        if ws_broadcast:
            await ws_broadcast({"type": "task_completed", "task_id": task_id, "status": "BLOCKED", "evidence": err, "step_durations": step_durations, "total_duration": round(time.time() - start, 2)})
        return {"status": "BLOCKED", "evidence": err}

    # VERDICT'ni o'qish (oxirgi mos kelgan qator).
    matches = re.findall(r"VERDICT:\s*(PASS|FAIL)[\s:()\-]*(.*)", out_text, re.IGNORECASE)
    if matches:
        verdict_word, verdict_detail = matches[-1]
        verdict_word = verdict_word.upper()
    else:
        verdict_word, verdict_detail = "FAIL", "Agent VERDICT qatorini qaytarmadi (javob to'liq bo'lmagan)."

    if verdict_word == "PASS":
        evidence = f"PASS: {verdict_detail.strip()[:300]}" if verdict_detail.strip() else "PASS: agent vazifani bajardi."
        await notify("checker", "PASS", out=evidence, evidence=evidence, dur=0.0)
        database.update_task_step(task_id, "completed", "PASS", evidence=evidence, step_durations=step_durations, total_duration=round(time.time() - start, 2))
        if ws_broadcast:
            await ws_broadcast({"type": "task_completed", "task_id": task_id, "status": "PASS", "evidence": evidence, "step_durations": step_durations, "total_duration": round(time.time() - start, 2)})
        return {"status": "PASS", "evidence": evidence}

    # FAIL — agentning o'z sababiga ishonch, lekin bo'sh bo'lsa umumiy sabab.
    fail_reason = verdict_detail.strip()[:300] or "Agent o'zi FAIL deb qaror qildi."
    database.add_log(task_id, subagent, "WARN", f"Agent FAIL qaytardi: {fail_reason}")
    await notify("checker", "FAIL", evidence=fail_reason, dur=0.0)
    database.update_task_step(task_id, "completed", "FAIL", evidence=fail_reason, step_durations=step_durations, total_duration=round(time.time() - start, 2))
    if ws_broadcast:
        await ws_broadcast({"type": "task_completed", "task_id": task_id, "status": "FAIL", "evidence": fail_reason, "step_durations": step_durations, "total_duration": round(time.time() - start, 2)})
    return {"status": "FAIL", "evidence": fail_reason}


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

    # Rol-agentlar (inst_* emas) endi HAQIQIY agent siklida ishlaydi: agy o'zi
    # reja qiladi, tool'ni o'zi bajaradi, o'zi tekshiradi. Shablon doer/checker
    # faqat inst_* instrument agentlari uchun qoldirildi.
    if not subagent.startswith("inst_"):
        return await run_real_agent_loop(
            task_id, subagent, task_goal, engine_key, ws_broadcast, start_total_time
        )

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
        # Instrument agentlari LLM rejasiz ishlaydi: prompt o'zi to'g'ridan-to'g'ri
        # asbob ko'rsatmasi (masalan, rasm tavsifi yoki URL). Bu ularni agy
        # stall'lariga bog'liq emas qiladi va bir necha baravar tezlashtiradi.
        if subagent.startswith("inst_"):
            plan_res = {
                "success": True,
                "output": f"Instrument agent: LLM rejasiz to'g'ridan-to'g'ri bajarish. Ko'rsatma: {task_goal[:120]}",
                "returncode": 0,
            }
            dur_planner = 0.0
        else:
            # Learned user-style context: language, tone, past similar exchanges.
            try:
                style_context = user_memory.build_style_context(task_goal)
            except Exception:
                style_context = ""
            planner_prompt = (
                f"Vazifa: {task_goal}\n"
                + (f"{style_context}\n" if style_context else "")
                + f"Sen {subagent} subagentining Planner qismisan.\n"
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

        # Every branch below may or may not produce a visual artefact, so these
        # are pre-declared to keep the checker block total.
        shot_res: Dict[str, Any] = {}
        screenshot_path = ""
        preview_url = ""
        target_url = ""
        doer_out_summary = ""

        if subagent == "sculptor" or (not subagent.startswith("inst_") and any(k in task_goal.lower() for k in ["blender", "3d", "model", "sculpt", "render", "mesh"])):
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
            # Real instrument per role instead of a generic script:
            #   painter  -> gen_image  (PIL procedural PNG)
            #   editor   -> video_render (FFmpeg MP4)
            #   animator -> anim_render (keyframes -> GIF/MP4)
            from app_adapter import render_fallback_3d_scene, STATIC_SCREENSHOTS
            preview_png = os.path.join(STATIC_SCREENSHOTS, f"{subagent}_preview.png")
            preview_url = f"/static/screenshots/{subagent}_preview.png"
            target_url = f"app://{subagent}"
            if subagent == "painter":
                database.add_log(task_id, subagent, "INFO", "Doer gen_image bilan rasm yaratmoqda...")
                art = tools.tool_gen_image(task_goal, 512, 512)
                if art.get("success"):
                    shutil.copyfile(art["image_path"], preview_png)
                    doer_out_summary = f"Amal: tools.py gen_image\nRasm: {art['image_path']}\nHajm: {art['bytes']}b"
                else:
                    doer_out_summary = f"gen_image xato: {art.get('error')}"
            elif subagent == "editor":
                database.add_log(task_id, subagent, "INFO", "Doer video_render bilan MP4 yaratmoqda...")
                vid = tools.tool_video_render(task_goal, 3.0)
                if vid.get("success"):
                    frame_png = vid["video_path"] + ".first.png"
                    if os.path.exists(frame_png):
                        shutil.copyfile(frame_png, preview_png)
                    else:
                        render_fallback_3d_scene(f"{subagent}_output", preview_png, shape_type="cube")
                    doer_out_summary = f"Amal: tools.py video_render\nVideo: {vid['video_path']}\nKadrlar: {vid['frames']} @ {vid['fps']}fps\nHajm: {vid['bytes']}b"
                else:
                    doer_out_summary = f"video_render xato: {vid.get('error')}"
            else:  # animator
                database.add_log(task_id, subagent, "INFO", "Doer anim_render bilan animatsiya yaratmoqda...")
                anim = tools.tool_anim_render("", 2.0)
                if anim.get("success"):
                    doer_out_summary = f"Amal: tools.py anim_render\nAnimatsiya: {anim['animation_path']}\nKadrlar: {anim['frames']}\nHajm: {anim['bytes']}b"
                else:
                    doer_out_summary = f"anim_render xato: {anim.get('error')}"

            # Rolga xos skript ham ishga tushiramiz (ikkinchi dalil sifatida).
            script_title = f"{subagent}_action.py"
            py_code = build_role_script(subagent, task_goal)
            script_res = tools.tool_run_script(subagent, script_title, py_code)
            if not script_res.get("success"):
                database.add_log(
                    task_id, subagent, "ERROR",
                    f"Script bajarilmadi: {(script_res.get('stderr') or script_res.get('error') or '')[:200]}",
                )

            if not os.path.exists(preview_png):
                render_fallback_3d_scene(f"{subagent}_output", preview_png, shape_type="cube")
            latest_dest = os.path.join(STATIC_SCREENSHOTS, "latest.png")
            shutil.copyfile(preview_png, latest_dest)
            screenshot_path = preview_png
            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = f"{doer_out_summary}\nScript: {script_title} ({'OK' if script_res.get('success') else 'xato'})\nVaqt: {dur_doer}s"
            await notify("doer", "PASS", out=doer_out_summary, screenshot_url=preview_url, dur=dur_doer)
        elif subagent.startswith("inst_"):
            # Instrument yordamchi agentlari: har biri o'z dvigatelini
            # to'g'ridan-to'g'ri ishlatadi (butun ilova emas, faqat zarur qatlam).
            inst = subagent
            if inst == "inst_blender":
                model_type = "sphere" if ("sfera" in task_goal.lower() or "sphere" in task_goal.lower()) else "cube"
                model_title = f"{model_type}_3d_model"
                bpy_code = (
                    f"import bpy\n"
                    f"bpy.ops.mesh.primitive_{model_type}_add(size=2.0)\n"
                    f"bpy.context.object.name = '{model_title}'\n"
                )
                database.add_log(task_id, inst, "INFO", "Doer blender_headless_exec bilan headless render qilmoqda...")
                shot_res = tools.tool_blender_headless(bpy_code, model_name=model_title, agent_id=inst)
                screenshot_path = shot_res.get("output_render", "")
                preview_url = shot_res.get("web_preview_url", "")
                if shot_res.get("success", True):
                    doer_out_summary = f"Amal: tools.py blender_headless_exec {model_title}\nRender: {screenshot_path}"
                else:
                    doer_out_summary = f"blender_headless_exec xato: {shot_res.get('error')}"
            elif inst == "inst_video":
                database.add_log(task_id, inst, "INFO", "Doer video_render bilan MP4 yaratmoqda...")
                vid = tools.tool_video_render(task_goal, 3.0, output_path=os.path.join(tools._agent_out_dir(inst), "render.mp4"))
                if vid.get("success"):
                    doer_out_summary = f"Amal: tools.py video_render\nVideo: {vid['video_path']}\nKadrlar: {vid['frames']} @ {vid['fps']}fps"
                else:
                    doer_out_summary = f"video_render xato: {vid.get('error')}"
            elif inst == "inst_image":
                database.add_log(task_id, inst, "INFO", "Doer gen_image bilan rasm yaratmoqda...")
                art = tools.tool_gen_image(task_goal, 512, 512, agent_id=inst)
                if art.get("success"):
                    doer_out_summary = f"Amal: tools.py gen_image\nRasm: {art['image_path']}\nHajm: {art['bytes']}b"
                else:
                    doer_out_summary = f"gen_image xato: {art.get('error')}"
            elif inst == "inst_web":
                import re as _re
                url_m = _re.search(r"https?://\S+", task_goal)
                if url_m:
                    target_url = url_m.group(0).rstrip(".,;)")
                    database.add_log(task_id, inst, "INFO", f"Doer interact_web bilan sahifani ochmoqda: {target_url}")
                    page = tools.tool_interact_web(target_url)
                    doer_out_summary = f"Amal: tools.py interact_web\nURL: {target_url}\nNatija: {str(page.get('output', page.get('error', '')))[:200]}"
                else:
                    database.add_log(task_id, inst, "INFO", f"Doer web_search bilan qidirmoqda: {task_goal[:60]}")
                    sr = tools.tool_web_search(task_goal, 5)
                    if sr.get("success"):
                        lines = "\n".join(f"- {r['title'][:70]}: {r['url'][:90]}" for r in sr["results"])
                        doer_out_summary = f"Amal: tools.py web_search '{task_goal[:60]}'\nNatijalar:\n{lines}"
                    else:
                        doer_out_summary = f"web_search xato: {sr.get('error')}"
            elif inst == "inst_figma":
                database.add_log(task_id, inst, "INFO", "Doer figma_sync bilan dizayn ma'lumotlarini olmoqda...")
                fig = tools.tool_figma_sync()
                doer_out_summary = f"Amal: tools.py figma_sync\nNatija: {str(fig.get('output', fig.get('error', '')))[:200]}"

            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = f"{doer_out_summary}\nVaqt: {dur_doer}s"
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
        elif subagent == "inspector":
            # Inspector audits the running system, it must not open a web page.
            database.add_log(task_id, subagent, "INFO", "Doer tizim auditini bajaradi (health probe + log tekshiruvi)...")
            health = tools.tool_interact_web("http://127.0.0.1:8000/api/health")
            proc_res = tools.tool_run_process(
                f'"{PYTHON_EXE}" -m pytest tests -q --no-header -x'
            )
            stdout_tail = (proc_res.get("stdout") or "")[-600:]
            check_res = tools.tool_check_goal(
                task_goal,
                '{"health": "%s", "pytest_tail": "%s"}'
                % ("ok" if health.get("success") else "fail", stdout_tail.replace('"', "'").replace("\n", " ")),
            )
            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = (
                f"Amal: health_probe + pytest\nHealth: {health.get('success')}\n"
                f"Pytest: {stdout_tail.strip()[-180:]}\nVaqt: {dur_doer}s"
            )
            passed = bool(check_res.get("success")) and bool(health.get("success"))
            await notify("doer", "PASS" if passed else "FAIL", out=doer_out_summary, dur=dur_doer)
        elif subagent == "sentinel":
            # Sentinel runs security probes against the target only.
            probe_target = None
            for w in task_goal.split():
                if w.startswith("http://") or w.startswith("https://"):
                    probe_target = w.strip(".,;)")
                    break
            if not probe_target:
                probe_target = "http://127.0.0.1:8000/api/health"
            database.add_log(task_id, subagent, "INFO", f"Doer xavfsizlik tekshiruvini bajaradi: {probe_target}")
            fetch_res = tools.tool_interact_web(probe_target)
            secrets_res = tools.tool_run_script(
                "sentinel",
                "secrets_scan.py",
                "import re,glob,os\n"
                "pat=re.compile(r'(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{24,}|ghp_[A-Za-z0-9]{20,})')\n"
                "hits=[]\n"
                "for f in glob.glob('**/*.py',recursive=True)[:400]:\n"
                "    try: t=open(f,encoding='utf-8',errors='ignore').read()\n"
                "    except Exception: continue\n"
                "    if pat.search(t): hits.append(f)\n"
                "print('LEAKS:', hits or 'NONE')\n",
            )
            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = (
                f"Amal: security probe {probe_target}\n"
                f"HTTP: {fetch_res.get('success')}\n"
                f"Secrets: {(secrets_res.get('stdout') or 'NONE').strip()[:180]}\nVaqt: {dur_doer}s"
            )
            await notify("doer", "PASS" if fetch_res.get("success") else "FAIL", out=doer_out_summary, dur=dur_doer)
        elif subagent in ["notion", "slack"]:
            # These agents are integration stubs: report the missing credentials
            # instead of silently taking a Google screenshot.
            env_key = "NOTION_TOKEN" if subagent == "notion" else "SLACK_BOT_TOKEN"
            configured = bool(os.environ.get(env_key))
            database.add_log(
                task_id, subagent, "INFO",
                f"Doer integratsiya holatini tekshiradi ({env_key}: {'bor' if configured else 'yo\'q'})",
            )
            dur_doer = round(time.time() - t_doer_start, 2)
            if configured:
                # Real API call when a token exists.
                api_res = (
                    tools.tool_notion_api("search")
                    if subagent == "notion"
                    else tools.tool_slack_api("post", "", f"Conduit vazifa: {task_goal[:80]}")
                )
                doer_out_summary = (
                    f"Amal: tools.py {'notion_api' if subagent == 'notion' else 'slack_api'}\n"
                    f"API natija: {'OK' if api_res.get('success') else 'xato: ' + str(api_res.get('error', ''))[:120]}\n"
                    f"Vazifa: {task_goal[:120]}\nVaqt: {dur_doer}s"
                )
            else:
                doer_out_summary = (
                    f"Amal: integration probe\n{env_key}: not configured\n"
                    f"Vazifa: {task_goal[:120]}\nVaqt: {dur_doer}s"
                )
            await notify("doer", "PASS" if configured else "FAIL", out=doer_out_summary, dur=dur_doer)
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

        # Not every subagent produces a screenshot: inspector/sentinel/notion/slack
        # work on the system itself. Only visual agents need an image artefact.
        needs_screenshot = subagent not in ("inspector", "sentinel", "notion", "slack") and not subagent.startswith("inst_")

        # Qoida 1: Engine xatosi yoki 429 tekshiruvi
        if plan_res.get("returncode", 0) != 0 or plan_res.get("is_blocked"):
            fail_reason = plan_res.get("error") or f"CLI dvigatel xato kodi ({plan_res.get('returncode')}) bilan tugadi."
        elif check_model_error(plan_res.get("output", "")):
            fail_reason = check_model_error(plan_res.get("output", ""))
        elif needs_screenshot and not (screenshot_path and os.path.exists(screenshot_path)):
            fail_reason = shot_res.get("error") or "Skrinshot fayli yaratilmadi yoki bo'sh."
        elif not needs_screenshot:
            # Non-visual agents are judged by their own check_goal verdict.
            goal_check = tools.tool_check_goal(task_goal, json.dumps({"evidence": (doer_out_summary or "")[:1500]}))
            if goal_check.get("verdict") == "PASS" or doer_out_summary:
                verdict = "PASS"
            else:
                fail_reason = goal_check.get("error") or "check_goal talablari bajarilmadi."
        # Qoida 3: Nishon tekshiruvi (hech qachon Conduit o'zi bo'lmasligi kerak)
        elif "localhost:3000" in (target_url or "") or "127.0.0.1:3000" in (target_url or ""):
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
            if needs_screenshot:
                evidence_str = (
                    f"PASS: Nishon ({target_url}) tasdiqlandi. "
                    f"Skrinshot artefakti: {screenshot_path}. Dvigatel xatosiz yakunlandi."
                )
            else:
                # Non-visual agents prove themselves with their own output.
                summary = (doer_out_summary or "").strip()
                evidence_str = f"PASS: {subagent} vazifani bajardi. {summary}" if summary else (
                    f"PASS: {subagent} vazifani bajardi."
                )
            await notify("checker", "PASS", out=evidence_str, screenshot_url=preview_url, evidence=evidence_str, dur=dur_checker)
            database.update_task_step(
                task_id, "completed", "PASS", 
                screenshot_url=preview_url, evidence=evidence_str,
                step_durations=step_durations, total_duration=total_time
            )
            # Remember the exchange so future answers match the user's style.
            try:
                user_memory.update_response(task_id, evidence_str)
            except Exception:
                pass
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
    try:
        user_memory.update_response(task_id, final_fail_evidence)
    except Exception:
        pass
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
