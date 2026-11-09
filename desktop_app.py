"""
Conduit Studio Standalone PC Desktop Application.
Runs Conduit as a true native Windows desktop application window (no browser tabs, no address bar).
Uses PyWebView (Edge WebView2) or Edge Standalone App Mode.
"""

import os
import sys
import time
import socket
import subprocess
import webview

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
PYTHON_EXE = sys.executable

def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def ensure_services():
    # Start Backend if not already running
    if not is_port_open(8000):
        print("[Conduit App] Backend (FastAPI, 8000) ishga tushirilmoqda...")
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.Popen(
            [PYTHON_EXE, "main.py"],
            cwd=BACKEND_DIR,
            creationflags=creationflags
        )

    # Start Frontend if not already running
    if not is_port_open(3000):
        print("[Conduit App] Frontend (Next.js, 3000) ishga tushirilmoqda...")
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.Popen(
            "npx next dev -p 3000",
            shell=True,
            cwd=FRONTEND_DIR,
            creationflags=creationflags
        )

    # Wait for services to respond
    for i in range(25):
        if is_port_open(3000) and is_port_open(8000):
            break
        time.sleep(1)

def main():
    ensure_services()
    print("[Conduit App] Standalone PC Oynasi ochilmoqda...")

    try:
        # Create standalone native application window
        window = webview.create_window(
            title="Conduit Studio",
            url="http://localhost:3000",
            width=1540,
            height=940,
            min_size=(1080, 720),
            resizable=True,
            confirm_close=False,
            background_color="#090d16"
        )
        webview.start(debug=False)
    except Exception as e:
        print(f"[Conduit App] WebView fallback to Edge App Mode: {e}")
        subprocess.run(["cmd.exe", "/c", "start msedge --app=http://localhost:3000 --window-size=1540,940"])

if __name__ == "__main__":
    main()
