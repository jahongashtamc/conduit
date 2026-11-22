"""Haqiqiy PTY terminal sessiyasi (Windows, pywinpty).

Avvalgi versiya subprocess+pipe ishlatardi — interaktiv CLI (agy, claude)
kiritishni kutib osilib qolardi, chunki haqiqiy PTY yo'q edi. Endi
winpty.PtyProcess bilan haqiqiy pseudo-terminal ochiladi:

- powershell.exe PTY'da ishlaydi (cwd = ish papkasi)
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
import logging
import os
import re
import shlex
import shutil
import time
import uuid
from typing import Any, Set

from fastapi import WebSocket

LOGGER = logging.getLogger("nexus.terminal")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCROLLBACK_LIMIT = 1200  # qatorlar (qayta ulanishda qayta chiqarish uchun)

# Programmatik buyruq yozilgandan keyin bu qtancha vaqt ichida kelgan
# terminal so'rov javoblari (DA/DSR) tashlab yuboriladi. Sababi: xterm.js
# brauzerda \x1b[c (DA) so'roviga avtomatik \x1b[?1;2c javob qaytaradi; bu
# javob aynan buyruq yozilayotgan paytga WS orqali PTY'ga yozilsa, PowerShell
# kiritishini buzadi (masalan "python" -> "[?1;2cython" -> ParserError).
RUN_GUARD_SECONDS = 0.40

# Terminal javob ketma-ketliklari — FAQAT javob patternlari. Ehtiyotkorlik:
# oddiy regex (istalgan harf finali) strelka tugmalarini (\x1b[A) ham yutib
# yuborardi. Shuning uchun faqat raqam/?/lye ega ketma-ketliklar moslanadi:
#   \x1b[?...X  — DA javobi (xterm.js avtomatik javobi, ? prefiksi)
#   \x1b[<raqam>R — DSR kursor holati javobi
#   \x1b[<raqam>t — oyna o'lchavi hisoboti
#   \x1b[><raqam>c — ikkilamchi DA
# Strelkalar (\x1b[A), Home/End (\x1b[H/F), \x1b[3~ — hech qachon moslanmaydi.
_TERMINAL_RESPONSE_RE = re.compile(
    r"^(?:\x1b\[\?[0-9;]*[a-zA-Z]|\x1b\[>?[0-9;]+[cRt]|\x1b\[0c)+$"
)

# Terminal SO'ROV ketma-ketliklari (PTY chiqishida dastur yuboradi):
#   \x1b[6n — kursor joyi so'rovi (DSR)
#   \x1b[c / \x1b[0c — birinchi DA so'rovi
#   \x1b[>c / \x1b[>0c — ikkilamchi DA so'rovi
_TERMINAL_QUERY_RE = re.compile(r"\x1b\[6n|\x1b\[0?c|\x1b\[>[0-9]*c")

# Alternativ ekran (TUI) kirish/chiqish ketma-ketliklari.
_ALT_SCREEN_ENTER_RE = re.compile(r"\x1b\[\?(?:1049|1047|47)h")
_ALT_SCREEN_EXIT_RE = re.compile(r"\x1b\[\?(?:1049|1047|47)l")

DOC_MARKER_PREFIX = "<!-- CONDUIT-STUDIO-GUIDE"
DOC_MARKER = "<!-- CONDUIT-STUDIO-GUIDE v3 -->"
DOC_MARKER_RE = re.compile(r"<!-- CONDUIT-STUDIO-GUIDE[^>]*-->")
DOC_FILES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")


def _subagent_list_for_docs() -> str:
    """Subagentlarni agentga bog'langan chaqiriladigan tool'lar sifatida ko'rsatadi."""
    try:
        import tool_registry  # type: ignore
        return tool_registry.compact_tool_lines()
    except Exception as exc:
        LOGGER.error("Tool katalogi generatsiya qilinmadi: %s: %s", type(exc).__name__, exc)
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
            except Exception as exc:
                LOGGER.error("Subagent metadata o'qilmadi (%s): %s: %s", app_json, type(exc).__name__, exc)
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

# Nexus Studio — Agent uchun yo'riqnoma

Sen **Nexus studiyasi ichida** ishlayapsan (cwd = ish papkasi).
Bu studiya HAR QANDAY AI agent uchun (Claude Code, agy, Codex CLI, Gemini CLI,
Cursor va boshqalar) — studiya agentga bog'liq emas.
Bu studiyada rasm, video, 3D, brauzer, Figma va boshqa ishlar uchun tayyor
sub-agentlar bor. Ular **senga tool sifatida bog'langan**: sen asosiy agent sifatida
ishlaysan, vazifani tahlil qilib kerakli subagent-tool'ni chaqirasen.
**Bunday ishlarni o'zing qilma** — `conduit` CLI orqali topshir va natijani
foydalanuvchiga ko'rsat.

## Asosiy buyruqlar

```text
conduit tools                       # SENGA BOG'LANGAN subagent-toollar katalogi (JSON: --json)
conduit budget                      # qolgan token/narx byudjeti (JSON: --json)
conduit list                        # sub-agentlar ro'yxati + holati
conduit run <subagent> "<vazifa>"   # TOOL CHAQIRUVI: vazifa yaratadi, task_id qaytaradi
conduit watch <task_id>             # vazifani JONLI kuzatish (qadamlar + loglar)
conduit status <task_id>            # holat, qadamlar, loglar
conduit result <task_id>            # chiqqan fayllar yo'li (artefaktlar)
conduit wait <task_id>              # vazifa tugashini kutadi
conduit browser <url>               # studiya brauzer oynasini yo'naltirish
conduit screenshot [fayl.jpg]       # brauzer oynasi kadrini saqlash
```

Har bir buyruq `--json` bilan JSON chiqaradi (agent o'qishi uchun qulay):
`conduit list --json`.

## Tool'lar qanday ishlaydi (MUHIM)

- Har bir subagent senga **tool** sifatida bog'langan. Asosiy kontekstga faqat
  uning **qisqa tavsifi** yuklanadi (pastdagi ro'yxat). To'liq rol prompti
  faqat `conduit run` bilan subagent ishga tushgandagina yuklanadi.
- Shuning uchun tavsiflarni o'zing uzoq matn bilan to'ldirma; katalog uchun
  `conduit tools --json` ga qara (har tool: tavsif, input sxema, ruxsat etilgan
  toollar, taxminiy token va narx).
- agy uchun bu tool'lar `.agents/agents/conduit_<id>.md` sifatida ham native ro'yxatga
  olinadi (lokal, global sozlama tegilmadi). Lekin studiya ishini har doim
  `conduit run` orqali bajar — u task kuzatuvi va dalillarni ta'minlaydi.
- Tool allowlist har subagentning `role.md` sidan keladi; boshqa tool ishlatish rad etiladi.
- Har bir subagent so'rovi **umumiy token/narx limitiga** hisoblanadi. Delegatsiyadan
  oldin `conduit budget --json` bilan qolgan byudjetni tekshir; katalogdagi
  `within_remaining_budget=false` tool'ni chaqirma. Byudjet tugasa vazifalar
  `BLOCKED` bo'ladi.
- Katta log yoki fayl tarkibini o'z kontekstingga ko'chirma — subagent faqat
  qisqa natija va dalil yo'lini qaytarsin.

## Ish tartibi

1. Vazifani tahlil qil, kerakli subagent-tool'ni tanla (ro'yxat pastda).
   `conduit budget --json` bilan byudjetni tekshir.
2. `conduit run <subagent> "<aniq vazifa>"` — task_id ol (bu tool chaqiruvi).
3. `conduit watch <task_id>` bilan jonli kuzat (yoki `conduit wait <task_id>`).
4. `conduit result <task_id>` bilan chiqqan fayllar yo'lini ol va
   foydalanuvchiga ko'rsat (natijalar studiyadagi Artefakt galereyasiga tushadi).

## Qattiq qoidalar (so'ralmagan ish TAQIQLANGAN)
- Faqat foydalanuvchi aytgan vazifani bajar. O'zingcha qo'shimcha ish, fayl o'qish,
  kod o'zgartirish yoki boshqa buyruq chaqirish — TAQIQLANGAN.
- CLI sintaksisi yetishmasa, FAQAT `conduit --help` yoki `conduit list --json` ga qara.
  Test fayllarini, boshqa papkalarni yoki manba kodni o'rganma.
- **MCP toollarini chaqirish TAQIQLANGAN** (ular global sozlamadan keladi va ishlamasligi
  mumkin). 3D/video/rasm/brauzer ishlari FAQAT `conduit run <subagent> "..."` orqali bajariladi.
- Vazifa noaniq bo'lsa, taxmin qilma — foydalanuvchidan aniq so'ra.
- `conduit run` bilan topshirgach, `conduit wait` bilan kut va natijani xabar qil.
  Yana o'zing qo'shimcha tekshiruv o'tkazma.

## Muhit o'zgaruvchilari

- `CONDUIT_API` — backend manzili (default `http://127.0.0.1:8000`)
- `CONDUIT_SESSION` — shu terminal sessiyasining ID si

## Senga bog'langan subagent-tool'lar

{_subagent_list_for_docs()}

To'liq sxema, ruxsat etilgan toollar va token/narx bahosi: `conduit tools --json`.
Har bir tool chaqiruvi: `conduit run <subagent> "<vazifa>"`.
'''


def _ensure_agent_docs() -> None:
    """AGENTS.md / CLAUDE.md / GEMINI.md — guide blokini avtomatik yangilaydi.
    Blok marker'dan fayl oxirigacha davom etadi (oxirgi bo'lim sifatida qo'shilgan),
    shuning uchun eskirgan blokni marker'dan boshlab butunlay almashtiramiz."""
    guide = _studio_guide_md()
    for fname in DOC_FILES:
        path = os.path.join(ROOT_DIR, fname)
        try:
            existing = ""
            if os.path.isfile(path):
                with open(path, encoding="utf-8", errors="replace") as f:
                    existing = f.read()
            match = DOC_MARKER_RE.search(existing)
            if match:
                line_start = existing.rfind("\n", 0, match.start()) + 1
                updated = existing[:line_start] + guide
                if updated != existing:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(updated)
                        print(f"[terminal] {fname} guide bloki yangilandi.")
                continue
            block = f"\n\n{guide}" if existing.strip() else guide
            with open(path, "a" if existing.strip() else "w", encoding="utf-8") as f:
                f.write(block)
                print(f"[terminal] {fname} ga guide bloki qo'shildi.")
        except OSError as exc:
            print(f"[terminal] {fname} yangilanmadi: {exc}")

    # agy/Claude Code kabi agentlarga subagentlar NATIVE tool sifatida ham bog'lanadi.
    # Faqat lokal .agents/agents/ papkasi — global sozlamaga tegilmaydi.
    try:
        import native_subagents  # type: ignore
        native = native_subagents.sync_native_subagents(ROOT_DIR)
        print(f"[terminal] {native['count']} ta native subagent definitsiyasi yangilandi.")
    except Exception as exc:
        LOGGER.error("Native subagent definitsiyalari yaratilmadi: %s: %s", type(exc).__name__, exc)


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
        # Programmatik yozishdan keyingi guard oynasi (monotonic vaqt).
        # Sessiya ochilishida ham 3s guard: PSReadLine/xterm.js DA javoblari
        # aynan start paytida stray input bo'lib ko'rinadi ([?1;2c matn sifatida).
        self._run_guard_until: float = time.monotonic() + 3.0
        # So'rov kutilayotgan oyna: dastur PTY chiqishida DA/DSR so'rov yuborsa
        # 1s ichida kelgan javoblar haqiqiy deb PTY'ga uzatiladi.
        self._query_seen_until: float = 0.0
        # Faqat alternativ ekran rejimida (vim/agy/claude TUI) terminal
        # javoblari PTY'ga uzatiladi. Oddiy PowerShell promptida ular sizib,
        # matn sifatida ko'rinadi ([?1;2c) va kiritishni buzadi.
        self._alt_screen: bool = False
        # Tanlangan agent PTY da ishga tushirilganmi — keyingi tanlovda eskisini yopish uchun.
        self._agent_launched: bool = False
        # PowerShell prompti ko'ringanda o'rnatiladi — buyruq faqat shundan keyin yoziladi.
        self._prompt_ready = asyncio.Event()

    # ------------------------------------------------------------------ PTY

    def _spawn_pty(self) -> None:
        """Yangi powershell PTY ochadi (blocking — executor'da chaqiriladi)."""
        from winpty import PtyProcess

        shell = shutil.which("powershell.exe") or "powershell.exe"
        # winpty spawn qavslarni qabul qilmaydi (not executable xatosi) —
        # System32 yo'lida bo'shliq yo'q, shuning uchun yalang'ach yo'l ishlaydi.
        # Agent CLI env: CONDUIT_API + CONDUIT_SESSION + bin papka PATH'da.
        self.session_id = uuid.uuid4().hex[:8]
        self._alt_screen = False
        self._query_seen_until = 0.0
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
            "\x1b[90m[Nexus PTY] PowerShell sessiyasi boshlandi "
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
                    "\x1b[33m[Nexus PTY] Reader tiklandi — chiqish oqimi qayta yoqildi.\x1b[0m\r\n"
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
                        f"\x1b[33m[Nexus PTY] O'qishda xato ({type(exc).__name__}), qayta urinilmoqda...\x1b[0m\r\n"
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
            # Alternativ ekran holatini kuzatamiz: faqat shu rejimda ishlaydigan
            # TUI'lar (vim, agy, claude) terminal javoblarini kutadi.
            if _ALT_SCREEN_ENTER_RE.search(text):
                self._alt_screen = True
            elif _ALT_SCREEN_EXIT_RE.search(text):
                self._alt_screen = False
            # Terminal SO'ROVlarini aniqlash (DSR \x1b[6n, DA \x1b[c, \x1b[>c):
            # dastur so'rov yuborsa, xterm.js javobi 1s ichida PTY'ga yetib
            # borishi SHART — aks holda dastur javobni kutib qoladi. So'rov
            # yo'q paytda kelgan javoblar stray input bo'lib, PowerShell ularni
            # matn sifatida ko'rsatadi ([?1;2c kabi) — ular tashlanadi.
            if _TERMINAL_QUERY_RE.search(text):
                self._query_seen_until = time.monotonic() + 1.0
            self._append_scrollback(text)
            if "PS " in text and ">" in text:
                self._prompt_ready.set()
            await self.broadcast(text, record=False)
        self._append_scrollback("\x1b[90m[Nexus PTY] Sessiya tugadi.\x1b[0m\r\n")
        await self.broadcast("\x1b[90m[Nexus PTY] Sessiya tugadi.\x1b[0m\r\n", record=False)

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
            except Exception as exc:
                LOGGER.warning("PTY chiqishi WS ga yuborilmadi: %s: %s", type(exc).__name__, exc)
                self.active_websockets.discard(ws)

    async def connect_client(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_websockets.add(websocket)
        # Qayta ulanishda butun buferni qayta chiqaramiz (sessiya tirik qoladi).
        if self.scrollback_buffer:
            try:
                await websocket.send_text("\r\n".join(self.scrollback_buffer) + "\r\n")
            except Exception as exc:
                LOGGER.warning("Scrollback qayta yuborilmadi: %s: %s", type(exc).__name__, exc)
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
                except Exception as exc:
                    LOGGER.warning("PTY pong yuborilmadi: %s: %s", type(exc).__name__, exc)
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
                if mtype == "launch_agent":
                    # Kirishda tanlangan AI agentni PTY da ochish.
                    engine_key = str(payload.get("engine") or "").strip()
                    registry: dict = {}
                    try:
                        with open(os.path.join(ROOT_DIR, "agents.json"), encoding="utf-8") as _f:
                            registry = json.load(_f).get("agents", {})
                    except (OSError, json.JSONDecodeError) as exc:
                        self._append_scrollback(f"\x1b[31m[Nexus PTY] agents.json o'qilmadi: {exc}\x1b[0m\r\n")
                    meta = registry.get(engine_key) or {}
                    binary = str(meta.get("binary") or engine_key).strip()
                    if not re.fullmatch(r"[A-Za-z0-9_.-]+", binary):
                        self._append_scrollback(
                            f"\x1b[31m[Nexus PTY] Noto'g'ri agent buyrug'i: {binary!r}\x1b[0m\r\n"
                        )
                        return
                    # Interactive rejim uchun agentga xos flaglar (agents.json).
                    launch = str(meta.get("interactive_command") or binary)
                    launch = launch.replace("{workspace}", ROOT_DIR.replace("\\", "/"))
                    try:
                        parts = shlex.split(launch, posix=False)
                    except ValueError as exc:
                        self._append_scrollback(f"\x1b[31m[Nexus PTY] Buyruq parchalanmadi: {exc}\x1b[0m\r\n")
                        return
                    # Shell inyeksiyasiga yo'l yo'q: faqat oddiy tokenlar.
                    if any(any(ch in token for ch in ';&|`$()<>\n\r') for token in parts):
                        self._append_scrollback(
                            "\x1b[31m[Nexus PTY] Agent buyrug'ida taqiqlangan belgilar bor.\x1b[0m\r\n"
                        )
                        return
                    name = str(meta.get("name") or engine_key)
                    # Eski agent ishlab turgan bo'lsa, PTY ni qayta yaratamiz —
                    # aks holda buyruq uning TUI ichiga tushib ketadi.
                    if self._agent_launched:
                        await self.shutdown()
                    # Faqat PowerShell prompti ko'ringanda yozamiz (aks holda buyruq
                    # chiqish oqimiga aralashib CommandNotFoundError beradi).
                    try:
                        await asyncio.wait_for(self._prompt_ready.wait(), timeout=10)
                    except asyncio.TimeoutError:
                        self._append_scrollback(
                            "\x1b[33m[Conduit PTY] Prompt kutilmadi — agent ishga tushirilmadi.\x1b[0m\r\n"
                        )
                        return
                    self._agent_launched = True
                    self._write_pty(" ".join(parts) + "\r")
                    await self.broadcast(
                        f"\x1b[90m[Nexus] {name} ishga tushirildi (tanlangan agent).\x1b[0m\r\n",
                        record=False,
                    )
                    return
                if mtype == "agent_prompt":
                    # Foydalanuvchi matnini to'g'ridan-to'g'ri ishlab turgan AI agentga yozamiz.
                    text = str(payload.get("text") or "").strip()
                    if not text:
                        return
                    if "\r" in text or "\n" in text or any(ord(c) < 32 for c in text):
                        self._append_scrollback(
                            "\x1b[31m[Nexus PTY] Agent xabarida taqiqlangan belgilar bor.\x1b[0m\r\n"
                        )
                        return
                    self._write_pty(text + "\r")
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
                        # Guard oynasi: buyruq yozilgandan keyingi qisqa vaqt
                        # ichida kelgan xterm avtomatik javoblari (DA/DSR)
                        # tashlab yuboriladi — aks holda ular buyruq matni
                        # bilan aralashib PowerShell ParserError beradi.
                        self._run_guard_until = time.monotonic() + RUN_GUARD_SECONDS
                        self._write_pty(cmd + "\r")
                    return
                # boshqa JSON — PTY'ga raw yozamiz

        # RAW kiritish: har bir belgi (shu jumladan \x03, \r) to'g'ridan-to'g'ri PTY'ga.
        # Sof terminal javoblari (DA/DSR) faqat alternativ ekran TUI'si so'rov
        # yuborganda (1s ichida) uzatiladi. Oddiy PowerShell promptida ular
        # stray input bo'lib, matn sifatida ko'rinadi ([?1;2c) — tashlanadi.
        # Foydalanuvchining haqiqiy klavish kiritishi (harflar, strelkalar,
        # Ctrl+C) hech qachon filtrlanmaydi.
        if _TERMINAL_RESPONSE_RE.match(msg):
            # Alternativ ekran TUI'si so'rov yuborgan bo'lsa — javob uzatiladi.
            # Aks holda (oddiy shell prompti) bu javob matn sifatida sizib,
            # keyingi buyruqni buzadi: "[?1;2cython" -> ParserError.
            if not self._alt_screen or time.monotonic() >= self._query_seen_until:
                return
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
        self._agent_launched = False
        self._prompt_ready.clear()
        # Eski sessiyaning xato loglari yangi oynada ko'rinib qolmasligi uchun.
        self.scrollback_buffer.clear()
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
        await self.broadcast("\x1b[90m[Nexus PTY] Sessiya yopildi.\x1b[0m\r\n", record=False)
