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
