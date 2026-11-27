"""`purge_test_tasks` SQL joker belgisi regressiyasi.

Topilgan nuqson (2026-11-27, jonli-sahna skaneri): SQLite'da `LIKE` uchun `_`
bitta ixtiyoriy belgini bildiradi. `LIKE 'test_%'` shuning uchun `test-abc`,
`test1`, `testXYZ`, `testemonial_report` kabi HAQIQIY vazifalarni ham
o'chirardi — foydalanuvchi ishi jimgina yo'qolardi (startup'da, kuzatuvsiz).

Bu test ikkala tomonni ham ushlab turadi:
  * `test_` prefiksli qatorlar O'CHIRILADI (test artefaktlari UI'ga chiqmasin),
  * boshqa har qanday qator SAQLANADI.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database  # noqa: E402

# `test_` prefiksli — o'chirilishi SHART.
PURGEABLE = ["test_purge_probe_a", "test_abc"]
# `_` joker bo'lgani uchun avval o'chib ketardi — saqlanishi SHART.
PROTECTED = ["test-abc", "test1", "testXYZ", "testemonial_report"]


def _delete(task_ids: list[str]) -> None:
    if not task_ids:
        return
    marks = ",".join("?" * len(task_ids))
    conn = database.get_connection()
    try:
        conn.execute(f"DELETE FROM logs WHERE task_id IN ({marks})", task_ids)
        conn.execute(f"DELETE FROM tasks WHERE task_id IN ({marks})", task_ids)
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def seeded():
    _delete(PURGEABLE + PROTECTED)
    for tid in PURGEABLE + PROTECTED:
        database.create_task(tid, "purge probe", "p", "scout")
    yield
    _delete(PURGEABLE + PROTECTED)


def test_purge_only_removes_the_literal_test_prefix(seeded):
    database.purge_test_tasks()

    remaining = {t["task_id"] for t in database.get_tasks(limit=200)}

    lost = [tid for tid in PROTECTED if tid not in remaining]
    assert not lost, (
        f"haqiqiy vazifalar o'chirildi: {lost}. `LIKE 'test_%'` dagi `_` joker "
        "belgi — ESCAPE bilan qochirilishi shart."
    )

    kept = [tid for tid in PURGEABLE if tid in remaining]
    assert not kept, f"test vazifalari tozalanmadi: {kept}"


def test_purge_is_idempotent(seeded):
    """Ikkinchi chaqiruv hech narsani buzmaydi."""
    database.purge_test_tasks()
    database.purge_test_tasks()

    remaining = {t["task_id"] for t in database.get_tasks(limit=200)}
    assert all(tid in remaining for tid in PROTECTED)
