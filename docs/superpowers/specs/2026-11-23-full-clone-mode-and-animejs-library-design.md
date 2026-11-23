# To'liq klonlash rejimi + Anime.js kutubxonasi — dizayn

Sana: 2026-11-23
Tanlangan yondashuv: **1 — Full clone manager + offline library** (foydalanuvchi `1` deb tasdiqladi).

## Intent va sabab

Foydalanuvchi Nexus/Conduit studiyasiga GitHub repositoriyalarni **haqiqatan klonlaydigan** to'liq rejim qo'shishni xohlaydi (minimal forma emas). Shuningdek `https://animejs.com/documentation/timer` dagi animatsiya/Timer imkoniyatlarini to'liq kutubxona sifatida studiyaga oflayn yuklab qo'yishni xohlaydi. Maqsad: agentlar tashqi CDN'ga bog'lanmay, loyiha ichidagi kutubxona va klonlangan kod bilan ishlashi.

## Maqsadlar

- `POST /api/clones` orqali ixtiyoriy GitHub HTTPS URL'ni tekshirib, `git clone --depth 1` bilan loyiha ichiga klonlash.
- Klonlar ro'yxati, holati, logi, ochish/qayta yangilash/o'chirish.
- Klon jarayoni real vaqtda ko'rinadi (WS orqali progress).
- Anime.js v4 to'liq paketi + Timer/SVG/WAAPI/Easings hujjatlari va mahalliy demo `vendor/libraries/animejs/` ichida, CDN'siz.
- Ikkita aniq manzil: `https://github.com/morluto/rea.git` va Anime.js (`https://github.com/juliangarnier/anime`) klonlanadi.
- Barcha xatolar loglanadi/ko'rinadi; jim yutish yo'q.

## No-goals / anti-goals

- Global git config, global auth yoki MCP sozlamalariga tegish — **taqiqlanadi**.
- `npx rea-agents setup` ni ishga tushirish — agent konfiguratsiyasini o'zgartiradi, **taqiqlanadi**.
- `backend/tools.py::tool_run_process()` (`shell=True`, fire-and-forget) bilan klonlash — ishonchsiz.
- CDN'ga bog'liq Anime.js ulanish — oflayn bo'lishi shart.
- Minimal "faqat forma" yoki stub — foydalanuvchi aniq rad etdi.

## Cheklovlar

- Ishchi papka: `C:\Users\Kapitan\Documents\Проект по умолчанию\conduit`.
- Klonlar faqat `clones/` (loyiha ichida) ga yoziladi; yo'l `workspace_manager.resolve_safe_path()` bilan tekshiriladi.
- Faqat `https://` Git URL qabul qilinadi; `file://`, `ssh://`, `javascript:` va boshqa sxemalar rad etiladi.
- `git` binary mavjudligi `shutil.which('git')` bilan tekshiriladi (mavjud: `/api/connections`).
- Jarayon `subprocess.run([...], check=True, capture_output=True, text=True)` bilan, shell'siz.
- Commit pin ixtiyoriy: `git rev-parse HEAD` olinib saqlanadi; keyingi refresh uchun ishlatiladi.

## Yondashuvlar (tanlov oldidan)

1. **Full clone manager + offline library** — tanlandi. Mustaqil `backend/clone_manager.py`, to'liq API/UI, Anime.js oflayn paket. Afzalligi: haqiqiy rejim, qayta ishlatiladigan, kuzatuvchi. Kamchiligi: eng ko'p kod (~200-300 qator).
2. **Clone inside workspace** — klonlar `workspaces/<agent>/` ichiga, subagentga bog'lanadi. Afzalligi: tez. Kamchiligi: umumiy menejer/UI yo'q, foydalanuvchi "to'liq rejim" demagan.
3. **Faqat git/gh command tool** — eng tez, lekin to'liq rejim emas; rad etildi.

## Qurilish qarorlari (mening tanlovim)

- Ma'lumot modeli: `clones/registry.json` (id, url, name, path, commit_pin, status, created_at, last_error, log_tail).
- API:
  - `POST /api/clones` `{"url": "...", "name"?: "...", "commit_pin"?: "..."}` → task_id/clone_id (async yoki sync; kichik klonlar uchun sync + WS progress).
  - `GET /api/clones` → ro'yxat.
  - `GET /api/clones/{id}` → tafsilot + log.
  - `POST /api/clones/{id}/refresh` → qayta klonlash.
  - `DELETE /api/clones/{id}` → papkani o'chirish (faqat `clones/` ichida, tasdiqlangan id).
- WS: `/ws/clones` yoki mavjud `/ws/live` orqali `clone_progress` eventlari.
- UI: `Window5Workspace.tsx` ichida `Klonalar` bo'limi: URL input, nom, "Klonlash", ro'yxat (holat, commit, log, Ochish/Yangilash/O'chirish).
- Anime.js: `vendor/libraries/animejs/` ichida `package.json`, `lib/` (yoki `dist/anime.es.js`), `docs/timer.md`, `demos/timer.html` + mahalliy import. `npm i animejs@4` faqat shu papkada, global emas.
- Xavfsizlik: URL validatsiyasi, path traversal guard, shell'siz subprocess, hech qanday maxfiy kalit loglanmaydi.

## Foydalanuvchi hal qilmagan (mening qarorim)

- Klonlar `clones/` papkasida saqlanadi — klonlar soni kam bo'lgani uchun registry JSON yetarli, yangi DB jadvali kiritilmaydi.
- Anime.js uchun `npm install animejs@4` only in `vendor/libraries/animejs` (paket manbasi rasmiy npm). Import faqat mahalliy.

## Tayyorlik mezonlari

- `POST /api/clones` bilan `https://github.com/morluto/rea.git` muvaffaqiyatli klonlanadi, `git HEAD` saqlanadi.
- Anime.js oflayn kutubxonasi va Timer demo'si mavjud, CDN yo'q.
- `pytest` yashil, `tsc/lint/build/doctor` 0, API/WEB 200.
- `gate.py verify` OK, lokal commit (push yo'q).
