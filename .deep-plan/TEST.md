# TEST

## 1. Ishga tushirish / build

Natija: O'TDI. `python -m pytest backend/tests -q` → `171 passed, 2 skipped, 4 warnings in 114.21s`, `PYTEST=0`. `python -m compileall -q backend` → `0`. `python conduit.py doctor` → `0 FAIL`, `Zarur hamma narsa tayyor`. Frontend: `npx tsc --noEmit` → `0`, `npm run build` → `0`, `npm run lint` → `0` (2 ESLint warning, exit 0). Backend/frontend asosiy repodan qayta ishga tushirildi: `/health=200`, `WEB=200`.

## 2. Asosiy funksiyalar

Natija: O'TDI. Video: real lokal 1s klip bilan `tool_video_render` MP4 yaratadi; `inputs` va `frames` qaytaradi; kirish klipsiz chaqiruv `success:false` qaytaradi. DeepX/DeepSearch: `KernelMode.DEEPSEARCH` qo'shildi, `/api/kernel/settings` uni qabul qiladi (sinovdan keyin `standard` ga qaytarildi); `POST /api/tools/deepsearch {"topic":"React query"}` → `SUCCESS=True`, `CANDIDATES=12`, `SOURCE_ERRORS=1`, `research/react_query.md` yozildi. Figma: token yo'q holatda `needs_config`, mock REST javobi bilan haqiqiy document/token/component ma'lumoti o'qildi va foydalanuvchi talabi bo'yicha filtrlandi. Hisobot: haqiqiy `task_id` bilan `/api/tasks/task_250f4a9a/report?format=markdown` → `200`, 2608 belgi, PASS hisobot.

## 3. Chegara va xato holatlari

Natija: O'TDI. Klipsiz video rad etiladi; ffmpeg filtergraph bir necha klip bilan sinovdan o'tdi; swarm bosqichi `asyncio.wait_for` bilan hard-timeout oladi (`test_swarm_stage_timeout`, sekin mock bilan); GitHub code search 401 xatosi `source_errors` ichida halol ko'rsatiladi; `FIGMA_TOKEN` yo'q holatda soxta spec qaytarilmaydi; mavjud bo'lmagan vazifa ID si `topilmadi` deb xabar qilinadi (bu to'g'ri xatti-harakat).

## 4. Xavfsizlik tekshiruvi

Natija: O'TDI. Figma tokeni loglarga chiqarilmaydi, faqat `needs_config`/`api_error` holati qaytariladi; video kirish yo'llari mavjud fayl va hajm bo'yicha tekshiriladi; global config/auth/MCP o'zgartirilmadi; hisobotda statik tasdiqlanmagan xavfsizlik da'volari olib tashlandi, tool whitelist haqiqiy `security_guard` ma'lumotidan olinadi.

## 5. Regressiya

Natija: O'TDI. Oldingi 165 passed/2 skipped natijasi buzilmadi: yangi testlar bilan birga `171 passed, 2 skipped`. Video, Figma, report, kernel va terminal testlari alohida ham o'tdi (33 targeted test).

## 6. Qo'lda ko'rish / jonlilik

Natija: O'TDI. Playwright with real UI: `HISOBOT_TAB=1`, `REPORT_TEXT=1`, `GAPS={'x':0,'y':0}`; skrinshot `C:\Users\Kapitan\AppData\Local\Temp\opencode\four_defects_ui.png` da Hisobot tabi, HTML/MD havolalari va PASS holati ko'rinadi. Video galereyasi uchun real MP4 artefakti mavjud; Figma uchun real hisob ma'lumoti yo'qligi sabab UI faqat mock REST bilan tekshirildi.

## 7. Tekshirilmaganlar

Natija: TEKSHIRILMADI (sababi aniq). Haqiqiy foydalanuvchi Figma tokeni/file keyi va haqiqiy video kliplari yo'q; ular bilan ishlash mock REST va lokal ffmpeg testsrc klip bilan qoplandi. GitHub token yo'q, shuning uchun code search 401 holati haqiqiy, lekin muallifli qidiruv sinov qilinmadi.
