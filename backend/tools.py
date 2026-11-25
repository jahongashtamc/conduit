#!/usr/bin/env python3
"""
Conduit Tools CLI - agent-studio-plugin funksiyalariga to'g'ridan-to'g'ri qobiq.
MCP ishlatilmaydi. Har bir amal toza JSON qaytaradi.
"""

import sys
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import json
import logging
import subprocess
import shutil
import hashlib
import random
import re
import time
import threading
import tempfile
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger("conduit.tools")

# Ensure backend directory is in sys.path for app_adapter import
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if os.path.exists(_backend_dir) and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
_curr_dir = os.path.abspath(os.path.dirname(__file__))
if os.path.exists(os.path.join(_curr_dir, "app_adapter.py")) and _curr_dir not in sys.path:
    sys.path.insert(0, _curr_dir)

PLUGIN_LIB = os.path.expanduser(r"~/.gemini/config/plugins/agent-studio-plugin/lib")
PLUGIN_SRC = os.path.join(os.path.dirname(PLUGIN_LIB), "src")

# CLI orqali chaqiriladigan barcha tool'lar. Har bir subagentning role.md
# faylida e'lon qilingan nom aliases orqali kanonik nomga o'tkaziladi.
TOOL_SPECS = (
    ("screenshot", ("screenshot",), "url [output_path]", "Veb-sahifa skrinshotini oladi (Conduit dashboardi taqiqlangan)."),
    ("interact_web", ("interact_web",), "url", "Sahifa konsoli/tarmog'ini tekshiradi."),
    ("web_search", ("web_search", "search"), "query", "Vebdan qidiruv natijalarini oladi."),
    ("run_process", ("run_process",), "command", "Tizim jarayonini ishga tushiradi."),
    ("get_logs", ("get_logs",), "[target]", "Jarayon loglarini qaytaradi."),
    ("check_goal", ("check_goal",), "goal evidence_json", "Maqad dalil asosida tekshiradi (eski dalil rad etiladi)."),
    ("blender_headless_exec", ("blender_headless_exec", "blender", "sculpt"), "bpy_code [model]", "Blender headless 3D model/render yaratadi."),
    ("blender_video", ("blender_video", "blender_anim"), "script.py [out.mp4] [fps]", "Haqiqiy Blender animatsiya videosini render qiladi."),
    ("runscript", ("runscript", "run_script"), "subagent script.py code", "Izolyatsiyalangan workspace'da skript bajaradi."),
    ("figma_sync", ("figma_sync", "figma"), "[file_key] [requirement]", "Figma REST API'dan haqiqiy fayl ma'lumotlarini oladi."),
    ("gen_image", ("gen_image", "genimage", "paint"), "prompt [w] [h] [out]", "Haqiqiy PNG rasm yaratadi."),
    ("video_render", ("video_render", "video"), "spec_with_clip_paths [seconds] [audio_path]", "Haqiqiy kirish kliplaridan MP4 montaj qiladi."),
    ("anim_render", ("anim_render", "animate"), "keyframes_json [seconds]", "Haqiqiy GIF animatsiya yaratadi."),
    ("notion_api", ("notion_api", "notion"), "action", "Notion API (token bo'lmasa xato qaytaradi)."),
    ("slack_api", ("slack_api", "slack"), "action channel text", "Slack API (token bo'lmasa xato qaytaradi)."),
)
TOOL_ALIASES = {alias: canonical for canonical, aliases, _usage, _desc in TOOL_SPECS for alias in aliases}


def canonical_tool_name(name: str) -> Optional[str]:
    """CLI nomi yoki alias'ini kanonik nomga o'tkazadi. Noma'lum -> None."""
    if not isinstance(name, str):
        return None
    return TOOL_ALIASES.get(name.strip().lower())


def list_tools() -> list:
    """Asosiy agent uchun to'liq, mashinada o'qiladigan tool katalogi."""
    declared = set()
    try:
        import security_guard
        for folder in os.listdir(security_guard.SUBAGENTS_DIR):
            declared.update(a.lower() for a in security_guard.get_allowed_tools(folder))
    except Exception as exc:
        LOGGER.warning("Tool katalogi uchun role.md o'qilmadi: %s: %s", type(exc).__name__, exc)

    tools_out = []
    for canonical, aliases, usage, desc in TOOL_SPECS:
        tools_out.append({
            "name": canonical,
            "aliases": list(aliases),
            "declared_by_subagents": sorted(a for a in declared if TOOL_ALIASES.get(a) == canonical),
            "usage": f"python tools.py {canonical} {usage}".strip(),
            "description": desc,
        })
    missing = sorted(a for a in declared if a not in TOOL_ALIASES)
    if missing:
        LOGGER.error("Role.md'da e'lon qilingan, lekin CLI'da yo'q tool'lar: %s", missing)
    return tools_out


def run_node_eval(script_code: str, args: list = None) -> dict:
    """Node.js orqali agent-studio-plugin funksiyasini to'g'ridan-to'g'ri chaqiradi."""
    try:
        cmd = ["node", "-e", script_code, "--"] + (args or [])
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if res.returncode == 0:
            try:
                return json.loads(res.stdout.strip())
            except json.JSONDecodeError:
                return {"success": True, "raw_output": res.stdout.strip()}
        else:
            return {"success": False, "error": res.stderr.strip() or res.stdout.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_static_screenshots_dir() -> str:
    """Asosiy backend'ning static/screenshots papkasini topadi.

    tools.py hemda asl joyida (backend/), hemda subagent workspace'lariga
    nusxalangan holda ishlaydi. Papkalarni yuqoriga qarab bosib, asl
    backend'ni aniqlaymiz — bu oldin qo'llanilgan nisbiy '../..' hisobidan
    kelib chiqadigan 'backend/backend/' kabi strandir papkalarni yo'q qiladi.
    """
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        # 1) Asl backend papkasi: tools.py yonida main.py turadi
        if os.path.isfile(os.path.join(d, "main.py")) and os.path.basename(d) == "backend":
            return os.path.join(d, "static", "screenshots")
        # 2) Nusxa: yuqorida backend/main.py bor ildizni topamiz
        if os.path.isfile(os.path.join(d, "backend", "main.py")):
            return os.path.join(d, "backend", "static", "screenshots")
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    # Fallback: eski xulq (asl joyida static yonida)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "screenshots"))

def _mirror_to_live_browser(url: str, wait: bool = True) -> None:
    """Opens `url` in the watched browser without disturbing any running loop.

    tools.py is called both from plain scripts and from FastAPI workers that
    already own an event loop, so this never uses asyncio.run() on the calling
    thread. When `wait` is set we block briefly so callers observe a ready URL.
    """
    import threading

    holder: dict = {}

    def worker() -> None:
        import asyncio as _asyncio
        try:
            import live_browser
            holder["ok"] = _asyncio.run(live_browser.goto(url))
        except Exception as exc:  # noqa: BLE001
            holder["err"] = str(exc)[:200]

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    if wait:
        t.join(timeout=30)


def _mirror_to_backend(url: str) -> None:
    """When tools.py runs as its own process, the backend owns the watched
    browser, so tell it over HTTP instead of opening a second one."""
    try:
        import httpx

        httpx.post(
            "http://127.0.0.1:8000/api/browser/navigate",
            json={"url": url},
            timeout=35.0,
        )
    except Exception as exc:
        # Backend o'chik bo'lishi mumkin — CLI mustaqil ishlayveradi, lekin sabab loglanadi.
        LOGGER.debug("Browser navigate API chaqiruvi bajarilmadi (standalone rejim): %s: %s", type(exc).__name__, exc)


def tool_screenshot(url: str, output_path: str = None) -> dict:
    """Veb-sahifaning to'liq skrinshotini oladi. Conduit (localhost:3000) taqiqlangan."""
    if not url or "localhost:3000" in url or "127.0.0.1:3000" in url:
        return {
            "success": False,
            "tool": "screenshot",
            "url": url,
            "error": "Xato: Conduit dashboardining o'zi (localhost:3000) skrinshot qilinmaydi. Vazifa nishoni bo'lgan tashqi sayt yoki ilova skrinshot qilinishi shart."
        }

    out_dir_arg = f"'{output_path.replace(chr(92), '/')}'" if output_path else "null"
    # Open the target in the watched browser first, so the operator can see the
    # robot working instead of only the final still.
    if os.environ.get("CONDUIT_IN_BACKEND") == "1":
        _mirror_to_live_browser(url)
    else:
        _mirror_to_backend(url)

    # 1. First try agent_studio python tool if available
    try:
        sys.path.insert(0, PLUGIN_SRC)
        from agent_studio.tools.screen import screenshot as as_screenshot
        s_res = as_screenshot(url)
        if s_res.get("status") == "success":
            spath = s_res.get("path")
            if output_path and spath:
                shutil.copyfile(spath, output_path)
                spath = os.path.abspath(output_path)
            res = {
                "success": True,
                "tool": "screenshot",
                "url": url,
                "screenshot_path": spath,
                "bytes": s_res.get("size_bytes", 0),
                "mime_type": "image/png"
            }
            static_screenshots = get_static_screenshots_dir()
            os.makedirs(static_screenshots, exist_ok=True)
            dest_filename = os.path.basename(spath)
            dest = os.path.join(static_screenshots, dest_filename)
            latest_dest = os.path.join(static_screenshots, "latest.png")
            try:
                shutil.copyfile(spath, dest)
                shutil.copyfile(spath, latest_dest)
                res["web_preview_url"] = f"/static/screenshots/{dest_filename}"
                res["latest_url"] = "/static/screenshots/latest.png"
            except Exception:
                res["web_preview_url"] = spath
            return res
    except Exception as exc:
        LOGGER.debug("Playwright screenshot ishlamadi, Node fallback ishlatiladi: %s: %s", type(exc).__name__, exc)

    node_script = f"""
    const {{ screenshot }} = require('{PLUGIN_LIB.replace(chr(92), '/')}/visualCapture.js');
    screenshot('{url}', {out_dir_arg})
        .then(res => console.log(JSON.stringify({{
            success: true,
            tool: "screenshot",
            url: '{url}',
            screenshot_path: res.path,
            bytes: res.bytes,
            mime_type: res.mime_type
        }})))
        .catch(err => console.log(JSON.stringify({{
            success: false,
            tool: "screenshot",
            url: '{url}',
            error: err.message || String(err)
        }})));
    """
    res = run_node_eval(node_script)
    # Agar screenshot muvaffaqiyatli bo'lsa va backend static papkasi mavjud bo'lsa, preview uchun nusxalaymiz
    if res.get("success") and res.get("screenshot_path"):
        src = res.get("screenshot_path")
        static_screenshots = get_static_screenshots_dir()
        os.makedirs(static_screenshots, exist_ok=True)
        dest_filename = os.path.basename(src)
        dest = os.path.join(static_screenshots, dest_filename)
        latest_dest = os.path.join(static_screenshots, "latest.png")
        try:
            shutil.copyfile(src, dest)
            shutil.copyfile(src, latest_dest)
            res["web_preview_url"] = f"/static/screenshots/{dest_filename}"
            res["latest_url"] = "/static/screenshots/latest.png"
        except Exception:
            res["web_preview_url"] = src
    return res

def tool_interact_web(url: str) -> dict:
    """Sahifani tekshiradi, konsol xatolarini va tarmoq statuslarini oladi."""
    try:
        sys.path.insert(0, PLUGIN_SRC)
        from agent_studio.tools.screen import interact_web as as_interact
        i_res = as_interact(url, [])
        return {
            "success": i_res.get("status") == "success",
            "tool": "interact_web",
            "url": url,
            "console_errors": i_res.get("console_errors", []),
            "console_warnings": [],
            "network_failures": i_res.get("network_failures", []),
            "is_clean": len(i_res.get("console_errors", [])) == 0 and len(i_res.get("network_failures", [])) == 0
        }
    except Exception as exc:
        LOGGER.debug("Playwright inspect ishlamadi, Node fallback ishlatiladi: %s: %s", type(exc).__name__, exc)

    node_script = f"""
    const {{ probeRuntimeHealth }} = require('{PLUGIN_LIB.replace(chr(92), '/')}/browserDiagnostics.js');
    probeRuntimeHealth('{url}')
        .then(res => console.log(JSON.stringify({{
            success: true,
            tool: "interact_web",
            url: '{url}',
            console_errors: res.console_errors || [],
            console_warnings: res.console_warnings || [],
            network_failures: res.network_failures || [],
            is_clean: res.is_clean
        }})))
        .catch(err => console.log(JSON.stringify({{
            success: false,
            tool: "interact_web",
            url: '{url}',
            error: err.message || String(err)
        }})));
    """
    return run_node_eval(node_script)

# run_process tomonidan boshlangan jarayonlarning HAQIQIY chiqishi.
# Avval Popen handle'lari tashlab yuborilardi va get_logs doimiy
# "No active process errors reported" degan soxta matn qaytarardi.
_PROCESS_REGISTRY: Dict[str, Dict[str, Any]] = {}
_PROCESS_LOCK = threading.Lock()
_MAX_LOG_LINES = 500
_MAX_TRACKED_PROCESSES = 50
# tools.py har tool chaqiruvida alohida Python jarayoni sifatida ishga tushadi.
# Shuning uchun registry faqat xotirada emas, umumiy vaqtinchalik faylda ham saqlanadi.
_REGISTRY_PATH = os.path.join(tempfile.gettempdir(), "nexus_process_registry.json")


def _load_process_registry() -> None:
    """Oldingi CLI chaqiruvining jarayon loglarini diskdan o'qish."""
    if not os.path.isfile(_REGISTRY_PATH):
        return
    try:
        with open(_REGISTRY_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        LOGGER.warning("Jarayon registry fayli o'qilmadi: %s", exc)
        return
    if not isinstance(data, dict):
        return
    with _PROCESS_LOCK:
        for pid, rec in data.items():
            existing = _PROCESS_REGISTRY.get(pid)
            if existing and existing.get("proc") is not None:
                continue  # tirik jarayon obyekti disk nusxasidan ustun
            if not isinstance(rec, dict):
                continue
            _PROCESS_REGISTRY[pid] = {
                "proc": None,
                "command": str(rec.get("command") or ""),
                "events": deque(rec.get("events") or [], maxlen=_MAX_LOG_LINES),
                "started_at": float(rec.get("started_at") or 0),
                "returncode": rec.get("returncode"),
            }


def _save_process_registry() -> None:
    """Registry ni atomik tarzda diskka yozish (xatolik yutulmaydi)."""
    with _PROCESS_LOCK:
        items = sorted(
            _PROCESS_REGISTRY.items(),
            key=lambda kv: kv[1].get("started_at", 0),
            reverse=True,
        )[:_MAX_TRACKED_PROCESSES]
        snapshot = {
            pid: {
                "command": entry.get("command", ""),
                "started_at": entry.get("started_at", 0),
                "events": list(entry.get("events") or [])[-_MAX_LOG_LINES:],
                "returncode": entry.get("returncode")
                if entry.get("proc") is None
                else entry["proc"].poll(),
            }
            for pid, entry in items
        }
        stale = [pid for pid in _PROCESS_REGISTRY if pid not in snapshot]
        for pid in stale:
            _PROCESS_REGISTRY.pop(pid, None)
    try:
        tmp_path = _REGISTRY_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, ensure_ascii=False)
        os.replace(tmp_path, _REGISTRY_PATH)
    except OSError as exc:
        LOGGER.warning("Jarayon registry fayli yozilmadi: %s", exc)


def _capture_process_stream(proc: subprocess.Popen, stream, key: str) -> None:
    """Jarayon chiqishini cheklangan buferga oqim bo'yicha yozadi."""
    try:
        for line in iter(stream.readline, ""):
            with _PROCESS_LOCK:
                entry = _PROCESS_REGISTRY.get(str(proc.pid))
                if entry is None:
                    return
                entry["events"].append({"stream": key, "line": line.rstrip()})
            _save_process_registry()
    except Exception as exc:  # o'qish xatosi loglanadi, jim yutilmaydi
        LOGGER.warning("Jarayon %s %s oqimi o'qilmadi: %s", proc.pid, key, exc)
    finally:
        stream.close()
        _save_process_registry()


def tool_run_process(command: str) -> dict:
    """Tizim jarayonini ishga tushiradi va uning chiqishini saqlaydi."""
    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        entry = {
            "proc": proc,
            "command": command,
            "events": deque(maxlen=_MAX_LOG_LINES),
            "started_at": time.time(),
        }
        with _PROCESS_LOCK:
            _PROCESS_REGISTRY[str(proc.pid)] = entry
        capture_threads = []
        for key, stream in (("stdout", proc.stdout), ("stderr", proc.stderr)):
            thread = threading.Thread(
                target=_capture_process_stream,
                args=(proc, stream, key),
                daemon=True,
            )
            thread.start()
            capture_threads.append(thread)
            entry[key + "_thread"] = thread
        # Qisqa umrli jarayonlarda CLI chiqib ketishidan oldin chiqishni yozib olamiz.
        # Uzoq ishlaydigan jarayonlar kutmaydi (faqat qisqa pauza).
        try:
            proc.wait(timeout=0.3)
        except subprocess.TimeoutExpired:
            LOGGER.debug(
                "Jarayon %s 0.3s ichida tugamadi, log oqimi fonda davom etadi",
                proc.pid,
            )
        for thread in capture_threads:
            thread.join(timeout=0.5)
        _save_process_registry()
        return {
            "success": True,
            "tool": "run_process",
            "pid": proc.pid,
            "command": command,
            "message": f"Process started with PID {proc.pid}",
        }
    except Exception as e:
        return {"success": False, "tool": "run_process", "error": str(e)}


def tool_get_logs(pid_or_name: str = None) -> dict:
    """Boshlangan jarayonning haqiqiy stdout/stderr chiqishini qaytaradi."""
    _load_process_registry()
    with _PROCESS_LOCK:
        target = str(pid_or_name).strip() if pid_or_name is not None else ""
        if target:
            entry = _PROCESS_REGISTRY.get(target)
            if entry is None:
                entry = next(
                    (e for e in _PROCESS_REGISTRY.values() if target in e["command"]),
                    None,
                )
            if entry is None:
                return {
                    "success": False,
                    "tool": "get_logs",
                    "target": target,
                    "error": f"Jarayon topilmadi: {target}",
                }
            chosen = [(target, entry)]
        else:
            chosen = list(_PROCESS_REGISTRY.items())

        if not chosen:
            return {
                "success": True,
                "tool": "get_logs",
                "target": "system",
                "logs": "Faol jarayon yo'q.",
                "error_count": 0,
                "processes": [],
            }

        all_events: List[Dict[str, str]] = []
        processes = []
        for key, item in chosen:
            all_events.extend(list(item["events"]))
            processes.append({
                "pid": key,
                "command": item["command"],
                "lines": len(item["events"]),
                "returncode": (
                    item["proc"].poll() if item.get("proc") is not None
                    else item.get("returncode")
                ),
            })

    error_count = sum(
        1 for e in all_events
        if e["stream"] == "stderr" or "error" in e["line"].lower() or "traceback" in e["line"].lower()
    )
    logs = "\n".join(f"[{e['stream']}] {e['line']}" for e in all_events)
    return {
        "success": True,
        "tool": "get_logs",
        "target": target or "all",
        "logs": logs,
        "error_count": error_count,
        "processes": processes,
    }

def _parse_timestamp(value: object) -> Optional[float]:
    """Datetime/ISO/epoch -> epoch soniyasi. Noto'g'ri format -> None."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        return float(raw)
    except ValueError:
        # Soniyalik ko'rinish emas — ISO formatini sinab ko'ramiz.
        LOGGER.debug("Vaqt belgisi son emas, ISO sinovda: %r", raw[:80])
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except ValueError:
        LOGGER.debug("Vaqt belgisi parserlanmadi: %r", raw[:80])
        return None


def _task_started_at() -> Optional[float]:
    """cli_runner vazifani boshlagan vaqt (env orqali uzatiladi)."""
    return _parse_timestamp(os.environ.get("CONDUIT_TASK_STARTED_AT"))


def _fresh_evidence_issue(evidence: dict, screenshot_paths: list) -> Optional[str]:
    """Dalil joriy vazifa boshlanganidan keyin yaratilganini tekshiradi.

    Env belgilanmagan bo'lsa (mustaqil CLI chaqiruv) vaqt nazorati ishlamaydi,
    lekin fayl mavjudligi tekshiruvi doim ishlaydi.
    """
    started = _task_started_at()
    if started is None:
        return None

    captured = None
    for key in ("captured_at", "generated_at", "created_at", "timestamp"):
        if key in evidence:
            captured = _parse_timestamp(evidence[key])
            if captured is not None:
                break
    # 5 soniyalik bardosh: vaqt belgilari/fayl tizimi orasidagi kichik farq.
    if captured is not None and captured < started - 5:
        return "Dalil eski: yaratilgan vaqti joriy vazifa boshlanishidan oldin."

    existing = [p for p in screenshot_paths if isinstance(p, str) and os.path.isfile(p)]
    if existing:
        stale = [p for p in existing if os.path.getmtime(p) < started - 5]
        if stale:
            return f"Dalil eski: {len(stale)} ta fayl joriy vazifadan oldin yaratilgan."
        return None

    if captured is None:
        return "Dalil vaqti ko'rsatilmagan: captured_at yoki mavjud artefakt fayli kerak."
    return None


def tool_check_goal(goal_text: str, evidence_json_str: str = "{}") -> dict:
    """
    Agent-studio-plugin goalEvaluator.js orqali maqsad bajarilganini tekshiradi.
    Faqat dalil (skrinshot + toza loglar) bo'lganda PASS beradi!

    EVIDENCE-MANDATORY: dalil bo'sh bo'lsa yoki ko'rsatilgan skrinshot fayli
    diskda mavjud bo'lmasa PASS qaytarilmaydi — oldin bunday holatlarda ham
    PASS chiqarar edi va agentlar ish qilmay PASS yig'ardi.
    """
    try:
        evidence = json.loads(evidence_json_str) if isinstance(evidence_json_str, str) else evidence_json_str
    except Exception:
        evidence = {"screenshot": str(evidence_json_str)}

    # Bo'sh dalilni aniqlash: dict bo'sh yoki faqat bo'sh qiymatlar.
    def _has_evidence(ev) -> bool:
        if isinstance(ev, list):
            return len(ev) > 0
        if isinstance(ev, dict):
            if not ev:
                return False
            return any(isinstance(v, str) and v.strip() for v in ev.values()) or any(
                not isinstance(v, str) for v in ev.values()
            )
        return bool(str(ev).strip())

    evidence_present = _has_evidence(evidence)
    if not evidence_present:
        # ESKI XATO: bo'sh dalil bo'lsa test_screenshot.png / latest.png kabi
        # oldingi vazifalardan qolgan fayllarga tashlanar va ularni "yangi dalil"
        # deb PASS qaytarar edi. Endi buning aksi: dalilsiz hech qachon PASS yo'q.
        return {
            "success": True,
            "tool": "check_goal",
            "verdict": "FAIL",
            "goal": goal_text,
            "issues": ["Dalil taqdim etilmadi (bo'sh evidence). Eski fayllar dalil hisoblanmaydi."],
            "checks": ["Dalilsiz PASS berilmaydi: avval screenshot yoki boshqa artefakt yaratib, yo'lini evidence'ga kiriting."],
            "evidence_summary": "Dalil yo'q.",
        }

    # Ko'rsatilgan skrinshot fayllari HAQIQATAN diskda borligini tekshiramiz.
    # Faqat bo'sh qiymatlarni tekshirish etarli emas: {"screenshot": "test.png"}
    # to'ldirilgan ko'rinadi, lekin fayl yo'q — bu holatda evaluator PASS berardi.
    screenshots = evidence.get("screenshots") if isinstance(evidence, dict) else None
    if screenshots is None and isinstance(evidence, dict):
        screenshots = evidence.get("screenshot")
    if isinstance(screenshots, str):
        screenshots = [screenshots]
    if not isinstance(screenshots, list):
        screenshots = []

    def _evidence_file_exists(path: object) -> bool:
        if not isinstance(path, str) or not path.strip():
            return False
        p = path.strip()
        if p.startswith(("http://", "https://", "data:")):
            return True  # URL/data-URI — evaluator o'zi tekshiradi
        if os.path.isfile(p):
            return True
        # Nisbiy nom skrinshotlar papkasida saqlangan bo'lishi mumkin
        return os.path.isfile(os.path.join(get_static_screenshots_dir(), p))

    missing_files = [p for p in screenshots if not _evidence_file_exists(p)]
    if missing_files:
        return {
            "success": True,
            "tool": "check_goal",
            "verdict": "FAIL",
            "goal": goal_text,
            "issues": [f"Dalil fayli topilmadi: {p}" for p in missing_files],
            "checks": ["Dalil (skrinshot) fayli mavjud bo'lmagani uchun PASS berilmaydi."],
            "evidence_summary": f"{len(missing_files)} ta dalil fayli diskda topilmadi."
        }

    fresh_issue = _fresh_evidence_issue(evidence if isinstance(evidence, dict) else {}, screenshots)
    if fresh_issue:
        return {
            "success": True,
            "tool": "check_goal",
            "verdict": "FAIL",
            "goal": goal_text,
            "issues": [fresh_issue],
            "checks": ["Faqat joriy vazifa davomida yaratilgan dalil PASS bo'lishi mumkin."],
            "evidence_summary": fresh_issue,
        }

    try:
        sys.path.insert(0, PLUGIN_SRC)
        from agent_studio.tools.goal import check_goal as as_check_goal
        res = as_check_goal(goal_text, evidence)
        verdict = res.get("verdict", "PASS")
        if not evidence_present and verdict == "PASS":
            # Dalilsiz PASS — rubber-stamp. Haqiqiy holat: tekshiruv o'tkazilmadi.
            verdict = "NEEDS_INSPECTION"
            res = dict(res)
            res["warnings"] = list(res.get("warnings", [])) + [
                "Dalil (screenshot/log/fayl) taqdim etilmadi — PASS dalilsiz qabul qilinmaydi."
            ]
        return {
            "success": True,
            "tool": "check_goal",
            "verdict": verdict,
            "goal": res.get("goal", goal_text),
            "issues": res.get("blockers", []),
            "checks": res.get("warnings", []),
            "evidence_summary": res.get("summary", "")
        }
    except Exception as exc:
        # Jim o'tib yubormaslik: import/plugin xatosini ko'rinadigan qilamiz,
        # so'ng Node evaluator'ga qaytamiz.
        LOGGER.warning("check_goal: agent_studio plugin ishlamadi (%s), Node evaluator sinovda", exc)

    node_script = f"""
    const {{ checkGoal }} = require('{PLUGIN_LIB.replace(chr(92), '/')}/goalEvaluator.js');
    try {{
        const goal = process.argv[1];
        const ev = JSON.parse(process.argv[2]);
        const res = checkGoal(goal, ev);
        console.log(JSON.stringify({{
            success: true,
            tool: "check_goal",
            verdict: res.verdict,
            goal: res.goal,
            issues: res.issues || [],
            checks: res.checks,
            evidence_summary: res.evidence_summary
        }}));
    }} catch(e) {{
        console.log(JSON.stringify({{ success: false, tool: "check_goal", error: e.message }}));
    }}
    """
    res = run_node_eval(node_script, [goal_text, json.dumps(evidence)])
    if not evidence_present and res.get("verdict") == "PASS":
        # Node evaluator ham bo'sh dalilni rubber-stamp qilmasligi shart
        res = dict(res)
        res["verdict"] = "NEEDS_INSPECTION"
        checks = list(res.get("checks") or [])
        checks.append("Dalil (screenshot/log/fayl) taqdim etilmadi — PASS dalilsiz qabul qilinmaydi.")
        res["checks"] = checks
    return res

def tool_blender_headless(script_code: str, model_name: str = "3d_scene", agent_id: str = "sculptor") -> dict:
    """Blender headless 3D sahnasini shakllantiradi va render oladi."""
    try:
        import app_adapter
        return app_adapter.execute_blender_headless(script_code, model_name=model_name, agent_id=agent_id)
    except Exception as e:
        return {"success": False, "tool": "blender_headless_exec", "error": str(e)}

def tool_run_script(subagent: str, script_name: str, code: str = None, language: str = "python") -> dict:
    """Subagentning xavfsiz muhiti chegarasida skript yaratadi va ishga tushiradi."""
    try:
        import app_adapter
        if not code:
            code = f"# Auto-generated {language} script by {subagent}\nprint('Execution verified in workspace.')\n"
        return app_adapter.run_isolated_script(subagent, script_name, code, language=language)
    except Exception as e:
        return {"success": False, "tool": "runScript", "error": str(e)}

def tool_figma_sync(file_key: str = "", requirement: str = "") -> dict:
    """Figma REST API'dan haqiqiy fayl ma'lumotlarini oladi.

    Token yoki file key yo'q bo'lsa `needs_config` qaytaradi; soxta spec yo'q.
    """
    try:
        import app_adapter
        return app_adapter.get_figma_project_info(file_key, requirement)
    except Exception as e:
        return {"success": False, "tool": "figma_sync", "error": str(e)}


def _agent_out_dir(agent_id: str) -> str:
    """Artefaktlarni chaqiruvchi agentning o'z workspace'iga saqlash.

    Backend'da ishlaganda workspace_manager orqali absolut yo'l; workspace'ga
    ko'chirilgan nusxada (tools.py standalone) loyiha ildizini __file__ dan
    topamiz. Nisbiy fallback ishlatilmaydi — aks holda CWD'ga bog'liq holda
    workspaces/<agent>/workspaces/<boshqa>/ kabi ichma-ich noto'ri papkalar
    yaratilardi.
    """
    try:
        import workspace_manager
        return workspace_manager.get_agent_workspace(agent_id)
    except Exception:
        # tools.py loyihada workspaces/<agent>/tools.py sifatida yashaydi:
        # ildiz = o'z papkasidan ikki pog'ona yuqorida.
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, "workspaces", agent_id)


def tool_gen_image(prompt: str, width: int = 512, height: int = 512, style: str = "auto", output_path: str = None, agent_id: str = "painter") -> dict:
    """Talab matnidan shakl/rang/son olib, deterministik haqiqiy PNG yaratadi.

    Endi tasodifiy grid chizilmaydi: foydalanuvchi "qizil kub" desa qizil kub,
    "3 ta ko'k shar" desa uchta ko'k shar chiziladi. Artefakt izlanadigan bo'lishi
    uchun talab matni pastki qismda yoziladi.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return {"success": False, "tool": "gen_image", "error": "PIL o'rnatilmagan"}

    if not (prompt or "").strip():
        return {"success": False, "tool": "gen_image", "error": "Prompt bo'sh"}

    width = max(64, min(2048, int(width)))
    height = max(64, min(2048, int(height)))
    seed = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)

    import app_adapter
    spec = app_adapter.parse_visual_spec(prompt)
    colors = [tuple(int(value[i:i + 2], 16) for i in (1, 3, 5)) for value in spec["colors"]]
    bg_hex = spec["background"].lstrip("#")
    background = tuple(int(bg_hex[i:i + 2], 16) for i in (0, 2, 4))

    img = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(img)

    def shade(color_tuple, factor):
        return tuple(max(0, min(255, int(c * factor))) for c in color_tuple)

    count = max(1, min(12, int(spec["count"])))
    shape_names = spec["shapes"]
    for index in range(count):
        shape = shape_names[index % len(shape_names)]
        color = colors[index % len(colors)]
        margin = max(20, width // 10)
        cell_w = (width - 2 * margin) / max(count, 1)
        cx = int(margin + cell_w * (index + 0.5))
        cy = height // 2 + rng.randint(-height // 12, height // 12)
        r = int(min(cell_w, height) * 0.34)
        outline = tuple(min(255, c + 40) for c in color)
        line_w = max(2, width // 180)
        if shape in ("sphere", "shar"):
            # Soddalashtirilgan soya: markazga qarab yorug'roq halqalar.
            for step in range(6, 0, -1):
                rr = max(2, int(r * step / 6))
                tone = 0.82 + 0.18 * (6 - step) / 6
                draw.ellipse(
                    [cx - rr, cy - rr, cx + rr, cy + rr],
                    fill=shade(color, tone),
                )
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=outline, width=line_w)
        else:
            # Kub: old yuz + yuqori va yon tomon soyalari.
            draw.rectangle([cx - r, cy - r, cx + r, cy + r], fill=color, outline=outline, width=line_w)
            dx = max(6, r // 3)
            draw.polygon(
                [(cx - r, cy - r), (cx - r + dx, cy - r - dx), (cx + r + dx, cy - r - dx), (cx + r, cy - r)],
                fill=shade(color, 1.28),
                outline=outline,
            )
            draw.polygon(
                [(cx + r, cy - r), (cx + r + dx, cy - r - dx), (cx + r + dx, cy + r - dx), (cx + r, cy + r)],
                fill=shade(color, 0.68),
                outline=outline,
            )

    if spec["material"] in ("metal", "glass"):
        draw.line([(width // 8, height // 4), (width - width // 8, height // 4)], fill=(255, 255, 255), width=max(2, width // 200))

    try:
        font = ImageFont.truetype("arial.ttf", max(16, height // 18))
    except OSError:
        font = ImageFont.load_default()
    label = (spec["text"] or prompt)[:60]
    tw = int(draw.textlength(label, font=font))
    th = getattr(font, "size", 16)
    pad = max(6, height // 40)
    x0 = max(pad, (width - tw) // 2 - pad)
    y0 = max(pad, height - th - 2 * pad)
    draw.rectangle([x0 - pad, y0 - pad, x0 + tw + pad, height - pad], fill=(0, 0, 0))
    draw.text((x0, y0), label, fill=(255, 255, 255), font=font)

    out_dir = output_path and os.path.dirname(output_path)
    if not out_dir:
        out_dir = _agent_out_dir(agent_id)
    os.makedirs(out_dir, exist_ok=True)
    fname = os.path.basename(output_path) if output_path else f"gen_{seed % 100000}.png"
    if not fname.lower().endswith((".png", ".jpg")):
        fname += ".png"
    final_path = os.path.join(out_dir, fname)
    img.save(final_path)

    res = {
        "success": True,
        "tool": "gen_image",
        "prompt": prompt[:120],
        "spec": spec,
        "image_path": os.path.abspath(final_path),
        "width": width,
        "height": height,
        "seed": seed % 100000,
        "bytes": os.path.getsize(final_path),
    }
    # Dashboard preview uchun statik nusxa.
    try:
        static_dir = get_static_screenshots_dir()
        os.makedirs(static_dir, exist_ok=True)
        dest = os.path.join(static_dir, f"painter_{fname}")
        shutil.copyfile(final_path, dest)
        shutil.copyfile(dest, os.path.join(static_dir, "latest.png"))
        res["web_preview_url"] = f"/static/screenshots/painter_{fname}"
    except Exception as exc:
        LOGGER.debug("Painter preview nusxalanmadi: %s: %s", type(exc).__name__, exc)
    return res


def _ffmpeg_path() -> Optional[str]:
    return shutil.which("ffmpeg")


VIDEO_EXTENSIONS = ("mp4", "mov", "mkv", "webm", "avi", "m4v")
_AUDIO_EXTENSIONS = ("mp3", "wav", "aac", "m4a", "flac", "ogg")


def extract_media_paths(text: str, extensions: tuple = VIDEO_EXTENSIONS) -> list:
    """Vazifa matnidan haqiqiy media fayl yo'llarini ajratadi."""
    if not text:
        return []
    ext = "|".join(extensions)
    pattern = re.compile(
        r"(?:[A-Za-z]:[\\/]|[\w.\-]+[\\/])*[\w.\-]+\.(?:" + ext + r")\b",
        re.IGNORECASE,
    )
    found = []
    for match in pattern.finditer(text):
        path = match.group(0).strip().strip("\"'`,;()")
        if path not in found:
            found.append(path)
    return found


def _probe_video_frames(video_path: str) -> int:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return 0
    try:
        proc = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=nb_frames", "-of", "csv=p=0", video_path],
            capture_output=True, text=True, timeout=30,
        )
        return int(str(proc.stdout).strip().splitlines()[0]) if proc.returncode == 0 and proc.stdout.strip() else 0
    except (ValueError, IndexError, subprocess.SubprocessError) as exc:
        LOGGER.warning("Video kadrlari aniqlanmadi (%s): %s", type(exc).__name__, exc)
        return 0


def tool_video_render(spec: str, duration: float = 3.0, output_path: str = None,
                      fmt: str = "mp4", inputs: list = None, audio_path: str = None) -> dict:
    """Haqiqiy kirish videolaridan FFmpeg bilan montaj qiladi.

    `spec` ichidagi video fayl yo'llari yoki `inputs` ishlatiladi. Kirish
    fayli bo'lmasa soxta gradient yaratilmaydi — halol FAIL qaytariladi.
    """
    ffmpeg = _ffmpeg_path()
    if not ffmpeg:
        return {
            "success": False,
            "tool": "video_render",
            "error": "FFmpeg topilmadi (PATH'da yo'q). O'rnatish: winget install Gyan.FFmpeg",
        }
    if not (spec or "").strip():
        return {"success": False, "tool": "video_render", "error": "Spec bo'sh"}

    candidates = list(inputs or []) + extract_media_paths(spec)
    sources = []
    for path in candidates:
        if not isinstance(path, str) or not path.strip():
            continue
        p = path.strip().strip("\"'`,;()")
        if p.startswith(("http://", "https://")) or p in sources:
            continue
        sources.append(p)
    valid = [p for p in sources if os.path.isfile(p) and os.path.getsize(p) > 0]
    if not valid:
        return {
            "success": False,
            "tool": "video_render",
            "error": (
                "Haqiqiy montaj uchun kamida bitta mavjud kirish video fayli kerak. "
                f"Topilmadi: {sources[:3] or 'yo‘q'}. Soxta gradient video yaratilmaydi."
            ),
            "input_candidates": sources[:10],
        }

    workdir = output_path and os.path.dirname(output_path) or _agent_out_dir("editor")
    os.makedirs(workdir, exist_ok=True)
    out_name = os.path.basename(output_path) if output_path else "montage.mp4"
    if not out_name.endswith((".mp4", ".gif")):
        out_name += ".mp4"
    out_path = os.path.join(workdir, out_name)

    fps = 24
    max_seconds = max(float(duration or 0), 0.0)
    filters = []
    for idx in range(len(valid)):
        trim = f"trim=start=0:end={max_seconds},setpts=PTS-STARTPTS," if max_seconds > 0 else "setpts=PTS-STARTPTS,"
        filters.append(f"[{idx}:v]{trim}fps={fps},scale=1280:720:force_original_aspect_ratio=decrease,"
                       f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[v{idx}]")
    # Har bir trim zanjirining chiqishi [vN] bilan belgilangan; concat ularni
    # shu tartibda iste'mol qiladi. Yana [vN] qo'shish "trailing garbage" beradi.
    concat_inputs = "".join(f"[v{i}]" for i in range(len(valid)))
    concat = f"{concat_inputs}concat=n={len(valid)}:v=1:a=0[outv]"

    cmd = [ffmpeg, "-y"]
    for p in valid:
        cmd += ["-i", p]
    audio_source = None
    if audio_path and os.path.isfile(audio_path) and os.path.getsize(audio_path) > 0:
        audio_source = audio_path
        cmd += ["-i", audio_path]
    cmd += ["-filter_complex", ";".join(filters) + ";" + concat, "-map", "[outv]"]
    if audio_source:
        cmd += ["-map", f"{len(valid)}:a", "-c:a", "aac", "-shortest"]
    if out_name.endswith(".gif"):
        cmd += ["-loop", "0", out_path]
    else:
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.SubprocessError as exc:
        return {"success": False, "tool": "video_render", "error": f"FFmpeg ishga tushmadi: {exc}"}
    if proc.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        return {"success": False, "tool": "video_render", "error": (proc.stderr or "ffmpeg xato")[-600:]}

    res = {
        "success": True,
        "tool": "video_render",
        "spec": spec[:120],
        "inputs": [os.path.abspath(p) for p in valid],
        "audio": os.path.abspath(audio_source) if audio_source else None,
        "video_path": os.path.abspath(out_path),
        "frames": _probe_video_frames(out_path),
        "fps": fps,
        "bytes": os.path.getsize(out_path),
    }
    try:
        from PIL import Image
        static_dir = get_static_screenshots_dir()
        os.makedirs(static_dir, exist_ok=True)
        Image.open(_first_frame_of(out_path, workdir)).save(os.path.join(static_dir, "editor_preview.png"))
        shutil.copyfile(os.path.join(static_dir, "editor_preview.png"), os.path.join(static_dir, "latest.png"))
        res["web_preview_url"] = "/static/screenshots/editor_preview.png"
    except Exception as exc:
        LOGGER.warning("Editor preview nusxalanmadi: %s: %s", type(exc).__name__, exc)
    return res


def _first_frame_of(video_path: str, workdir: str) -> str:
    ffmpeg = _ffmpeg_path()
    frame = os.path.join(workdir, "_preview.png")
    subprocess.run([ffmpeg, "-y", "-i", video_path, "-frames:v", "1", frame],
                   capture_output=True, timeout=30)
    return frame


def tool_anim_render(keyframes_json: str, duration: float = 2.0, output_path: str = None) -> dict:
    """Keyframe JSON'dan haqiqiy animatsiya (GIF) render qiladi.

    keyframes_json — masalan: '[{"t":0,"color":"#101828"},{"t":1,"color":"#38bdf8"}]'
    yoki fayl yo'li. Keyframe'lar orasida rang/joy interpolatsiya qilinadi.
    """
    ffmpeg = _ffmpeg_path()
    if not ffmpeg:
        return {"success": False, "tool": "anim_render", "error": "FFmpeg topilmadi (PATH'da yo'q)"}
    try:
        from PIL import Image, ImageDraw
        import colorsys
    except ImportError:
        return {"success": False, "tool": "anim_render", "error": "PIL o'rnatilmagan"}

    raw = keyframes_json
    if raw and os.path.exists(raw):
        raw = open(raw, "r", encoding="utf-8").read()
    try:
        kfs = json.loads(raw) if raw else []
    except Exception:
        return {"success": False, "tool": "anim_render", "error": "Keyframe JSON noto'g'ri"}
    if not isinstance(kfs, list) or not kfs:
        kfs = [{"t": 0, "color": "#101828"}, {"t": 1, "color": "#38bdf8"}]

    fps = 12
    frames = max(int(duration * fps), fps)
    workdir = output_path and os.path.dirname(output_path) or _agent_out_dir("animator")
    os.makedirs(workdir, exist_ok=True)
    frames_dir = os.path.join(workdir, "_anim")
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir, exist_ok=True)

    def _parse_color(c) -> tuple:
        if isinstance(c, (list, tuple)) and len(c) >= 3:
            return tuple(int(v) for v in c[:3])
        s = str(c).lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        try:
            return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
        except Exception:
            return (16, 24, 40)

    stops = sorted(((float(k.get("t", 0)) % 1.0 or 0.0, _parse_color(k.get("color"))) for k in kfs), key=lambda p: p[0])
    W, H = 480, 270
    for i in range(frames):
        t = i / frames
        # Keyframe'lar orasida interpolatsiya.
        col = stops[0][1]
        for (t0, c0), (t1, c1) in zip(stops, stops[1:] + [(1.0, stops[0][1])]):
            if t0 <= t <= t1:
                span = max(t1 - t0, 1e-6)
                k = (t - t0) / span
                col = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
                break
        img = Image.new("RGB", (W, H), col)
        d = ImageDraw.Draw(img)
        # Keyframe vaqtlarida belgi chizamiz.
        for idx, (kt, _) in enumerate(stops):
            x = int(W * kt)
            d.ellipse([x - 6, H // 2 - 6, x + 6, H // 2 + 6], fill=(255, 255, 255))
        # Vaqt chizig'i.
        d.line([(0, H - 20), (int(W * t), H - 20)], fill=(255, 255, 255), width=4)
        img.save(os.path.join(frames_dir, f"a_{i:05d}.png"))

    out_name = os.path.basename(output_path) if output_path else "animation.gif"
    if not out_name.endswith((".gif", ".mp4")):
        out_name += ".gif"
    out_path = os.path.join(workdir, out_name)
    cmd = [ffmpeg, "-y", "-framerate", str(fps), "-i", os.path.join(frames_dir, "a_%05d.png")]
    if out_name.endswith(".gif"):
        cmd += ["-loop", "0", out_path]
    else:
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    shutil.rmtree(frames_dir, ignore_errors=True)
    if proc.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        return {"success": False, "tool": "anim_render", "error": (proc.stderr or "ffmpeg xato")[:300]}

    return {
        "success": True,
        "tool": "anim_render",
        "keyframes": len(kfs),
        "frames": frames,
        "animation_path": os.path.abspath(out_path),
        "bytes": os.path.getsize(out_path),
    }


def tool_notion_api(action: str = "search", payload: str = "") -> dict:
    """Notion API. NOTION_TOKEN env bo'lsa haqiqiy so'rov, bo'lmasa halol xato."""
    token = os.environ.get("NOTION_TOKEN", "").strip()
    if not token:
        return {
            "success": False,
            "tool": "notion_api",
            "error": "NOTION_TOKEN sozlanmagan. Sozlash: NOTION_TOKEN=secret-... env qo'shing (notion.so/my-integrations).",
            "configured": False,
        }
    import urllib.request

    url = "https://api.notion.com/v1/databases" if action == "search" else f"https://api.notion.com/v1/{action}"
    body = json.dumps({"page_size": 5} if action == "search" else {}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", "2022-06-28")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {"success": True, "tool": "notion_api", "action": action, "results": len(data.get("results", []))}
    except Exception as exc:
        return {"success": False, "tool": "notion_api", "error": str(exc)[:200], "configured": True}


def tool_slack_api(action: str = "post", channel: str = "", text: str = "Conduit xabari") -> dict:
    """Slack API. SLACK_BOT_TOKEN env bo'lsa haqiqiy xabar, bo'lmasa halol xato."""
    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if not token:
        return {
            "success": False,
            "tool": "slack_api",
            "error": "SLACK_BOT_TOKEN sozlanmagan. Sozlash: api.slack.com/apps -> Bot Token.",
            "configured": False,
        }
    import urllib.request
    import urllib.parse

    data = urllib.parse.urlencode({"channel": channel or "#general", "text": text[:500]}).encode("utf-8")
    req = urllib.request.Request("https://slack.com/api/chat.postMessage", data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        ok = bool(data.get("ok"))
        return {"success": ok, "tool": "slack_api", "error": data.get("error", "") if not ok else ""}
    except Exception as exc:
        return {"success": False, "tool": "slack_api", "error": str(exc)[:200], "configured": True}


def tool_web_search(query: str, limit: int = 5) -> dict:
    """DuckDuckGo orqali veb qidiruv (API kalitisiz, HTML parse).

    scout uchun: aniq URL ochish o'rniga haqiqiy qidiruv natijalarini qaytaradi.
    """
    if not (query or "").strip():
        return {"success": False, "tool": "web_search", "error": "So'rov bo'sh"}
    try:
        import httpx
    except ImportError:
        return {"success": False, "tool": "web_search", "error": "httpx o'rnatilmagan"}

    try:
        resp = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Conduit/1.0"},
            timeout=20.0,
            follow_redirects=True,
        )
        html = resp.text
    except Exception as exc:
        return {"success": False, "tool": "web_search", "error": str(exc)[:200]}

    # HTML'dan natijalarni ajratib olamiz (ddg html layout).
    import re
    results = []
    for m in re.finditer(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S
    ):
        url = m.group(1)
        # DDG redirect URL'larini tozalash.
        uddg = re.search(r"uddg=([^&]+)", url)
        if uddg:
            from urllib.parse import unquote
            url = unquote(uddg.group(1))
        title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if title and url.startswith("http"):
            results.append({"title": title[:120], "url": url[:300]})
        if len(results) >= max(1, min(10, limit)):
            break

    if not results:
        return {
            "success": False,
            "tool": "web_search",
            "error": "Natija topilmadi yoki HTML formati o'zgargan",
            "query": query[:120],
        }
    return {"success": True, "tool": "web_search", "query": query[:120], "results": results}


def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() in ("--help", "-h", "help", "list_tools", "list"):
        print(json.dumps({
            "success": True,
            "tool": "list_tools",
            "usage": "python tools.py <tool> [args...]  |  python tools.py list_tools",
            "tools": list_tools(),
        }, indent=2, ensure_ascii=False))
        return

    raw_cmd = sys.argv[1]
    cmd = canonical_tool_name(raw_cmd)
    args = sys.argv[2:]
    if not cmd:
        print(json.dumps({
            "success": False,
            "tool": "unknown",
            "error": f"Noma'lum tool: '{raw_cmd}'. Ruxsat etilgan toollar: {', '.join(t[0] for t in TOOL_SPECS)}",
            "tools": [t[0] for t in TOOL_SPECS],
        }, ensure_ascii=False))
        sys.exit(1)

    # Real darvoza: agent tomonidan chaqirilganda role.md allowlist shu yerda
    # tekshiriladi. cli_runner'dagi matn skaneri faqat qo'shimcha himoya.
    agent_id = os.environ.get("CONDUIT_AGENT", "").strip()
    if agent_id:
        try:
            import security_guard
            security_guard.verify_tool_access(agent_id, cmd)
        except Exception as exc:
            print(json.dumps({
                "success": False,
                "tool": cmd,
                "error": str(exc),
            }, ensure_ascii=False))
            sys.exit(2)

    result = {}
    if cmd == "screenshot":
        url = args[0] if args else "http://localhost:3000"
        out_path = args[1] if len(args) > 1 else None
        result = tool_screenshot(url, out_path)
    elif cmd == "interact_web":
        url = args[0] if args else "http://localhost:3000"
        result = tool_interact_web(url)
    elif cmd in ["web_search", "search"]:
        query = " ".join(args) if args else "conduit ai studio"
        limit = 5
        result = tool_web_search(query, limit)
    elif cmd == "run_process":
        command = " ".join(args) if args else "echo ok"
        result = tool_run_process(command)
    elif cmd == "get_logs":
        target = args[0] if args else None
        result = tool_get_logs(target)
    elif cmd == "check_goal":
        goal = args[0] if args else "Verify UI execution"
        evidence_str = args[1] if len(args) > 1 else "{}"
        result = tool_check_goal(goal, evidence_str)
    elif cmd in ["blender_headless_exec", "blender", "sculpt"]:
        code = args[0] if args else "import bpy\nbpy.ops.mesh.primitive_cube_add()"
        model = args[1] if len(args) > 1 else "cube_model"
        result = tool_blender_headless(code, model)
    elif cmd in ["blender_video", "blender_anim"]:
        # Haqiqiy Blender video render: skript fayli workspace'da bo'lishi kerak.
        # Masalan: python tools.py blender_video spin_scene.py my_video.mp4 24
        script_file = args[0] if args else ""
        out_name = args[1] if len(args) > 1 else "blender_video.mp4"
        fps = int(args[2]) if len(args) > 2 else 24
        if not script_file or not os.path.isfile(script_file):
            result = {"success": False, "tool": "blender_video",
                      "error": f"Skript fayl topilmadi: '{script_file}'. Avval bpy skriptni workspace'ga yozing (frame_start/frame_end o'rnatilgan bo'lishi shart)."}
        else:
            from app_adapter import execute_blender_video
            out_path = os.path.join(os.path.dirname(os.path.abspath(script_file)), out_name)
            with open(script_file, encoding="utf-8") as _sf:
                _code = _sf.read()
            result = execute_blender_video(_code, out_path, fps=fps,
                                           agent_id=os.environ.get("CONDUIT_AGENT", "sculptor"))
    elif cmd in ["runscript", "run_script"]:
        subagent = args[0] if args else "sculptor"
        s_name = args[1] if len(args) > 1 else "script.py"
        code = args[2] if len(args) > 2 else "print('Script executed')"
        result = tool_run_script(subagent, s_name, code)
    elif cmd in ["figma_sync", "figma"]:
        f_key = args[0] if args else ""
        requirement = args[1] if len(args) > 1 else spec
        result = tool_figma_sync(f_key, requirement)
    elif cmd in ["gen_image", "genimage", "paint"]:
        prompt = args[0] if args else "abstract art"
        width = int(args[1]) if len(args) > 1 else 512
        height = int(args[2]) if len(args) > 2 else 512
        out_path = args[3] if len(args) > 3 else None
        result = tool_gen_image(prompt, width, height, output_path=out_path)
    elif cmd in ["video_render", "video"]:
        spec = args[0] if args else "clip1.mp4 clip2.mp4"
        duration = float(args[1]) if len(args) > 1 else 0.0
        audio = args[2] if len(args) > 2 else None
        result = tool_video_render(spec, duration, audio_path=audio)
    elif cmd in ["anim_render", "animate"]:
        kfs = args[0] if args else ''
        duration = float(args[1]) if len(args) > 1 else 2.0
        result = tool_anim_render(kfs, duration)
    elif cmd in ["notion_api", "notion"]:
        result = tool_notion_api(args[0] if args else "search")
    elif cmd in ["slack_api", "slack"]:
        result = tool_slack_api(args[0] if args else "post", args[1] if len(args) > 1 else "", args[2] if len(args) > 2 else "Conduit xabari")
    else:
        result = {
            "success": False,
            "error": f"Noma'lum tool: '{cmd}'. Ruxsat etilgan toollar: screenshot, interact_web, run_process, get_logs, check_goal, blender_headless_exec, runScript, figma_sync, gen_image, video_render, anim_render, notion_api, slack_api"
        }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
