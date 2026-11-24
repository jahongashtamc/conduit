# REJA

## 1. Sifat mezonlari xaritasi va repro dalillarni tasdiqlash

Nima qilinadi va qaysi fayllar: allaqachon o'tkazilgan repro natijalari `.deep-plan/DEBUG.md` ga yoziladi; `tools.py`, `kernel.py`, `cli_runner.py`, `app_adapter.py`, `main.py`, `report_generator.py` dagi aniq qatorlar bog'lanadi.

Tugash sharti: 4 ta asosiy nuqson uchun alohida dalil bor: gradient video, deepx 240s timeout, hardcode Figma, raqamli ID bilan report xatosi.

Eng sodda variant: yangi fayl ochmay, mavjud DEBUG.md bo'limlarini to'ldirish.

## 2. Video montajni haqiqiy media bilan ishlashga o'tkazish

Nima qilinadi va qaysi fayllar: `backend/tools.py::tool_video_render` va `backend/engine/cli_runner.py` editor branch; kirish klip/audio yo'lini olish, FFmpeg `concat/trim/atrim` bilan haqiqiy MP4 yaratish, kirish yo'q bo'lsa FAIL.

Tugash sharti: ikki test klipi bilan chaqiruvda haqiqiy MP4 chiqadi, kesimlar va chiqish fayli hisobotda bor; kirishsiz chaqiruv FAIL.

Eng sodda variant: yangi media framework emas, mavjud FFmpeg binary va `concat` filtri.

## 3. DeepX/DeepSearch rejimlarini ishlatishga keltirish

Nima qilinadi va qaysi fayllar: `backend/engine/kernel.py`, `backend/main.py`, `backend/engine/deepsearch.py`, `backend/tests/*`; DEEPSEARCH qo'shish, swarm bosqichiga `asyncio.wait_for`, bitta self-heal, soxtadan farqli halol audit, 401 va relevance xatosi.

Tugash sharti: `active_mode=deepsearch` qabul qilinadi; sekin bosqich 60s ichida FAIL yoki tiklanadi; hech qanday `Sertifikatlangan` soxta yozuvi qolmaydi; 401 "manba mavjud emas" deb ko'rsatiladi.

Eng sodda variant: yangi orkestrator emas, mavjud kernel ichida qattiq timeout va aniq xato xabari.

## 4. Figma agentini real ma'lumot yoki halol xatoga o'tkazish

Nima qilinadi va qaysi fayllar: `backend/tools.py::tool_figma_sync`, `backend/app_adapter.py::get_figma_project_info`, `backend/engine/cli_runner.py` designer branch; token/fayl kaliti bo'lsa REST, bo'lmasa `needs_config`, talab bo'yicha filtr.

Tugash sharti: hardcode token/component/spec qolmaydi; token yo'q holatda aniq xato; token bor holatda mock REST testida haqiqiy fayl ma'lumoti qaytariladi.

Eng sodda variant: mavjud `urllib`/`httpx` bilan bitta REST chaqiruv.

## 5. Umumiy hisobotni har qanday mavjud vazifa uchun ochish

Nima qilinadi va qaysi fayllar: `backend/main.py` report endpoint, `backend/report_generator.py`, `backend/database.py`, testlar; raqamli ID normalizatsiyasi va statik xavfsizlik da'volarining halol qilinishi.

Tugash sharti: `GET /api/tasks/<raqamli_id>/report` mavjud vazifa uchun haqiqiy ma'lumot qaytaradi; yo'q ID uchun aniq xato; hisobotda isbotlanmagan da'vo yo'q.

Eng sodda variant: ID ni `int` ga o'tkazib qayta so'rash.

## 6. To'liq tekshiruv, hujjat va integratsiya

Nima qilinadi va qaysi fayllar: barcha o'zgarishlar, `.deep-plan/TEST.md`, `DEBUG.md`, `DECISIONS.md`, `.agents/time-log.md`; `pytest backend/tests -q`, `compileall`, `doctor`, `tsc`, `build`, `gate.py verify`, git.

Tugash sharti: barcha buyruqlar 0/OK, git toza, faqat rejadagi fayllar o'zgargan, commit va merge qilingan.

Eng sodda variant: mavjud tekshiruv buyruqlarini qayta ishga tushirish.

TASDIQ: HA
