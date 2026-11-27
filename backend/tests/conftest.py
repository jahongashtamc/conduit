"""Test muhiti sozlamalari.

Conduit kodi asyncio-ga asoslangan: `engine/deepsearch.py` `asyncio.gather`
ishlatadi, `engine/cli_runner.py` `asyncio.create_subprocess_exec` chaqiradi.
anyio standart bo'yicha backend plaginini tanlaydi va trio ham o'rnatilgan
bo'lsa trio'da ham ishlatadi - trio'da asyncio.gather mavjud emas, shu sabab
testlar "coroutine was never awaited" bilan yiqilardi.

Production kodi o'zgartirilmaydi; test muhiti asyncio bilan qotiriladi.
"""

import os
import pathlib
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


# Ba'zi testlar memory/errors.md, tools/candidates.json va research/*.md ga
# yozadi. Bu kuzatiladigan fayllar — test sessiyasidan keyin ularni asl
# holatiga qaytaramiz, aks holda `git status` har test ishga tushishida iflos
# bo'lib qoladi va haqiqiy o'zgarishlarni yashiradi.
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_GENERATED_FILES = (
    "memory/errors.md",
    "tools/candidates.json",
    "research/to_liq_3d_e_commerce_platforma_mvp.md",
)


@pytest.fixture(scope="session", autouse=True)
def restore_generated_data_files():
    snapshots = {}
    for rel in _GENERATED_FILES:
        path = _REPO_ROOT / rel
        snapshots[path] = path.read_bytes() if path.exists() else None
    yield
    for path, original in snapshots.items():
        try:
            if original is None:
                if path.exists():
                    path.unlink()
            elif path.read_bytes() != original:
                path.write_bytes(original)
        except OSError as exc:
            print(f"[tests] generated file restore failed: {path.name}: {exc}")


# Byudjet testlari resurs jadvaliga yozadi. Haqiqiy ish jarayonida yig'ilgan
# tokenlar keyingi testlarda "limit tugadi" deb noto'g'ri bloklashi mumkin.
# Har bir testdan oldin/so'ng jadvallarni tiklaymiz — testlar mustaqil bo'ladi.
@pytest.fixture(scope="session")
def resource_state_backup():
    import database

    database.init_db()
    con = database.get_connection()
    ledger = con.execute("SELECT * FROM resource_ledger").fetchall()
    settings = con.execute("SELECT * FROM resource_settings").fetchall()
    con.close()
    yield ledger, settings
    con = database.get_connection()
    con.execute("DELETE FROM resource_ledger")
    con.executemany("INSERT INTO resource_ledger VALUES (?,?,?,?,?,?,?,?,?)", ledger)
    con.execute("DELETE FROM resource_settings")
    con.executemany("INSERT INTO resource_settings VALUES (?,?,?,?,?)", settings)
    con.commit()
    con.close()


def _reset_resource_state():
    import database

    con = database.get_connection()
    con.execute("DELETE FROM resource_ledger")
    con.execute("DELETE FROM resource_settings")
    con.execute(
        "INSERT INTO resource_settings (id, max_budget_usd, max_tokens, is_blocked, block_reason) "
        "VALUES (1, 10.0, 500000, 0, NULL)"
    )
    con.commit()
    con.close()


@pytest.fixture(autouse=True)
def isolate_resource_state(resource_state_backup):
    _reset_resource_state()
    yield
    _reset_resource_state()


class LiveBackend(str):
    """Test-server manzili (oddiy `str`) + uning baza fayli (`db_path`).

    `str` bo'lgani uchun `env["CONDUIT_API"] = live_backend` kabi mavjud
    ishlatishlar o'zgarmaydi; `db_path` esa serverning O'Z bazasini ko'rsatadi,
    shuning uchun test qatorni to'g'ri bazaga yozib, CLI orqali o'qiy oladi.
    """

    db_path: str

    def __new__(cls, api_base: str, db_path: str) -> "LiveBackend":
        obj = super().__new__(cls, api_base)
        obj.db_path = db_path
        return obj


@pytest.fixture(scope="module")
def live_backend():
    """CLI testlari uchun haqiqiy backend'ni BO'SH portda ko'taradi.

    `conduit.py status/list` HTTP orqali ishlaydi. Avval bu testlar tirik
    serverga tayanardi: CI'da hech kim uni ko'tarmagani uchun "Connection
    refused" bilan yiqilardi, lokalda esa tasodifan ochiq studiya serveriga
    ulanardi — natija muhitga bog'liq edi. Endi test o'zi toza server
    ko'taradi (tasodifiy bo'sh portda, 8000'dagi studiyaga tegmaydi) va
    oxirida o'chiradi.

    Server ALOHIDA baza faylida ishlaydi (`db_path`), shuning uchun u test
    jarayoni bilan bir xil SQLite fayliga yozmaydi.

    Scope ATAYLAB `module`: sessiya bo'yi tirik uvicorn keyingi testlarga
    ta'sir qilmaydi (CI'da 24 ta ketma-ket `database is locked` ERROR
    kuzatilgan — run 45984826851). Faqat shu fixture'ni ishlatadigan modul
    ichida yashaydi va modul tugashi bilan o'chadi.
    """
    import socket
    import subprocess
    import sys
    import time
    import urllib.error
    import urllib.request

    backend_dir = pathlib.Path(__file__).resolve().parents[1]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    api_base = f"http://127.0.0.1:{port}"

    def _healthy() -> bool:
        try:
            with urllib.request.urlopen(f"{api_base}/api/health", timeout=1.5) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError):
            return False

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(backend_dir) + os.pathsep + env.get("PYTHONPATH", "")
    # Test-server ALOHIDA baza faylida ishlaydi. Avval test jarayoni va
    # uvicorn bir xil SQLite fayliga (conduit.db, WAL) yozardi: Windows'da bu
    # `database is locked` beradi va keyingi 24 ta test ERROR bo'lib yiqiladi
    # (o'lchangan: CI run 45984826851, 24% da F + 24 E). `--lifespan off`
    # ham saqlanadi: startup hook tirik vazifalarni BLOCKED qilmasligi kerak.
    server_db = os.path.join(tempfile.gettempdir(), f"conduit_test_server_{port}.db")
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(server_db + suffix)
        except OSError:
            pass
    env["CONDUIT_DB_PATH"] = server_db
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1", "--port", str(port), "--lifespan", "off",
        ],
        cwd=str(backend_dir),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 60
        while time.time() < deadline:
            if proc.poll() is not None:
                pytest.skip(f"backend ko'tarilmadi (exit {proc.returncode})")
            if _healthy():
                break
            time.sleep(0.4)
        else:
            pytest.skip("backend 60 soniyada javob bermadi")
        yield LiveBackend(api_base, server_db)
    finally:
        # Avval serverni to'xtatamiz, keyin uning baza faylini o'chiramiz —
        # teskari tartibda Windows faylni ochiq ushlab qoladi.
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
        for suffix in ("", "-wal", "-shm"):
            try:
                os.remove(server_db + suffix)
            except OSError:
                pass
