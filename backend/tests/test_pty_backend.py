"""PTY backend tanlovi regressiyasi.

Topilgan nuqson (2026-11-27): pywinpty 3.x `spawn()` da backend berilmasa
avtomatik tanlaydi va bu mashinada Ctrl+C umuman ishlamaydigan backend'ga
tushib qoladi. O'lchov (pywinpty 3.1.2, 4 ta urinish): ConPTY=1 -> 4/4
muvaffaqiyat; WinPTY=0 yoki env yo'q -> 0/4 (terminal osilib qoladi).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="ConPTY faqat Windows'da")
def test_spawn_forces_conpty_backend(monkeypatch):
    """`_spawn_pty` ConPTY backend'ni majburlashi shart."""
    import terminal_session

    monkeypatch.delenv("PYWINPTY_BACKEND", raising=False)
    session = terminal_session.TerminalSession()

    # winpty'ni soxtalashtiramiz: spawn chaqirilganini va env'ni tekshiramiz
    class _FakePty:
        pid = 1234

        def __init__(self):
            self.alive = True

        def isalive(self):
            return True

    captured = {}

    class _FakePtyProcess:
        @staticmethod
        def spawn(*args, **kwargs):
            captured["backend_env"] = os.environ.get("PYWINPTY_BACKEND")
            captured["args"] = args
            return _FakePty()

    import winpty

    monkeypatch.setattr(winpty, "PtyProcess", _FakePtyProcess)
    monkeypatch.setattr(session, "_start_reader", lambda: None)
    monkeypatch.setattr(session, "_append_scrollback", lambda *_: None)

    session._spawn_pty()

    assert captured["backend_env"] == "1", (
        f"PYWINPTY_BACKEND=1 bo'lishi shart, olindi: {captured['backend_env']!r}. "
        "Aks holda Ctrl+C ishlamaydi."
    )


@pytest.mark.skipif(sys.platform != "win32", reason="ConPTY faqat Windows'da")
def test_ctrl_c_uses_sendintr(monkeypatch):
    """Ctrl+C uchun pywinpty'ning rasmiy `sendintr()` API'si ishlatiladi."""
    import asyncio

    import terminal_session

    session = terminal_session.TerminalSession()
    calls = []

    class _FakePty:
        def isalive(self):
            return True

        def sendintr(self):
            calls.append("sendintr")

        def write(self, data):  # pragma: no cover - bo'lmasligi kerak
            calls.append(f"write:{data!r}")

    session.pt = _FakePty()
    session._ensure_pty = lambda: True  # type: ignore[method-assign]

    asyncio.run(session.handle_input("\x03"))

    assert calls == ["sendintr"], f"kutilgan sendintr, olindi: {calls}"
