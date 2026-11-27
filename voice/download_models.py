#!/usr/bin/env python
"""ONNX ovoz modellarini yuklab oladi va sha256 bilan tekshiradi.

Nega kerak: `voice/models/` dagi ONNX fayllari (114 MB × 2) git'da
saqlanmaydi. Toza checkout'da `voice_speak` ishlamaydi va foydalanuvchi
"model fayli yo'q" xatosidan boshqa hech narsa ko'rmaydi — qayerdan
olishni bilmaydi. Bu skript manbani (`voice/models.json` dagi `source`),
fayl ro'yxatini va kutilgan sha256 ni o'zi o'qiydi.

Ishlatish (repo ildizidan):

    python voice/download_models.py              # ikkala model
    python voice/download_models.py --model male # faqat erkak ovozi
    python voice/download_models.py --force      # mavjudlarini qayta yuklash
    python voice/download_models.py --check      # faqat tekshirish, yuklamasdan

Ishonchlilik: har fayl avval `*.part` ga yoziladi, sha256 mos kelsagina
o'z nomiga ko'chiriladi — yarim yuklangan fayl model sifatida qolmaydi.
Tarmoq xatosi aniq xabar bilan qaytadi (jim yutilmaydi).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

VOICE_DIR = Path(__file__).resolve().parent
REGISTRY = VOICE_DIR / "models.json"
CHUNK = 1024 * 1024
USER_AGENT = "Conduit-Studio-VoiceModelFetcher/1.0"


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text_normalized(path: Path) -> str:
    """Matn fayli uchun CRLF'ga chidamli sha256.

    `voice/models.json` dagi hash'lar LF shakli uchun hisoblangan. Windows'da
    `core.autocrlf=true` checkout fayllarni CRLF qiladi va xom hash mos
    kelmaydi (o'lchangan: config.json 24a2feeb… vs kutilgan 468fadd0…).
    `voice_doctor` ham shu normalizatsiyani ishlatadi — izchil bo'lishi shart.
    """
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# ONNX — binary, JSON/txt — matn. Matn fayllari uchun ikkala hash ham qabul
# qilinadi (ba'zi checkout'larda LF qoladi).
TEXT_SUFFIXES = (".json", ".txt", ".md")


def file_state(path: Path, expected: str) -> tuple[bool, str]:
    """(to'g'rimi, izoh) — mavjud faylni kutilgan hash bilan solishtiradi."""
    if not path.is_file():
        return False, "yo'q"
    size = path.stat().st_size
    if size == 0:
        return False, "bo'sh fayl"

    actual = sha256_of(path)
    if actual == expected:
        return True, f"sha256 mos ({size:,} bayt)"

    if path.suffix.lower() in TEXT_SUFFIXES:
        normalized = sha256_text_normalized(path)
        if normalized == expected:
            return True, f"sha256 mos, CRLF normallashtirildi ({size:,} bayt)"

    return False, f"sha256 MOS EMAS (kutilgan {expected[:12]}…, olindi {actual[:12]}…)"


def verify_downloaded(path: Path, expected: str) -> tuple[bool, str]:
    """Yuklangan faylni tekshiradi.

    Tarmoqdan kelgan fayl CRLF bo'lishi shart emas — agar u matn bo'lsa va
    xom hash mos kelmasa, normalizatsiya ham tekshiriladi (manba CRLF
    saqlashi mumkin).
    """
    actual = sha256_of(path)
    if actual == expected:
        return True, "sha256 mos"
    if path.suffix.lower() in TEXT_SUFFIXES:
        if sha256_text_normalized(path) == expected:
            return True, "sha256 mos (CRLF normallashtirildi)"
    return False, f"sha256 MOS EMAS (kutilgan {expected[:12]}…, olindi {actual[:12]}…)"


def download_once(url: str, dest: Path, expected_sha: str, label: str) -> None:
    """Faylni `dest` ga yuklaydi, sha256 mos kelsagina qoldiradi (atomar)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".part")

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    written = 0

    print(f"  yuklanmoqda: {label}")
    try:
        with urllib.request.urlopen(request, timeout=60) as response, open(partial, "wb") as sink:
            total = int(response.headers.get("Content-Length") or 0)
            while True:
                block = response.read(CHUNK)
                if not block:
                    break
                sink.write(block)
                digest.update(block)
                written += len(block)
                if total:
                    pct = written * 100 // total
                    print(f"\r    {pct:3d}%  {written / 1e6:7.1f} / {total / 1e6:.1f} MB",
                          end="", flush=True)
                else:
                    print(f"\r    {written / 1e6:7.1f} MB", end="", flush=True)
        print()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        partial.unlink(missing_ok=True)
        raise SystemExit(
            f"XATO: {label} yuklanmadi: {type(exc).__name__}: {exc}\n"
            f"  Manba: {url}\n"
            "  Tarmoq/proksi tekshirilganini qayta urinib ko'ring."
        ) from exc

    actual = digest.hexdigest()
    verified = actual == expected_sha or (
        dest.suffix.lower() in TEXT_SUFFIXES
        and sha256_text_normalized(partial) == expected_sha
    )
    if not verified:
        partial.unlink(missing_ok=True)
        raise SystemExit(
            f"XATO: {label} buzilgan yoki boshqa fayl.\n"
            f"  kutilgan sha256: {expected_sha}\n"
            f"  olingan sha256:  {actual}\n"
            "  Fayl o'chirildi — model manbasi o'zgargan bo'lishi mumkin."
        )

    os.replace(partial, dest)


def huggingface_url(source: str, relative: str) -> str:
    """`https://huggingface.co/<repo>` + fayl yo'li -> `/resolve/main/<fayl>`."""
    base = source.rstrip("/")
    if not base.startswith("https://huggingface.co/"):
        raise SystemExit(
            f"XATO: qo'llab-quvvatlanmagan manba: {source}\n"
            "  Hozircha faqat huggingface.co domeni ishlatiladi."
        )
    return f"{base}/resolve/main/{relative.lstrip('/')}"


def process_model(model: dict, *, force: bool, check_only: bool) -> tuple[int, int, int]:
    """(yuklandi, o'tkazib yuborildi, xato) qaytaradi."""
    model_id = model.get("id", "?")
    model_dir = VOICE_DIR / model.get("dir", "")
    files: dict = model.get("files") or {}
    source = model.get("source") or ""

    print(f"\n{model_id}  ({model.get('label', '')})")
    print(f"  manba: {source}")
    print(f"  litsenziya: {model.get('license', 'nomalum')}")

    if not files:
        print("  XATO: registrda `files` yo'q")
        return 0, 0, 1
    if not source:
        print("  XATO: registrda `source` yo'q")
        return 0, 0, 1

    downloaded = skipped = failed = 0
    for relative, expected in files.items():
        target = model_dir / relative
        ok, note = file_state(target, expected)

        if ok and not force:
            print(f"  OK      {relative} — {note}")
            skipped += 1
            continue

        if check_only:
            print(f"  YO'Q    {relative} — {note}")
            failed += 1
            continue

        if ok and force:
            print(f"  qayta   {relative} — {note}")
        try:
            download_once(huggingface_url(source, relative), target, expected, relative)
        except SystemExit as exc:
            print(f"  XATO    {relative}: {exc}")
            failed += 1
            continue

        ok2, note2 = verify_downloaded(target, expected)
        if ok2:
            print(f"  YUKLANDI {relative} — {note2}")
            downloaded += 1
        else:
            print(f"  XATO    {relative} — {note2}")
            failed += 1

    return downloaded, skipped, failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", choices=["male", "female", "all"], default="all",
                        help="qaysi model (default: all)")
    parser.add_argument("--force", action="store_true", help="mavjud fayllarni qayta yuklash")
    parser.add_argument("--check", action="store_true", help="faqat holatni tekshirish")
    args = parser.parse_args()

    registry = load_registry()
    models = registry.get("models") or []
    if args.model != "all":
        wanted = f"_{args.model}_"
        models = [m for m in models if wanted in f"_{m.get('id', '')}_"]
    if not models:
        print("XATO: registrda mos model topilmadi", file=sys.stderr)
        return 1

    total_dl = total_skip = total_fail = 0
    for model in models:
        dl, sk, fl = process_model(model, force=args.force, check_only=args.check)
        total_dl += dl
        total_skip += sk
        total_fail += fl

    print("\n" + "=" * 60)
    if args.check:
        print(f"TEKSHIRUV: {total_skip} fayl joyida, {total_fail} fayl yo'q/buzuq")
    else:
        print(f"YAKUN: {total_dl} yuklandi, {total_skip} joyida, {total_fail} xato")
    if total_fail:
        print("Model to'liq emas — voice_speak ONNX backend ishlamaydi "
              "(faqat SAPI zaxirasi qoladi).")
        return 1
    print("Barcha model fayllari joyida va sha256 mos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
