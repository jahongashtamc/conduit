"""Test muhiti sozlamalari.

Conduit kodi asyncio-ga asoslangan: `engine/deepsearch.py` `asyncio.gather`
ishlatadi, `engine/cli_runner.py` `asyncio.create_subprocess_exec` chaqiradi.
anyio standart bo'yicha backend plaginini tanlaydi va trio ham o'rnatilgan
bo'lsa trio'da ham ishlatadi - trio'da asyncio.gather mavjud emas, shu sabab
testlar "coroutine was never awaited" bilan yiqilardi.

Production kodi o'zgartirilmaydi; test muhiti asyncio bilan qotiriladi.
"""

import pathlib

import pytest


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
