# SKANER

Avtomatik faktlar `gate.py scan` dan. Pastdagi bo'limlarni agent o'zi kodni o'qib to'ldiradi.

<!-- AUTO:START -->
## Avtomatik faktlar

- Fayllar (skaner qilingan): 793
- Tillar (fayl soni / qator): .py 110/19941, .tsx 24/8636, .ts 4/520, .js 3/78, .sh 1/72, .css 1/276
- Manifest va sozlama fayllari: .gitignore, README.md, backend\requirements.txt, frontend\package.json, frontend\tsconfig.json
- Kirish nuqtalari (taxminiy): backend\main.py
- Eng katta fayllar: backend\main.py (1544), backend\database.py (1444), backend\engine\cli_runner.py (1432), frontend\src\components\Window2Browser.tsx (994), backend\engine\kernel.py (985)
- Test fayllari: 33
- CI (.github/workflows): bor
- Git: oxirgi commit: 11536a9 test: restore generated data files after test session; o'zgartirilgan fayllar: 8
- TODO/FIXME/HACK/XXX belgilari: 0
- MAXFIY QIYMAT GUMONI: 4 ta (qiymat ko'rsatilmaydi):
  - API kalit (sk-...): backend\inspector_executor.py:80
  - API kalit (sk-...): backend\inspector_executor.py:82
  - API kalit (sk-...): backend\tests\test_security.py:49
  - API kalit (sk-...): backend\tests\test_security.py:51
- Xavfli naqshlar (qo'lda tekshirish kerak):
  - jim except (xatoni yutadi): 30 ta, masalan conduit.py:53, conduit.py:341, conduit.py:475
  - shell=True / os.system: 5 ta, masalan .opencode\skills\webapp-testing\scripts\with_server.py:68, .opencode\skills\webapp-testing\scripts\with_server.py:71, backend\app_adapter.py:139
  - SQL satrni birlashtirish: 5 ta, masalan backend\database.py:1420, backend\pipeline.py:132, backend\pipeline.py:146
  - eval/exec: 4 ta, masalan backend\live_browser.py:82, backend\live_browser.py:85, backend\live_browser_session.py:86
  - innerHTML / dangerouslySetInnerHTML: 1 ta, masalan frontend\src\components\Window1Terminal.tsx:130
<!-- AUTO:END -->

## 1. Tuzilma va asosiy oqim: qismlar nima qiladi, ma'lumot qayerdan qayerga o'tadi (fayllarni o'qib yoz)

PTY chiqishi `backend/terminal_session.py` dagi `_reader_loop` da o'qiladi, `collapse_spinner_frames` orqali faqat yalang'och spinner kadrlari joyida qayta chiziladi, so'ngra `_append_scrollback` xom bo'lakni `_scrollback_chunks` ga va qatorlarga bo'lingan shaklini `scrollback_buffer` ga yozadi. WS `/ws/terminal` orqali jonli bo'laklar yuboriladi; qayta ulanishda `connect_client` xom bo'laklarni `""` bilan birlashtirib qayta o'ynaydi, shu sabab agy TUI'sining `\x1b[3A` qayta chizishi buzulmaydi. Frontend `Window1Terminal.tsx` xterm.js ga `term.write(e.data)` bilan yozadi. Brauzer oqimi: `Window2Browser.tsx` manzil formi → `POST /api/browser/navigate` → `backend/main.py:browser_navigate` → `url_validation.normalize_navigation_url` → 422 yoki `live_browser.navigate`. Asosiy server FastAPI/uvicorn, testlar `backend/tests/` da pytest bilan yozilgan.

## 2. Zaif va xavfli joylar: avtomatik faktlardagi gumonlarni qo'lda tekshirib, haqiqiymi yoki yo'qmi yoz

Skanner topgan 4 ta `sk-...` gumoni haqiqiy kalit emas: ular redaction test fixture'lari (`test_security.py`) va xavfsizlik tekshiruvi namunalari (`inspector_executor.py`); avvalgi audit ularni tasdiqlagan. 30 ta "jim except" gumoni skaner tomonidan naqsh bo'yicha sanlangan; bu vazifada ularga tegilmadi, lekin oldingi auditda production kodidagi作为 xatolarni yutadigan holatlar loglangan holda tuzatilgani qayd etilgan. `innerHTML` gumoni xterm.js ichki render qismi bo'lib, foydalanuvchi HTML'ini to'g'ridan-to'g'ri kiritmaydi. `shell=True` va SQL gumonlari bu ikki xatoni tuzatish oqimiga kirmaydi; ular alohida audit mavzusi sifatida qoldi. Yangi URL tekshiruvi xavfli sxemalarni, bo'sh hostni, foydalanuvchi ma'lumotini, uzunlik va portni rad etadi; global konfiguratsiya/auth/MCP o'zgartirilmadi.

## 3. Test va sifat holati: testlar bormi, ishga tushirdingmi, natijasi qanday (haqiqiy chiqish)

Testlar bor va to'liq ishga tushirildi: `python -m pytest backend/tests -q` → `148 passed, 2 skipped, 4 warnings in 283.02s`, chiqish kodi 0. Yangi testlar: spinner kadrlarini yig'ish, bitta bo'lak/triple newline, cursor-up kadrlariga tegmaslik, scrollback replay, URL normalizatsiyasi va API 422. `python -m compileall -q backend conduit.py` → 0; `python conduit.py doctor` → 0 FAIL; `npx tsc --noEmit` → 0; `npm run build` → 0; `npm run lint` → 0. Jonli tekshiruvda replay `BAD_JOIN 0`, `GOOD_JOIN 345`, `TAIL_IN_REPLAY True`; URL UI `RAW_GOTO False`, `FRIENDLY True`.

## 4. Bilmaydigan va tekshirilmagan joylar: nimani o'qimading yoki tushunmading (halol ro'yqat)

Barcha 793 fayl o'qilmadi; faqat ikki xato oqimi va tegishli testlar to'liq o'qildi. Global foydalanuvchi auth/MCP sozlamalari tekshirilmadi va o'zgartirilmadi. Opsiyonali CLI'lar (`gemini_cli`, `cursor_cli`, `qwen_cli`, `kimi_cli`, `glm_cli`, `aider`) o'rnatilmagan, shuning uchun ularning terminal oqimi jonli sinovdan o'tmadi. `npm audit` dagi postcss/next zaifliklari major Next 16 migratsiyasini talab qiladi; bu vazifa doirasida tuzatilmadi va `docs/SKILLS_AND_AUDIT.md` da qayd etilgan. Uzoq muddatli ishlab chiqarish muhitida PPTY/TUI boshqa agentlar bilan sinov qilinmadi.
