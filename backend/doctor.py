"""Conduit tizim salomatligi tekshiruvi (doctor).

MVP uchun asosiy talab: foydalanuvchi dasturni birinchi marta ishga tushirganda
"nima ishlamayapti?" savoliga bir buyruq bilan javob olishi kerak.

    python conduit.py doctor

Har bir tekshiruv (name, status, detail) qaytaradi:
    OK   — ishlaydi
    WARN — ishlaydi, lekin cheklov bor (masalan token sozlanmagan)
    FAIL — MVP uchun zarur narsa yetishmaydi
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from typing import List, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

Check = Tuple[str, str, str]  # (nom, holat, tafsilot)


def _check(name: str, ok: bool, detail: str, warn_only: bool = False) -> Check:
    if ok:
        return (name, "OK", detail)
    return (name, "WARN" if warn_only else "FAIL", detail)


def check_python() -> Check:
    v = sys.version_info
    ok = v >= (3, 10)
    return _check("Python", ok, f"{v.major}.{v.minor}.{v.micro} (3.10+ kerak)")


def check_node() -> Check:
    p = shutil.which("node")
    if not p:
        return ("Node.js", "FAIL", "topilmadi — frontend va live brauzer uchun kerak")
    try:
        out = subprocess.run([p, "--version"], capture_output=True, text=True, timeout=15)
        return _check("Node.js", out.returncode == 0, out.stdout.strip() or "o'rnatilgan")
    except Exception as e:
        return ("Node.js", "FAIL", str(e)[:80])


def check_python_packages() -> List[Check]:
    res = []
    for mod, minfo in (
        ("httpx", "backend HTTP so'rovlari"),
        ("psutil", "jarayon boshqaruvi"),
        ("PIL", "painter gen_image"),
        ("numpy", "hisob-kitob"),
        ("websockets", "terminal WebSocket"),
    ):
        try:
            __import__(mod)
            res.append((mod, "OK", minfo))
        except ImportError:
            res.append((mod, "FAIL", f"o'rnatilmagan — {minfo} uchun kerak"))
    return res


def check_playwright() -> Check:
    try:
        import playwright  # noqa: F401
    except ImportError:
        return ("Playwright", "FAIL", "modul o'rnatilmagan (frontend/node_modules ham bo'lsa, python uchun kerak)")
    # Chromium binary tekshiruvi.
    local = os.path.expandvars(r"%LOCALAPPDATA%\ms-playwright")
    has_chromium = os.path.isdir(local) and any("chromium" in d for d in os.listdir(local))
    if not has_chromium:
        return ("Playwright", "WARN", "modul bor, lekin chromium topilmadi (scout brauzeri ishlamasligi mumkin)")
    return ("Playwright", "OK", "modul + chromium tayyor")


def check_ffmpeg() -> Check:
    p = shutil.which("ffmpeg")
    return _check("FFmpeg", bool(p), p or "topilmadi — editor video_render ishlamaydi (winget install Gyan.FFmpeg)")


def check_blender() -> Check:
    import glob
    cands = glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe")
    exe = next((c for c in cands if os.path.exists(c)), None)
    if not exe:
        return ("Blender", "WARN", "topilmadi — sculptor simulyatsiya rejimida ishlaydi")
    return ("Blender", "OK", exe)


def check_cli_engines() -> List[Check]:
    res = []
    for name, binary in (("agy (Gemini)", "agy"), ("claude", "claude")):
        p = shutil.which(binary)
        res.append(_check(f"CLI: {name}", bool(p), p or "PATH'da yo'q", warn_only=(name != "agy (Gemini)")))
    return res


def check_engine_connection() -> Check:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/engine/status", timeout=6) as r:
            d = json.loads(r.read().decode("utf-8"))
        active = d.get("active_engine") or "?"
        connected = d.get("is_connected", d.get("connected", False))
        return _check(
            "Engine ulanishi", bool(connected),
            f"active={active}, ulanmagan — CLI javob bermayapti" if not connected else f"active={active}",
        )
    except Exception as e:
        return ("Engine ulanishi", "WARN", f"backend ishlamayapti ({str(e)[:50]}) — CONDUIT.bat bilan ishga tushiring")


def check_services() -> List[Check]:
    res = []
    for name, url in (("Backend API", "http://127.0.0.1:8000/api/health"), ("Frontend", "http://localhost:3000/")):
        try:
            with urllib.request.urlopen(url, timeout=6) as r:
                res.append(_check(name, r.status == 200, f"HTTP {r.status}"))
        except Exception as e:
            res.append((name, "WARN", f"isga tushmagan ({str(e)[:40]}) — CONDUIT.bat ishga tushiring"))
    return res


def check_database() -> Check:
    try:
        import sqlite3
        db = os.path.join(BACKEND, "conduit.db")
        con = sqlite3.connect(db, timeout=5)
        n = con.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        con.close()
        return _check("Ma'lumotlar bazasi", True, f"{os.path.basename(db)}, {n} vazifa")
    except Exception as e:
        return ("Ma'lumotlar bazasi", "FAIL", str(e)[:80])


def check_tokens() -> List[Check]:
    res = []
    for name, env in (("Notion tokeni", "NOTION_TOKEN"), ("Slack tokeni", "SLACK_BOT_TOKEN"), ("GitHub tokeni", "GITHUB_TOKEN")):
        has = bool(os.environ.get(env, "").strip())
        res.append(_check(name, has, "sozlangan" if has else "sozlanmagan (ixtiyoriy)", warn_only=True))
    return res


def run_all_checks() -> List[Check]:
    checks: List[Check] = [check_python(), check_node()]
    checks += check_python_packages()
    checks += [check_playwright(), check_ffmpeg(), check_blender()]
    checks += check_cli_engines()
    checks += [check_engine_connection()]
    checks += check_services()
    checks += [check_database()]
    checks += check_tokens()
    return checks


def run_doctor(verbose: bool = True) -> Tuple[List[Check], bool]:
    """Barcha tekshiruvlarni ishga tushiradi. Returns (checks, all_critical_ok)."""
    checks = run_all_checks()
    all_ok = all(status != "FAIL" for _, status, _ in checks)
    if verbose:
        icon = {"OK": "\033[32mOK  \033[0m", "WARN": "\033[33mWARN\033[0m", "FAIL": "\033[31mFAIL\033[0m"}
        print("\n\033[1;36mCONDUIT TIZIM TEKSHIRUVI (doctor)\033[0m")
        print("-" * 66)
        for name, status, detail in checks:
            print(f"  {icon.get(status, status)} {name:<20} {detail}")
        print("-" * 66)
        if all_ok:
            print("\033[32mZarur hamma narsa tayyor — MVP ishlatishga mumkin.\033[0m")
        else:
            print("\033[31mFAIL bandlarni tuzating — aks holda ba'zi agentlar ishlamaydi.\033[0m")
        print()
    return checks, all_ok
