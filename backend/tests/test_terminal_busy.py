"""Agent band bo'lganda terminal xabarlari navbatga tushmasligi testi."""

import asyncio
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
