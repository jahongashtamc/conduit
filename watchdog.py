#!/usr/bin/env python3
"""Conduit Watchdog — o'z-o'zini davolovchi nazoratchi.

Har ishga tushishda:
  1. Backend (:8000) — o'chiq bo'lsa uvicorn'ni qayta ishga tushiradi.
  2. Frontend (:3000) — o'chiq bo'lsa `npm run start` ni qayta ishga tushiradi.
  3. Health smoke-test — /api/health JSON qaytarmasa qayta ishga tushirish.
  4. Har bir harakat va holat watchdog.log ga yoziladi (dalil jurnali).

Windows Task Scheduler har 15 daqiqada chaqiradi (ConduitWatchdog task).
Xatolar jimjit yutilmaydi — barchasi log'ga yoziladi.
"""
import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

# Yo'llar fayl joylashgan papkadan olinadi: boshqa foydalanuvchi/mashinaga
# ko'chirilganda ham o'z nusxasini nazorat qiladi, eski papkaga bog'lanmaydi.
ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")
LOG_PATH = os.path.join(ROOT, "watchdog.log")
PY = sys.executable

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)


def http_ok(url: str, timeout: float = 8.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return 200 <= r.status < 300
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        logging.warning("%s javob bermadi: %s", url, e)
        return False


def port_pid(port: int):
    """Portda turgan jarayonning PID ini qaytaradi yoki None."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-NetTCPConnection -LocalPort {port} -State Listen "
             f"-ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess"],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        return int(out) if out.isdigit() else None
    except (subprocess.SubprocessError, ValueError) as e:
        logging.warning("port %d tekshiruvida xato: %s", port, e)
        return None


def kill_pid(pid: int, label: str) -> None:
    try:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                       capture_output=True, timeout=30)
        logging.info("%s (pid %d) o'chirildi — qayta ishga tushiriladi", label, pid)
    except subprocess.SubprocessError as e:
        logging.error("%s ni o'chirishda xato: %s", label, e)


def start_backend() -> None:
    """Backend uvicorn'ni qayta ishga tushiradi (eski jarayonni to'xtatib)."""
    pid = port_pid(8000)
    if pid:
        kill_pid(pid, "backend")
        time.sleep(2)
    try:
        subprocess.Popen(
            [PY, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=BACKEND_DIR,
            stdout=open(os.path.join(ROOT, "backend.log"), "ab"),
            stderr=open(os.path.join(ROOT, "backend.err.log"), "ab"),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        logging.info("backend qayta ishga tushirildi")
    except OSError as e:
        logging.error("backend start xatosi: %s", e)


def start_frontend() -> None:
    pid = port_pid(3000)
    if pid:
        kill_pid(pid, "frontend")
        time.sleep(2)
    try:
        subprocess.Popen(
            ["cmd", "/c", "npm", "run", "start"],
            cwd=FRONTEND_DIR,
            stdout=open(os.path.join(ROOT, "frontend.log"), "ab"),
            stderr=open(os.path.join(ROOT, "frontend.err.log"), "ab"),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        logging.info("frontend qayta ishga tushirildi")
    except OSError as e:
        logging.error("frontend start xatosi: %s", e)


def wait_until(url: str, tries: int = 12, delay: float = 5.0) -> bool:
    for _ in range(tries):
        if http_ok(url):
            return True
        time.sleep(delay)
    return False


def main() -> int:
    logging.info("=== watchdog ishga tushdi ===")
    problems = 0

    # 1. Backend
    if not http_ok("http://127.0.0.1:8000/api/health"):
        problems += 1
        logging.warning("backend O'CHIQ — tiklanmoqda")
        start_backend()
        if wait_until("http://127.0.0.1:8000/api/health"):
            logging.info("backend TIKLANDI — /api/health 200")
        else:
            logging.error("backend tiklanmadi — QO'LDA TEKSHIRISH KERAK")
    else:
        logging.info("backend OK")

    # 2. Frontend
    if not http_ok("http://127.0.0.1:3000"):
        problems += 1
        logging.warning("frontend O'CHIQ — tiklanmoqda")
        start_frontend()
        if wait_until("http://127.0.0.1:3000"):
            logging.info("frontend TIKLANDI — HTTP 200")
        else:
            logging.error("frontend tiklanmadi — QO'LDA TEKSHIRISH KERAK")
    else:
        logging.info("frontend OK")

    logging.info("=== watchdog tugadi: %d muammo ===", problems)
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    if "--loop" in sys.argv:
        # Uzluksiz rejim: berilgan soat davomida har 15 daqiqada tekshiradi
        # (Windows Task Scheduler bu mashinada jarayon ishga tushirmaydi —
        # shuning uchun doimiy fon jarayoni ishlatiladi).
        hours = 18.0
        for a in sys.argv:
            if a.startswith("--hours="):
                hours = float(a.split("=", 1)[1])
        deadline = time.time() + hours * 3600
        logging.info("=== LOOP REJIM: %.1f soat, har 15 daqiqada ===", hours)
        while time.time() < deadline:
            try:
                main()
            except Exception as e:
                logging.error("watchdog siklida xato: %s", e)
            time.sleep(15 * 60)
        logging.info("=== LOOP REJIM tugadi (%.1f soat) ===", hours)
        sys.exit(0)
    sys.exit(main())
