"""Watchdog must manage the copy it lives in, not a hardcoded foreign path."""

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_watchdog_paths_are_self_relative():
    spec = importlib.util.spec_from_file_location(
        "nexus_watchdog_under_test", ROOT / "watchdog.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert pathlib.Path(module.ROOT).resolve() == ROOT
    assert pathlib.Path(module.BACKEND_DIR).resolve() == ROOT / "backend"
    assert pathlib.Path(module.FRONTEND_DIR).resolve() == ROOT / "frontend"
    assert module.PY == sys.executable
