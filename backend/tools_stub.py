"""Conduit workspace tools.py — YAGONA MASTER'ga yo'naltiruvchi stub.

Master nusxa: <repo>/backend/tools.py. Bu stub uni faqat __main__ sifatida
ishga tushiradi. Kod takrorlanmasligi uchun (ilgari 19 nusxa duplikat bo'lgan)
barcha workspace'lar shu stubdan foydalanadi — tahrirlash faqat master'da.
"""
import os
import runpy

_master = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "tools.py"))
if not os.path.isfile(_master):
    raise SystemExit(f"Conduit master tools.py topilmadi: {_master}")

runpy.run_path(_master, run_name="__main__")
