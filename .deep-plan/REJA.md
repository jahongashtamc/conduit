# REJA

Har qadamda tugash sharti va eng sodda variant yozilgan.

## 1. Clone manager va API yaratish

Nima qilinadi va qaysi fayllar: `backend/clone_manager.py` (URL validatsiyasi, `clones/registry.json`, `git clone --depth 1`, HEAD olish, ro'yxat, o'chirish), `backend/main.py` (`POST/GET/DELETE /api/clones`), `backend/tests/test_clone_manager.py`.
Tugash sharti: `https://github.com/morluto/rea.git` haqiqatdan klonlanadi, HEAD registry'da saqlanadi, xato URL rad etiladi, `pytest` yangi testlar bilan yashil.
Eng sodda variant: yangi DB jadvali yo'q, oddiy JSON registry va `subprocess.run(shell=False)`.

## 2. Klonalar UI va Anime.js oflayn kutubxonasini qo'shish

Nima qilinadi va qaysi fayllar: `frontend/src/components/Window5Workspace.tsx` (`Klonalar` bo'limi), `vendor/libraries/animejs/` (mahalliy `animejs@4` paketi, `docs/timer.md`, `demos/timer.html`), `docs/SKILLS_AND_AUDIT.md` yoki `DECISIONS.md` qaror yozuvi.
Tugash sharti: UI dan klon yaratish/ro'yxat/o'chirish ishlaydi; Anime.js Timer demosi mahalliy fayllar bilan ochiladi, CDN havolasi yo'q.
Eng sodda variant: mavjud `Window5Workspace` ichiga bo'lim, yangi route emas.

## 3. To'liq tekshiruv, hujjat va commit

Nima qilinadi va qaysi fayllar: `.deep-plan/TEST.md`, `.deep-plan/DEBUG.md`, `.deep-plan/PROGRESS.md`, `DECISIONS.md`, `.agents/time-log.md`; pytest, compileall, doctor, tsc, lint, build, health, `gate.py check/approve/verify`, lokal commit.
Tugash sharti: barcha testlar yashil, `gate.py verify OK`, git faqat ko'zlangan o'zgarishlar bilan toza, lokal commit (push yo'q).
Eng sodda variant: oldingi vazifadagi tasdiqlangan tekshiruv buyruqlarini qayta ishlatish.

TASDIQ: HA
