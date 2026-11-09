"""
Real Interactive Windows PowerShell Terminal for Conduit.
Direct native shell execution:
- Merged STDOUT/STDERR so all tool outputs, agy CLI, Python, and system commands stream live.
- PATH includes C:\\Users\\user\\AppData\\Local\\agy\\bin, Python, and project tools.
- Preserves persistent scrollback history across reconnections.
"""

import os
import sys
import asyncio
import json
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
            "Windows PowerShell (Conduit Native Shell)\r\n"
            "Copyright (C) Microsoft Corporation. All rights reserved.\r\n"
            "Conduit & agy AI vositalari yoqilgan.\r\n\r\n"
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

        # JSON packet support from quick buttons
        if msg.startswith("{") and msg.endswith("}"):
            try:
                payload = json.loads(msg)
                msg_type = payload.get("type")
                if msg_type == "run":
                    cmd = payload.get("command", "").strip()
                    if cmd:
                        await self.broadcast(f"{cmd}\r\n")
                        self.input_buffer = ""
                        asyncio.create_task(self._execute_command(cmd))
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

                if cmd.lower() in ("clear", "cls"):
                    self.scrollback_buffer.clear()
                    await self.broadcast(f"\x1b[2J\x1b[HPS {self.cwd}> ")
                    continue

                # Handle cd command
                if cmd.lower().startswith("cd "):
                    target_dir = cmd[3:].strip().strip('"\'')
                    new_path = os.path.abspath(os.path.join(self.cwd, target_dir))
                    if os.path.isdir(new_path):
                        self.cwd = new_path
                    else:
                        await self.broadcast(f"cd : Yo'l topilmadi: {target_dir}\r\n")
                    await self.broadcast(f"PS {self.cwd}> ")
                    continue

                asyncio.create_task(self._execute_command(cmd))

            elif char in ("\x7f", "\x08"):  # Backspace
                if len(self.input_buffer) > 0:
                    self.input_buffer = self.input_buffer[:-1]
                    await self.broadcast("\b \b")
            else:
                self.input_buffer += char
                await self.broadcast(char)

    async def _execute_command(self, cmd_str: str):
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

            # Execute directly in native powershell with merged stdout/stderr
            self.active_process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                cmd_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.cwd,
                env=env
            )

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

                text = text.replace("\r\n", "\n").replace("\n", "\r\n")
                await self.broadcast(text)

            await self.active_process.wait()

        except Exception as e:
            await self.broadcast(f"[XATO]: {str(e)}\r\n")
        finally:
            self.active_process = None
            await self.broadcast(f"PS {self.cwd}> ")
