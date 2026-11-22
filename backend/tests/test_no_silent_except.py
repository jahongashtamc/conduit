"""Jim yutiladigan xatolar qaytib kelmasligi uchun doimiy eshik.

Faqat ishlab chiqarish kodi (backend/*.py, backend/engine/*.py) tekshiriladi.
Qabul qilingan istisnolar:
  * main.py:1446 — oddiy 1.5 s polling pauzasi (xato emas, izoblangan).
"""

import ast
import os

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ALLOWED = {("main.py", 1446)}


def test_no_silent_except_in_production_code():
    offenders = []
    for dirpath, dirnames, filenames in os.walk(BACKEND):
        dirnames[:] = [d for d in dirnames if d not in {"tests", "__pycache__"}]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = os.path.join(dirpath, filename)
            source = open(path, encoding="utf-8", errors="replace").read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ExceptHandler)
                    and len(node.body) == 1
                    and isinstance(node.body[0], ast.Pass)
                ):
                    rel = os.path.relpath(path, BACKEND).replace("\\", "/")
                    if (rel, node.lineno) not in ALLOWED:
                        offenders.append(f"{rel}:{node.lineno}")
    assert not offenders, "Jim yutilgan xatolar: " + ", ".join(offenders)
