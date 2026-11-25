# TEST

## 1. Ishga tushirish / build

Natija: O'TDI. `python -m pytest backend/tests -q` → `186 passed, 2 skipped, 4 warnings in 309.17s`, `FULL=0`. `python -m compileall -q backend` → `0`. `python conduit.py doctor` → `0 FAIL` (faqat ixtiyoriy Notion/Slack/GitHub token WARN). Frontend `tsc 0`, `build 0`, `lint 0` (2 oldingi warning). Backend asosiy repodan restart qilingach `/health=200`, frontend 200.

## 2. Asosiy funksiyalar

Natija: O'TDI. `parse_visual_spec('3 ta qizil shar va ko\'k kub, "NEXUS", fon qora, metall')` → ranglar `#DC2626/#2563EB`, shakllar cube/sphere, count 3, text NEXUS, material metal, bg `#0F172A`. `tool_gen_image` shu spec bilan 2D rasm yaratdi: 2 qizil kub + 1 ko'k shar, markazda NEXUS, tungi fon, 5200 bayt. Blender render 12.87s, 460668 bayt: 2 qizil kub + 1 ko'k metall shar, tungi ko'k fon va NEXUS yozuvi. `cli_runner` sculptor shoxi endi hardcoded kub emas, spec asosida sahnani quradi.

## 3. Chegara va xato holatlari

Natija: O'TDI. `fon qora` endi obyekt rangi sifatida qo'shilmaydi; `ko'k` apostrofi matn deb o'qilmaydi (faqat ikki qo'shtirnoq/guillemet matn); uzun matn 60 belgiga qisqartiriladi. 2D rasm va Blender render ikkalasi ham vizual tekshirildi; eski tasodifiy grid va umumiy kub yo'q.

## 4. Xavfsizlik tekshiruvi

Natija: O'TDI. Foydalanuvchi matni kod sifatida bajarilmaydi, `repr()` bilan kiritiladi; HTML hisobotda `html.escape()` ishlatiladi (oldingi test o'tgan); global config/auth/MCP o'zgartirilmadi; xatolar loglanadi.

## 5. Regressiya

Natija: O'TDI. `test_visual_spec_quality.py` → 3 passed. Oldingi 5 soatlik 180 passed/2 skipped natijasi 186 passed/2 skipped gacha kengaydi; hech qanday eski test buzilmadi. `test_no_silent_except`, CLI JSON va XSS testlari ham o'tdi.

## 6. Qo'lda ko'rish / jonlilik

Natija: O'TDI. `C:\Users\Kapitan\AppData\Local\Temp\opencode\spec_image.png` va `workspaces/sculptor/render_snapshot.png` ochildi; ikkalasida ham talab ko'rinadi: ranglar, shakllar, son va yozuv. UI Playwright: `BODY_LEN 5038`, `HAS_REPORT True`, gaps `x=0,y=0`; backend/frontend jonli.

## 7. Tekshirilmaganlar

Natija: TEKSHIRILMADI (sababi aniq). Tashqi text-to-image modeli yo'q va ruxsat so'ralmadi; shuning uchun natija deterministik PIL/Blender bilan cheklangan. Yangi tillardagi rang/shakl nomlari lug'atda yo'q bo'lsa, foydalanuvchi ularni aniq yozishi kerak.
