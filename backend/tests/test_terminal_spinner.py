"""PTY spinner kadrlari terminalda zinapoya hosil qilmasligi testi."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import terminal_session  # noqa: E402


FRAMES = (
    "\r⣻  Running command...\x1b[m\x1b[K\n\n"
    "\r⣽  Running comman\n\n"
    "\r⣾  Running command\n\n"
    "\r⣷  Running command.\n\n"
    "\r⣯  Running command...\n\n"
)


def test_spinner_frames_collapse_to_single_line():
    out = terminal_session.collapse_spinner_frames(FRAMES)
    assert out.count("\n") <= 2, repr(out)
    assert "Running command" in out
    # Har bir oraliq kadr bir xil satrga qaytariladi (\r), yangi satrga emas.
    assert out.count("\r") >= 4, repr(out)


def test_single_frame_chunk_is_collapsed():
    # Bo'laklar alohida keladi: bitta kadr ham zinapoya yaratmasligi kerak.
    chunk = "\r⣻  Running comman\n\n"
    out = terminal_session.collapse_spinner_frames(chunk)
    assert "\n" not in out, repr(out)
    assert out.startswith("\r⣻  Running comman"), repr(out)
    assert out.endswith("\x1b[K"), repr(out)


def test_partial_and_triple_newline_frames_are_collapsed():
    # Haqiqiy PTY bo'laklarida matn qisqa (`Runn`) va `\n\n\n` keladi.
    chunk = "\r⣻ \n\n\n\r⢿  Runn\n\n\n\r⣽  Runnin\n\n\n"
    out = terminal_session.collapse_spinner_frames(chunk)
    assert "\n" not in out, repr(out)
    assert out.count("\x1b[K") == 3, repr(out)


def test_cursor_up_running_frame_is_not_touched():
    # `Running` bo'lsa ham \x1b[2A bilan o'zini qayta chizadi — tegmaymiz.
    tui = "\r\x1b[2A⣽  Running command...\n\n"
    assert terminal_session.collapse_spinner_frames(tui) == tui


def test_normal_output_is_not_touched():
    normal = "PS C:\\repo> conduit list\r\n1. scout\r\n2. painter\r\n"
    assert terminal_session.collapse_spinner_frames(normal) == normal


def test_cursor_up_tui_output_is_not_touched():
    # agy "Generating" kadrlari \x1b[3A bilan o'zini qayta chizadi — ularga tegmaslik kerak.
    tui = "\r\x1b[3A⣽  Loading\n\n\n\x1b[8D\r\x1b[3A⣾  Loading..\n\n\n"
    assert terminal_session.collapse_spinner_frames(tui) == tui


def test_scrollback_replay_preserves_cursor_up_frames(monkeypatch):
    # Qayta ulanishda bo'laklar orasiga \r\n qo'yilsa, \x1b[3A noto'g'ri
    # satrga ko'tarilib, spinner zinapoya hosil qiladi. Xom bo'laklar saqlanishi shart.
    frames = (
        "\x1b[?25l\r\x1b[3A⣯  \x1b[90mRunning command...\x1b[m\n\n\n\x1b[19D\x1b[?25h",
        "\x1b[?25l\r\x1b[3A⣷  \x1b[90mRunning comman\x1b[m\n\n\n\x1b[13D\x1b[?25h",
    )
    session = terminal_session.TerminalSession()
    for frame in frames:
        session._append_scrollback(frame)

    class DummyWebSocket:
        def __init__(self):
            self.messages = []

        async def accept(self):
            return None

        async def send_text(self, text):
            self.messages.append(text)

    ws = DummyWebSocket()
    monkeypatch.setattr(session, "_ensure_pty", lambda: True)
    asyncio.run(session.connect_client(ws))  # type: ignore[arg-type]

    replay = ws.messages[0]
    assert replay == "".join(frames), repr(replay)
    assert "\r\n" not in replay, repr(replay)
    assert replay.count("\x1b[3A") == 2
