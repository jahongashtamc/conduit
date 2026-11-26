import os
import re
import sys
import json
import logging
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
import agent_env

LOGGER = logging.getLogger("nexus.cli_runner")

# Bitta boshlang'ich urinish + eng ko'pi 2 ta qayta urinish (cheksiz sikl yo'q).
MAX_ARTIFACT_ATTEMPTS = 3

CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "engine.json"))
AGENTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agents.json"))
# Workspace'ga faqat yupqa yo'naltiruvchi stub ko'chiriladi (kod duplikatsiyasi bo'lmasin).
TOOLS_PY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools_stub.py"))
PYTHON_EXE = sys.executable

# MCP'siz rejim uchun bo'sh MCP konfiguratsiya fayli (claude --strict-mcp-config).
EMPTY_MCP_CONFIG = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "empty_mcp.json"))


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

def load_agents_registry() -> dict:
    """agents.json — universal agent ro'yxati. Yangi agent = bitta yozuv, kod o'zgarmaydi."""
    if os.path.exists(AGENTS_FILE):
        try:
            with open(AGENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            agents = data.get("agents")
            if isinstance(agents, dict) and agents:
                return agents
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[cli_runner] agents.json o'qilmadi ({exc}) — config/engine.json ishlatiladi.", file=sys.stderr)
    return {}


def load_engine_config() -> dict:
    cfg: Dict[str, Any] = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as exc:
            # engine.json bukilgan bo'lsa agents.json ustuvor qoladi, lekin ogohlantiramiz
            print(f"[cli_runner] engine.json o'qilmadi ({type(exc).__name__}: {exc}) — agents.json ishlatiladi", flush=True)
    # Universal ro'yxat: agents.json ustun, engine.json dagi engines esa
    # agents.json da yo'q agentlar uchun zaxira sifatida qoladi.
    registry = load_agents_registry()
    if registry:
        legacy = cfg.get("engines", {})
        merged = dict(legacy)
        merged.update(registry)
        cfg["engines"] = merged
        return cfg
    return cfg or {
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

def resolve_native_executable(resolved: str) -> Optional[str]:
    """claude.CMD kabi Windows wrapper skriptlaridan haqiqiy .exe ni chiqaradi.

    nvm/npm global o'rnatmalar .CMD wrapper qoldiradi; create_subprocess_exec
    ularni to'g'ridan-to'g'ri ocholmaydi (WinError 2), cmd /c esa yo'ldagi
    bo'shliqlarda yiqiladi. Shuning uchun wrapper ichidan haqiqiy .exe yo'lini
    o'qib olamiz (%~dp0 / %dp0% wrapper papkasiga almashtiriladi).
    """
    lower = resolved.lower()
    if lower.endswith(".exe"):
        return resolved
    if not lower.endswith((".cmd", ".bat")):
        return resolved
    try:
        with open(resolved, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"[cli_runner] wrapper o'qilmadi ({resolved}): {exc}", file=sys.stderr)
        return None
    base = os.path.dirname(resolved)
    for match in re.finditer(r'"?([^"\r\n]*?\.exe)"?', text, re.IGNORECASE):
        cand = match.group(1)
        cand = cand.replace("%~dp0", base + os.sep).replace("%dp0%", base + os.sep)
        cand = os.path.normpath(cand.strip('"'))
        if os.path.isfile(cand):
            return cand
    return None


def kill_process_tree(pid: int):
    """Jarayonni barcha bola jarayonlari bilan birga majburiy o'ldiradi."""
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except Exception as exc:
                LOGGER.warning("Bola jarayon o'ldirilmadi (pid %s): %s: %s", getattr(child, 'pid', '?'), type(exc).__name__, exc)
        parent.kill()
    except Exception as exc:
        LOGGER.warning("Jarayon daraxti tozalanmadi (pid %s): %s: %s", pid, type(exc).__name__, exc)

def kill_all_cli_processes():
    for task_id, proc in list(active_processes.items()):
        if proc.returncode is None:
            kill_process_tree(proc.pid)
    active_processes.clear()

class FatalModelError(RuntimeError):
    """Model yoki gateway xatosi: qayta urinishdan foyda yo'q, fallback kerak."""


def extract_token_usage(event: Dict[str, Any]) -> Dict[str, int]:
    """Turli CLI'larning NDJSON hodisalaridan haqiqiy token sarfini ajratadi."""
    candidate: Any = event.get("usage") or {}
    if not isinstance(candidate, dict) or not candidate:
        message = event.get("message")
        if isinstance(message, dict):
            candidate = message.get("usage") or {}
    if not isinstance(candidate, dict) or not candidate:
        result = event.get("result")
        if isinstance(result, dict):
            candidate = result.get("usage") or {}
    if not isinstance(candidate, dict):
        return {}

    def pick(*keys: str) -> int:
        for key in keys:
            value = candidate.get(key)
            if isinstance(value, (int, float)) and value >= 0:
                return int(value)
        return 0

    prompt_tokens = pick("input_tokens", "prompt_tokens", "prompt_token_count", "inputTokens")
    completion_tokens = pick(
        "output_tokens", "completion_tokens", "generated_token_count",
        "outputTokens", "candidates_token_count",
    )
    if not (prompt_tokens or completion_tokens):
        return {}
    return {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}


def merge_usage_snapshot(snapshot: Dict[str, int], event: Dict[str, Any]) -> Dict[str, int]:
    """Cumulative usage hodisalarini qo'shmay, oxirgisini qabul qiladi."""
    usage = extract_token_usage(event)
    if usage:
        snapshot.update(usage)
    return snapshot


def check_model_error(output_text: str) -> Optional[str]:
    """CLI chiqishida 429, auth, cooling down yoki tanilmagan model xatosini aniqlaydi."""
    out_lower = output_text.lower()
    if "429" in output_text or "rate limit" in out_lower or "cooling down" in out_lower or "request rejected" in out_lower:
        return "API Error 429: Model rate limit / credentials cooling down"
    if (
        "no active credentials" in out_lower
        or "failed to authenticate" in out_lower
        or "invalid_api_key" in out_lower
        or "authentication_error" in out_lower
        or "api error: 401" in out_lower
    ):
        return "Auth xatosi: API kalit/credential yaroqsiz yoki yo'q (401) — zaxira modelga o'tish kerak"
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

def _evidence_artifacts(evidence: str, screenshot_path: str = "") -> list:
    """Dalil matnidagi haqiqiy artefakt obyektlari (fayl/URL) ni ajratadi.

    Faqat kalit so'z ('render', 'model', 'figma') dalil emas: checker shu
    artefaktlarning mavjudligini talab qiladi.
    """
    artifacts = [screenshot_path] if screenshot_path else []
    artifacts.extend(re.findall(
        r"(?:[A-Za-z]:[\\/]|/|https?://|[\w.-]+[\\/])[\w./\\:%-]+\."
        r"(?:png|jpe?g|gif|webp|mp4|webm|mov|blend|obj|fbx|glb|gltf|fig|md|json|txt|pdf)\b",
        evidence or "",
        re.IGNORECASE,
    ))
    # Figma dizayn URL'lari kengaytmasiz keladi.
    artifacts.extend(re.findall(r"https?://[^\s,;]+(?:figma\.com|figma)[^\s,;]*", evidence or "", re.IGNORECASE))
    return [a for a in artifacts if isinstance(a, str) and a.strip()]


def _artifact_is_real(path: str) -> bool:
    """Artefakt yo'li haqiqiy, bo'sh bo'lmagan fayl yoki URL ekanini tekshiradi.

    Studiya artefaktlari ko'pincha nisbiy yo'l yoki `/api/screenshots/...`
    shaklida keladi, shuning uchun bir nechta asosiy papka sinovdan o'tkaziladi.
    """
    raw = (path or "").strip()
    if not raw:
        return False
    if raw.startswith(("http://", "https://", "data:")):
        return True
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [raw]
    if not os.path.isabs(raw):
        candidates.extend([
            os.path.join(backend_dir, raw),
            os.path.join(backend_dir, "static", "screenshots", os.path.basename(raw)),
            os.path.join(os.getcwd(), raw),
        ])
    if raw.startswith("/api/screenshots/"):
        candidates.append(os.path.join(backend_dir, "static", "screenshots", os.path.basename(raw)))
    for candidate in candidates:
        try:
            if os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
                return True
        except OSError as exc:
            LOGGER.debug("Artefakt tekshiruvida xato %r: %s", candidate, exc)
    return False


def validate_evidence_against_goal(goal: str, subagent: str, evidence: str, screenshot_path: str = "") -> Tuple[bool, str]:
    """Checker dalilning vazifa talablariga mosligini qat'iy tekshiradi."""
    g_lower = goal.lower()
    e_lower = evidence.lower()
    artifacts = [a for a in _evidence_artifacts(evidence, screenshot_path) if _artifact_is_real(a)]
    has_artifact = bool(artifacts)

    # 1. Figma / Dizayn / Spec vazifalari
    if any(k in g_lower for k in ["figma", "dizayn", "design", "spec", "maket"]):
        # Faqat umumiy dizayn artefakti belgilari — muayyan fayl kaliti/tokeni
        # hardcoded qilib qo'yilmasligi kerak (noto'g'ri musbat natija beradi).
        has_figma = any(k in e_lower for k in ["figma", "spec", "pc_studio_spec.md", ".fig", "diagram"])
        if not has_figma or ("localhost:3000" in e_lower and "figma" not in e_lower):
            return False, "Yolg'on dalil rad etildi: Vazifa Figma dizayni talab qilgan, lekin lokal veb-skrinshot taqdim etildi. Figma spec yoki dizayn fayli mavjud emas."
        if not has_artifact:
            return False, "Dalil rad etildi: Figma/dizayn vazifasi uchun aniq artefakt (fayl yoki dizayn URL) topilmadi — faqat so'zlar bor."

    # 2. 3D / Blender / Sculptor vazifalari
    if any(k in g_lower for k in ["blender", "3d", "model", "sculpt", "mesh", "render"]) or subagent == "sculptor":
        has_3d = any(k in e_lower for k in ["blender", "3d", "render", "snapshot", "model", "cube", "sphere", "obj", "blend", "scene"])
        if not has_3d:
            return False, "Dalil rad etildi: 3D Blender render yoki model artefakti topilmadi."
        visual_artifacts = [a for a in artifacts if re.search(
            r"\.(?:png|jpe?g|gif|webp|mp4|webm|mov|blend|obj|fbx|glb|gltf)$", a, re.IGNORECASE
        )]
        if not visual_artifacts:
            return False, "Dalil rad etildi: 3D vazifa uchun ko'rinadigan artefakt (png/mp4/blend/obj) topilmadi — faqat kalit so'zlar bor."

    # 3. Google / Veb qidiruv vazifalari
    if any(k in g_lower for k in ["google", "qidir", "search"]):
        has_search = any(k in e_lower for k in ["google", "qidiruv", "search", "natija"]) or ("screenshot" in e_lower and "localhost" not in e_lower)
        if not has_search:
            return False, "Dalil rad etildi: Google qidiruv natijasi yoki veb-skrinshot topilmadi."
        if not has_artifact:
            return False, "Dalil rad etildi: Qidiruv vazifasi uchun skrinshot/artefakt yo'q — faqat matn bor."

    return True, "Dalil vazifaga to'liq mos keladi."


def goal_check_passed(goal_check: Dict[str, Any]) -> bool:
    """Faqat aniq PASS verdicti qabul qilinadi; matn yoki success dalil emas."""
    return goal_check.get("verdict") == "PASS"


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

    # Bo'sh MCP konfiguratsiyasi workspace_manager.get_agent_workspace() da yoziladi.
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
    _noise_count = 0  # NDJSON bo'lmagan CLI shovqin qatorlari hisoblagichi
    # Provider to'g'ridan-to'g'ri e'lon qilgan token sarfi (taxmin o'rniga).
    # MUHIM: agy/claude har bir bosqichda CUMULATIVE usage yuboradi — ularni
    # qo'shib bo'lmaydi. Oxirgi (result) hodisa yakuniy hisob hisoblanadi.
    usage_snapshot: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0}

    def with_usage(res: Dict[str, Any]) -> Dict[str, Any]:
        res["usage"] = dict(usage_snapshot)
        return res

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
            # MCP'siz rejim: agent ro'yxatida mcp_free_args bo'lsa ular qo'shiladi.
            # Bu faqat Conduit chaqiruvi uchun — foydalanuvchining global
            # sozlamalariga tegilmaydi. claude: ~60s -> ~9s.
            mcp_free = engine_meta.get("mcp_free_args") or []
            for extra in mcp_free:
                argv.append(str(extra).replace("{mcp_config}", EMPTY_MCP_CONFIG))
            # Windows: .cmd/.bat fayllar (masalan nvm'dagi claude.CMD) create_subprocess_exec
            # bilan to'g'ridan-to'g'ri ochilmaydi (WinError 2) — cmd /c orqali o'raymiz.
            # Haqiqiy .exe bo'lsa to'liq yo'lgan almashtiramiz (PATH bog'liqligi yo'qoladi).
            if argv and not os.path.isabs(argv[0]):
                resolved = shutil.which(argv[0])
                if resolved:
                    native = resolve_native_executable(resolved)
                    if native:
                        argv[0] = native
                    else:
                        err = (
                            f"CLI wrapper haqiqiy .exe ga aniqlanmadi: {resolved}. "
                            f"agents.json dagi binary'ni to'g'ridan-to'g'ri .exe yo'liga almashtiring."
                        )
                        database.add_log(task_id, subagent, "ERROR", err)
                        return with_usage({"success": False, "is_blocked": True, "error": err, "output": ""})
            argv = [a.replace("__CONDUIT_PROMPT__", agent_prompt_raw) for a in argv]
        except Exception as exc:
            LOGGER.warning("CLI buyrug'i parchalanmadi, shell rejimiga qaytildi: %s: %s", type(exc).__name__, exc)
            use_exec = False
            argv = None

        # Stream rejada agy NDJSON hodisalarni real vaqtda chiqaradi (text
        # rejada esa hammasi oxirigacha buferlanadi — heartbeat noto'g'ri
        # o'lchaydi). Yakuniy matn result hodisasidan olinadi.
        # stream_json=True so'rovi faqat stream-json'ni QO'LLOVCHI dvigatellarga
        # qo'llanadi (codex --json, claude/agy --output-format). Boshqa CLI'lar
        # (opencode, crush) matn rejimida ishlaydi — aks holda ular noma'lum
        # flag bilan yordam matnini chiqarib, 1 kod bilan chiqadi.
        engine_supports_stream = bool(
            engine_meta.get("stream_json_flag") or (argv and "--output-format" in argv)
        )
        if stream_json and use_exec and argv and engine_supports_stream:
            sj_flag = engine_meta.get("stream_json_flag")
            if sj_flag:
                # Ba'zi CLI'lar (codex) stream rejani alohida flag bilan yoqadi.
                if sj_flag not in argv:
                    argv.append(sj_flag)
            elif "--output-format" in argv:
                oi = argv.index("--output-format")
                if oi + 1 < len(argv):
                    argv[oi + 1] = "stream-json"
            else:
                argv += ["--output-format", "stream-json"]
            # Ba'zi CLI'lar stream-json uchun qo'shimcha flag talab qiladi
            # (masalan claude: --verbose). agents.json dan o'qiladi.
            for extra in engine_meta.get("stream_json_extra_args") or []:
                if extra not in argv:
                    argv.append(extra)

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
            # Agent'ga xos env + MCP'siz izolyatsiyalangan HOME (agar sozlangan bo'lsa).
            proc_env = None
            extra_env = dict(engine_meta.get("env") or {})
            # tools.py ichida role.md allowlist'ni qo'llash va dalil yangiligini
            # tekshirish uchun chaqiruv kontekstini uzatamiz (global sozlamaga tegmaydi).
            extra_env.update({
                "CONDUIT_AGENT": subagent,
                "CONDUIT_TASK_ID": task_id,
                "CONDUIT_TASK_STARTED_AT": str(time.time()),
            })
            if engine_meta.get("isolated_home"):
                extra_env.update(agent_env.isolated_home(True))
            if extra_env:
                proc_env = os.environ.copy()
                proc_env.update({str(k): str(v) for k, v in extra_env.items()})
            if use_exec and argv:
                proc = await asyncio.create_subprocess_exec(
                    *argv,
                    cwd=ws_dir,
                    env=proc_env,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    limit=4 * 1024 * 1024  # stream-json katta NDJSON qatorlari (64KB default yetmaydi)
                )
            else:
                proc = await asyncio.create_subprocess_shell(
                    cmd_str,
                    cwd=ws_dir,
                    env=proc_env,
                    stdin=asyncio.subprocess.DEVNULL,  # CLI stdin kutib qotmasligi uchun
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    limit=4 * 1024 * 1024
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
                nonlocal _noise_count
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
                    if stream_json and engine_supports_stream and line.startswith("{"):
                        try:
                            ev = json.loads(line)
                        except Exception as exc:
                            LOGGER.debug("NDJSON qatori o'qilmadi: %s: %s", type(exc).__name__, exc)
                            ev = None
                        if ev:
                            # Universal token usage: agy/claude/codex hodisalarida
                            # usage.message.usage yoki result.usage bo'lishi mumkin.
                            # Qo'shish emas: har hodisa jamini qayta e'lon qiladi.
                            merge_usage_snapshot(usage_snapshot, ev)
                            # UNIVERSAL NDJSON parser: agy {"event": ...} formatida,
                            # claude {"type": ...} formatida hodisa yuboradi.
                            etype = ev.get("event") or ev.get("type") or ""
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
                            elif etype == "assistant":
                                # claude: agent javob matni assistant hodisalarida keladi.
                                msg = ev.get("message", {}) or {}
                                for block in (msg.get("content") or []):
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        txt = (block.get("text") or "").strip()
                                        if txt:
                                            safe_line = security_guard.sanitize_text(txt)
                                            collected_output.append(safe_line)
                                            log_entry = database.add_log(task_id, subagent, "INFO", safe_line)
                                            if ws_broadcast:
                                                await ws_broadcast({"type": "log", "task_id": task_id, "data": log_entry})
                            elif etype == "item.completed":
                                # codex: {"type":"item.completed","item":{"type":"agent_message","text":"..."}}
                                item = ev.get("item", {}) or {}
                                itype = item.get("type", "")
                                if itype == "agent_message":
                                    txt = (item.get("text") or "").strip()
                                    if txt:
                                        safe_line = security_guard.sanitize_text(txt)
                                        collected_output.append(safe_line)
                                        log_entry = database.add_log(task_id, subagent, "INFO", safe_line)
                                        if ws_broadcast:
                                            await ws_broadcast({"type": "log", "task_id": task_id, "data": log_entry})
                                elif itype == "error":
                                    msg = f"[codex] {item.get('message', '')[:200]}"
                                    log_entry = database.add_log(task_id, subagent, "WARNING", msg)
                                    if ws_broadcast:
                                        await ws_broadcast({"type": "log", "task_id": task_id, "data": log_entry})
                            elif etype == "turn.completed":
                                stream_final["status"] = "success"
                            elif etype == "result":
                                # agy: {"event":"result","result":{"response":...}}
                                # claude: {"type":"result","subtype":"success","result":"..."}
                                rr = ev.get("result", {})
                                if isinstance(rr, dict):
                                    stream_final["text"] = (rr.get("response") or rr.get("result") or "")
                                    stream_final["status"] = (rr.get("status") or rr.get("subtype") or "")
                                elif rr:
                                    stream_final["text"] = str(rr)
                                    stream_final["status"] = ev.get("subtype") or ""
                            continue

                    if stream_json and engine_supports_stream:
                        # NDJSON bo'lmagan qatorlar (claude retry ogohlantirislari,
                        # stderr shovqini) — jimjit yutilmaydi, DEBUG sifatida ko'rinadi.
                        # Har 5-chi qator log'ga yoziladi (shovqin cheklovi).
                        _noise_count += 1
                        if _noise_count % 5 == 1:
                            log_entry = database.add_log(task_id, subagent, "DEBUG", f"[cli] {line[:160]}")
                            if ws_broadcast:
                                await ws_broadcast({"type": "log", "task_id": task_id, "data": log_entry})
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
                                catalog_cmds = {"list_tools", "help", "--help", "-h"}
                                if tool_name and tool_name.lower() not in allowed_tools and tool_name.lower() not in catalog_cmds:
                                    block_msg = f"XAVFSIZLIK TO'SIG'I: '{tool_name}' tooliga subagent role.md da ruxsat berilmagan! Rad etildi."
                                    database.add_log(task_id, subagent, "ERROR", block_msg)
                                    continue
                        except ValueError as exc:
                            LOGGER.debug("tools.py buyruq nomi ajratilmadi: %s: %s", line[:80], exc)

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
                return with_usage({
                    "success": False,
                    "model_error": str(fe),
                    "model": target_model,
                    "returncode": proc.returncode,
                    "output": "\n".join(collected_output),
                })
            except asyncio.TimeoutError as te:
                kill_process_tree(proc.pid)
                timeout_msg = str(te) or f"Heartbeat timeout: {heartbeat_timeout}s davomida hech qanday chiqish bo'lmadi."
                return with_usage({"success": False, "is_blocked": True, "heartbeat_timeout": True, "error": timeout_msg, "output": "\n".join(collected_output)})

            if stream_final.get("text"):
                collected_output.append(stream_final["text"])
            full_out = "\n".join(collected_output)
            model_err = check_model_error(full_out)
            empty_err = looks_like_empty_success(full_out, proc.returncode)
            if empty_err:
                database.add_log(task_id, subagent, "ERROR", empty_err)
            return with_usage({
                "success": proc.returncode == 0 and not model_err and not empty_err,
                "model_error": model_err or empty_err,
                "model": target_model,
                "returncode": proc.returncode,
                "output": full_out
            })
        except Exception as e:
            err = f"CLI xatosi: {str(e)}"
            database.add_log(task_id, subagent, "ERROR", err)
            return with_usage({"success": False, "is_blocked": True, "error": err, "output": ""})

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
                    return with_usage(fallback_res)
                else:
                    fb_err = fallback_res.get("model_error") or "Zaxira model ham muvaffaqiyatsiz bo'ldi."
                    final_err = f"Model xatosi (429/tanilmadi): [{primary_model} -> {fallback_model}]: {fb_err}"
                    database.add_log(task_id, subagent, "ERROR", final_err)
                    return with_usage({
                        "success": False,
                        "is_blocked": True,
                        "error": final_err,
                        "output": fallback_res.get("output", "")
                    })
            else:
                final_err = f"Model xatosi [{primary_model}]: {primary_err}"
                database.add_log(task_id, subagent, "ERROR", final_err)
                return with_usage({"success": False, "is_blocked": True, "error": final_err, "output": run_res.get("output", "")})

        if isinstance(run_res, dict) and stream_final.get("text"):
            run_res["final_text"] = stream_final["text"]
            run_res["stream_status"] = stream_final.get("status", "")
        return with_usage(run_res)
    finally:
        if task_id in active_processes:
            del active_processes[task_id]

def load_inner_guides(subagent: str) -> str:
    """subagents/<id>/inner/{planner,doer,checker}.md ni promptga yig'adi.

    Ilgari bu fayllar hech qayerda o'qilmasdi: `run_real_agent_loop` faqat
    `role.md` ni promptga qo'shardi, holbuki docstring "PLANNER: role.md va
    inner/planner.md dan ko'rsatma yig'ib reja tuzadi" deb yozilgan edi.
    Natijada `painter/inner/doer.md` kabi qisqa fayllar butunlay e'tiborsiz
    qolardi va agent qaysi tool'ni qanday chaqirishini bilmasdi.

    Bo'sh yoki topilmagan fayllar jimgina o'tkazib yuboriladi (blok umuman
    qo'shilmaydi), shuning uchun inner papkasi bo'lmagan yangi subagentlar
    avvalgidek ishlayveradi.
    """
    inner_dir = os.path.join(security_guard.SUBAGENTS_DIR, subagent, "inner")
    if not os.path.isdir(inner_dir):
        return ""
    parts: list[str] = []
    for step, title in (
        ("planner", "REJA (planner)"),
        ("doer", "BAJARISH (doer)"),
        ("checker", "TEKSHIRISH (checker)"),
    ):
        path = os.path.join(inner_dir, f"{step}.md")
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                body = fh.read().strip()
        except OSError as exc:
            LOGGER.warning("inner/%s.md o'qilmadi (%s): %s", step, subagent, exc)
            continue
        if not body:
            continue
        # Sarlavha (# ...) qatorini olib tashlaymiz — blok o'z sarlavhasini beradi.
        lines = [ln for ln in body.splitlines() if not ln.lstrip().startswith("# ")]
        body = "\n".join(lines).strip()
        if body:
            parts.append(f"### {title}\n{body}")
    if not parts:
        return ""
    return "## Ichki bosqich ko'rsatmalari (inner/*.md)\n" + "\n\n".join(parts) + "\n\n"


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
    except Exception as exc:
        LOGGER.error("Agent uslubi konteksti olinmadi: %s: %s", type(exc).__name__, exc)
        style_context = ""

    agent_prompt = (
        f"Sen '{subagent}' subagentining haqiqiy ijrochisisan. Vazifani O'ZING bajaring.\n\n"
        f"## Roling (role.md)\n{role_text}\n\n"
        + load_inner_guides(subagent)
        + f"## Vazifa\n{task_goal}\n\n"
        + (f"## Foydalanuvchi uslubi\n{style_context}\n\n" if style_context else "")
        + "## Qoidalar (qat'iy)\n"
        "1. FAQAT yuqoridagi vazifani bajar. So'ralmagan ish, qo'shimcha fayl o'qish, "
        "boshqa papkalarni o'rganish, kod o'zgartirish yoki qo'shimcha buyruq chaqirish TAQIQLANGAN.\n"
        "2. Vazifa noaniq bo'lsa — taxmin qilma, foydalanuvchidan aniq so'ra.\n"
        "3. Ishchi papkada tools.py bor. Toollarni o'zing bajaring: python tools.py <tool> [args]\n"
        f"4. Senga ruxsat etilgan toollar: {', '.join(allowed)}. Boshqa tool ishlatish taqiqlanadi.\n"
        "5. CLI sintaksisi kerak bo'lsa, faqat `conduit --help` yoki `conduit list --json` bilan cheklan.\n"
        "6. Yolg'on natija chiqarma — har amal real chiqish bilan tasdiqlansin.\n"
        '7. Yakunda o\'z ishingni tekshir: python tools.py check_goal "<vazifa>" "{}"\n'
        "8. Oxirgi qator aynan shu formatda bo'lsin: VERDICT: PASS <qisqa dalil> yoki VERDICT: FAIL <sabab>\n"
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
        return {"status": "BLOCKED", "evidence": err, "usage": result.get("usage")}

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
        return {"status": "PASS", "evidence": evidence, "usage": result.get("usage")}

    # FAIL — agentning o'z sababiga ishonch, lekin bo'sh bo'lsa umumiy sabab.
    fail_reason = verdict_detail.strip()[:300] or "Agent o'zi FAIL deb qaror qildi."
    database.add_log(task_id, subagent, "WARN", f"Agent FAIL qaytardi: {fail_reason}")
    await notify("checker", "FAIL", evidence=fail_reason, dur=0.0)
    database.update_task_step(task_id, "completed", "FAIL", evidence=fail_reason, step_durations=step_durations, total_duration=round(time.time() - start, 2))
    if ws_broadcast:
        await ws_broadcast({"type": "task_completed", "task_id": task_id, "status": "FAIL", "evidence": fail_reason, "step_durations": step_durations, "total_duration": round(time.time() - start, 2)})
    return {"status": "FAIL", "evidence": fail_reason, "usage": result.get("usage")}


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

    previous_failure = ""

    for attempt in range(1, MAX_ARTIFACT_ATTEMPTS + 1):
        retry_note = ""
        if previous_failure:
            retry_note = (
                f"\nOldingi urinish FAIL sababi: {previous_failure}\n"
                "Bu sababni bartaraf et; eski dalilni qayta ishlatma.\n"
            )
            database.add_log(
                task_id, subagent, "WARN",
                f"Qayta urinish {attempt}/{MAX_ARTIFACT_ATTEMPTS}: oldingi FAIL sababi: {previous_failure}",
            )
        # 1. PLANNER
        await notify("planner", "working")
        t_planner_start = time.time()
        # Instrument agentlari LLM rejasiz ishlaydi: prompt o'zi to'g'ridan-to'g'ri
        # asbob ko'rsatmasi (masalan, rasm tavsifi yoki URL). Bu ularni agy
        # stall'lariga bog'liq emas qiladi va bir necha baravar tezlashtiradi.
        if subagent.startswith("inst_"):
            plan_res = {
                "success": True,
                "output": f"Instrument agent: LLM rejasiz to'g'ridan-to'g'ri bajarish. Ko'rsatma: {task_goal[:120]}{retry_note}",
                "returncode": 0,
            }
            dur_planner = 0.0
        else:
            # Learned user-style context: language, tone, past similar exchanges.
            try:
                style_context = user_memory.build_style_context(task_goal)
            except Exception as exc:
                LOGGER.error("Planner uslub konteksti olinmadi: %s: %s", type(exc).__name__, exc)
                style_context = ""
            planner_prompt = (
                f"Vazifa: {task_goal}\n"
                + (f"{style_context}\n" if style_context else "")
                + (f"{retry_note}\n" if retry_note else "")
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
            from app_adapter import build_scene_script_from_goal, parse_visual_spec
            visual_spec = parse_visual_spec(task_goal)
            model_title = "nexus_3d_scene"
            bpy_code = build_scene_script_from_goal(task_goal)
            database.add_log(
                task_id, subagent, "INFO",
                f"Doer talab bo'yicha sahnani qurmoqda: shakllar={visual_spec['shapes']}, "
                f"ranglar={visual_spec['colors']}, soni={visual_spec['count']}",
            )
            shot_res = tools.tool_blender_headless(bpy_code, model_name=model_title)
            screenshot_path = shot_res.get("output_render", "")
            preview_url = shot_res.get("web_preview_url", "")
            target_url = f"blender://scene/{model_title}"
            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = (
                f"Amal: tools.py blender_headless_exec {model_title}\n"
                f"Talab: shakllar={visual_spec['shapes']}, ranglar={visual_spec['colors']}, "
                f"soni={visual_spec['count']}, material={visual_spec['material']}, "
                f"matn={visual_spec['text'] or 'yoq'}\n"
                f"Render fayli: {screenshot_path}\nVaqt: {dur_doer}s"
            )
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
            role_ok = False
            if subagent == "painter":
                database.add_log(task_id, subagent, "INFO", "Doer gen_image bilan rasm yaratmoqda...")
                art = tools.tool_gen_image(task_goal, 512, 512)
                role_ok = bool(art.get("success"))
                if art.get("success"):
                    shutil.copyfile(art["image_path"], preview_png)
                    doer_out_summary = f"Amal: tools.py gen_image\nRasm: {art['image_path']}\nHajm: {art['bytes']}b"
                else:
                    doer_out_summary = f"gen_image xato: {art.get('error')}"
            elif subagent == "editor":
                database.add_log(task_id, subagent, "INFO", "Doer video_render bilan haqiqiy kliplardan MP4 yaratmoqda...")
                clips = tools.extract_media_paths(task_goal)
                vid = tools.tool_video_render(task_goal, 0.0, inputs=clips)
                role_ok = bool(vid.get("success"))
                if vid.get("success"):
                    preview_from_video = vid.get("web_preview_url")
                    if preview_from_video:
                        src = os.path.join(tools.get_static_screenshots_dir(), "editor_preview.png")
                        if os.path.exists(src):
                            shutil.copyfile(src, preview_png)
                    doer_out_summary = (
                        f"Amal: tools.py video_render (haqiqiy montaj)\n"
                        f"Kirish kliplari: {', '.join(vid['inputs'])}\n"
                        f"Video: {vid['video_path']}\nKadrlar: {vid['frames']} @ {vid['fps']}fps\n"
                        f"Hajm: {vid['bytes']}b"
                    )
                else:
                    doer_out_summary = f"video_render xato: {vid.get('error')}"
            else:  # animator
                database.add_log(task_id, subagent, "INFO", "Doer anim_render bilan animatsiya yaratmoqda...")
                anim = tools.tool_anim_render("", 2.0)
                role_ok = bool(anim.get("success"))
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
            await notify("doer", "PASS" if role_ok else "FAIL", out=doer_out_summary, screenshot_url=preview_url, dur=dur_doer)
        elif subagent.startswith("inst_"):
            # Instrument yordamchi agentlari: har biri o'z dvigatelini
            # to'g'ridan-to'g'ri ishlatadi (butun ilova emas, faqat zarur qatlam).
            inst = subagent
            inst_ok = False
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
                inst_ok = bool(shot_res.get("success"))
                if inst_ok:
                    doer_out_summary = f"Amal: tools.py blender_headless_exec {model_title}\nRender: {screenshot_path}"
                else:
                    doer_out_summary = f"blender_headless_exec xato: {shot_res.get('error')}"
            elif inst == "inst_video":
                database.add_log(task_id, inst, "INFO", "Doer video_render bilan haqiqiy kliplardan MP4 yaratmoqda...")
                clips = tools.extract_media_paths(task_goal)
                vid = tools.tool_video_render(
                    task_goal, 0.0, output_path=os.path.join(tools._agent_out_dir(inst), "render.mp4"),
                    inputs=clips,
                )
                inst_ok = bool(vid.get("success"))
                if inst_ok:
                    doer_out_summary = f"Amal: tools.py video_render\nVideo: {vid['video_path']}\nKadrlar: {vid['frames']} @ {vid['fps']}fps"
                else:
                    doer_out_summary = f"video_render xato: {vid.get('error')}"
            elif inst == "inst_image":
                # O'lcham vazifa matnidan olinadi ("640x480 png yarat"); avval
                # bu yerda 512x512 qattiq kodlangan edi va so'ralgan o'lcham
                # butunlay yo'qolar, agent esa baribir PASS olardi.
                from app_adapter import parse_image_size

                width_, height_ = parse_image_size(task_goal)
                database.add_log(
                    task_id, inst, "INFO",
                    f"Doer gen_image bilan rasm yaratmoqda ({width_}x{height_})...",
                )
                art = tools.tool_gen_image(task_goal, width_, height_, agent_id=inst)
                inst_ok = bool(art.get("success"))
                if inst_ok:
                    doer_out_summary = (
                        f"Amal: tools.py gen_image\nRasm: {art['image_path']}\n"
                        f"O'lcham: {width_}x{height_}\nHajm: {art['bytes']}b"
                    )
                else:
                    doer_out_summary = f"gen_image xato: {art.get('error')}"
            elif inst == "inst_web":
                import re as _re
                url_m = _re.search(r"https?://\S+", task_goal)
                if url_m:
                    target_url = url_m.group(0).rstrip(".,;)")
                    database.add_log(task_id, inst, "INFO", f"Doer interact_web bilan sahifani ochmoqda: {target_url}")
                    page = tools.tool_interact_web(target_url)
                    inst_ok = bool(page.get("success"))
                    doer_out_summary = f"Amal: tools.py interact_web\nURL: {target_url}\nNatija: {str(page.get('output', page.get('error', '')))[:200]}"
                else:
                    database.add_log(task_id, inst, "INFO", f"Doer web_search bilan qidirmoqda: {task_goal[:60]}")
                    sr = tools.tool_web_search(task_goal, 5)
                    inst_ok = bool(sr.get("success"))
                    if inst_ok:
                        lines = "\n".join(f"- {r['title'][:70]}: {r['url'][:90]}" for r in sr["results"])
                        doer_out_summary = f"Amal: tools.py web_search '{task_goal[:60]}'\nNatijalar:\n{lines}"
                    else:
                        doer_out_summary = f"web_search xato: {sr.get('error')}"
            elif inst == "inst_figma":
                database.add_log(task_id, inst, "INFO", "Doer figma_sync bilan dizayn ma'lumotlarini olmoqda...")
                fig = tools.tool_figma_sync()
                inst_ok = bool(fig.get("success"))
                doer_out_summary = f"Amal: tools.py figma_sync\nNatija: {str(fig.get('output', fig.get('error', '')))[:200]}"

            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = f"{doer_out_summary}\nVaqt: {dur_doer}s"
            await notify("doer", "PASS" if inst_ok else "FAIL", out=doer_out_summary, screenshot_url=preview_url, dur=dur_doer)
        elif subagent == "designer":
            database.add_log(task_id, subagent, "INFO", "Doer Figma REST API'dan haqiqiy faylni olmoqda...")
            figma_res = tools.tool_figma_sync(requirement=task_goal)
            from app_adapter import STATIC_SCREENSHOTS
            preview_png = os.path.join(STATIC_SCREENSHOTS, "designer_preview.png")
            designer_ok = bool(figma_res.get("success"))
            if designer_ok:
                # Haqiqiy API natijasining qisqa vizual xulosasi (soxta Figma skrinshoti emas).
                try:
                    from PIL import Image, ImageDraw
                    img = Image.new("RGB", (960, 540), (15, 23, 42))
                    draw = ImageDraw.Draw(img)
                    tokens = figma_res.get("tokens") or {}
                    lines = [
                        "FIGMA REST API - REAL FILE DATA",
                        f"File: {str(figma_res.get('file_name', ''))[:48]}",
                        f"Components: {len(figma_res.get('components') or [])}",
                        f"Colors: {len(tokens.get('colors') or [])}",
                        f"Fonts: {len(tokens.get('font_families') or [])}",
                        str(figma_res.get("source_url", ""))[:70],
                    ]
                    for idx, line in enumerate(lines):
                        draw.text((24, 24 + idx * 28), line, fill=(226, 232, 240))
                    os.makedirs(STATIC_SCREENSHOTS, exist_ok=True)
                    img.save(preview_png, "PNG")
                    shutil.copyfile(preview_png, os.path.join(STATIC_SCREENSHOTS, "latest.png"))
                    screenshot_path = preview_png
                    preview_url = "/static/screenshots/designer_preview.png"
                    target_url = figma_res.get("source_url") or "https://www.figma.com"
                except Exception as exc:
                    designer_ok = False
                    database.add_log(task_id, subagent, "ERROR", f"Figma preview yaratilmadi: {exc}")
                    figma_res = {"error": f"Preview yaratilmadi: {exc}"}
            dur_doer = round(time.time() - t_doer_start, 2)
            if designer_ok:
                doer_out_summary = (
                    f"Amal: Figma REST API ({figma_res.get('file_name')})\n"
                    f"Manba: {figma_res.get('source_url')}\n"
                    f"Komponentlar: {len(figma_res.get('components') or [])} ta\n"
                    f"Ranglar: {len((figma_res.get('tokens') or {}).get('colors') or [])} ta\n"
                    f"Vaqt: {dur_doer}s"
                )
            else:
                doer_out_summary = f"Figma olinmadi: {figma_res.get('error') or figma_res.get('status')} (Vaqt: {dur_doer}s)"
            await notify("doer", "PASS" if designer_ok else "FAIL", out=doer_out_summary,
                         screenshot_url=preview_url if designer_ok else None, dur=dur_doer)
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
                '{"health": "%s", "pytest_tail": "%s", "captured_at": %f}'
                % (
                    "ok" if health.get("success") else "fail",
                    stdout_tail.replace('"', "'").replace("\n", " "),
                    time.time(),
                ),
            )
            dur_doer = round(time.time() - t_doer_start, 2)
            doer_out_summary = (
                f"Amal: health_probe + pytest\nHealth: {health.get('success')}\n"
                f"Pytest: {stdout_tail.strip()[-180:]}\nVaqt: {dur_doer}s"
            )
            # success faqat "checker ishga tushdi" degani; haqiqiy natija verdict.
            passed = goal_check_passed(check_res) and bool(health.get("success"))
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
            goal_check = tools.tool_check_goal(
                task_goal,
                json.dumps({
                    "evidence": (doer_out_summary or "")[:1500],
                    "captured_at": time.time(),
                }),
            )
            if goal_check_passed(goal_check):
                verdict = "PASS"
            else:
                # ESKI XATO: doer matni bor ekan, verdict FAIL bo'lsa ham PASS edi.
                issues = goal_check.get("issues") or goal_check.get("checks") or []
                fail_reason = " | ".join(str(x) for x in issues[:2]) or (
                    goal_check.get("error") or "check_goal talablari bajarilmadi."
                )
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
                ev_summary = json.dumps({
                    "screenshot": screenshot_path,
                    "target_url": target_url,
                    "captured_at": time.time(),
                })
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
            except Exception as exc:
                # Xotira yangilanmasa vazifa natijasiga ta'sir qilmaydi, lekin jim yutilmaydi
                database.add_log(task_id, subagent, "WARNING", f"Xotira yangilanmadi: {type(exc).__name__}: {exc}")
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
            previous_failure = fail_reason
            database.add_log(
                task_id, subagent, "WARNING",
                f"Aylanish {attempt}/{MAX_ARTIFACT_ATTEMPTS} {evidence_str}. "
                + ("Qayta urinilmoqda..." if attempt < MAX_ARTIFACT_ATTEMPTS else "Qayta urinish tugadi."),
            )
            if attempt < MAX_ARTIFACT_ATTEMPTS:
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
    except Exception as exc:
        database.add_log(task_id, subagent, "WARNING", f"Xotira (FAIL) yangilanmadi: {type(exc).__name__}: {exc}")
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
