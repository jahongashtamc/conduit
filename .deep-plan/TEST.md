# TEST

Har bo'limda haqiqiy buyruq chiqishi va `Natija:` qatori yozilgan.

## 1. Ishga tushirish / build: buyruq va HAQIQIY chiqish

Buyruqlar: `python -m compileall -q backend conduit.py`, `python conduit.py doctor`, `cd frontend && npx tsc --noEmit`, `npm run build`, `npm run lint`.
Haqiqiy chiqish: `COMPILEALL=0`, `DOCTOR=0` (`Zarur hamma narsa tayyor — MVP ishlatishga mumkin.`), `TSC=0`, `BUILD=0`, `LINT=0` (`✔ No ESLint warnings or errors`). Backend `http://127.0.0.1:8000/api/health` va frontend `http://127.0.0.1:3000/` 200 qaytardi.

Natija: O'TDI — besh tekshiruv ham 0 chiqish kodi bilan tugadi, xizmatlar jonli.

## 2. Asosiy funksiyalar: har biri uchun qadam va natija

1) Terminal: `capture_chunks.py` orqali 164 bo'lak yig'ildi, 21 tasida `Running` bor; `verify_replay2.py` qayta ulanishdan keyin `BAD_JOIN 0`, `GOOD_JOIN 345`, `TAIL_IN_REPLAY True`, `FRAMES 19` berdi. 2) Brauzer: API ga `-hel`, `https://-hel`, `javascript:alert(1)` yuborildi; mos ravishda 422 `Noto'g'ri host nomi`, 422 `Noto'g'ri host nomi`, 422 `Faqat http va https sxemalari qo'llab-quvvatlanadi`. To'g'ri kiritishlar `example.com` → `https://example.com/`, `localhost:3000` → `http://localhost:3000/` normallashtirildi. 3) UI: Playwright `-hel` ni manzil maydoniga yozib Enter bosdi; `ALERTS ["Noto'g'ri host nomi", '']`, `RAW_GOTO False`, `FRIENDLY True`.

Natija: O'TDI — ikkala xato ham jonli muhitda tasdiqlangan tarzda tuzatildi.

## 3. Chegara va xato holatlari: bo'sh, noto'g'ri, juda katta, tarmoqsiz, ruxsatsiz

`test_url_validation.py` bo'sh satr, `-hel`, `https://-hel`, `http://`, `javascript:`, `file:///`, `https://bad_host.example`, `https://exa mple.com` va 2048 belgidan uzun kiritishni rad etadi; `test_browser_navigation_api.py` noto'g'ri URL uchun 422 va `live_browser.navigate` chaqirilmasligini tekshiradi. Tarmoqsiz holatda backend 502 emas, aniq 422 qaytaradi; ruxsatsiz sxema (javascript/file) bloklanadi. Bo'laklar alohida kelganda ham `test_single_frame_chunk_is_collapsed` o'tadi.

Natija: O'TDI — chegara va xato holatlari uchun barcha parametrli testlar yashil.

## 4. Xavfsizlik tekshiruvi: kalitlar, kiritilgan ma'lumot, ruxsat

`grep`/skaner 4 ta `sk-...` mosligini ko'rsatdi; ular `backend/inspector_executor.py` va `backend/tests/test_security.py` dagi redaksiya testlaridir, haqiqiy kalit emas. Yangi validator sxemani (`^[A-Za-z][A-Za-z0-9+.-]*:`) tekshiradi, `host:port` ni sxema deb bilmaydi, foydalanuvchi ma'lumotlari (`user:pass@host`) va 2048 belgidan ortiq kiritishni rad etadi, portni `urlsplit().port` orqali tekshiradi. Global konfiguratsiya, auth va MCP sozlamalariga tegilmadi; maxfiy qiymat loglarga yozilmadi.

Natija: O'TDI — xavfli kiritish bloklanadi, maxfiy ma'lumot topilmadi, global sozlamalar o'zgarmadi.

## 5. Regressiya: avval ishlagan narsa buzilmaganmi

`python -m pytest backend/tests -q` to'liq yangi testlar bilan `148 passed, 2 skipped, 4 warnings in 283.02s (0:04:43)`, chiqish kodi 0. Bungacha 124 passed edi; qo'shilgan 24 ta test (spinner, scrollback, URL, API) ham o'tdi. Oldingi `scrollback_buffer` matn qidirish uchun saqlanib qolgani uchun `test_bosqich1.py` va `test_terminal_busy.py` ham yashil.

Natija: O'TDI — 148 test o'tdi, 2 test atayin o'tkazib yuborildi, regressiya yo'q.

## 6. Qo'lda ko'rish / jonlilik: UI, telefon, animatsiya, ovoz (mos bo'lsa)

Playwright 1600×1000 oynada `visual_term_check.py`: `ROWS {'total': 21, 'running': 0, 'sample': []}`, `CONSOLE_ERRORS []`, skrinshot `terminal_after_fix.png`. `visual_peak_check.py`: `PEAK_RUNNING_ROWS 0`, `PEAK_SAMPLE []`; band agent xabari navbatga tushmaydi (`SECOND_ECHOED False`). `verify_url_ui.py`: `ALERTS ["Noto'g'ri host nomi", '']`, `RAW_GOTO False`, `FRIENDLY True`, skrinshot `url_ui.png`. Telefon o'lchami va ovoz bu ikki xatoga aloqador emas, alohida tekshirilmadi.

Natija: O'TDI — terminal toza ko'rinadi, brauzer xatosi tushunarli, console xatosi yo'q.

## 7. Tekshirilmaganlar: halol ro'yxat va sababi (yo'q bo'lsa, shuni yoz)

793 ta faylning hammasi o'qilmadi — faqat ikki xatoga tegishli oqim va testlar to'liq o'qildi. Global auth/MCP sozlamalari o'zgartirilmaganligi sababli ular bilan bog'liq integratsiya sinovdan o'tkazilmadi. 7 ta ixtiyoriy CLI o'rnatilmagan. `npm audit` dagi `postcss`/`next` zaifliklari Next 16 major migratsiyasini talab qilgani uchun major o'zgarish sifatida keyingi vazifaga qoldirildi (`docs/SKILLS_AND_AUDIT.md`). Boshqa AI CLI'larning uzoq TUI sessiyasi tekshirilmadi.

Natija: TEKSHIRILMADI — yuqoridagi besh holat vazifa doirasidan tashqari yoki atayin o'zgartirilmagan; qolgan barcha tekshiruvlar O'TDI.
