#!/usr/bin/env python3
"""Conduit AI Studio — Windows desktop application launcher.

Starts the FastAPI backend and the Next.js frontend if they are not already
running, waits until both answer, then opens Conduit in a borderless desktop
window (browser --app mode, so there is no address bar or tab strip) and shows
a splash screen while the services boot.

Usage:
    python conduit_app.py             # normal start
    python conduit_app.py --dev       # run Next.js dev server
    python conduit_app.py --no-window # start services only, do not open a window
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

BACKEND_PORT = 8000
FRONTEND_PORT = 3000
BACKEND_HEALTH = f"http://127.0.0.1:{BACKEND_PORT}/api/health"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"

WINDOW_SIZE = "1600,1000"
IS_WINDOWS = os.name == "nt"
NO_WINDOW = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0


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
    request = urllib.request.Request(
        url, headers={"User-Agent": "ConduitDesktop"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status < 400
    except (urllib.error.URLError, OSError, ValueError):
        return False


def wait_for(url: str, label: str, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if url_ok(url):
            return True
        time.sleep(0.5)
    log(f"{label} {int(timeout)}s ichida javob bermadi.")
    return False


def python_executable() -> str:
    """Prefers the project venv, else the interpreter running this script."""
    for candidate in (
        os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe"),
        os.path.join(ROOT_DIR, "venv", "Scripts", "python.exe"),
    ):
        if os.path.exists(candidate):
            return candidate
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
    handle = open(log_path, "ab")
    subprocess.Popen(
        [
            python_executable(),
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(BACKEND_PORT),
        ],
        cwd=BACKEND_DIR,
        stdout=handle,
        stderr=subprocess.STDOUT,
        creationflags=NO_WINDOW,
    )
    return wait_for(BACKEND_HEALTH, "Backend", timeout=60)


def start_frontend(dev: bool) -> bool:
    if port_in_use(FRONTEND_PORT):
        log(f"Frontend allaqachon ishlayapti (port {FRONTEND_PORT}).")
        return True

    log(f"Frontend ishga tushirilmoqda (port {FRONTEND_PORT})...")
    log_path = os.path.join(ROOT_DIR, "frontend.log")
    handle = open(log_path, "ab")

    if dev:
        cmd = ["npx", "next", "dev", "-p", str(FRONTEND_PORT)]
    else:
        # A production build starts in ~1s instead of ~20s. Build it on demand.
        if not os.path.isdir(os.path.join(FRONTEND_DIR, ".next")):
            log("Production build topilmadi, `next build` bajarilmoqda...")
            subprocess.run(
                ["npx", "next", "build"],
                cwd=FRONTEND_DIR,
                stdout=handle,
                stderr=subprocess.STDOUT,
                shell=IS_WINDOWS,
            )
        cmd = ["npx", "next", "start", "-p", str(FRONTEND_PORT)]

    subprocess.Popen(
        cmd, cwd=FRONTEND_DIR, stdout=handle, stderr=subprocess.STDOUT, shell=IS_WINDOWS
    )
    return wait_for(FRONTEND_URL, "Frontend", timeout=120)


# --------------------------------------------------------------------------- #
# window
# --------------------------------------------------------------------------- #
def find_browser() -> str | None:
    """Returns an Edge/Chrome executable that supports --app mode."""
    local = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(
            os.environ.get("ProgramFiles(x86)", ""),
            r"Microsoft\Edge\Application\msedge.exe",
        ),
        os.path.join(
            os.environ.get("ProgramFiles", ""), r"Microsoft\Edge\Application\msedge.exe"
        ),
        os.path.join(local, r"Microsoft\Edge\Application\msedge.exe"),
        os.path.join(
            os.environ.get("ProgramFiles", ""),
            r"Google\Chrome\Application\chrome.exe",
        ),
        os.path.join(
            os.environ.get("ProgramFiles(x86)", ""),
            r"Google\Chrome\Application\chrome.exe",
        ),
        os.path.join(local, r"Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def open_window() -> None:
    browser = find_browser()
    if browser is None:
        log("Edge/Chrome topilmadi, standart brauzerda ochilmoqda.")
        import webbrowser

        webbrowser.open(FRONTEND_URL)
        return

    log(f"Desktop oynasi ochilmoqda: {os.path.basename(browser)}")
    subprocess.Popen(
        [
            browser,
            f"--app={FRONTEND_URL}",
            f"--window-size={WINDOW_SIZE}",
            "--disable-extensions",
            "--disable-default-apps",
            "--no-first-run",
            "--no-default-browser-check",
        ]
    )


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Conduit AI Studio desktop app")
    parser.add_argument("--dev", action="store_true", help="Next.js dev server")
    parser.add_argument(
        "--no-window", action="store_true", help="Faqat servislarni ishga tushirish"
    )
    args = parser.parse_args()

    print("=" * 62)
    print("   CONDUIT AI STUDIO — DESKTOP APPLICATION")
    print("=" * 62)

    if not os.path.isdir(BACKEND_DIR) or not os.path.isdir(FRONTEND_DIR):
        log(f"Loyiha papkalari topilmadi: {ROOT_DIR}")
        return 1

    if not start_backend():
        log("Backend ishga tushmadi. backend.log ni tekshiring.")
        return 1

    if not start_frontend(dev=args.dev):
        log("Frontend ishga tushmadi. frontend.log ni tekshiring.")
        return 1

    # First-run health check: surface missing prerequisites immediately
    # instead of letting the user discover a dead agent later.
    try:
        sys.path.insert(0, BACKEND_DIR)
        import doctor
        checks, all_ok = doctor.run_doctor(verbose=False)
        bad = [(n, d) for n, s, d in checks if s == "FAIL"]
        warn = [(n, d) for n, s, d in checks if s == "WARN"]
        if bad:
            log(f"DIQQAT: {len(bad)} ta kritik muammo:")
            for n, d in bad:
                log(f"  FAIL {n}: {d}")
            log("To'liq tekshiruv: python conduit.py doctor")
        elif warn:
            log(f"Tizim tayyor ({len(warn)} ta ixtiyoriy sozlama yo'q: python conduit.py doctor)")
        else:
            log("Tizim tekshiruvi: hamma narsa tayyor")
    except Exception as exc:
        log(f"Doctor tekshiruvi o'tkazilmadi: {exc}")

    if args.no_window:
        log(f"Servislar tayyor: {FRONTEND_URL}")
        return 0

    open_window()
    log(f"Tayyor: {FRONTEND_URL}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
