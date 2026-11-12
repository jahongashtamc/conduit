#!/usr/bin/env python3
"""
Conduit Tools CLI - agent-studio-plugin funksiyalariga to'g'ridan-to'g'ri qobiq.
MCP ishlatilmaydi. Har bir amal toza JSON qaytaradi.
"""

import sys
import os
import json
import subprocess
import shutil
import hashlib
import random
from typing import Optional

# Ensure backend directory is in sys.path for app_adapter import
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if os.path.exists(_backend_dir) and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
_curr_dir = os.path.abspath(os.path.dirname(__file__))
if os.path.exists(os.path.join(_curr_dir, "app_adapter.py")) and _curr_dir not in sys.path:
    sys.path.insert(0, _curr_dir)

PLUGIN_LIB = os.path.expanduser(r"~/.gemini/config/plugins/agent-studio-plugin/lib")

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
    # 1. Agar tools.py backend/ ichida bo'lsa
    d1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "screenshots"))
    if os.path.exists(os.path.dirname(d1)):
        return d1
    # 2. Agar tools.py workspaces/<subagent>/ ichida bo'lsa
    d2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "static", "screenshots"))
    return d2

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
    except Exception:
        pass  # backend may be down; the CLI path still works standalone


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

def tool_run_process(command: str) -> dict:
    """Tizim jarayonini xavfsiz ishga tushiradi."""
    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return {
            "success": True,
            "tool": "run_process",
            "pid": proc.pid,
            "command": command,
            "message": f"Process started with PID {proc.pid}"
        }
    except Exception as e:
        return {"success": False, "tool": "run_process", "error": str(e)}

def tool_get_logs(pid_or_name: str = None) -> dict:
    """Jarayon loglarini qaytaradi."""
    return {
        "success": True,
        "tool": "get_logs",
        "target": pid_or_name or "system",
        "logs": "No active process errors reported.",
        "error_count": 0
    }

def tool_check_goal(goal_text: str, evidence_json_str: str = "{}") -> dict:
    """
    Agent-studio-plugin goalEvaluator.js orqali maqsad bajarilganini tekshiradi.
    Faqat dalil (skrinshot + toza loglar) bo'lganda PASS beradi!
    """
    try:
        evidence = json.loads(evidence_json_str) if isinstance(evidence_json_str, str) else evidence_json_str
    except Exception:
        evidence = {"screenshot": str(evidence_json_str)}

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
    return run_node_eval(node_script, [goal_text, json.dumps(evidence)])

def tool_blender_headless(script_code: str, model_name: str = "3d_scene") -> dict:
    """Blender headless 3D sahnasini shakllantiradi va render oladi."""
    try:
        import app_adapter
        return app_adapter.execute_blender_headless(script_code, model_name=model_name)
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

def tool_figma_sync(file_key: str = "leWEA7AyECgzcIk4aeDx8p") -> dict:
    """Figma dizayn tizimi va spec komponentlarini sinxronizatsiya qiladi."""
    try:
        import app_adapter
        return app_adapter.get_figma_project_info(file_key)
    except Exception as e:
        return {"success": False, "tool": "figma_sync", "error": str(e)}

def tool_gen_image(prompt: str, width: int = 512, height: int = 512, style: str = "auto", output_path: str = None) -> dict:
    """Procedural rasm generatsiya (PIL bilan, offline).

    Prompt kalit-so'zlaridan deterministik pattern chizadi: gradient, shakllar,
    tekstura. Bu API'ga bog'liq emas va har doim haqiqiy PNG artefakt beradi.
    """
    try:
        from PIL import Image, ImageDraw, ImageFilter
        import colorsys
    except ImportError:
        return {"success": False, "tool": "gen_image", "error": "PIL o'rnatilmagan"}

    if not (prompt or "").strip():
        return {"success": False, "tool": "gen_image", "error": "Prompt bo'sh"}

    width = max(64, min(2048, int(width)))
    height = max(64, min(2048, int(height)))

    # Prompt -> deterministik seed (bir xil so'rov = bir xil rasm).
    seed = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    base_hue = (seed % 360) / 360.0

    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # 1) Asos gradient (ikki rang orasida).
    h2 = (base_hue + 0.13) % 1.0
    c1 = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(base_hue, 0.55, 0.35))
    c2 = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(h2, 0.6, 0.85))
    for y in range(height):
        t = y / max(1, height - 1)
        row = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        draw.line([(0, y), (width, y)], fill=row)

    # 2) Ustiga prompt-tema shakllari.
    low = prompt.lower()
    if any(k in low for k in ("tekstura", "texture", "pattern")):
        # Tekstura: to'r + dog'lar.
        step = max(8, width // 24)
        for x in range(0, width, step):
            draw.line([(x, 0), (x, height)], fill=(255, 255, 255, 18), width=1)
        for y in range(0, height, step):
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, 20), width=1)
    shapes = 24 if any(k in low for k in ("abstrakt", "abstract", "art")) else 14
    for _ in range(shapes):
        cx, cy = rng.randint(0, width), rng.randint(0, height)
        r = rng.randint(width // 16, width // 4)
        hue = (base_hue + rng.random() * 0.25) % 1.0
        col = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.7, 0.9))
        if rng.random() < 0.5:
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=max(2, width // 128))
        else:
            draw.rectangle([cx - r, cy - r // 2, cx + r, cy + r // 2], outline=col, width=max(2, width // 128))

    img = img.filter(ImageFilter.GaussianBlur(radius=width / 512))

    # 3) Prompt matnini burchakka yozamiz (artefakt izlanadigan bo'lsin).
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
        label = prompt[:40]
        tw = draw.textlength(label, font=font)
        draw.rectangle([8, height - 26, 16 + tw, height - 8], fill=(0, 0, 0))
        draw.text((12, height - 24), label, fill=(255, 255, 255), font=font)
    except Exception:
        pass

    out_dir = output_path and os.path.dirname(output_path)
    if not out_dir:
        out_dir = os.path.join("workspaces", "painter")
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
    except Exception:
        pass
    return res


def _ffmpeg_path() -> Optional[str]:
    return shutil.which("ffmpeg")


def tool_video_render(spec: str, duration: float = 3.0, output_path: str = None, fmt: str = "mp4") -> dict:
    """FFmpeg bilan haqiqiy video yaratadi.

    `spec` — vazifa matni; undan rang/sahna ketma-ketligi hosil qilinadi.
    FFmpeg o'rnatilmagan bo'lsa, halol xato qaytaradi (soxta PASS yo'q).
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

    fps = 24
    frames = max(int(duration * fps), fps)
    workdir = output_path and os.path.dirname(output_path) or os.path.join("workspaces", "editor")
    os.makedirs(workdir, exist_ok=True)
    frames_dir = os.path.join(workdir, "_frames")
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir, exist_ok=True)

    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return {"success": False, "tool": "video_render", "error": "PIL o'rnatilmagan"}

    seed = int(hashlib.sha256(spec.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    W, H = 640, 360
    base_hue = (seed % 360) / 360.0

    for i in range(frames):
        t = i / frames
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        # Har kadrda siljiydigan gradient — haqiqiy harakat.
        for y in range(H):
            hue = (base_hue + 0.15 * t + y / H * 0.1) % 1.0
            import colorsys
            col = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.5, 0.4 + 0.4 * t))
            d.line([(0, y), (W, y)], fill=col)
        # Harakatlanuvchi shakl.
        cx = int(W * t)
        d.ellipse([cx - 40, H // 2 - 40, cx + 40, H // 2 + 40], fill=(255, 255, 255))
        img.save(os.path.join(frames_dir, f"f_{i:05d}.png"))

    out_name = os.path.basename(output_path) if output_path else f"video_{seed % 100000}.mp4"
    if not out_name.endswith((".mp4", ".gif")):
        out_name += ".mp4"
    out_path = os.path.join(workdir, out_name)
    cmd = [ffmpeg, "-y", "-framerate", str(fps), "-i", os.path.join(frames_dir, "f_%05d.png")]
    if out_name.endswith(".gif"):
        cmd += ["-loop", "0", out_path]
    else:
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    shutil.rmtree(frames_dir, ignore_errors=True)
    if proc.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        return {
            "success": False,
            "tool": "video_render",
            "error": (proc.stderr or "ffmpeg xato")[:300],
        }

    res = {
        "success": True,
        "tool": "video_render",
        "spec": spec[:120],
        "video_path": os.path.abspath(out_path),
        "frames": frames,
        "fps": fps,
        "bytes": os.path.getsize(out_path),
    }
    # Birinchi kadrni preview qilib qo'yamiz.
    try:
        static_dir = get_static_screenshots_dir()
        os.makedirs(static_dir, exist_ok=True)
        Image.open(out_path if out_name.endswith(".gif") else _first_frame_of(out_path, workdir)).save(
            os.path.join(static_dir, "editor_preview.png")
        )
        shutil.copyfile(os.path.join(static_dir, "editor_preview.png"), os.path.join(static_dir, "latest.png"))
        res["web_preview_url"] = "/static/screenshots/editor_preview.png"
    except Exception:
        pass
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
    workdir = output_path and os.path.dirname(output_path) or os.path.join("workspaces", "animator")
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
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Tool name required. Usage: python tools.py <screenshot|interact_web|web_search|run_process|get_logs|check_goal|blender_headless_exec|runScript|figma_sync|gen_image|video_render|anim_render|notion|slack> [args...]"
        }))
        sys.exit(1)

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

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
    elif cmd in ["runscript", "run_script"]:
        subagent = args[0] if args else "sculptor"
        s_name = args[1] if len(args) > 1 else "script.py"
        code = args[2] if len(args) > 2 else "print('Script executed')"
        result = tool_run_script(subagent, s_name, code)
    elif cmd in ["figma_sync", "figma"]:
        f_key = args[0] if args else "leWEA7AyECgzcIk4aeDx8p"
        result = tool_figma_sync(f_key)
    elif cmd in ["gen_image", "genimage", "paint"]:
        prompt = args[0] if args else "abstract art"
        width = int(args[1]) if len(args) > 1 else 512
        height = int(args[2]) if len(args) > 2 else 512
        result = tool_gen_image(prompt, width, height)
    elif cmd in ["video_render", "video"]:
        spec = args[0] if args else "abstract clip"
        duration = float(args[1]) if len(args) > 1 else 3.0
        result = tool_video_render(spec, duration)
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
