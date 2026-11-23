"""Loyiha ichidagi haqiqiy GitHub klonlarini boshqarish.

Global git/auth/MCP sozlamalariga tegmaydi: faqat ``<repo>/clones`` ichida
ishlaydi. Barcha xatolar loglanadi va foydalanuvchiga qaytariladi.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

from security_guard import sanitize_text

LOGGER = logging.getLogger("nexus.clone_manager")

ROOT = Path(__file__).resolve().parents[1]
CLONES_ROOT = ROOT / "clones"
REGISTRY_FILE = CLONES_ROOT / "registry.json"
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,80}$")
_CLONE_TIMEOUT_SECONDS = 600


class CloneError(ValueError):
    """Klonlash yoki klon ma'lumotlari bilan bog'liq xato."""


def _ensure_root() -> Path:
    CLONES_ROOT.mkdir(parents=True, exist_ok=True)
    return CLONES_ROOT


def validate_clone_url(raw: str) -> str:
    """Faqat https git manzilini qabul qiladi; foydalanuvchi ma'lumoti taqiq."""
    url = (raw or "").strip()
    if not url or len(url) > 2048:
        raise CloneError("Manzil bo'sh yoki juda uzun")
    if any(ch.isspace() or ord(ch) < 32 for ch in url):
        raise CloneError("Manzilda bo'sh joy yoki boshqaruv belgisi bor")
    parts = urlsplit(url)
    if parts.scheme.lower() != "https":
        raise CloneError("Faqat https manzil qo'llab-quvvatlanadi")
    if not parts.hostname:
        raise CloneError("Host nomi topilmadi")
    if parts.username or parts.password:
        raise CloneError("Manzilda foydalanuvchi/parol bo'lmasligi kerak")
    if not re.fullmatch(r"[A-Za-z0-9.-]+", parts.hostname):
        raise CloneError("Noto'g'ri host nomi")
    return url.rstrip("/")


def derive_name(url: str, explicit: Optional[str] = None) -> str:
    """Klon papkasi nomini URL dan yoki aniq qiymatdan oladi."""
    candidate = (explicit or "").strip()
    if not candidate:
        path = urlsplit(url).path.rstrip("/")
        candidate = path.rsplit("/", 1)[-1]
        if candidate.endswith(".git"):
            candidate = candidate[:-4]
    if not _NAME_RE.fullmatch(candidate) or candidate in {".", ".."}:
        raise CloneError("Noto'g'ri klon nomi")
    return candidate


def _target_path(name: str) -> Path:
    if not _NAME_RE.fullmatch(name) or name in {".", ".."}:
        raise CloneError("Noto'g'ri klon nomi")
    root = _ensure_root().resolve()
    target = (root / name).resolve()
    if target.parent != root or not str(target).startswith(str(root) + os.sep):
        raise CloneError("Klon manzili loyiha papkasidan tashqarida")
    return target


def _load_registry() -> Dict[str, Dict[str, Any]]:
    _ensure_root()
    if not REGISTRY_FILE.exists():
        return {}
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.error("Klon registri o'qilmadi: %s: %s", type(exc).__name__, sanitize_text(str(exc)))
        raise CloneError("Klon registri buzilgan") from exc
    if not isinstance(data, dict):
        raise CloneError("Klon registri noto'g'ri formatda")
    return data


def _save_registry(registry: Dict[str, Dict[str, Any]]) -> None:
    _ensure_root()
    tmp = REGISTRY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(REGISTRY_FILE)


def _git(args: List[str], cwd: Optional[Path] = None) -> str:
    binary = shutil.which("git")
    if not binary:
        raise CloneError("git topilmadi")
    try:
        result = subprocess.run(  # noqa: S603 - shell=False, arguments are a list
            [binary, *args],
            cwd=str(cwd) if cwd else None,
            check=True,
            capture_output=True,
            text=True,
            timeout=_CLONE_TIMEOUT_SECONDS,
        )
    except subprocess.CalledProcessError as exc:
        detail = sanitize_text((exc.stderr or exc.stdout or "").strip()[:500])
        LOGGER.error("git buyrugi bajarilmadi: %s: %s", args[0], detail)
        raise CloneError(f"git xatosi: {detail or 'noma\'lum xato'}") from exc
    except subprocess.TimeoutExpired as exc:
        LOGGER.error("git vaqti tugadi: %s", args[0])
        raise CloneError("git vaqti tugadi") from exc
    return result.stdout.strip()


def _head(target: Path) -> str:
    return _git(["rev-parse", "HEAD"], cwd=target)


def clone_repository(url: str, name: Optional[str] = None, commit_pin: Optional[str] = None) -> Dict[str, Any]:
    """Haqiqiy klonlash: shallow clone, ixtiyoriy commit pin, HEAD saqlash."""
    target_url = validate_clone_url(url)
    clone_name = derive_name(target_url, name)
    target = _target_path(clone_name)
    if commit_pin is not None and not re.fullmatch(r"[0-9a-fA-F]{7,40}", commit_pin.strip()):
        raise CloneError("Noto'g'ri commit pin")

    registry = _load_registry()
    if clone_name in registry:
        raise CloneError("Bu nom allaqachon klonlangan")

    if target.exists():
        raise CloneError("Maqsad papkasi allaqachon mavjud")

    _git(["clone", "--depth", "1", target_url, str(target)])
    if commit_pin:
        _git(["checkout", commit_pin.strip()], cwd=target)
    head = _head(target)

    entry: Dict[str, Any] = {
        "id": clone_name,
        "url": target_url,
        "path": str(target.relative_to(CLONES_ROOT)).replace("\\", "/"),
        "commit_pin": commit_pin.strip() if commit_pin else head,
        "head": head,
        "status": "ready",
        "last_error": None,
    }
    registry[clone_name] = entry
    _save_registry(registry)
    LOGGER.info("Klon yaratildi: %s (%s)", clone_name, head[:12])
    return entry


def list_clones() -> List[Dict[str, Any]]:
    return list(_load_registry().values())


def get_clone(name: str) -> Dict[str, Any]:
    registry = _load_registry()
    if name not in registry:
        raise CloneError("Klon topilmadi")
    return registry[name]


def delete_clone(name: str) -> Dict[str, str]:
    registry = _load_registry()
    if name not in registry:
        raise CloneError("Klon topilmadi")
    target = _target_path(name)
    if target.exists():
        # Git obyektlari Windows'da read-only bo'ladi — ularni o'chirishdan
        # oldin yozish huquqini qaytaramiz (faqat clones/ ichida).
        def _rm_readonly(func, path, exc_info):
            os.chmod(path, 0o200)
            func(path)

        shutil.rmtree(target, onerror=_rm_readonly)
    registry.pop(name, None)
    _save_registry(registry)
    LOGGER.info("Klon o'chirildi: %s", name)
    return {"ok": "true", "id": name}


def refresh_clone(name: str) -> Dict[str, Any]:
    entry = get_clone(name)
    target = _target_path(name)
    if not (target / ".git").exists():
        raise CloneError("Klon papkasi git repositoriyasi emas")
    _git(["fetch", "--depth", "1", "origin"], cwd=target)
    _git(["reset", "--hard", "FETCH_HEAD"], cwd=target)
    entry["head"] = _head(target)
    entry["status"] = "ready"
    entry["last_error"] = None
    registry = _load_registry()
    registry[name] = entry
    _save_registry(registry)
    return entry
