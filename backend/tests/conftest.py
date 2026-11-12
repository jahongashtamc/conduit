"""Test muhiti sozlamalari.

Conduit kodi asyncio-ga asoslangan: `engine/deepsearch.py` `asyncio.gather`
ishlatadi, `engine/cli_runner.py` `asyncio.create_subprocess_exec` chaqiradi.
anyio standart bo'yicha backend plaginini tanlaydi va trio ham o'rnatilgan
bo'lsa trio'da ham ishlatadi - trio'da asyncio.gather mavjud emas, shu sabab
testlar "coroutine was never awaited" bilan yiqilardi.

Production kodi o'zgartirilmaydi; test muhiti asyncio bilan qotiriladi.
"""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
