"""Live browser view for Conduit subagents.

A single long-lived Chromium (see live_browser_session.py) backs the "Jonli"
tab in the UI. Any subagent that wants the operator to see what it is doing
calls `goto()` here; the UI polls `/api/browser/frame` for real frames.

State exposed to the UI:
    is_open, url, title, frame_count, last_error
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

import live_browser_session as session_mod

_state: Dict[str, Any] = {
    "url": "",
    "title": "",
    "is_open": False,
    "last_frame_at": 0.0,
    "frame_count": 0,
    "last_error": "",
}
_lock = asyncio.Lock()
_last_frame: Optional[bytes] = None


def state() -> Dict[str, Any]:
    return dict(_state)


def set_error(message: str) -> None:
    _state["last_error"] = str(message)[:400]


def clear() -> None:
    global _last_frame
    _last_frame = None
    _state.update({"is_open": False, "url": "", "title": "", "last_error": ""})


def last_frame_bytes() -> Optional[bytes]:
    return _last_frame


def _update_from(res: Dict[str, Any]) -> None:
    if res.get("url"):
        _state["url"] = res["url"]
    if res.get("title"):
        _state["title"] = res["title"]


async def goto(url: str) -> bool:
    """Opens a URL in the watched browser so the operator can follow along."""
    async with _lock:
        res = await session_mod.session().goto(url)
        if res.get("success"):
            _state["is_open"] = True
            _state["last_error"] = ""
            _update_from(res)
            return True
        _state["last_error"] = str(res.get("error", ""))[:300]
        return False


async def frame() -> Optional[bytes]:
    """Current JPEG frame of the watched browser."""
    global _last_frame
    async with _lock:
        data = await session_mod.session().frame()
        if data:
            _last_frame = data
            _state["frame_count"] = int(_state.get("frame_count", 0)) + 1
            _state["last_frame_at"] = time.time()
            _state["is_open"] = True
            _state["last_error"] = ""
            if not _state["url"]:
                # The helper knows the real URL even when goto() raced.
                res = await session_mod.session().eval("location.href")
                if res.get("success") and res.get("result"):
                    _state["url"] = str(res["result"])
                    title = await session_mod.session().eval("document.title")
                    if title.get("success") and title.get("result"):
                        _state["title"] = str(title["result"])
        elif not _state["is_open"]:
            _state["last_error"] = session_mod.session().last_error[:300]
        return _last_frame


async def click_in_view(x: float, y: float) -> bool:
    async with _lock:
        return await session_mod.session().click(x, y)


async def navigate(url: str) -> bool:
    return await goto(url)


async def shutdown() -> None:
    await session_mod.session().close()
    clear()
