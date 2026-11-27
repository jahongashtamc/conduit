"""Voice testlari uchun muhit sozlamalari.

`voice` paketi repo ILDIZIDA yashaydi (`conduit/voice/`). Testlar esa
`conduit/voice/tests/` dan ishga tushadi, ya'ni pytest rootdir'i `voice/`
bo'ladi va repo ildizi `sys.path`da bo'lmaydi:

    ModuleNotFoundError: No module named 'voice'

Bu `voice/tests/test_audio.py`, `test_engine.py`, `test_text.py` — uchta
faylni yiqitardi (2026-11-27 da o'lchangan: 48 test yig'ildi, 1 collection
ERROR). Ildizni shu yerda bir marta qo'shamiz.
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
