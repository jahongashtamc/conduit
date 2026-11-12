# Conduit Uchinchi Tomon Asboblari (THIRD-PARTY NOTICES)

Ushbu hujjat Conduit studiyasi ichiga olingan tashqi ochiq kodli asboblar, MCP serverlar,
kutubxonalar va ularning mualliflik litsenziyalari to'g'risidagi rasmiy reyestrdir.

> **Holat izohi (2026-11-12 tekshiruvi).** Quyidagi `tools/vendor/` yozuvlari Conduit
> repozitoriyasida **mavjud emas** — `tools/vendor/` papkasi repoda umuman yo'q.
> Har bir yozuvning haqiqiy holati "Holat" ustunida ko'rsatilgan. Bu reyestr niyatni
> (qaysi asbob qayerdan olinishi kerakligini) qayd etadi, mavjudlikni da'vo qilmaydi.

## Repozitoriya ichida haqiqatan mavjud

| Asbob | Manba | Litsenziya | Fayllar | Holat |
|---|---|---|---|---|
| **Conduit Studio** (asosiy kod) | ushbu repo | belgilanmagan | `backend/`, `frontend/`, `subagents/` | Mavjud |

Conduit ichida ishlatiladigan tashqi **Python/Node paketlar** alohida fayllarda qayd etiladi:
`backend/requirements.txt` (FastAPI, uvicorn, pydantic, psutil, pillow, httpx) va
`frontend/package.json` (Next.js, React, Tailwind, GSAP, xterm, zustand). Ularning litsenziyalari
o'z paketlarida (npm/PyPI) saqlanadi; kod repozitoriyga ko'chirilmagan.

## `tools/` katalogi (repozitoriyada mavjud)

`tools/` ichida vendor kod emas, faqat **Conduit'ning o'z adapterlari** bor:

| Fayl | Vazifasi |
|---|---|
| `tools/adapters/blender_script_runner_adapter.py` | Blender skript yurgizish adapteri |
| `tools/adapters/gpl_restricted_tool_adapter.py` | GPL-cheklangan asbob adapteri |
| `tools/adapters/resolve_timeline_automator_adapter.py` | DaVinci Resolve timeline adapteri |
| `tools/registry.json` | Asboblar reyestri |
| `tools/candidates.json` | Nomzod asboblar ro'yxati |

## `tools.lock.json` dagi yozuvlar — haqiqiy holat

| Yozuv | E'lon qilingan manba | Haqiqiy holat |
|---|---|---|
| `resolve_cli_automator` | `github.com/post-tools/resolve-tools` (MIT) | ❌ **Repoda yo'q.** `tools/vendor/resolve_cli_automator/` papkasi mavjud emas. Repozitoriyadan tashqarida (`~/.gemini/antigravity/scratch/conduit/tools/vendor/`) faqat `LICENSE` va `conduit_tool.json` stub bor — bajariluvchi kod yo'q. |
| `blender_studio_assets` | `http://127.0.0.1:8991/heavy/asset_pack.bin` (MIT, 1.25 GB) | ❌ **Mavjud emas.** Manba URL — localhost manzil, u hech qanday servis emas (ulanish rad etiladi). Papka bo'sh, 1.25 GB fayl yo'q. `sha256` hech qachon haqiqiy faylga mos kelmagan. |

### Nima uchun bu yozuvlar noto'g'ri

1. **`installed_path` repozitoriyadan tashqariga ishora qiladi.** Conduit ko'chirilganda
   (masalan boshqa kompyuterga klonlanganda) bu yo'llar mavjud bo'lmaydi. Vendor kod
   repozitoriya ichida (`tools/vendor/`) turishi kerak.
2. **`127.0.0.1:8991` manba emas.** Litsenziya va kredit saqlanishi uchun manba haqiqiy,
   ochiq, tekshiriladigan URL bo'lishi shart.
3. **`sha256` tasdiqlanmagan.** Hash mavjud bo'lmagan fayl uchun yozilgan, ya'ni
   yaxlitlik tekshiruvi o'tkazilmagan.

### Qachon to'g'rilanadi

Vendor asbob haqiqatan olinganda:
1. Kod `tools/vendor/<asbob>/` ichiga, asl `LICENSE` fayli bilan qo'yiladi.
2. `tools.lock.json` dagi `url` haqiqiy ochiq manbaga, `sha256` esa real fayl hashiga almashtiriladi.
3. Shu jadvalga aniq commit/versiya va olingan sana yoziladi.

Shu paytgacha `tools.lock.json` dagi yuqoridagi ikki yozuvni **tasdiqlangan deb hisoblash mumkin emas**.
