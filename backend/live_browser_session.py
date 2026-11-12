"""Live browser session for subagents.

Node-based tools (visualCapture.js) launch a browser, take one screenshot and
close it — nothing to watch. This module keeps one Chromium alive, driven over
CDP by a small Node helper, so the UI can poll real frames while a subagent is
working.

Protocol (all JSON on stdout, one reply per request line on stdin):
    {"cmd":"goto","url":"..."}      -> {"success":true,"url":"...","title":"..."}
    {"cmd":"frame"}                 -> {"success":true,"data":"<base64 jpeg>"}
    {"cmd":"click","x":1,"y":2}     -> {"success":true}
    {"cmd":"eval","script":"..."}   -> {"success":true,"result":...}
    {"cmd":"close"}                 -> {"success":true}
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import shutil
import sys
from typing import Any, Dict, Optional

_NODE_HELPER = r"""
const path = require('path');
const readline = require('readline');

let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (e) {
  // The module lives in frontend/node_modules in this project; try the
  // obvious fallbacks before giving up.
  const candidates = [
    path.join(__dirname, '..', '..', 'frontend', 'node_modules', 'playwright'),
    path.join(__dirname, '..', 'node_modules', 'playwright'),
    'C:\\Users\\Kapitan\\conduit\\frontend\\node_modules\\playwright'
  ];
  let loaded = false;
  for (const c of candidates) {
    try {
      ({ chromium } = require(c));
      loaded = true;
      break;
    } catch (_) { /* keep trying */ }
  }
  if (!loaded) {
    console.log(JSON.stringify({ success: false, error: 'playwright module missing: ' + e.message }));
    process.exit(1);
  }
}

let browser = null;
let page = null;

async function ensure() {
  if (browser && page && !page.isClosed()) return;
  browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  page = await ctx.newPage();
}

const handlers = {
  async goto(msg) {
    await ensure();
    await page.goto(msg.url, { waitUntil: 'domcontentloaded', timeout: 25000 });
    return { success: true, url: page.url(), title: await page.title() };
  },
  async frame() {
    await ensure();
    const buf = await page.screenshot({ type: 'jpeg', quality: 60, timeout: 8000 });
    return { success: true, data: buf.toString('base64'), url: page.url(), title: await page.title() };
  },
  async click(msg) {
    await ensure();
    await page.mouse.click(msg.x, msg.y);
    return { success: true };
  },
  async eval(msg) {
    await ensure();
    const result = await page.evaluate(msg.script);
    return { success: true, result };
  },
  async close() {
    if (browser) { await browser.close(); browser = null; page = null; }
    return { success: true };
  }
};

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', async (line) => {
  if (!line.trim()) return;
  let msg;
  try { msg = JSON.parse(line); } catch (e) {
    console.log(JSON.stringify({ success: false, error: 'bad json' }));
    return;
  }
  const fn = handlers[msg.cmd];
  if (!fn) { console.log(JSON.stringify({ success: false, error: 'unknown cmd: ' + msg.cmd })); return; }
  try {
    console.log(JSON.stringify(await fn(msg)));
  } catch (e) {
    console.log(JSON.stringify({ success: false, error: String(e && e.message || e) }));
  }
});
"""


class LiveBrowserSession:
    """One long-lived Chromium, driven over a line protocol."""

    def __init__(self) -> None:
        self._proc: Optional[asyncio.subprocess.Process] = None
        self._lock = asyncio.Lock()
        self._helper: Optional[str] = None
        self.last_error = ""

    def _write_helper(self) -> str:
        if self._helper and os.path.exists(self._helper):
            return self._helper
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".agent-studio")
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, "live_browser_helper.cjs")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(_NODE_HELPER)
        self._helper = path
        return path

    async def _ensure_proc(self) -> bool:
        if self._proc and self._proc.returncode is None:
            return True
        node = shutil.which("node")
        if not node:
            self.last_error = "node.exe topilmadi (PATH)"
            return False
        helper = self._write_helper()
        # Run from backend/ so `require('playwright')` resolves against the
        # project's node_modules.
        cwd = os.path.dirname(os.path.abspath(__file__))
        try:
            self._proc = await asyncio.create_subprocess_exec(
                node,
                helper,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
        except Exception as exc:  # noqa: BLE001
            self.last_error = f"node ishga tushmadi: {exc}"
            return False
        return True

    async def send(self, msg: Dict[str, Any], timeout: float = 35.0) -> Dict[str, Any]:
        async with self._lock:
            if not await self._ensure_proc():
                return {"success": False, "error": self.last_error}
            proc = self._proc
            if proc is None or proc.stdin is None or proc.stdout is None:
                return {"success": False, "error": "node jarayoni yo'q"}
            try:
                proc.stdin.write((json.dumps(msg) + "\n").encode("utf-8"))
                await proc.stdin.drain()
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout)
            except asyncio.TimeoutError:
                self.last_error = f"node javob bermadi ({timeout}s)"
                return {"success": False, "error": self.last_error}
            except Exception as exc:  # noqa: BLE001
                self.last_error = str(exc)[:300]
                return {"success": False, "error": self.last_error}

            if not line:
                err = b""
                try:
                    if proc.stderr is not None:
                        err = await asyncio.wait_for(proc.stderr.read(600), timeout=3)
                except Exception:
                    pass
                self.last_error = "node yopildi: " + err.decode("utf-8", "replace")[:250]
                return {"success": False, "error": self.last_error}

            try:
                return json.loads(line.decode("utf-8", "replace"))
            except Exception:
                self.last_error = "node javobi noto'g'ri JSON"
                return {"success": False, "error": self.last_error}

    async def goto(self, url: str) -> Dict[str, Any]:
        return await self.send({"cmd": "goto", "url": url}, timeout=40)

    async def frame(self) -> Optional[bytes]:
        res = await self.send({"cmd": "frame"}, timeout=20)
        if not res.get("success"):
            return None
        try:
            return base64.b64decode(res.get("data", ""))
        except Exception:
            return None

    async def click(self, x: float, y: float) -> bool:
        res = await self.send({"cmd": "click", "x": x, "y": y}, timeout=15)
        return bool(res.get("success"))

    async def eval(self, script: str) -> Dict[str, Any]:
        return await self.send({"cmd": "eval", "script": script}, timeout=25)

    async def close(self) -> None:
        if self._proc and self._proc.returncode is None:
            await self.send({"cmd": "close"}, timeout=10)
            try:
                self._proc.terminate()
            except Exception:
                pass
        self._proc = None


_session = LiveBrowserSession()


def session() -> LiveBrowserSession:
    return _session
