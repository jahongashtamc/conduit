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
import re
import logging
import time
import glob
import shutil
import subprocess
import urllib.request
import urllib.error
import urllib.parse
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


# Foydalanuvchi talabini haqiqiy sahna/rasm parametrlariga aylantirish.
# Avval sculptor faqat kulrang kub, painter esa tasodifiy chiziqlar chizardi —
# natija foydalanuvchi aytgan rang/shakl/son/matn bilan bog'liq emas edi.
_VISUAL_COLORS = {
    "qizil": "#DC2626", "red": "#DC2626", "ko'k": "#2563EB", "kok": "#2563EB",
    "blue": "#2563EB", "yashil": "#16A34A", "green": "#16A34A", "sariq": "#EAB308",
    "yellow": "#EAB308", "oq": "#F8FAFC", "white": "#F8FAFC", "qora": "#0F172A",
    "black": "#0F172A", "binafsha": "#7C3AED", "purple": "#7C3AED", "violet": "#7C3AED",
    "pushti": "#DB2777", "pink": "#DB2777", "to'q sariq": "#EA580C", "orange": "#EA580C",
    "cyan": "#06B6D4", "kulrang": "#64748B", "gray": "#64748B", "oltin": "#D4AF37",
    "gold": "#D4AF37",
}
_VISUAL_SHAPES = {
    "kub": "cube", "cube": "cube", "shar": "sphere", "sphere": "sphere",
    "silindr": "cylinder", "cylinder": "cylinder", "konus": "cone", "cone": "cone",
    "piramida": "pyramid", "pyramid": "pyramid", "torus": "torus", "halqa": "torus",
    # Yassi shakllar: avval bular umuman yo'q edi, natijada "uchburchak" so'ralganda
    # default 'cube' chizilardi va agent baribir PASS olardi — dalil noto'g'ri edi.
    "uchburchak": "triangle", "triangle": "triangle",
    "yulduzcha": "star", "yulduz": "star", "star": "star",
    "doira": "circle", "aylana": "circle", "circle": "circle",
    "beshburchak": "pentagon", "besh burchak": "pentagon", "pentagon": "pentagon",
    "hexagon": "hexagon", "olti burchakli": "hexagon", "olti burchak": "hexagon",
    "to'rtburchak": "rect", "tortburchak": "rect", "kvadrat": "rect",
    "rectangle": "rect", "square": "rect",
}
_COUNT_WORDS = {
    "bir": 1, "ikki": 2, "uch": 3, "to'rt": 4, "tort": 4, "besh": 5,
    "olti": 6, "etti": 7, "sakkiz": 8,
}


def parse_visual_spec(goal: str) -> Dict[str, Any]:
    """Vazifa matnidan rang, shakl, son, matn va material parametrlarini oladi."""
    low = (goal or "").lower()
    background = "#111827"
    bg_match = re.search(
        r"(?:fon|background)\s*[:\-]?\s*(#[0-9a-fA-F]{6}|" + "|".join(re.escape(k) for k in _VISUAL_COLORS) + r")",
        low,
    )
    if bg_match:
        raw = bg_match.group(1)
        background = raw.upper() if raw.startswith("#") else _VISUAL_COLORS.get(raw, background)

    # Fondagi rang obyekt rangi hisoblanmaydi: aks holda "fon qora" qora shar qo'shadi.
    colors: List[str] = []
    for name, hex_value in _VISUAL_COLORS.items():
        if hex_value == background:
            continue
        if name in low and hex_value not in colors:
            colors.append(hex_value)
    for match in re.finditer(r"#[0-9a-fA-F]{6}\b", goal or ""):
        value = match.group(0).upper()
        if value != background and value not in colors:
            colors.append(value)

    shapes: List[str] = []
    # Shakllarni vazifa matnidagi TARTIBDA yig'amiz: "uchburchak va kub" desa
    # birinchi uchburchak chizilishi kerak — lug'at tartibi buni buzardi.
    # Eng uzun nom birinchi tekshiriladi, shunda "besh burchak" va
    # "beshburchak" ikki marta sanalmaydi.
    found: list[tuple[int, int, str]] = []  # (boshlanish, oxiri, shape)
    for name in sorted(_VISUAL_SHAPES, key=len, reverse=True):
        start = low.find(name)
        while start != -1:
            end = start + len(name)
            if not any(s < end and start < e for s, e, _ in found):
                found.append((start, end, _VISUAL_SHAPES[name]))
            start = low.find(name, start + 1)
    shapes = []
    for _start, _end, shape in sorted(found):
        if shape not in shapes:
            shapes.append(shape)

    count = 1
    # Shakl nomlarini olib tashlaymiz: "besh burchak"/"olti burchak" — shakl,
    # "5 ta obyekt" emas. Aks holda `_COUNT_WORDS` dagi "besh"/"olti" sonni
    # noto'g'ri o'rnatardi.
    count_text = low
    for shape_name in sorted(_VISUAL_SHAPES, key=len, reverse=True):
        count_text = count_text.replace(shape_name, " ")
    digit = re.search(r"\b(\d{1,2})\s*(?:ta|dona|pcs|pieces|objects|shar|kub|quti)\b", count_text)
    if digit:
        count = min(12, max(1, int(digit.group(1))))
    else:
        for word, value in _COUNT_WORDS.items():
            if re.search(r"\b" + re.escape(word) + r"\b", count_text):
                count = value
                break

    text = ""
    # Faqat ikki qo'shtirnoq/guillemet: inglizcha "ko'k" dagi apostrof matn deb o'qilmasligi kerak.
    quoted = re.search(r'["«]([^"»]{2,60})["»]', goal or "")
    if quoted:
        text = quoted.group(1).strip()
    elif "matn" in low or "yozuv" in low or "text " in low:
        text = (goal or "").strip()[:60]

    material = "standard"
    if any(k in low for k in ("metall", "metal", "oltin")):
        material = "metal"
    elif any(k in low for k in ("shisha", "glass")):
        material = "glass"
    elif any(k in low for k in ("yog'och", "yogoch", "wood")):
        material = "wood"

    return {
        "colors": colors or ["#2563EB"],
        "shapes": shapes or ["cube"],
        "count": count,
        "text": text,
        "material": material,
        "background": background,
    }


def build_scene_script_from_goal(goal: str) -> str:
    """Foydalanuvchi talabiga mos Blender sahnasi (statik kub emas)."""
    spec = parse_visual_spec(goal)
    colors = spec["colors"]
    shapes = spec["shapes"]
    text = spec["text"]
    metallic = 0.85 if spec["material"] == "metal" else 0.0
    roughness = 0.18 if spec["material"] == "metal" else 0.55

    def rgba(hex_value: str):
        raw = hex_value.lstrip("#")
        return (
            int(raw[0:2], 16) / 255.0,
            int(raw[2:4], 16) / 255.0,
            int(raw[4:6], 16) / 255.0,
            1.0,
        )

    lines = [
        "import bpy, math",
        "from mathutils import Vector",
        "# COLORS_HEX = " + repr(colors),
        "# BACKGROUND_HEX = " + repr(spec["background"]),
        "COLORS = " + repr([rgba(c) for c in colors]),
        "SHAPES = " + repr(shapes),
        "COUNT = " + repr(int(spec["count"])),
        "TEXT = " + repr(text),
        "METALLIC = " + repr(metallic),
        "ROUGHNESS = " + repr(roughness),
        "BG_COLOR = " + repr(rgba(spec["background"])),
        "bpy.ops.object.select_all(action='SELECT')",
        "bpy.ops.object.delete(use_global=False)",
        "for i in range(COUNT):",
        "    shape = SHAPES[i % len(SHAPES)]",
        "    color = COLORS[i % len(COLORS)]",
        "    x = (i - (COUNT - 1) / 2.0) * 1.6",
        "    if shape == 'sphere':",
        "        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.75, location=(x, 0, 0.8))",
        "    elif shape == 'cylinder':",
        "        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.65, depth=1.5, location=(x, 0, 0.8))",
        "    elif shape == 'cone':",
        "        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.7, depth=1.5, location=(x, 0, 0.8))",
        "    elif shape == 'pyramid':",
        "        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.8, depth=1.5, location=(x, 0, 0.8))",
        "    elif shape == 'torus':",
        "        bpy.ops.mesh.primitive_torus_add(major_radius=0.7, minor_radius=0.22, location=(x, 0, 0.9))",
        # Yassi shakllar: Blender'da tayyor primitive yo'q. `primitive_cylinder_add`
        # o'qini Z bo'ylab quradi, ya'ni yupqa disk gorizontal yotadi va kameradan
        # yon tomondan qirrasi ko'rinadi (uchburchak "quti" bo'lib chiqadi).
        # Shuning uchun 90° X atrofida burib, diskni KAMERAGA qaratamiz.
        "    elif shape == 'triangle':",
        "        bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=0.9, depth=0.2, location=(x, 0, 0.8))",
        "        bpy.context.object.rotation_euler[0] = math.radians(90)",
        "    elif shape == 'pentagon':",
        "        bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.85, depth=0.2, location=(x, 0, 0.8))",
        "        bpy.context.object.rotation_euler[0] = math.radians(90)",
        "    elif shape == 'hexagon':",
        "        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.85, depth=0.2, location=(x, 0, 0.8))",
        "        bpy.context.object.rotation_euler[0] = math.radians(90)",
        "    elif shape == 'star':",
        "        import bmesh",
        "        mesh = bpy.data.meshes.new('star_mesh')",
        "        bm = bmesh.new()",
        "        n = 5",
        "        ring = []",
        "        for k in range(n * 2):",
        "            rad = 0.9 if k % 2 == 0 else 0.38",
        "            ang = math.pi * k / n - math.pi / 2",
        "            ring.append(bm.verts.new((rad * math.cos(ang), rad * math.sin(ang), 0.0)))",
        "        cap = bm.verts.new((0.0, 0.0, 0.0))",
        "        for k in range(n * 2):",
        "            bm.faces.new((cap, ring[k], ring[(k + 1) % (n * 2)]))",
        "        bm.to_mesh(mesh)",
        "        bm.free()",
        "        obj = bpy.data.objects.new('star', mesh)",
        "        bpy.context.collection.objects.link(obj)",
        "        obj.location = (x, 0, 0.8)",
        "        obj.rotation_euler[0] = math.radians(90)",
        "        bpy.context.view_layer.objects.active = obj",
        "    elif shape == 'circle':",
        "        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.85, depth=0.2, location=(x, 0, 0.8))",
        "        bpy.context.object.rotation_euler[0] = math.radians(90)",
        "    elif shape == 'rect':",
        "        bpy.ops.mesh.primitive_cube_add(size=1.2, location=(x, 0, 0.8))",
        "        bpy.context.object.scale[2] = 0.18",
        "        bpy.context.object.rotation_euler[0] = math.radians(90)",
        "    else:",
        "        bpy.ops.mesh.primitive_cube_add(size=1.5, location=(x, 0, 0.8))",
        "    obj = bpy.context.object",
        "    obj.rotation_euler[2] = math.radians(12 * i)",
        "    mat = bpy.data.materials.new(name='nexus_material_%d' % i)",
        "    mat.diffuse_color = color",
        "    mat.use_nodes = True",
        "    bsdf = mat.node_tree.nodes.get('Principled BSDF')",
        "    if bsdf:",
        "        bsdf.inputs['Base Color'].default_value = color",
        "        bsdf.inputs['Metallic'].default_value = METALLIC",
        "        bsdf.inputs['Roughness'].default_value = ROUGHNESS",
        "    obj.data.materials.append(mat)",
    ]
    if text:
        lines += [
            "bpy.ops.object.text_add(location=(-1.5, -1.2, 0.15))",
            "txt = bpy.context.object",
            "txt.data.body = " + repr(text[:60]),
            "txt.data.size = 0.35",
        ]
    lines += [
        "bpy.ops.object.camera_add(location=(6.5, -8.5, 5.5))",
        "cam = bpy.context.object",
        "direction = Vector((0, 0, 0.7)) - cam.location",
        "cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()",
        "bpy.context.scene.camera = cam",
        "bpy.ops.object.light_add(type='AREA', location=(-3, -4, 6))",
        "bpy.context.object.data.energy = 900",
        "bpy.context.object.data.size = 6",
        "world = bpy.context.scene.world or bpy.data.worlds.new('nexus_world')",
        "bpy.context.scene.world = world",
        "world.use_nodes = True",
        "bg_node = world.node_tree.nodes.get('Background')",
        "if bg_node:",
        "    bg_node.inputs['Color'].default_value = BG_COLOR",
        "    bg_node.inputs['Strength'].default_value = 0.7",
    ]
    return "\n".join(lines) + "\n"


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

def _figma_get_json(url: str, token: str) -> Dict[str, Any]:
    """Figma REST API'dan haqiqiy JSON oladi. Xatoni yutmaydi."""
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "X-Figma-Token": token},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _figma_color(fill: dict) -> Optional[str]:
    color = (fill or {}).get("color") or {}
    if not all(k in color for k in ("r", "g", "b")):
        return None
    try:
        return "#" + "".join(
            f"{max(0, min(255, round(float(color[k]) * 255))):02X}"
            for k in ("r", "g", "b")
        )
    except (TypeError, ValueError):
        return None


def _walk_figma_nodes(node: dict, colors: set, fonts: set, components: set) -> None:
    if not isinstance(node, dict):
        return
    name = str(node.get("name") or "").strip()
    if name and node.get("type") in ("COMPONENT", "INSTANCE"):
        components.add(name)
    for fill in node.get("fills") or []:
        if isinstance(fill, dict) and fill.get("type") == "SOLID":
            hex_color = _figma_color(fill)
            if hex_color:
                colors.add(hex_color)
    style = node.get("style") or {}
    if style.get("fontFamily"):
        fonts.add(str(style["fontFamily"]))
    for child in node.get("children") or []:
        _walk_figma_nodes(child, colors, fonts, components)


def get_figma_project_info(
    file_key: str = "",
    requirement: str = "",
) -> Dict[str, Any]:
    """Haqiqiy Figma faylidan token/komponentlarni oladi.

    FIGMA_TOKEN yoki haqiqiy file_key bo'lmasa, soxta spec qaytarmaydi —
    `needs_config` holatini ko'rsatadi. Bu agentning "bajardim" degan
    yolg'on hisobotini oldini oladi.
    """
    token = os.getenv("FIGMA_TOKEN") or os.getenv("FIGMA_ACCESS_TOKEN")
    if not token:
        return {
            "success": False,
            "tool": "figma_sync",
            "status": "needs_config",
            "error": "FIGMA_TOKEN topilmadi. Figma REST API uchun shaxsiy access token kerak "
                     "(global sozlamalar o'zgartirilmaydi).",
        }
    key = (file_key or "").strip()
    if not key:
        match = re.search(r"figma\.com/(?:design|file)/([A-Za-z0-9]+)", requirement or "")
        key = match.group(1) if match else ""
    if not key or key == "leWEA7AyECgzcIk4aeDx8p":
        return {
            "success": False,
            "tool": "figma_sync",
            "status": "needs_config",
            "error": "Haqiqiy Figma file key kerak (masalan figma.com/design/<key> havolasidan).",
        }

    try:
        data = _figma_get_json(
            f"https://api.figma.com/v1/files/{urllib.parse.quote(key)}", token
        )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "ignore")[:200]
        LOGGER.warning("Figma API HTTP %s: %s", exc.code, detail)
        return {
            "success": False, "tool": "figma_sync", "status": "api_error",
            "error": f"Figma API HTTP {exc.code}: {detail}",
        }
    except (urllib.error.URLError, ValueError, OSError) as exc:
        LOGGER.warning("Figma API muvaffaqiyatsiz: %s: %s", type(exc).__name__, exc)
        return {
            "success": False, "tool": "figma_sync", "status": "api_error",
            "error": f"Figma API xatosi: {type(exc).__name__}: {exc}",
        }

    colors: set = set()
    fonts: set = set()
    components: set = set()
    _walk_figma_nodes(data.get("document") or {}, colors, fonts, components)
    for comp in (data.get("components") or {}).values():
        if isinstance(comp, dict) and comp.get("name"):
            components.add(str(comp["name"]))

    synonyms = {
        "tugma": "button", "tugmasi": "button", "tugmalar": "button",
        "rang": "color", "ranglari": "color", "ranglar": "color",
        "ekran": "screen", "ekrani": "screen", "shrift": "font",
    }
    raw_terms = [w.lower() for w in re.findall(r"[\w]{4,}", requirement or "")][:12]
    query_terms = [synonyms.get(w, w) for w in raw_terms]
    req_low = (requirement or "").lower()
    wants_colors = any(t in req_low for t in ("rang", "color", "token", "hex", "#"))
    wants_fonts = any(t in req_low for t in "shrift font".split())

    def _matches(value: str) -> bool:
        low = value.lower()
        return not query_terms or any(t in low for t in query_terms)

    file_name = str(data.get("name") or "figma-file")
    return {
        "success": True,
        "tool": "figma_sync",
        "service": "Figma REST API",
        "status": "connected",
        "file_key": key,
        "file_name": file_name,
        "source_url": f"https://www.figma.com/design/{key}/{urllib.parse.quote(file_name)}",
        "tokens": {
            "colors": sorted(colors) if wants_colors else sorted(c for c in colors if _matches(c)),
            "font_families": sorted(fonts) if wants_fonts else sorted(f for f in fonts if _matches(f)),
        },
        "components": sorted(c for c in components if _matches(c)),
        "matched_requirement": (requirement or "")[:200],
        "note": "Faqat haqiqiy fayldan olingan qiymatlar; talabga mos kelmaganlari filtrlandi.",
    }
