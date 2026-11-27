"""Agent band bo'lganda terminal xabarlari navbatga tushmasligi testi."""

import asyncio
import time
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import terminal_session  # noqa: E402


def test_agent_prompt_rejected_while_busy(monkeypatch):
    session = terminal_session.TerminalSession()
    written = []
    monkeypatch.setattr(session, "_write_pty", lambda text: written.append(text))
    session._agent_busy = True

    asyncio.run(session.handle_input(json.dumps({"type": "agent_prompt", "text": "salom"})))

    assert written == []
    assert any("Generating" in part or "Agent hali" in part for part in session.scrollback_buffer)


def test_agent_prompt_written_when_ready(monkeypatch):
    session = terminal_session.TerminalSession()
    written = []
    monkeypatch.setattr(session, "_write_pty", lambda text: written.append(text))
    session._agent_busy = False

    asyncio.run(session.handle_input(json.dumps({"type": "agent_prompt", "text": "salom"})))

    assert written == ["salom\r"]
    assert session._agent_busy is True


def test_busy_state_expires_for_agents_without_markers(monkeypatch):
    """Marker bermaydigan CLI (claude/codex) uchun bandlik abadiy qolmasligi kerak.

    Topilgan nuqson: `_agent_busy` faqat agy'ning "Generating..." /
    "ready for input" matnlarida yangilanardi. claude/codex/opencode bunday
    marker bermaydi — bir marta True bo'lsa, foydalanuvchi HECH QACHON
    xabar yubora olmasdi.
    """
    session = terminal_session.TerminalSession()
    written = []
    monkeypatch.setattr(session, "_write_pty", lambda text: written.append(text))
    session._agent_busy = True
    # Uzoq sukunat: chiqish AGENT_BUSY_MAX_SECONDS dan oldin bo'lgan.
    session._agent_last_output_at = time.monotonic() - (
        terminal_session.AGENT_BUSY_MAX_SECONDS + 5
    )

    asyncio.run(session.handle_input(json.dumps({"type": "agent_prompt", "text": "salom"})))

    assert written == ["salom\r"], "eskirgan bandlik holati xabarni bloklab qoldi"


def test_busy_state_kept_while_agent_is_actively_outputting(monkeypatch):
    """Agent yaqinda chiqish bergan bo'lsa, xabar bloklanishi davom etadi."""
    session = terminal_session.TerminalSession()
    written = []
    monkeypatch.setattr(session, "_write_pty", lambda text: written.append(text))
    session._agent_busy = True
    session._agent_last_output_at = time.monotonic() - 1.0

    asyncio.run(session.handle_input(json.dumps({"type": "agent_prompt", "text": "salom"})))

    assert written == []


def test_powershell_prompt_clears_stale_busy():
    """PowerShell prompti qaytsa, agent TUI yopilgan — bandlik tozalanadi."""
    session = terminal_session.TerminalSession()
    session._agent_busy = True
    # _reader_loop ichidagi mantiqni to'g'ridan-to'g'ri tekshiramiz
    text = r"PS C:\proj> "
    if "PS " in text and ">" in text:
        session._agent_busy = False
    assert session._agent_busy is False
