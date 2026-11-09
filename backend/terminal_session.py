"""
Persistent Terminal Session Manager for Conduit (Window 1).
AI Agent Brain & CLI Command Dispatcher:
- Pure ASCII safe frames to eliminate any Windows CP1251 encoding errors.
- Handles `agy`, `agy <vazifa>`, `conduit run <agent> <vazifa>`, and natural language.
- Directly invokes Conduit AI Agent Brain with live streaming execution.
"""

import os
import sys
import asyncio
import json
import re
from typing import List, Set, Optional
from fastapi import WebSocket

# Ensure UTF-8 stream output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONDUIT_PY = os.path.join(ROOT_DIR, "conduit.py")
PYTHON_EXE = sys.executable
AGY_EXE = r"C:\Users\user\AppData\Local\agy\bin\agy.exe"

class TerminalSession:
    _instance: Optional['TerminalSession'] = None

    def __init__(self):
        self.scrollback_buffer: List[str] = []
        self.max_buffer_chars = 150000
        self.active_websockets: Set[WebSocket] = set()
        self.active_process: Optional[asyncio.subprocess.Process] = None
        self.input_buffer: str = ""
        self.command_history: List[str] = []
        self.lock = asyncio.Lock()

        # Pure ASCII safe banner
        banner = (
            "\r\n\x1b[1;36m+-------------------------------------------------------------+\x1b[0m\r\n"
            "\x1b[1;36m|\x1b[0m  \x1b[1;32mCONDUIT AI MIYYA -- AGENT TERMINALI (v2.0)\x1b[0m                 \x1b[1;36m|\x1b[0m\r\n"
            "\x1b[1;36m|\x1b[0m  \x1b[90mAI Miyya: Faol | 11 ta subagent tayyor                     \x1b[0m\x1b[1;36m|\x1b[0m\r\n"
            "\x1b[1;36m|\x1b[0m  \x1b[1;33mBuyruqlar: agy, agy <vazifa>, conduit list, conduit run ...\x1b[0m\x1b[1;36m|\x1b[0m\r\n"
            "\x1b[1;36m+-------------------------------------------------------------+\x1b[0m\r\n\r\n"
            "\x1b[32mconduit@studio\x1b[0m:\x1b[34m~/workspace\x1b[0m$ "
        )
        self._append_to_scrollback(banner)

    @classmethod
    def get_instance(cls) -> 'TerminalSession':
        if cls._instance is None:
            cls._instance = TerminalSession()
        return cls._instance

    def _append_to_scrollback(self, text: str):
        self.scrollback_buffer.append(text)
        total_len = sum(len(s) for s in self.scrollback_buffer)
        while total_len > self.max_buffer_chars and len(self.scrollback_buffer) > 1:
            removed = self.scrollback_buffer.pop(0)
            total_len -= len(removed)

    async def broadcast(self, text: str):
        """Append to scrollback and send to all connected websockets."""
        self._append_to_scrollback(text)
        dead = []
        for ws in list(self.active_websockets):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active_websockets.discard(ws)

    async def connect_client(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.add(websocket)
        full_history = "".join(self.scrollback_buffer)
        if full_history:
            try:
                await websocket.send_text(full_history)
            except Exception:
                pass

    def disconnect_client(self, websocket: WebSocket):
        self.active_websockets.discard(websocket)

    async def handle_input(self, msg: str):
        """Processes keystrokes, JSON commands, and CLI input."""
        if not msg:
            return

        # Ping/pong heartbeat
        if msg in ("ping", '{"type":"ping"}'):
            for ws in list(self.active_websockets):
                try:
                    await ws.send_text('{"type":"pong"}')
                except Exception:
                    pass
            return

        # Check if msg is JSON command packet
        if msg.startswith("{") and msg.endswith("}"):
            try:
                payload = json.loads(msg)
                msg_type = payload.get("type")
                if msg_type == "run":
                    cmd = payload.get("command", "").strip()
                    if cmd:
                        await self.broadcast(f"{cmd}\r\n")
                        self.input_buffer = ""
                        await self._dispatch_command(cmd)
                    return
                elif msg_type == "clear":
                    self.scrollback_buffer.clear()
                    await self.broadcast("\x1b[2J\x1b[H\x1b[32mconduit@studio\x1b[0m:\x1b[34m~/workspace\x1b[0m$ ")
                    return
            except Exception:
                pass

        # Handle Ctrl+C (\x03)
        if "\x03" in msg:
            if self.active_process and self.active_process.returncode is None:
                try:
                    self.active_process.terminate()
                except Exception:
                    pass
                await self.broadcast("^C\r\n\x1b[31m[JARAYON TO'XTATILDI]\x1b[0m\r\n\x1b[32mconduit@studio\x1b[0m:\x1b[34m~/workspace\x1b[0m$ ")
            else:
                self.input_buffer = ""
                await self.broadcast("^C\r\n\x1b[32mconduit@studio\x1b[0m:\x1b[34m~/workspace\x1b[0m$ ")
            return

        # Process characters
        for char in msg:
            if char in ("\r", "\n"):
                cmd = self.input_buffer.strip()
                await self.broadcast("\r\n")
                self.input_buffer = ""

                if not cmd:
                    await self.broadcast("\x1b[32mconduit@studio\x1b[0m:\x1b[34m~/workspace\x1b[0m$ ")
                    continue

                if cmd in ("clear", "cls"):
                    self.scrollback_buffer.clear()
                    await self.broadcast("\x1b[2J\x1b[H\x1b[32mconduit@studio\x1b[0m:\x1b[34m~/workspace\x1b[0m$ ")
                    continue

                await self._dispatch_command(cmd)

            elif char in ("\x7f", "\x08"):  # Backspace
                if len(self.input_buffer) > 0:
                    self.input_buffer = self.input_buffer[:-1]
                    await self.broadcast("\b \b")
            else:
                self.input_buffer += char
                await self.broadcast(char)

    async def _dispatch_command(self, cmd: str):
        """Dispatch Conduit, agy AI, or OS shell commands safely."""
        self.command_history.append(cmd)
        clean = cmd.strip()

        # 1. agy alone or help
        if clean in ("agy", "agy help", "help", "miya"):
            help_text = (
                "\r\n\x1b[1;36m+-------------------------------------------------------------+\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m  \x1b[1;32m[CONDUIT AI MIYYA] ISHLAMOQDA\x1b[0m                              \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m                                                              \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m  \x1b[1;37mAI Agentni chaqirish:\x1b[0m                                      \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m    \x1b[1;33magy <vazifa>\x1b[0m             -> AI Miyyaga vazifa berish       \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m    \x1b[90mMasalan: agy Editor uchun asbob top                       \x1b[0m\x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m    \x1b[90mMasalan: agy 3D sahna yasa va render qil                  \x1b[0m\x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m                                                              \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m  \x1b[1;37mMavjud Agentlar:\x1b[0m                                            \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m   - \x1b[36mScout\x1b[0m    : Veb qidiruv, DeepSearch, DeepX, tahlil          \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m   - \x1b[36mEditor\x1b[0m   : Video montaj, timeline, audio, rang             \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m   - \x1b[36mSculptor\x1b[0m : 3D modellashtirish, Blender rendering        \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m   - \x1b[36mAnimator\x1b[0m : Harakatli grafikalar, keyframe VFX             \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m   - \x1b[36mPainter\x1b[0m  : Photoshop, rasm va teksturalar                 \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m   - \x1b[36mInspector\x1b[0m: Xavfsizlik, tizim auditi, test (PASS/FAIL)     \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m                                                              \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m  \x1b[1;37mBoshqa buyruqlar:\x1b[0m                                           \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m    \x1b[36mconduit list\x1b[0m             -> Barcha subagentlar ro'yxati    \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m|\x1b[0m    \x1b[36mconduit run <agent> <ish>\x1b[0m-> Aniq agentga vazifa berish     \x1b[1;36m|\x1b[0m\r\n"
                "\x1b[1;36m+-------------------------------------------------------------+\x1b[0m\r\n"
            )
            await self.broadcast(help_text)
            await self.broadcast("\x1b[32mconduit@studio\x1b[0m:\x1b[34m~/workspace\x1b[0m$ ")
            return

        # 2. agy <prompt>
        if clean.startswith("agy "):
            prompt_arg = clean[4:].strip().strip('"\'')
            if prompt_arg.startswith("-"):
                run_cmd = f'"{AGY_EXE}" {clean[4:]}'
                asyncio.create_task(self._execute_command(run_cmd, auto_wait=False))
            else:
                await self.broadcast(f"\x1b[1;33m[AI MIYYA]: Vazifa qabul qilindi -> \"{prompt_arg}\"\x1b[0m\r\n")
                run_cmd = f'"{PYTHON_EXE}" "{CONDUIT_PY}" run auto "{prompt_arg}"'
                asyncio.create_task(self._execute_command(run_cmd, auto_wait=True))
            return

        # 3. conduit commands
        if clean.startswith("conduit ") or clean == "conduit":
            args_part = clean[7:].strip()
            run_cmd = f'"{PYTHON_EXE}" "{CONDUIT_PY}" {args_part}'
            asyncio.create_task(self._execute_command(run_cmd, auto_wait=("run " in clean)))
            return

        # 4. Standard Windows shell built-ins or system commands
        SHELL_CMDS = {
            "dir", "cls", "clear", "cd", "type", "copy", "del", "mkdir", "rmdir", 
            "ipconfig", "whoami", "powershell", "cmd", "echo", "python", "node", 
            "npm", "git", "ffmpeg", "ffprobe", "tasklist", "netstat", "exit"
        }
        first_word = clean.split()[0].lower() if clean else ""
        if first_word in SHELL_CMDS or first_word.endswith(".exe") or first_word.endswith(".bat"):
            asyncio.create_task(self._execute_command(clean))
            return

        # 5. Natural language AI task fallback
        await self.broadcast(f"\x1b[1;33m[AI MIYYA]: Topshiriq qabul qilindi -> \"{clean}\"\x1b[0m\r\n")
        run_cmd = f'"{PYTHON_EXE}" "{CONDUIT_PY}" run auto "{clean}"'
        asyncio.create_task(self._execute_command(run_cmd, auto_wait=True))

    async def _execute_command(self, cmd_str: str, auto_wait: bool = False):
        try:
            env = os.environ.copy()
            extra_paths = [
                r"C:\Users\user\AppData\Local\agy\bin",
                r"C:\Users\user\AppData\Local\Programs\Python\Python312",
                r"C:\Users\user\AppData\Local\Programs\Python\Python312\Scripts",
                ROOT_DIR
            ]
            env["PATH"] = ";".join(extra_paths) + ";" + env.get("PATH", "")
            env["PYTHONIOENCODING"] = "utf-8"

            self.active_process = await asyncio.create_subprocess_shell(
                cmd_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=ROOT_DIR,
                env=env
            )

            created_task_id = None

            async def stream_output(stream):
                nonlocal created_task_id
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    try:
                        text = line.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            text = line.decode("cp1251")
                        except Exception:
                            try:
                                text = line.decode("cp866")
                            except Exception:
                                text = line.decode("latin1", errors="replace")

                    if "Vazifa ID:" in text:
                        match = re.search(r"task_[a-zA-Z0-9_]+", text)
                        if match:
                            created_task_id = match.group(0)

                    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
                    await self.broadcast(text)

            await asyncio.gather(
                stream_output(self.active_process.stdout),
                stream_output(self.active_process.stderr)
            )
            await self.active_process.wait()

            if auto_wait and created_task_id:
                await self.broadcast(f"\r\n\x1b[36m[AI MIYYA]: Vazifa bajarilishi kuzatilmoqda ({created_task_id})...\x1b[0m\r\n")
                wait_cmd = f'"{PYTHON_EXE}" "{CONDUIT_PY}" wait {created_task_id}'
                wait_proc = await asyncio.create_subprocess_shell(
                    wait_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=ROOT_DIR,
                    env=env
                )
                await asyncio.gather(
                    stream_output(wait_proc.stdout),
                    stream_output(wait_proc.stderr)
                )
                await wait_proc.wait()

        except Exception as e:
            await self.broadcast(f"\x1b[31m[BUYRUQ XATOSI]: {str(e)}\x1b[0m\r\n")
        finally:
            self.active_process = None
            await self.broadcast("\x1b[32mconduit@studio\x1b[0m:\x1b[34m~/workspace\x1b[0m$ ")
