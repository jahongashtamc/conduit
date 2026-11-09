"""
Persistent Terminal Session Manager for Conduit (Window 1).
Maintains a persistent session independent of WebSocket connections:
- Survives WebSocket disconnects without killing running processes.
- Retains scrollback history and replays it upon client reconnection.
- Handles ping/pong heartbeats.
- Supports running Conduit CLI and system commands with live streaming.
"""

import os
import asyncio
from typing import List, Set, Optional
from fastapi import WebSocket

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONDUIT_PY = os.path.join(ROOT_DIR, "conduit.py")

class TerminalSession:
    _instance: Optional['TerminalSession'] = None

    def __init__(self):
        self.scrollback_buffer: List[str] = []
        self.max_buffer_chars = 150000
        self.active_websockets: Set[WebSocket] = set()
        self.active_process: Optional[asyncio.subprocess.Process] = None
        self.input_buffer: str = ""
        self.lock = asyncio.Lock()

        # Initial banner
        banner = (
            "\r\n\x1b[1;36m╭─────────────────────────────────────────────────────────────╮\x1b[0m\r\n"
            "\x1b[1;36m│\x1b[0m  \x1b[1;37mCONDUIT PERSISTENT AGENT TERMINAL (v1.1.0)\x1b[0m                 \x1b[1;36m│\x1b[0m\r\n"
            "\x1b[1;36m│\x1b[0m  \x1b[90mSession: Persistent (survives disconnects, scrollback saved)\x1b[0m\x1b[1;36m│\x1b[0m\r\n"
            "\x1b[1;36m│\x1b[0m  \x1b[90mBuyruqlar: conduit run <subagent> \"<task>\", conduit wait    \x1b[0m\x1b[1;36m│\x1b[0m\r\n"
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
        # Prune if too long
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
        # Notice: Process continues running in background! Does not terminate.

    async def handle_input(self, msg: str):
        """Processes keystrokes and runs CLI commands."""
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

                # Run command in background
                run_cmd = cmd
                if run_cmd.startswith("conduit ") or run_cmd == "conduit":
                    args_part = run_cmd[7:].strip()
                    run_cmd = f'python "{CONDUIT_PY}" {args_part}'

                asyncio.create_task(self._execute_command(run_cmd))

            elif char in ("\x7f", "\x08"):  # Backspace
                if len(self.input_buffer) > 0:
                    self.input_buffer = self.input_buffer[:-1]
                    await self.broadcast("\b \b")
            else:
                self.input_buffer += char
                await self.broadcast(char)

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
                    text = line.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\n", "\r\n")
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
