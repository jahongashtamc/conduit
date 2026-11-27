#!/usr/bin/env python
"""Testlarni modul bo'yicha alohida jarayonlarda yurgizadi.

Nega kerak (o'lchangan, 2026-11-27): Windows CI runner'da to'liq to'plam
o'rtasida BITTA test osilib qolsa, pytest davom eta olmaydi va job 30 daqiqalik
limitgacha jim turadi (run 45984826851, 45999365515, 46009755859). Bir
jarayonda yurgizish bitta nosoz testni butun job'ga tarqatadi.

Bu skript har modulni o'z jarayonida yurgizadi: osilgan modul o'z jarayoni
bilan o'chadi, qolgan modullar davom etadi va yakunda aniq hisobot beriladi.

Ishlatish (backend/ ichida):
    python scripts/run_tests_by_module.py [--timeout 180] [-q]

Chiqish kodi: barcha modullar yashil bo'lsa 0, aks holda 1.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def discover_modules() -> list[str]:
    """pytest yig'adigan test modullarini topadi (tests/manual hisobga olinmaydi)."""
    tests_dir = BACKEND / "tests"
    modules = sorted(
        p.name
        for p in tests_dir.glob("test_*.py")
        if p.is_file()
    )
    return [f"tests/{name}" for name in modules]


def run_module(module: str, timeout: float, verbose: bool) -> tuple[str, str, float, str]:
    """Bitta modulni alohida jarayonda yurgizadi -> (module, holat, vaqt, xulosa)."""
    cmd = [sys.executable, "-m", "pytest", "-q", "--timeout", str(int(timeout)), module]
    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(BACKEND),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout + 30,  # pytest timeout + jarayon zaxirasi
        )
        elapsed = time.time() - started
        tail = (proc.stdout or "").strip().splitlines()
        summary = tail[-1] if tail else (proc.stderr or "").strip().splitlines()[-1:] or ""
        if isinstance(summary, list):
            summary = summary[0] if summary else ""
        if proc.returncode == 0:
            return module, "OK", elapsed, summary
        return module, "FAIL", elapsed, summary
    except subprocess.TimeoutExpired:
        elapsed = time.time() - started
        return module, "OSILDI", elapsed, f"{timeout:.0f}s ichida tugamadi"
    except Exception as exc:  # noqa: BLE001 - hisobot uchun
        return module, "XATO", time.time() - started, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=240.0, help="har modul uchun sekund")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    modules = discover_modules()
    if not modules:
        print("Test modullari topilmadi", file=sys.stderr)
        return 1

    print(f"Modul bo'yicha yurgizish: {len(modules)} modul, "
          f"har biriga {args.timeout:.0f}s chegara\n")

    results = []
    started_all = time.time()
    for index, module in enumerate(modules, 1):
        name = module.split("/")[-1]
        print(f"[{index}/{len(modules)}] {name} ... ", end="", flush=True)
        result = run_module(module, args.timeout, args.verbose)
        results.append(result)
        _, status, elapsed, summary = result
        marker = {"OK": "OK", "FAIL": "FAIL", "OSILDI": "OSILDI", "XATO": "XATO"}[status]
        print(f"{marker} ({elapsed:.1f}s) {summary if status != 'OK' else ''}")

    total = time.time() - started_all
    bad = [r for r in results if r[1] != "OK"]

    print("\n" + "=" * 60)
    print(f"JAMI: {len(results)} modul, {total:.1f}s")
    if bad:
        print(f"MUAMMOLI: {len(bad)}")
        for module, status, elapsed, summary in bad:
            print(f"  {status:<7} {module} ({elapsed:.1f}s)")
            if summary:
                print(f"          {summary[:200]}")
        return 1
    print("Barcha modullar yashil")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
