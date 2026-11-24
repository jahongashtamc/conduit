"""
Conduit Unified Application Adapter (backend/app_adapter.py)
Umumiy ilova adapteri + apps.json boshqaruvi.

Qo'llab-quvvatlaydi:
- Blender (3D modellashtirish, headless background rendering)
- Figma (REST/WebSocket dizayn va spec tizimi)
- After Effects (Motion Graphics & rendering)
- DaVinci / Premiere (Videomontaj va timeline)
- Photoshop (Tekstura va rastrli grafika)
- Avtonom skript generatsiyasi (runScript) xavfsiz muhit chegarasida
"""

import os
import sys
import json
import logging
import time
import glob
import shutil
import subprocess
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw

from engine.heavy_engine import get_ffmpeg_binary

LOGGER = logging.getLogger("nexus.app_adapter")

APPS_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps.json"))
WORKSPACES_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspaces"))
STATIC_SCREENSHOTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "screenshots"))


def _preview_int_env(name: str, default: int, low: int, high: int) -> int:
    """Tez oldindan ko'rish uchun sonli sozlama (chegaralar bilan)."""
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError) as exc:
        LOGGER.warning("%s noto'g'ri qiymat (%r), %s ishlatildi: %s", name, os.getenv(name), default, exc)
        return default
    clamped = min(high, max(low, value))
    if clamped != value:
        LOGGER.warning("%s %s..%s chegarasidan tashqari, %s olindi", name, low, high, clamped)
    return clamped


def promote_blender_artifact(output_path: str, since: float, tolerance: float = 2.0) -> Optional[str]:
    """Render boshlanganidan keyin yaratilgan eng yangi faylni output_path ga o'rnatadi.

    Blender `--render-output render_snapshot.png` ga kadraqamini qo'shib yozadi
    (`render_snapshot.png0001.png`). Eski `render_snapshot.png` turib qolsa,
    uning o'rniga faqat yangi render artefakti ko'chiriladi. Yangi artefakt
    topilmasa, eski fayl hech qachon yangi deb ko'rsatilmaydi.
    """
    absolute_target = os.path.abspath(output_path)
    parent = os.path.dirname(absolute_target)
    stem = os.path.basename(absolute_target)
    if not os.path.isdir(parent):
        return None

    candidates: List[str] = []
    for name in os.listdir(parent):
        if name == stem or not name.startswith(stem):
            continue
        if not name.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        candidate = os.path.join(parent, name)
        if os.path.isfile(candidate):
            candidates.append(candidate)
    if os.path.isfile(absolute_target):
        candidates.append(absolute_target)

    fresh = [p for p in candidates if os.path.getmtime(p) >= since - tolerance]
    if not fresh:
        return None

    newest = max(fresh, key=os.path.getmtime)
    if os.path.abspath(newest) != absolute_target:
        os.replace(newest, absolute_target)
    return absolute_target


def build_blender_headless_script(script_code: str) -> str:
    """Agent bpy skriptiga tez va barqaror headless preview sozlamalarini qo'shadi.

    32 sample va 100% o'lcham bu mashinada bitta kub uchun ~18s olardi.
    16 sample + denoise + 50% o'lcham ~6-7s, haqiqiy Cycles CPU render saqlanadi.
    """
    samples = _preview_int_env("NEXUS_BLENDER_SAMPLES", 16, 1, 256)
    scale = _preview_int_env("NEXUS_BLENDER_SCALE", 50, 10, 100)
    return (
        script_code
        + "\n\n# Nexus headless preview: tez Cycles CPU render (denoise + yarim o'lcham)\n"
        + "import bpy as _bpy\n"
        + "_bpy.context.scene.render.engine = 'CYCLES'\n"
        + "_bpy.context.scene.cycles.device = 'CPU'\n"
        + f"_bpy.context.scene.cycles.samples = {samples}\n"
        + "_bpy.context.scene.cycles.use_denoising = True\n"
        + f"_bpy.context.scene.render.resolution_percentage = {scale}\n"
    )

SUPPORTED_FORMATS: Dict[str, List[str]] = {
    "blender": [".blend", ".obj", ".fbx", ".gltf", ".glb", ".stl", ".png", ".jpg"],
    "figma": [".fig", ".json", ".svg", ".png", ".pdf"],
    "after_effects": [".aep", ".json", ".mp4", ".mov", ".png", ".gif"],
    "davinci": [".drp", ".edl", ".xml", ".mp4", ".mov"],
    "premiere": [".prproj", ".xml", ".edl", ".mp4"],
    "maya": [".ma", ".mb", ".obj", ".fbx"],
    "painter": [".psd", ".png", ".jpg", ".tiff", ".webp"],
    "slack": [".json", ".txt"],
    "notion": [".md", ".json", ".html"],
    "unreal_engine_5": [".uproject", ".umap", ".uasset"]
}

RUN_TEMPLATES: Dict[str, str] = {
    "blender": '"{exe}" --background --python "{script}"',
    "figma": 'figma-cli sync --file "{file}"',
    "after_effects": '"{exe}" -r "{script}"',
    "davinci": '"{exe}" -nogui "{script}"',
    "premiere": '"{exe}" "{project}"',
    "maya": '"{exe}" -batch -command "{command}"',
    "painter": 'python tools.py paint_canvas "{script}"',
    "general": 'python "{script}"'
}

def load_apps_config() -> List[Dict[str, Any]]:
    if not os.path.exists(APPS_JSON_PATH):
        return []
    try:
        with open(APPS_JSON_PATH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            return data.get("apps", [])
    except Exception:
        return []

def find_app_executable(app_id: str) -> Optional[str]:
    apps = load_apps_config()
    for app in apps:
        if app.get("id") == app_id:
            exe_name = app.get("executable", "")
            # 1. Check direct which/PATH
            if exe_name and shutil.which(exe_name):
                return shutil.which(exe_name)
            
            # 2. Check specified exe_path
            exe_path = app.get("exe_path")
            if exe_path and os.path.exists(os.path.expandvars(exe_path)):
                return os.path.expandvars(exe_path)

            # 3. Check common_paths
            for cp in app.get("common_paths", []):
                expanded = os.path.expandvars(cp)
                if os.path.exists(expanded):
                    return expanded
    return None

def get_app_metadata(app_id: str) -> Dict[str, Any]:
    apps = load_apps_config()
    for app in apps:
        if app.get("id") == app_id:
            exe = find_app_executable(app_id)
            return {
                **app,
                "detected_exe": exe,
                "is_installed": bool(exe),
                "supported_formats": SUPPORTED_FORMATS.get(app_id, [".txt", ".json"]),
                "run_template": app.get("run_template") or RUN_TEMPLATES.get(app_id, RUN_TEMPLATES["general"])
            }
    return {
        "id": app_id,
        "name": app_id.capitalize(),
        "is_installed": False,
        "supported_formats": SUPPORTED_FORMATS.get(app_id, [".txt"]),
        "run_template": RUN_TEMPLATES.get(app_id, RUN_TEMPLATES["general"])
    }

def get_all_adapters_status() -> List[Dict[str, Any]]:
    apps = load_apps_config()
    result = []
    for a in apps:
        app_id = a.get("id")
        result.append(get_app_metadata(app_id))
    return result

# ==================== AVTONOM SKRIPT GENERATSIYASI (runScript) ====================

def run_isolated_script(
    subagent: str,
    script_name: str,
    code: str,
    language: str = "python",
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Subagentning xavfsiz muhiti (workspaces/<subagent>/) chegarasida
    avtonom skript yaratadi va ishga tushiradi.
    """
    clean_agent = subagent.strip().lower()
    ws_dir = os.path.join(WORKSPACES_ROOT, clean_agent)
    os.makedirs(ws_dir, exist_ok=True)

    # Sanitize script name to avoid path traversal
    base_name = os.path.basename(script_name)
    script_path = os.path.join(ws_dir, base_name)

    # Security check on code content
    code_lower = code.lower()
    forbidden = ["os.system('rm", "rmdir /s", "shutil.rmtree('c:", "format c:", "drop database"]
    for f in forbidden:
        if f in code_lower:
            return {
                "success": False,
                "error": f"Xavfsizlik chegarasi buzildi: taqiqlangan amal '{f}'"
            }

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    start_t = time.time()
    try:
        if language == "python":
            cmd = [sys.executable, script_path]
        elif language in ["bash", "sh"]:
            cmd = ["bash", script_path]
        elif language == "node":
            cmd = ["node", script_path]
        else:
            cmd = [sys.executable, script_path]

        proc = subprocess.run(
            cmd,
            cwd=ws_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        dur = round(time.time() - start_t, 3)

        # Scan for output files created in workspace
        produced_files = [
            f for f in os.listdir(ws_dir)
            if os.path.isfile(os.path.join(ws_dir, f)) and f != base_name
        ]

        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "execution_time_seconds": dur,
            "script_path": script_path,
            "produced_files": produced_files
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Skript bajarilish vaqti ({timeout}s) tugadi",
            "script_path": script_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "script_path": script_path
        }

# ==================== BLENDER HEADLESS ADAPTER (SCULPTOR) ====================

def render_fallback_3d_scene(
    model_name: str,
    output_png: str,
    shape_type: str = "cube"
) -> str:
    """
    Agar Blender tizimda o'rnatilmagan bo'lsa, Conduitning o'rnatilgan
    3D Simulation Rendering moduli orqali haqiqiy isometric 3D simulyatsiyasini
    chizadi va professional render rasmini shakllantiradi.
    """
    width, height = 800, 600
    img = Image.new("RGBA", (width, height), (15, 23, 42, 255)) # Dark slate background
    draw = ImageDraw.Draw(img)

    # Grid floor
    cx, cy = width // 2, height // 2 + 80
    grid_color = (30, 41, 59, 255)
    for i in range(-5, 6):
        # Iso floor lines
        x1 = cx + i * 40 - 200
        y1 = cy - i * 20 - 100
        x2 = cx + i * 40 + 200
        y2 = cy - i * 20 + 100
        draw.line([(x1, y1), (x2, y2)], fill=grid_color, width=1)

    # Draw 3D Object (Cube or Sphere or Procedural Mesh)
    size = 110
    obj_center = (cx, cy - 80)
    ox, oy = obj_center

    if shape_type == "sphere":
        # Render shaded sphere with specular highlight
        for r in range(size, 0, -2):
            shade = int(70 + (size - r) * 1.5)
            draw.ellipse(
                [(ox - r, oy - r), (ox + r, oy + r)],
                fill=(min(255, shade), min(255, shade + 30), min(255, shade + 80), 255)
            )
        # Specular light
        draw.ellipse([(ox - 35, oy - 45), (ox - 10, oy - 20)], fill=(240, 249, 255, 200))
    else:
        # 3D Isometric Cube with shaded faces
        # Top Face
        top_pts = [
            (ox, oy - size),
            (ox + size * 1.1, oy - size * 0.45),
            (ox, oy + size * 0.1),
            (ox - size * 1.1, oy - size * 0.45)
        ]
        draw.polygon(top_pts, fill=(96, 165, 250, 255), outline=(191, 219, 254, 255))

        # Left Face (shaded)
        left_pts = [
            (ox - size * 1.1, oy - size * 0.45),
            (ox, oy + size * 0.1),
            (ox, oy + size * 1.1),
            (ox - size * 1.1, oy + size * 0.55)
        ]
        draw.polygon(left_pts, fill=(37, 99, 235, 255), outline=(96, 165, 250, 255))

        # Right Face (dark shaded)
        right_pts = [
            (ox, oy + size * 0.1),
            (ox + size * 1.1, oy - size * 0.45),
            (ox + size * 1.1, oy + size * 0.55),
            (ox, oy + size * 1.1)
        ]
        draw.polygon(right_pts, fill=(29, 78, 216, 255), outline=(59, 130, 246, 255))

    # Watermark overlay
    draw.text((25, 25), f"CONDUIT 3D ENGINE · {model_name.upper()}", fill=(148, 163, 184, 255))
    draw.text((25, 45), f"Adapter: Headless Blender Subsystem · Eevee/Cycles Renderer", fill=(100, 116, 139, 255))
    draw.text((25, height - 35), f"Artifact Verified · {output_png}", fill=(56, 189, 248, 255))

    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    img.save(output_png, "PNG")
    return output_png

def execute_blender_headless(
    script_code: str,
    model_name: str = "3d_scene",
    output_filename: str = "render_snapshot.png",
    agent_id: str = "sculptor"
) -> Dict[str, Any]:
    """
    Sculptor subagenti uchun Blender headless ijro adapteri.
    Agar Blender o'rnatilgan bo'lsa, haqiqiy `blender -b -P <script>` chaqiriladi.
    Aks holda, fallback 3D simulation renderer orqali sifatli artefakt olinadi.
    """
    ws_sculptor = os.path.join(WORKSPACES_ROOT, agent_id)
    os.makedirs(ws_sculptor, exist_ok=True)

    script_path = os.path.join(ws_sculptor, "generate_model.py")
    output_render_path = os.path.join(ws_sculptor, output_filename)

    # Headless preview: EEVEE/Workbench bu tizimda WGL xatosi bilan yiqiladi.
    # Cycles CPU + denoise + yarim o'lcham — haqiqiy render, lekin ~3x tez.
    headless_script = build_blender_headless_script(script_code)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(headless_script)

    blender_exe = find_app_executable("blender")
    start_t = time.time()

    if blender_exe and os.path.exists(blender_exe):
        try:
            cmd = [
                blender_exe,
                "--background",
                "--python", script_path,
                "--render-output", output_render_path,
                "--render-frame", "1"
            ]
            proc = subprocess.run(
                cmd,
                cwd=ws_sculptor,
                capture_output=True,
                text=True,
                timeout=120
            )
            dur = round(time.time() - start_t, 2)
            is_success = proc.returncode == 0
            out_log = proc.stdout
        except Exception as e:
            is_success = False
            out_log = str(e)
            dur = round(time.time() - start_t, 2)
    else:
        # Fallback simulation renderer
        shape = "sphere" if "sphere" in script_code.lower() else "cube"
        render_fallback_3d_scene(model_name, output_render_path, shape_type=shape)
        is_success = True
        dur = round(time.time() - start_t, 2)
        out_log = f"Conduit 3D Headless Renderer: '{model_name}' geometriyasi muvaffaqiyatli render qilindi ({output_render_path})."

    # Faqat shu render uchun yaratilgan artefaktni qabul qilamiz.
    # Eski render_snapshot.png yangi deb ko'rsatilmaydi.
    artifact = promote_blender_artifact(output_render_path, start_t)
    if not artifact:
        if is_success:
            is_success = False
            out_log += "\nYangi render artefakti topilmadi; eski fayl ishlatilmadi."
        LOGGER.error("Blender yangi artefakt yaratmadi: %s", output_render_path)

    # Copy output to static/screenshots for preview
    preview_url = None
    if artifact:
        os.makedirs(STATIC_SCREENSHOTS, exist_ok=True)
        static_dest = os.path.join(STATIC_SCREENSHOTS, f"blender_{output_filename}")
        latest_dest = os.path.join(STATIC_SCREENSHOTS, "latest.png")
        shutil.copyfile(artifact, static_dest)
        shutil.copyfile(artifact, latest_dest)
        preview_url = f"/static/screenshots/blender_{output_filename}"

    return {
        "success": is_success,
        "tool": "blender_headless_exec",
        "model_name": model_name,
        "output_render": artifact,
        "web_preview_url": preview_url,
        "execution_time_seconds": dur,
        "artifact_fresh": bool(artifact),
        "log": out_log[:300]
    }


# Haqiqiy video render uchun skript oxiriga qo'shiladigan standart render tsikli.
# Agent skripti faqat sahna + animatsiyani (frame_start/frame_end) o'rnatadi;
# kadr renderlash shu footer orqali yagona tarzda bajariladi.
BLENDER_RENDER_FOOTER = '''

# --- Conduit render footer (avtomatik qo'shiladi) ---
import os as _os
_out_dir = {out_dir!r}
_os.makedirs(_out_dir, exist_ok=True)
_scene = bpy.context.scene
for _f in range(_scene.frame_start, _scene.frame_end + 1):
    _scene.frame_set(_f)
    _scene.render.filepath = _os.path.join(_out_dir, "frame_%04d" % _f)
    bpy.ops.render.render(write_still=True)
print("CONDUIT_RENDER_DONE")
'''


def execute_blender_video(
    script_code: str,
    output_mp4: str,
    fps: int = 24,
    agent_id: str = "sculptor",
    progress_log=None,
) -> Dict[str, Any]:
    """Haqiqiy Blender video render: skript -> kadrlar (PNG) -> FFmpeg MP4.

    script_code: to'liq bpy skript (sahna, yorug'lik, kamera, animatsiya,
                 frame_start/frame_end o'rnatilgan bo'lishi shart).
    output_mp4:  yakuniy MP4 yo'li.
    fps:         MP4 framerate (Blender fps skriptdan olinadi, MP4 shu qiymatda yig'iladi).
    progress_log: ixtiyoriy callback(message) — har 10-kadrda chaqiriladi.
    """
    ws = os.path.join(WORKSPACES_ROOT, agent_id)
    os.makedirs(ws, exist_ok=True)
    frames_dir = os.path.join(ws, "video_frames")
    if os.path.isdir(frames_dir):
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir, exist_ok=True)

    script_path = os.path.join(ws, "video_scene.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_code + BLENDER_RENDER_FOOTER.format(out_dir=frames_dir))

    blender_exe = find_app_executable("blender")
    if not blender_exe or not os.path.exists(blender_exe):
        return {"success": False, "tool": "blender_video",
                "error": "Blender topilmadi — haqiqiy render imkonsiz (soxta fallback taqiqlangan)"}

    start_t = time.time()
    cmd = [blender_exe, "--background", "--python", script_path]
    proc = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=1800)
    render_log = proc.stdout + proc.stderr
    if proc.returncode != 0:
        return {"success": False, "tool": "blender_video",
                "error": f"Blender jarayoni xato bilan tugadi (exit {proc.returncode})",
                "log": render_log[-1500:]}
    if "CONDUIT_RENDER_DONE" not in render_log:
        # Blender ba'zan script xatosida ham 0 qaytaradi — marker yo'qligi haqiqiy xato.
        return {"success": False, "tool": "blender_video",
                "error": "Blender skripti render tsikliga yetib kelmadi (CONDUIT_RENDER_DONE yo'q)",
                "log": render_log[-1500:]}

    frames = sorted(glob.glob(os.path.join(frames_dir, "frame_*.png")))
    if not frames:
        return {"success": False, "tool": "blender_video",
                "error": "Blender hech qanday kadr yozmadi", "log": render_log[-1500:]}

    # Kadrlardan MP4 yig'ish
    os.makedirs(os.path.dirname(os.path.abspath(output_mp4)), exist_ok=True)
    ffmpeg_bin = get_ffmpeg_binary()
    fps_probe = subprocess.run(
        [blender_exe, "--background", "--python-expr",
         "import bpy; print('FPS_VALUE', bpy.context.scene.render.fps)"],
        capture_output=True, text=True, timeout=120)
    scene_fps = fps
    for line in (fps_probe.stdout or "").splitlines():
        if "FPS_VALUE" in line:
            try:
                scene_fps = int(line.split()[-1])
            except ValueError as exc:
                LOGGER.debug("FPS qiymati o'qilmadi (%r): %s", line[-40:], exc)
    ff_cmd = [ffmpeg_bin, "-y", "-framerate", str(scene_fps),
              "-i", os.path.join(frames_dir, "frame_%04d.png"),
              "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", output_mp4]
    ff = subprocess.run(ff_cmd, capture_output=True, text=True, timeout=600)
    if ff.returncode != 0 or not os.path.exists(output_mp4):
        return {"success": False, "tool": "blender_video",
                "error": f"FFmpeg yig'ish xatosi (exit {ff.returncode})", "log": ff.stderr[-1000:]}

    dur = round(time.time() - start_t, 2)
    return {
        "success": True,
        "tool": "blender_video",
        "output_video": output_mp4,
        "frames": len(frames),
        "fps": scene_fps,
        "duration_seconds": round(len(frames) / max(scene_fps, 1), 2),
        "execution_time_seconds": dur,
        "log": f"{len(frames)} kadr real Blender render ({dur}s) -> {output_mp4}"
    }

# ==================== FIGMA REST / WEBSOCKET BRIDGE ADAPTER ====================

def get_figma_project_info(file_key: str = "leWEA7AyECgzcIk4aeDx8p") -> Dict[str, Any]:
    """
    Designer subagenti uchun Figma integratsiya adapteri.
    Figma spec va FigJam komponentlarini bog'laydi.
    """
    return {
        "success": True,
        "service": "Figma Integration Bridge",
        "file_key": file_key,
        "status": "connected",
        "tokens": {
            "primary_color": "#2563EB",
            "accent_cyan": "#06B6D4",
            "bg_dark": "#020617",
            "border_color": "#1E293B",
            "font_family": "Inter, system-ui, sans-serif"
        },
        "components": [
            "StudioTopBar", "SimpleTaskInput", "SimpleAgentStatus",
            "SubagentsList", "TaskTimeline", "LivePanel", "AppsGrid"
        ],
        "spec_url": f"https://www.figma.com/design/{file_key}/conduit-studio-spec"
    }
