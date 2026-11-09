"""
Persistent Terminal Session Manager for Conduit (Window 1).
Maintains a persistent session independent of WebSocket connections:
- Survives WebSocket disconnects without killing running processes.
- Retains scrollback history and replays it upon client reconnection.
- Handles ping/pong heartbeats.
- Supports running Conduit CLI and system commands with live streaming.
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
        self.max_buffer_chars = 150000
        self.active_websockets: Set[WebSocket] = set()
        self.active_process: Optional[asyncio.subprocess.Process] = None
        self.input_buffer: str = ""
        self.command_history: List[str] = []
        self.lock = asyncio.Lock()

        # Initial banner
        banner = (
            "\r\n\x1b[1;36m╭─────────────────────────────────────────────────────────────╮\x1b[0m\r\n"
            "\x1b[1;36m│\x1b[0m  \x1b[1;37mCONDUIT PERSISTENT AGENT TERMINAL (v1.2.0)\x1b[0m                 \x1b[1;36m│\x1b[0m\r\n"
            "\x1b[1;36m│\x1b[0m  \x1b[90mMuhit: Standalone PC Desktop App Mode\x1b[0m                      \x1b[1;36m│\x1b[0m\r\n"
            "\x1b[1;36m│\x1b[0m  \x1b[90mBuyruqlar: conduit list, conduit run <agent> <vazifa>, dir    \x1b[0m\x1b[1;36m│\x1b[0m\r\n"
            "\x1b[1;36m╰─────────────────────────────────────────────────────────────╯\x1b[0m\r\n\r\n"
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
        # Send full replay of scrollback history
        full_history = "".join(self.scrollback_buffer)
        if full_history:
            await websocket.send_text(full_history)

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
        """Dispatch Conduit or OS shell commands safely."""
        self.command_history.append(cmd)
        run_cmd = cmd
        if run_cmd.startswith("conduit ") or run_cmd == "conduit":
            args_part = run_cmd[7:].strip()
            run_cmd = f'"{PYTHON_EXE}" "{CONDUIT_PY}" {args_part}'

        asyncio.create_task(self._execute_command(run_cmd))

    async def _execute_command(self, cmd_str: str):
        try:
            self.active_process = await asyncio.create_subprocess_shell(
                cmd_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=ROOT_DIR
            )

            async def stream_output(stream):
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
                            text = line.decode("latin1", errors="replace")

                    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
                    await self.broadcast(text)

            await asyncio.gather(
                stream_output(self.active_process.stdout),
                stream_output(self.active_process.stderr)
            )
            await self.active_process.wait()
        except Exception as e:
            await self.broadcast(f"\x1b[31m[BUYRUQ XATOSI]: {str(e)}\x1b[0m\r\n")
        finally:
            self.active_process = None
            await self.broadcast("\x1b[32mconduit@studio\x1b[0m:\x1b[34m~/workspace\x1b[0m$ ")
