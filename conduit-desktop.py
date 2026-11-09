#!/usr/bin/env python3
"""
Conduit PC Studio — Standalone Desktop Application Launcher.
Launches the Conduit AI agent management studio in a dedicated PC desktop window
(Edge / Chrome native application mode or WebView) without browser tabs or URL bars.
"""

import os
import sys
import time
import subprocess
import socket
import urllib.request

CONDUIT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CONDUIT_DIR, "backend")
FRONTEND_DIR = os.path.join(CONDUIT_DIR, "frontend")
BACKEND_URL = "http://127.0.0.1:8000/api/health"
FRONTEND_URL = "http://localhost:3000"

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def wait_for_url(url: str, timeout: int = 15) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ConduitDesktopLauncher"})
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status in [200, 304]:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def find_desktop_browser():
    """Finds Edge or Chrome in app mode for a standalone desktop window."""
    candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def main():
    print("=" * 60)
    print("   CONDUIT AI STUDIO — PC WORKSTATION DESKTOP APP")
    print("=" * 60)

    # 1. Start Backend if not already running on port 8000
    if not is_port_in_use(8000):
        print("[1/3] Backend server ishga tushirilmoqda (port 8000)...")
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=BACKEND_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
    else:
        print("[1/3] Backend faol (port 8000).")

    # 2. Start Frontend if not already running on port 3000
    if not is_port_in_use(3000):
        print("[2/3] Frontend server ishga tushirilmoqda (port 3000)...")
        subprocess.Popen(
            ["npm.cmd" if os.name == "nt" else "npm", "run", "start"],
            cwd=FRONTEND_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
    else:
        print("[2/3] Frontend faol (port 3000).")

    # Wait for frontend readiness
    print("[3/3] PC App oynasi tayyorlanmoqda...")
    wait_for_url(FRONTEND_URL, timeout=10)

    # 3. Launch dedicated standalone desktop window
    browser_exe = find_desktop_browser()
    if browser_exe:
        print(f"[OK] Standalone Desktop oynasi ochilmoqda: {browser_exe}")
        # Launch borderless standalone application window
        args = [
            browser_exe,
            f"--app={FRONTEND_URL}",
            "--window-size=1600,1000",
            "--window-position=40,40",
            "--disable-extensions",
            "--disable-default-apps",
            "--app-auto-launched"
        ]
        proc = subprocess.Popen(args)
        print("Conduit PC App oynasi muvaffaqiyatli ochildi!")
        proc.wait()
    else:
        print("[Ogohlantirish] Standalone brauzer topilmadi, standart tizim oynasida ochilmoqda...")
        import webbrowser
        webbrowser.open(FRONTEND_URL)

if __name__ == "__main__":
    main()
