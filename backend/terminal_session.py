"""Haqiqiy PTY terminal sessiyasi (Windows, pywinpty).

Avvalgi versiya subprocess+pipe ishlatardi — interaktiv CLI (agy, claude)
kiritishni kutib osilib qolardi, chunki haqiqiy PTY yo'q edi. Endi
winpty.PtyProcess bilan haqiqiy pseudo-terminal ochiladi:

- powershell.exe PTY'da ishlaydi (cwd = Conduit papkasi)
- PTY chiqishi baytma-bayt WebSocket orqali frontendga (xterm.js) uzatiladi
- frontenddan kelgan hamma baytlar RAW holda PTY'ga yoziladi (Ctrl+C = "\\x03")
- resize: {"type":"resize","cols":N,"rows":M} -> pty.setwinsize()
- PTY sessiya WS uzilishida tirik qoladi, qayta ulanganda bufer qayta chiqadi
- {"type":"close"} yoki "To'xtatish" -> PTY jarayon daraxti to'liq o'ldiriladi
"""

from __future__ import annotations

import asyncio
import collections
import json
import os
import shutil
import uuid
from typing import Any, Set

from fastapi import WebSocket

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCROLLBACK_LIMIT = 1200  # qatorlar (qayta ulanishda qayta chiqarish uchun)

DOC_MARKER = "<!-- CONDUIT-STUDIO-GUIDE -->"
DOC_FILES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")


def _subagent_list_for_docs() -> str:
    """subagents/*/app.json dan sub-agent ro'yxatini MD jadval ko'rinishida generatsiya qiladi."""
    rows: list[str] = []
    sub_dir = os.path.join(ROOT_DIR, "subagents")
    if os.path.isdir(sub_dir):
        for name in sorted(os.listdir(sub_dir)):
            app_json = os.path.join(sub_dir, name, "app.json")
            if not os.path.isfile(app_json):
                continue
            try:
                with open(app_json, encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                continue
            aid = meta.get("id") or name
            atype = meta.get("type") or "role"
            desc = (meta.get("role_desc_uz") or meta.get("role_desc_en") or meta.get("description") or "").strip()
            rows.append(f"| `{aid}` | {atype} | {desc[:70]} |")
    if not rows:
        rows.append("| (ro'yxat bo'sh — `conduit list` bilan tekshiring) | | |")
    return "\n".join(rows)


def _studio_guide_md() -> str:
    """AGENTS.md / CLAUDE.md / GEMINI.md uchun bir xil mazmun."""
    return f'''{DOC_MARKER}

# Conduit Studio — Agent uchun yo'riqnoma

Sen **Conduit studiyasi ichida** ishlayapsan (cwd = Conduit loyiha papkasi).
Bu studiyada rasm, video, 3D, brauzer, Figma va boshqa ishlar uchun tayyor
sub-agentlar bor. **Bunday ishlarni o'zing qilma** — `conduit` CLI orqali
tegishli sub-agentga topshir va natijani foydalanuvchiga ko'rsat.

## Asosiy buyruqlar

```text
conduit list                        # sub-agentlar va asboblar ro'yxati + holati
conduit run <subagent> "<vazifa>"   # vazifa yaratadi, task_id qaytaradi
conduit status <task_id>            # holat, qadamlar, loglar
conduit result <task_id>            # chiqqan fayllar yo'li (artefaktlar)
conduit wait <task_id>              # vazifa tugashini kutadi
conduit browser <url>               # studiya brauzer oynasini yo'naltirish
conduit screenshot [fayl.jpg]       # brauzer oynasi kadrini saqlash
```

Har bir buyruq `--json` bilan JSON chiqaradi (agent o'qishi uchun qulay):
`conduit list --json`.

## Ish tartibi

1. Vazifani tahlil qil, kerakli sub-agentni tanla (ro'yxat pastda).
2. `conduit run <subagent> "<aniq vazifa>"` — task_id ol.
3. `conduit status <task_id>` bilan kuzat (yoki `conduit wait <task_id>`).
4. `conduit result <task_id>` bilan chiqqan fayllar yo'lini ol va
   foydalanuvchiga ko'rsat (natijalar studiyadagi Artefakt galereyasiga tushadi).

## Muhit o'zgaruvchilari

- `CONDUIT_API` — backend manzili (default `http://127.0.0.1:8000`)
- `CONDUIT_SESSION` — shu terminal sessiyasining ID si

## Mavjud sub-agentlar

| ID | Turi | Tavsif |
|----|------|--------|
{_subagent_list_for_docs()}
'''


def _ensure_agent_docs() -> None:
    """AGENTS.md / CLAUDE.md / GEMINI.md — mavjud bo'lsa ustidan yozmay,
    guide bloki bo'lmasa oxiriga qo'shadi."""
    guide = _studio_guide_md()
    for fname in DOC_FILES:
        path = os.path.join(ROOT_DIR, fname)
        try:
            existing = ""
            if os.path.isfile(path):
                with open(path, encoding="utf-8", errors="replace") as f:
                    existing = f.read()
            if DOC_MARKER in existing:
                continue  # allaqachon bor — ustidan yozmaymiz
            block = f"\n\n{guide}" if existing.strip() else guide
            with open(path, "a" if existing.strip() else "w", encoding="utf-8") as f:
                f.write(block)
        except Exception:
            continue


class TerminalSession:
    _instance: "TerminalSession | None" = None

    @classmethod
    def get_instance(cls) -> "TerminalSession":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self.active_websockets: Set[WebSocket] = set()
        self.scrollback_buffer: collections.deque = collections.deque(maxlen=SCROLLBACK_LIMIT)
        self.pt: Any = None  # winpty.PtyProcess
        self.reader_task: asyncio.Task | None = None
        self._pty_lock = asyncio.Lock()
        self.session_id: str = ""

    # ------------------------------------------------------------------ PTY

    def _spawn_pty(self) -> None:
        """Yangi powershell PTY ochadi (blocking — executor'da chaqiriladi)."""
        from winpty import PtyProcess

        shell = shutil.which("powershell.exe") or "powershell.exe"
        # winpty spawn qavslarni qabul qilmaydi (not executable xatosi) —
        # System32 yo'lida bo'shliq yo'q, shuning uchun yalang'ach yo'l ishlaydi.
        # Agent CLI env: CONDUIT_API + CONDUIT_SESSION + bin papka PATH'da.
        self.session_id = uuid.uuid4().hex[:8]
        _ensure_agent_docs()
        env = dict(os.environ)
        env["CONDUIT_API"] = "http://127.0.0.1:8000"
        env["CONDUIT_SESSION"] = self.session_id
        env["PATH"] = os.path.join(ROOT_DIR, "bin") + os.pathsep + env.get("PATH", "")
        self.pt = PtyProcess.spawn(
            f"{shell} -NoLogo -NoProfile",
            cwd=ROOT_DIR,
            dimensions=(30, 110),
            env=env,
        )
        self._append_scrollback(
            "\x1b[90m[Conduit PTY] PowerShell sessiyasi boshlandi "
            f"(pid {self.pt.pid}, sessiya {self.session_id}). "
            "'agy' yozib agent bilan ishlang; studiya buyruqlari: 'conduit list'.\x1b[0m\r\n"
        )

    def _ensure_pty(self) -> bool:
        """PTY yo'q yoki o'lgan bo'lsa yangisini ochadi. True = tayyor.

        MUHIM: PTY tirik lekin reader o'lgan holat ham bor — bunda terminal
        Muzlab qoladi (kiritish yoziladi, chiqish hech qachon qaytmaydi).
        Shuning uchun reader holati ham tekshiriladi va qayta ishga tushiriladi.
        """
        if self.pt is not None and self.pt.isalive():
            # Reader o'lgan bo'lsa qayta boshlaymiz (terminal freeze bug'i).
            if self.reader_task is None or self.reader_task.done():
                self._append_scrollback(
                    "\x1b[33m[Conduit PTY] Reader tiklandi — chiqish oqimi qayta yoqildi.\x1b[0m\r\n"
                )
                self._start_reader()
            return True
        try:
            self._spawn_pty()
            # Yangi sessiya — eski buffer chalkashmasligi uchun tozalaymiz.
            self.scrollback_buffer.clear()
            self._start_reader()
            return True
        except Exception as exc:  # noqa: BLE001
            self._append_scrollback(f"\x1b[31m[PTY xato] {exc}\x1b[0m\r\n")
            self.pt = None
            return False

    def _start_reader(self) -> None:
        if self.reader_task is None or self.reader_task.done():
            self.reader_task = asyncio.get_running_loop().create_task(self._reader_loop())

    async def _reader_loop(self) -> None:
        """PTY chiqishini uzluksiz o'qib broadcast qiladi (blocking read executor'da)."""
        loop = asyncio.get_running_loop()
        while True:
            pt = self.pt
            if pt is None or not pt.isalive():
                break
            try:
                # winpty read() blocking — executor orqali event loop'ni bloklamaymiz.
                data = await loop.run_in_executor(None, pt.read, 2048)
            except Exception as exc:
                # Jimkincha o'lib qolmaslik: sababni buferga yozamiz. PTY tirik
                # bo'lsa davom etamiz (vaqtinchalik o'qish xatosi bo'lishi mumkin).
                if pt.isalive():
                    self._append_scrollback(
                        f"\x1b[33m[Conduit PTY] O'qishda xato ({type(exc).__name__}), qayta urinilmoqda...\x1b[0m\r\n"
                    )
                    await asyncio.sleep(0.5)
                    continue
                break
            if not data:
                # read() bo'sh qaytarsa va PTY tirik bo'lsa — qisqa kutib davom
                # etamiz; aks holda reader o'lib terminal muzlab qoladi.
                if pt.isalive():
                    await asyncio.sleep(0.2)
                    continue
                break
            text = data if isinstance(data, str) else data.decode("utf-8", errors="replace")
            self._append_scrollback(text)
            await self.broadcast(text, record=False)
        self._append_scrollback("\x1b[90m[Conduit PTY] Sessiya tugadi.\x1b[0m\r\n")
        await self.broadcast("\x1b[90m[Conduit PTY] Sessiya tugadi.\x1b[0m\r\n", record=False)

    def _append_scrollback(self, text: str) -> None:
        # PTY chiqishi qator chegaralarini buzishi mumkin — oxirgi qatorni
        # to'liqlashtirib qo'shamiz.
        for part in text.split("\r\n"):
            self.scrollback_buffer.append(part)

    # ------------------------------------------------------------ WS hayot

    async def broadcast(self, text: str, record: bool = True) -> None:
        if record:
            self._append_scrollback(text)
        for ws in list(self.active_websockets):
            try:
                await ws.send_text(text)
            except Exception:
                self.active_websockets.discard(ws)

    async def connect_client(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_websockets.add(websocket)
        # Qayta ulanishda butun buferni qayta chiqaramiz (sessiya tirik qoladi).
        if self.scrollback_buffer:
            try:
                await websocket.send_text("\r\n".join(self.scrollback_buffer) + "\r\n")
            except Exception:
                pass
        if not self._ensure_pty():
            await self.broadcast("\x1b[31mPTY ochilmadi.\x1b[0m\r\n", record=False)

    def disconnect_client(self, websocket: WebSocket) -> None:
        self.active_websockets.discard(websocket)
        # WS uzilishda PTY TIRIK QOLADI (qayta ulanish uchun).
        # To'liq yopilish uchun frontend {"type":"close"} yuboradi.

    # ------------------------------------------------------------- kiritish

    async def handle_input(self, msg: str) -> None:
        if not msg:
            return

        # Heartbeat
        if msg in ("ping", '{"type":"ping"}'):
            for ws in list(self.active_websockets):
                try:
                    await ws.send_text('{"type":"pong"}')
                except Exception:
                    pass
            return

        # UI tugmalarining JSON paketlari
        if msg.startswith("{") and msg.endswith("}"):
            try:
                payload = json.loads(msg)
            except Exception:
                payload = None
            if isinstance(payload, dict):
                mtype = payload.get("type")
                if mtype == "resize":
                    self._resize(int(payload.get("cols") or 110), int(payload.get("rows") or 30))
                    return
                if mtype == "clear":
                    self.scrollback_buffer.clear()
                    await self.broadcast("\x1b[2J\x1b[H", record=False)
                    return
                if mtype == "close":
                    await self.shutdown()
                    return
                if mtype == "run":
                    cmd = (payload.get("command") or "").strip()
                    if cmd:
                        # Qulaylik: 'conduit ...' -> 'python conduit.py ...'
                        if cmd.split()[0].lower() == "conduit":
                            cmd = "python conduit.py " + cmd[len("conduit"):].strip()
                        self._write_pty(cmd + "\r")
                    return
                # boshqa JSON — PTY'ga raw yozamiz

        # RAW kiritish: har bir belgi (shu jumladan \x03, \r) to'g'ridan-to'g'ri PTY'ga.
        self._write_pty(msg)

    def _write_pty(self, data: str) -> None:
        if not self._ensure_pty():
            return
        try:
            self.pt.write(data)
        except Exception as exc:  # noqa: BLE001
            self._append_scrollback(f"\x1b[31m[PTY yozish xatosi] {exc}\x1b[0m\r\n")

    def _resize(self, cols: int, rows: int) -> None:
        if self.pt is None or not self.pt.isalive():
            return
        try:
            self.pt.setwinsize(max(4, rows), max(10, cols))
        except Exception:
            pass

    # ------------------------------------------------------------- tozalash

    async def shutdown(self) -> None:
        """PTY jarayon daraxtini to'liq o'ldiradi (zombie qolmaydi)."""
        async with self._pty_lock:
            pt, self.pt = self.pt, None
        if pt is None:
            return
        pid = getattr(pt, "pid", None)
        try:
            if pid:
                import psutil

                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.kill()
                        except Exception:
                            pass
                    psutil.wait_procs(children, timeout=3)
                except Exception:
                    pass
            pt.terminate(force=True)
        except Exception:
            pass
        await self.broadcast("\x1b[90m[Conduit PTY] Sessiya yopildi.\x1b[0m\r\n", record=False)
