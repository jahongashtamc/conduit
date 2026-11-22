"""Jim yutiladigan xatolar qaytib kelmasligi uchun doimiy eshik.

Ishlab chiqarish kodi (tests/ va __pycache__ bundan mustasno) tekshiriladi.
"""

import ast
import logging
import os

import main  # noqa: E402  (import qilganda logging sozlanadi)

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


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
                    offenders.append(f"{rel}:{node.lineno}")
    assert not offenders, "Jim yutilgan xatolar: " + ", ".join(offenders)


def test_studio_loggers_are_visible_at_debug_level():
    for name in ("nexus", "conduit"):
        logger = logging.getLogger(name)
        assert logger.level == logging.DEBUG
        assert logger.handlers, f"{name} loggerida handler yo'q — xatolar yana jim qoladi"
        assert logger.propagate is False
