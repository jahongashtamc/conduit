"""Brauzer navigatsiyasi uchun yagona URL validatsiyasi.

Noto'g'ri matn (masalan `-hel`) to'g'ridan-to'g'ri Playwright'ga berilsa,
fraktr yuzida `page.goto: Cannot navigate to invalid URL` xatosi chiqadi.
Bu chegara uni tushunarli xatoga aylantiradi va xavfli sxemalarni o'tkazmaydi.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_HOST_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
_MAX_URL_LENGTH = 2048


def normalize_navigation_url(raw: str) -> str:
    """Foydalanuvchi kiritgan matnni xavfsiz http(s) URL ga aylantiradi.

    Args:
        raw: Very short address-bar input.

    Returns:
        To'liq, tekshirilgan http(s) URL.

    Raises:
        ValueError: Kiritish bo'sh, uzun yoki yaroqsiz bo'lsa.
    """
    if not isinstance(raw, str):
        raise ValueError("URL matn bo'lishi kerak")
    value = raw.strip()
    if not value:
        raise ValueError("URL bo'sh")
    if len(value) > _MAX_URL_LENGTH:
        raise ValueError("URL juda uzun")
    if any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError("URL da bo'sh joy yoki boshqaruv belgisi bor")

    # `javascript:...`, `data:...` kabi sxemalarni rad etamiz. `localhost:3000`
    # kabi host:port oxiridagi raqamlar esa sxema emas — ularga ruxsat.
    scheme_match = _SCHEME_RE.match(value)
    if scheme_match and not re.match(r"^https?://", value, re.I):
        tail = value[scheme_match.end():]
        if not re.match(r"^\d+(?:[/?#]|$)", tail):
            raise ValueError("Faqat http va https sxemalari qo'llab-quvvatlanadi")

    if "://" not in value:
        authority = value.split("/", 1)[0]
        host = authority.rsplit(":", 1)[0] if authority.count(":") == 1 else authority
        is_local = host.lower() in _LOCAL_HOSTS or bool(_IPV4_RE.match(host))
        value = ("http://" if is_local else "https://") + value

    parts = urlsplit(value)
    if parts.scheme.lower() not in ("http", "https"):
        raise ValueError("Faqat http va https sxemalari qo'llab-quvvatlanadi")
    if parts.username or parts.password:
        raise ValueError("URL da foydalanuvchi ma'lumoti taqiqlanadi")
    host = parts.hostname
    if not host:
        raise ValueError("Host ko'rsatilmagan")
    try:
        parts.port
    except ValueError as exc:
        raise ValueError("Noto'g'ri port") from exc

    host_ok = (
        host.lower() in _LOCAL_HOSTS
        or bool(_IPV4_RE.match(host))
        or all(_HOST_LABEL_RE.match(label) for label in host.split("."))
    )
    if not host_ok:
        raise ValueError("Noto'g'ri host nomi")

    # `-hel`, `not-a-url` kabi matn texnik jihatdan host label'iga o'xshaydi,
    # lekin haqiqiy manzil emas: Playwright'da "Cannot navigate to invalid
    # URL" beradi. Tashqi domenlar uchun kamida bitta nuqta va raqam
    # bo'lmagan 2+ belgili TLD talab qilinadi (localhost/IP bundan mustasno).
    if host.lower() not in _LOCAL_HOSTS and not _IPV4_RE.match(host):
        labels = host.split(".")
        if len(labels) < 2:
            raise ValueError(
                f"To'liq domen kerak (masalan example.com), olindi: {host!r}"
            )
        tld = labels[-1]
        if not re.fullmatch(r"[A-Za-z]{2,63}", tld):
            raise ValueError(f"Noto'g'ri domen oxiri: {tld!r}")

    return urlunsplit(
        (parts.scheme.lower(), parts.netloc, parts.path, parts.query, parts.fragment)
    )
