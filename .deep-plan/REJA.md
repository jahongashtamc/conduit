# REJA

Har qadam mustaqil, eng sodda ishlaydigan variantdan boshlanadi. Foydalanuvchi @470@ xabarida `to'liq ishlasin ... expert darajasidagi tolliq ish` deb aniq ruxsat bergan; shuning uchun qo'shimcha savol yo'q.

## 1. Terminal zinapoyasini ildizidan tuzatish
Nima qilinadi va qaysi fayllar: `backend/terminal_session.py` da xom PTY bo'laklari `_scrollback_chunks` ga saqlanadi, `connect_client` ularni `""` bilan birlashtirib qayta chiqaradi; qator asosidagi `scrollback_buffer` matn qidirish uchun saqlanadi; barcha tozalash bitta `_clear_scrollback()` orqali amalga oshiriladi. Regressiya testi `backend/tests/test_terminal_spinner.py`.
Tugash sharti: qayta ulanishda replay bo'laklar birikmasi bilan bir xil, `\r\n` orasiga qo'yilmaydi, `\x1b[3A` kadrlari buzilmaydi; jonli `BAD_JOIN 0`, `GOOD_JOIN 345`, `TAIL_IN_REPLAY True`; testlar yashil.
Eng sodda variant: yangi kutubxona yo'q — faqat ikkinchi deque va `"".join()`; spinner regex faqat yalang'och kadrlar uchun qoladi.

## 2. Browser manzilini chegarada tekshirish
Nima qilinadi va qaysi fayllar: `backend/url_validation.py` yangi funksiya `normalize_navigation_url`; `backend/main.py::browser_navigate` uni chaqirib, xato bo'lsa 422 qaytaradi va to'g'ri URL'ni `live_browser.navigate` ga uzatadi; `frontend/src/components/Window2Browser.tsx` xavfli sxemani oldini oladi. Testlar: `test_url_validation.py`, `test_browser_navigation_api.py`.
Tugash sharti: `-hel` va `javascript:alert(1)` 422 bilan qisqa tushunarli detail qaytaradi; `example.com`/`localhost:3000` normalizatsiya qilinadi; UI da xom `page.goto` matni chiqmaydi (`RAW_GOTO False`, `FRIENDLY True`).
Eng sodda variant: `urllib.parse` + FastAPI `HTTPException`; frontend faqat qo'shimcha tekshiruv, asosiy himoya backendda.

## 3. To'liq tekshiruv, hujjat va kuzatuv
Nima qilinadi va qaysi fayllar: `.deep-plan/DEBUG.md`, `TEST.md`, `PROGRESS.md` haqiqiy natijalar bilan to'ldiriladi; `pytest`, `compileall`, `doctor`, `tsc`, `lint`, `build`, `GET/POST` health va `git status` ishga tushiriladi; `gate.py check/approve/verify`; `DECISIONS.md` va `.agents/time-log.md` yangilanadi.
Tugash sharti: `gate.py verify` OK, barcha testlar yashil, faqat ko'zlangan fayllar o'zgargan, o'zgarishlar lokal commit qilingan (push yo'q).
Eng sodda variant: barcha dalillar mavjud — faqat ularni fayllarga yozib, darvozadan o'tish.

TASDIQ: HA
