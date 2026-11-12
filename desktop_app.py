#!/usr/bin/env python3
"""Conduit AI Studio — haqiqiy Windows desktop ilovasi.

Bir marta bosilganda:
  1. FastAPI backend (port 8000) va Next.js frontend (port 3000) ishga tushadi
  2. pywebview orqali haqiqiy desktop oynasi ochiladi (WebView2, Edge)
  3. Oyna yopilganda ikkala servis jarayoni AVTOMATIK o'chiriladi —
     ortida port egallab turuvchi yashirin processlar qolmaydi.

Bu fayl PyInstaller bilan conduit.exe ga paketlanadi.
"""

from __future__ import annotations

import atexit
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request

import psutil
import webview

# PyInstaller onefile rejimida resurslar _MEIPASS ichida bo'ladi, lekin biz
# fayl tizimidagi real papkalarni ishlatamiz — shuning uchun exe o'zi
# loyiha ildizida yonaida turadi (onedir build).
if getattr(sys, "frozen", False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

BACKEND_PORT = 8000
FRONTEND_PORT = 3000
BACKEND_HEALTH = f"http://127.0.0.1:{BACKEND_PORT}/api/health"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"

IS_WINDOWS = os.name == "nt"
NO_WINDOW = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0

_spawned: list[subprocess.Popen] = []


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def log(message: str) -> None:
    print(f"[Conduit] {message}", flush=True)


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex((host, port)) == 0


def url_ok(url: str, timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ConduitDesktop"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except Exception:
        return False


def wait_for(url: str, name: str, timeout: float = 90.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if url_ok(url):
            log(f"{name} tayyor.")
            return True
        time.sleep(1.0)
    log(f"{name} {int(timeout)}s ichida javob bermadi.")
    return False


def python_executable() -> str:
    if getattr(sys, "frozen", False):
        # exe ichidan tizim Python'ini topamiz (venv yoki PATH).
        for cand in (
            os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Python\Python312\python.exe"),
        ):
            if os.path.exists(cand):
                return cand
        return "python"
    return sys.executable


# --------------------------------------------------------------------------- #
# services
# --------------------------------------------------------------------------- #
def start_backend() -> bool:
    if port_in_use(BACKEND_PORT):
        log(f"Backend allaqachon ishlayapti (port {BACKEND_PORT}).")
        return True
    log(f"Backend ishga tushirilmoqda (port {BACKEND_PORT})...")
    log_path = os.path.join(ROOT_DIR, "backend.log")
    with open(log_path, "ab") as handle:
        proc = subprocess.Popen(
            [python_executable(), "-m", "uvicorn", "main:app",
             "--host", "127.0.0.1", "--port", str(BACKEND_PORT)],
            cwd=BACKEND_DIR, stdout=handle, stderr=subprocess.STDOUT,
            creationflags=NO_WINDOW,
        )
    _spawned.append(proc)
    return wait_for(BACKEND_HEALTH, "Backend")


def start_frontend() -> bool:
    if port_in_use(FRONTEND_PORT):
        log(f"Frontend allaqachon ishlayapti (port {FRONTEND_PORT}).")
        return True
    if not os.path.isdir(os.path.join(FRONTEND_DIR, ".next")):
        log("XATO: frontend build topilmadi (.next yo'q). Ilgari 'npm run build' bajarilishi kerak.")
        return False
    log(f"Frontend ishga tushirilmoqda (port {FRONTEND_PORT}, production build)...")
    log_path = os.path.join(ROOT_DIR, "frontend.log")
    with open(log_path, "ab") as handle:
        proc = subprocess.Popen(
            ["npx", "next", "start", "-p", str(FRONTEND_PORT)],
            cwd=FRONTEND_DIR, stdout=handle, stderr=subprocess.STDOUT,
            shell=IS_WINDOWS, creationflags=NO_WINDOW if not IS_WINDOWS else 0,
        )
    _spawned.append(proc)
    return wait_for(FRONTEND_URL, "Frontend", timeout=60)


def stop_services() -> None:
    """Oyna yopilganda bizning jarayonlarimizni va port egallagan qoldiqlarni tozalaydi."""
    log("Servislar to'xtatilmoqda...")
    for proc in _spawned:
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    # Boshqa ilovalar ochgan portlar (masalan oldingi qotib qolgan nusxa) —
    # faqat o'zimiz boshlaganlarimiz o'lmagan taqdirda tozalaymiz.
    for port in (BACKEND_PORT, FRONTEND_PORT):
        for conn in psutil.net_connections(kind="tcp"):
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN and conn.pid:
                try:
                    p = psutil.Process(conn.pid)
                    if "python" in p.name().lower() or "node" in p.name().lower():
                        p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    log("Tayyor.")


# --------------------------------------------------------------------------- #
# window
# --------------------------------------------------------------------------- #
def on_window_closed() -> None:
    stop_services()


def main() -> int:
    print("=" * 62)
    print("   CONDUIT AI STUDIO")
    print("=" * 62)

    if not os.path.isdir(BACKEND_DIR) or not os.path.isdir(FRONTEND_DIR):
        log(f"Loyiha papkalari topilmadi: {ROOT_DIR}")
        return 1

    atexit.register(stop_services)

    if not start_backend():
        log("Backend ishga tushmadi. backend.log ni tekshiring.")
        return 1
    if not start_frontend():
        log("Frontend ishga tushmadi. frontend.log ni tekshiring.")
        return 1

    window = webview.create_window(
        "Conduit AI Studio",
        FRONTEND_URL,
        width=1600,
        height=1000,
        min_size=(1100, 700),
        background_color="#020617",
    )
    window.events.closed += on_window_closed
    webview.start(gui="edgechromium")
    return 0


if __name__ == "__main__":
    sys.exit(main())
