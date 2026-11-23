# TEST

Har bo'limda `Natija:` haqiqiy chiqish bilan yozildi.

## 1. Ishga tushirish / build: buyruq va HAQIQIY chiqish
`python -m compileall -q backend conduit.py` → COMPILEALL=0. `python conduit.py doctor` → 0 FAIL, `Zarur hamma narsa tayyor — MVP ishlatishga mumkin.`. `npx tsc --noEmit` → 0, `npm run build` → 0, `npm run lint` → 0 (faqat info darajasidagi react-hooks ogohlantirish, xato emas). API/WEB 200.
Natija: O'TDI

## 2. Asosiy funksiyalar: har biri uchun qadam va natija
`pytest backend/tests/test_clone_manager.py -q` → `3 passed in 3.56s` (https-only, haqiqiy git klonlash/yangilash/o'chirish, traversal rad etish). `POST /api/clones` bilan `https://github.com/morluto/rea.git` klonlandi: status ready, HEAD `2c38fd16287085867848ce152ae2e57bf68d2015`. `GET /library/animejs/demos/timer.html` 200, `dist/anime.esm.js` 200, `docs/timer.md` 200. Playwright demo: `TIMER 82% 55% ADVANCED True`, `PAUSE 59% 59% STOPPED True`, `CONSOLE_ERRORS []`.
Natija: O'TDI

## 3. Chegara va xato holatlari: bo'sh, noto'g'ri, juda katta, tarmoqsiz, ruxsatsiz
`http://`, `javascript:`, `git@` URL'lar rad etiladi. `../evil` nomi rad etiladi. Klon mavjud bo'lsa qayta klonlash rad etiladi. `get_clone` yo'q clone uchun `CloneError` (API 404). Resurs byudjeti testlari toza holatda izolyatsiya qilindi.
Natija: O'TDI

## 4. Xavfsizlik tekshiruvi: kalitlar, kiritilgan ma'lumot, ruxsat
Faqat https sxemasi, `resolve_safe_path` uslubi bilan `clones/` ichiga yo'l tekshiruvi, shell'siz `subprocess.run`, maxfiy ma'lumot loglanmaydi, global git/auth/MCP o'zgartirilmadi, `npx rea-agents setup` ishga tushirilmadi. 4 ta `sk-...` gumoni faqat redaction test fixture'lari.
Natija: O'TDI

## 5. Regressiya: avval ishlagan narsa buzilmaganmi
To'liq to'plam: `python -m pytest backend/tests -q` → `151 passed, 2 skipped, 4 warnings in 301.95s`, EXIT=0. Oldingi terminal/URL tuzatishlari ham yashil.
Natija: O'TDI

## 6. Qo'lda ko'rish / jonlilik: UI, telefon, animatsiya, ovoz (mos bo'lsa)
Klonalar UI `Window5Workspace.tsx` ga qo'shildi, tsc/lint/build yashil. Anime.js Timer demosi mahalliy fayldan ishga tushdi, progress 82%→55% o'zgardi, Pause to'xtatdi, console xatolari yo'q. Screenshot `animejs_demo.png` saqlandi.
Natija: O'TDI

## 7. Tekshirilmaganlar: halol ro'yxat va sababi (yo'q bo'lsa, shuni yoz)
Barcha 815 fayl o'qilmadi; boshqa agentlarning uzoq TUI ishi sinab ko'rilmadi; 7 ta ixtiyoriy CLI o'rnatilmagan; `npm audit` postcss/next (Next 16 migratsiyasi) keyingi vazifaga qoldirildi.
Natija: TEKSHIRILMADI (sabablari yuqorida)
