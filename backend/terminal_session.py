"""
Real Interactive Windows PowerShell & Shell Terminal for Conduit.
Direct native shell execution:
- Instant response to `agy` (online AI Agent info & guidance).
- Instant execution of `agy <vazifa>` (AI agent dispatches task and streams live output).
- Direct shell execution for `dir`, `python`, `git`, `conduit`, etc.
"""

import os
import sys
import asyncio
import json
import re
from typing import List, Set, Optional
from fastapi import WebSocket

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONDUIT_PY = os.path.join(ROOT_DIR, "conduit.py")
PYTHON_EXE = sys.executable

class TerminalSession:
    _instance: Optional['TerminalSession'] = None

    def __init__(self):
        self.scrollback_buffer: List[str] = []
        self.max_buffer_chars = 250000
        self.active_websockets: Set[WebSocket] = set()
        self.active_process: Optional[asyncio.subprocess.Process] = None
        self.input_buffer: str = ""
        self.cwd = ROOT_DIR

        # Native shell prompt
        banner = (
            "Windows PowerShell (Conduit Studio Shell)\r\n"
            "Copyright (C) Microsoft Corporation. All rights reserved.\r\n"
            "AI Agent (agy) va Conduit asboblari faol.\r\n\r\n"
            f"PS {self.cwd}> "
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

        # JSON packet support from UI buttons
        if msg.startswith("{") and msg.endswith("}"):
            try:
                payload = json.loads(msg)
                msg_type = payload.get("type")
                if msg_type == "run":
                    cmd = payload.get("command", "").strip()
                    if cmd:
                        await self.broadcast(f"{cmd}\r\n")
                        self.input_buffer = ""
                        await self._dispatch(cmd)
                    return
                elif msg_type == "clear":
                    self.scrollback_buffer.clear()
                    await self.broadcast(f"\x1b[2J\x1b[HPS {self.cwd}> ")
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
                await self.broadcast(f"^C\r\nPS {self.cwd}> ")
            else:
                self.input_buffer = ""
                await self.broadcast(f"^C\r\nPS {self.cwd}> ")
            return

        # Process characters
        for char in msg:
            if char in ("\r", "\n"):
                cmd = self.input_buffer.strip()
                await self.broadcast("\r\n")
                self.input_buffer = ""

                if not cmd:
                    await self.broadcast(f"PS {self.cwd}> ")
                    continue

                await self._dispatch(cmd)

            elif char in ("\x7f", "\x08"):  # Backspace
                if len(self.input_buffer) > 0:
                    self.input_buffer = self.input_buffer[:-1]
                    await self.broadcast("\b \b")
            else:
                self.input_buffer += char
                await self.broadcast(char)

    async def _dispatch(self, cmd: str):
        clean = cmd.strip()

        # 1. Clear screen
        if clean.lower() in ("clear", "cls"):
            self.scrollback_buffer.clear()
            await self.broadcast(f"\x1b[2J\x1b[HPS {self.cwd}> ")
            return

        # 2. Change directory
        if clean.lower().startswith("cd "):
            target_dir = clean[3:].strip().strip('"\'')
            new_path = os.path.abspath(os.path.join(self.cwd, target_dir))
            if os.path.isdir(new_path):
                self.cwd = new_path
            else:
                await self.broadcast(f"cd : Yo'l topilmadi: {target_dir}\r\n")
            await self.broadcast(f"PS {self.cwd}> ")
            return

        # 3. agy command (alone)
        if clean.lower() == "agy":
            agy_banner = (
                "\r\n\x1b[1;36mAntigravity AI Agent (AGY CLI) [ONLINE & ACTIVE]\x1b[0m\r\n"
                "\x1b[90mConduit Studio Sovereign AI Orchestration Node\x1b[0m\r\n\r\n"
                "\x1b[1mFoydalanish:\x1b[0m\r\n"
                "  \x1b[33magy <vazifa>\x1b[0m             -> AI agentga vazifa topshirish (masalan: agy Editor uchun asbob top)\r\n"
                "  \x1b[36mconduit list\x1b[0m             -> Barcha studiya subagentlari ro'yxati\r\n"
                "  \x1b[36mconduit run <agent> <ish>\x1b[0m-> Aniq agentni ishga tushirish\r\n\r\n"
            )
            await self.broadcast(agy_banner)
            await self.broadcast(f"PS {self.cwd}> ")
            return

        # 4. agy <vazifa>
        if clean.lower().startswith("agy "):
            task_prompt = clean[4:].strip().strip('"\'')
            if not task_prompt:
                await self.broadcast("Iltimos, vazifani kiriting: agy \"<vazifa>\"\r\n")
                await self.broadcast(f"PS {self.cwd}> ")
                return
            await self.broadcast(f"\x1b[1;33m[AI AGENT]: Vazifa qabul qilindi -> \"{task_prompt}\"\x1b[0m\r\n")
            run_cmd = f'"{PYTHON_EXE}" "{CONDUIT_PY}" run auto "{task_prompt}"'
            asyncio.create_task(self._execute_command(run_cmd, auto_wait=True))
            return

        # 5. conduit CLI commands
        if clean.lower().startswith("conduit ") or clean.lower() == "conduit":
            args_part = clean[7:].strip()
            run_cmd = f'"{PYTHON_EXE}" "{CONDUIT_PY}" {args_part}'
            asyncio.create_task(self._execute_command(run_cmd, auto_wait=("run " in clean)))
            return

        # 6. Shell execution (dir, ipconfig, python, git, etc.)
        asyncio.create_task(self._execute_command(clean))

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
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.cwd,
                env=env
            )

            created_task_id = None

            while True:
                line = await self.active_process.stdout.readline()
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

            await self.active_process.wait()

            # Auto wait for conduit task if requested
            if auto_wait and created_task_id:
                await self.broadcast(f"\r\n\x1b[36m[AI MIYYA]: Vazifa kuzatilmoqda ({created_task_id})...\x1b[0m\r\n")
                wait_cmd = f'"{PYTHON_EXE}" "{CONDUIT_PY}" wait {created_task_id}'
                wait_proc = await asyncio.create_subprocess_shell(
                    wait_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=self.cwd,
                    env=env
                )
                while True:
                    wline = await wait_proc.stdout.readline()
                    if not wline:
                        break
                    try:
                        wtext = wline.decode("utf-8")
                    except UnicodeDecodeError:
                        wtext = wline.decode("cp1251", errors="replace")
                    wtext = wtext.replace("\r\n", "\n").replace("\n", "\r\n")
                    await self.broadcast(wtext)
                await wait_proc.wait()

        except Exception as e:
            await self.broadcast(f"[XATO]: {str(e)}\r\n")
        finally:
            self.active_process = None
            await self.broadcast(f"PS {self.cwd}> ")
