"""Haqiqiy PTY terminal testlari — pytest, tirik server talab qilmaydi.

Avval bu tekshiruvlar `test_pty_terminal.py` / `test_pty_env.py` /
`test_pty_claude.py` nomli QO'LDA yurgiziladigan skriptlar edi: ular
`ws://127.0.0.1:8000` ga ulanardi, ya'ni CI'da umuman ishlamasdi va
`git status`da "sinov bor" degan yolg'on taassurot qoldirardi.

Bu fayl o'sha qamrovni haqiqiy pytest testlariga aylantiradi. TerminalSession
to'g'ridan-to'g'ri (WebSocket o'rniga yozib oluvchi soxta mijoz bilan)
boshqariladi — uvicorn ham, agent CLI ham kerak emas. Shuning uchun test
`windows-latest` CI job'ida ham ishlaydi.

Agent CLI bilan ishlaydigan qism (agy/claude TUI) bu yerga KIRMAYDI: u
tashqi dasturga bog'liq va CI'da deterministik emas. Uni `verify_all_agents.py`
kabi qo'lda skriptlar qoplaydi.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pytestmark = [
    pytest.mark.skipif(sys.platform != "win32", reason="PTY (pywinpty) faqat Windows'da"),
]

winpty = pytest.importorskip("winpty", reason="pywinpty o'rnatilmagan")


class RecordingClient:
    """WebSocket o'rnini bosuvchi: yuborilgan matnlarni yig'adi."""

    def __init__(self) -> None:
        self.sent: list[str] = []

    async def accept(self) -> None:
        return None

    async def send_text(self, text: str) -> None:
        self.sent.append(text)


async def _wait_for(session, needles, timeout: float = 30.0) -> tuple[bool, str]:
    """Scrollback'da `needles` dan biri paydo bo'lguncha kutadi."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        text = "".join(session._scrollback_chunks)
        for needle in needles:
            if needle in text:
                return True, text
        await asyncio.sleep(0.15)
    return False, "".join(session._scrollback_chunks)


async def _run_shell(session, command: str, marker: str, timeout: float = 25.0) -> bool:
    """Buyruq yozib, chiqishida markerni kutadi."""
    session._clear_scrollback()
    await session.handle_input(command + "\r")
    ok, _ = await _wait_for(session, [marker], timeout)
    return ok


@pytest.fixture
def pty_session():
    """Yangi TerminalSession (singleton emas — testlar bir-birini buzmasin)."""
    import terminal_session

    session = terminal_session.TerminalSession()
    yield session
    # Har holatda PTY daraxtini o'ldiramiz — osilib qolgan powershell
    # keyingi testlarga ta'sir qilmasligi shart.
    try:
        asyncio.run(session.shutdown())
    except Exception:  # noqa: BLE001 - tozalash hech qachon testni yiqitmasin
        try:
            if session.pt is not None:
                session.pt.terminate(force=True)
        except Exception:  # noqa: BLE001
            pass


def test_connection_starts_powershell_and_shows_prompt(pty_session):
    """Ulanish PTY ochadi va PowerShell prompti ko'rinadi."""

    async def scenario():
        client = RecordingClient()
        await pty_session.connect_client(client)
        try:
            ok, out = await _wait_for(pty_session, ["PS ", ">"], 30)
            assert ok, f"PowerShell prompti ko'rinmadi. Chiqish: {out[-400:]!r}"
            assert pty_session.session_id, "CONDUIT_SESSION uchun sessiya ID berilmadi"
        finally:
            await pty_session.shutdown()

    asyncio.run(scenario())


def test_echo_round_trip_reaches_the_client(pty_session):
    """Kiritish PTY'ga yetib boradi va chiqishi mijozga uzatiladi."""

    async def scenario():
        client = RecordingClient()
        await pty_session.connect_client(client)
        try:
            ready, _ = await _wait_for(pty_session, ["PS ", ">"], 30)
            assert ready, "PTY promptga chiqmadi"

            marker = "PTY_ECHO_MARKER_7391"
            assert await _run_shell(pty_session, f"echo {marker}", marker), (
                "echo chiqishi mijozga yetib kelmadi"
            )
            # Chiqish WS orqali ham yuborilgan bo'lishi shart, faqat
            # scrollback'da qolib ketmasligi kerak.
            assert any(marker in chunk for chunk in client.sent), (
                "marker client.sent ichida yo'q — broadcast ishlamayapti"
            )
        finally:
            await pty_session.shutdown()

    asyncio.run(scenario())


def test_ctrl_c_interrupts_a_running_command(pty_session):
    """Ctrl+C uzun buyruqni to'xtatadi va prompt qaytadi (ConPTY talabi)."""

    async def scenario():
        client = RecordingClient()
        await pty_session.connect_client(client)
        try:
            ready, _ = await _wait_for(pty_session, ["PS ", ">"], 30)
            assert ready, "PTY promptga chiqmadi"

            # Uzoq kutish buyrug'i — Ctrl+C bo'lmasa 60s davom etadi.
            pty_session._clear_scrollback()
            await pty_session.handle_input("Start-Sleep -Seconds 60\r")
            await asyncio.sleep(2.0)

            await pty_session.handle_input("\x03")
            await asyncio.sleep(2.0)

            marker = "AFTER_CTRL_C_8842"
            ok = await _run_shell(pty_session, f"echo {marker}", marker, timeout=25)
            assert ok, (
                "Ctrl+C dan keyin prompt qaytmadi — buyruq to'xtamadi "
                "(PYWINPTY_BACKEND ConPTY emas bo'lishi mumkin)"
            )
        finally:
            await pty_session.shutdown()

    asyncio.run(scenario())


def test_resize_message_is_accepted(pty_session):
    """{"type":"resize"} PTY o'lchamini xatosiz o'zgartiradi."""

    async def scenario():
        client = RecordingClient()
        await pty_session.connect_client(client)
        try:
            ready, _ = await _wait_for(pty_session, ["PS ", ">"], 30)
            assert ready, "PTY promptga chiqmadi"

            await pty_session.handle_input('{"type":"resize","cols":120,"rows":40}')
            marker = "RESIZE_OK_5512"
            assert await _run_shell(pty_session, f"echo {marker}", marker), (
                "resize'dan keyin terminal ishlamay qoldi"
            )
        finally:
            await pty_session.shutdown()

    asyncio.run(scenario())


def test_scrollback_is_replayed_to_a_reconnecting_client(pty_session):
    """Uzilishdan keyin qayta ulanadigan mijoz eski chiqishni oladi.

    Bu sessiyaning tirik qolish shartnomasi: PTY WS uzilishida o'lmaydi.
    """

    async def scenario():
        first = RecordingClient()
        await pty_session.connect_client(first)
        try:
            ready, _ = await _wait_for(pty_session, ["PS ", ">"], 30)
            assert ready, "PTY promptga chiqmadi"

            marker = "SCROLLBACK_KEEP_2207"
            assert await _run_shell(pty_session, f"echo {marker}", marker)

            # Mijoz "uziladi" — PTY tirik qolishi shart.
            pty_session.disconnect_client(first)
            assert pty_session.pt is not None and pty_session.pt.isalive(), (
                "WS uzilishida PTY o'ldi — sessiya tirik qolishi kerak"
            )

            second = RecordingClient()
            await pty_session.connect_client(second)
            replayed = "".join(second.sent)
            assert marker in replayed, (
                "qayta ulangan mijoz eski chiqishni olmadi (scrollback replay yo'q)"
            )
        finally:
            await pty_session.shutdown()

    asyncio.run(scenario())


def test_close_message_kills_the_process_tree(pty_session):
    """{"type":"close"} PTY'ni o'ldiradi — zombie powershell qolmaydi."""

    async def scenario():
        client = RecordingClient()
        await pty_session.connect_client(client)
        ready, _ = await _wait_for(pty_session, ["PS ", ">"], 30)
        assert ready, "PTY promptga chiqmadi"

        pid = pty_session.pt.pid
        await pty_session.handle_input('{"type":"close"}')
        await asyncio.sleep(2.5)

        assert pty_session.pt is None, "close'dan keyin pt tozalanmadi"
        alive = _process_alive(pid)
        assert not alive, f"powershell (pid {pid}) hali tirik — jarayon daraxti o'ldirilmadi"

    def _process_alive(pid: int) -> bool:
        try:
            import psutil

            return psutil.pid_exists(pid) and not psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
        except Exception:
            return False

    asyncio.run(scenario())


def test_heartbeat_ping_returns_pong(pty_session):
    """`ping` heartbeat'i `{"type":"pong"}` qaytaradi (WS tirikligi)."""

    async def scenario():
        client = RecordingClient()
        await pty_session.connect_client(client)
        try:
            ready, _ = await _wait_for(pty_session, ["PS ", ">"], 30)
            assert ready, "PTY promptga chiqmadi"

            client.sent.clear()
            await pty_session.handle_input("ping")
            assert any("pong" in s for s in client.sent), "ping javobsiz qoldi"
        finally:
            await pty_session.shutdown()

    asyncio.run(scenario())


def test_conduit_cli_is_reachable_from_the_pty_path(pty_session):
    """PTY muhitida `conduit` buyrug'i PATH'da bo'lishi shart.

    `bin/` PATH'ga qo'shilmasa foydalanuvchi terminalda `conduit list`
    yoza olmaydi — bu studiyaning asosiy kirish nuqtasi.
    """

    async def scenario():
        client = RecordingClient()
        await pty_session.connect_client(client)
        try:
            ready, _ = await _wait_for(pty_session, ["PS ", ">"], 30)
            assert ready, "PTY promptga chiqmadi"

            pty_session._clear_scrollback()
            await pty_session.handle_input("$env:CONDUIT_SESSION\r")
            ok, out = await _wait_for(pty_session, [pty_session.session_id], 20)
            assert ok, (
                "CONDUIT_SESSION muhit o'zgaruvchisi PTY ichida ko'rinmadi. "
                f"Chiqish: {out[-300:]!r}"
            )
        finally:
            await pty_session.shutdown()

    asyncio.run(scenario())


def test_conduit_api_env_is_not_forced_to_default_port(monkeypatch):
    """Tashqi CONDUIT_API hurmat qilinadi (boshqa portdagi backend uchun).

    Regressiya: `_spawn_pty` `env["CONDUIT_API"]` ni HAR DOIM
    `http://127.0.0.1:8000` ga yozardi. Test-server yoki boshqa portda
    ishlaydigan studiyada PTY ichidagi `conduit` buyruqlari noto'g'ri
    manzilga murojaat qilardi.
    """
    import terminal_session

    monkeypatch.setenv("CONDUIT_API", "http://127.0.0.1:54321")
    session = terminal_session.TerminalSession()

    captured = {}

    class _FakePty:
        pid = 4242

        def isalive(self):
            return True

    class _FakePtyProcess:
        @staticmethod
        def spawn(*args, **kwargs):
            captured["env"] = kwargs.get("env") or {}
            return _FakePty()

    monkeypatch.setattr(winpty, "PtyProcess", _FakePtyProcess)
    monkeypatch.setattr(session, "_start_reader", lambda: None)
    monkeypatch.setattr(session, "_append_scrollback", lambda *_: None)

    session._spawn_pty()

    assert captured["env"]["CONDUIT_API"] == "http://127.0.0.1:54321", (
        "tashqi CONDUIT_API 8000 ga majburlanmasligi kerak"
    )
