# DEBUG

## 1. Terminal `Running command...` zinapoyasi

Alomat: Foydalanuvchi oynasida AI agent buyruq bajarganda terminal `Runni / Runin / Running c / Running comm...` shaklida o'nlab satrlar bilan to'lib ketadi. Yangi ulanishda ham bu zinapoya takrorlanadi.

Ildiz sabab: Aslida agy spinner kadrlari `\x1b[3A` (cursor-up) va `\x1b[ND` bilan bir satr ichida qayta chiziladi — bu to'g'ri TUI xatti-harakati. Xato `backend/terminal_session.py::_append_scrollback` da yotardi: u PTY chiqishini `\r\n` bo'yicha satrlarga bo'lib saqlardi, `connect_client` esa bu satrlarni yana `\r\n` bilan birlashtirib qaytarardi. Kadrlar orasiga qo'shilgan sun'iy `\r\n` tufayli keyingi kadrning `\x1b[3A` ko'tarilishi noto'g'ri satrga tushib, kadrlar ustma-ust emas, pastma-past chizilardi. Dastlabki taxmin ("spinner kadrlari `\r` bilan yangi satr ochadi") noto'g'ri edi: xom baytlar `\x1b[3A` borligini ko'rsatdi.

Dalil: `capture_chunks.py` 164 bo'lak yig'ib, haqiqiy kadrlarni ko'rsatdi: `'\x1b[?25l\r\x1b[3A⣯  \x1b[90mRunning command...\x1b[m\n\n\n\x1b[19D\x1b[?25h'`. `analyze_chunks.py`: `FRAMES_BEFORE 131 FRAMES_AFTER 131 BARE_AFTER 0` — barcha kadrlar to'g'ri qayta chizishga ega. `verify_replay2.py`: tuzatishdan oldin bo'laklar orasida `\x1b[?25h\r\n\x1b[?25l` (BAD_JOIN) paydo bo'lgan; tuzatishdan keyin `BAD_JOIN 0`, `GOOD_JOIN 345`, `TAIL_IN_REPLAY True`, `FRAMES 19`. `visual_term_check.py`: `ROWS {'total': 21, 'running': 0, 'sample': []}`, `CONSOLE_ERRORS []`.

Tuzatish: `backend/terminal_session.py` da xom PTY bo'laklari uchun `_scrollback_chunks` dequesi qo'shildi; `_append_scrollback` endi xom bo'lakni ham, satr bo'laklarini ham saqlaydi; `connect_client` endi `"".join(self._scrollback_chunks)` bilan qaytaradi; barcha tozalash joylari bitta `_clear_scrollback()` orqali ikki buferni tozalaydi. `collapse_spinner_frames` faqat `\x1b[3A` siz "yalang'" spinner kadrlari uchun qoldirildi. Regressiya testi: `test_scrollback_replay_preserves_cursor_up_frames`.

Tekshiruv: `pytest backend/tests/test_terminal_spinner.py backend/tests/test_url_validation.py backend/tests/test_browser_navigation_api.py -q` → `24 passed in 1.29s`; to'liq `pytest backend/tests -q` → `148 passed, 2 skipped, 4 warnings in 283.02s`. Jonli replay o'lchovi: `BAD_JOIN 0`, `GOOD_JOIN 345`, `TAIL_IN_REPLAY True`. Ekran tekshiruvi: `running rows 0`, konsol xatosi yo'q.

## 2. Brauzer `-hel` uchun xom Playwright xatosi

Alomat: Manzil satriga `-hel` yozilganda oyna pastida qizil rangda `page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL ... navigating to "-hel"` chiqardi.

Ildiz sabab: `frontend/src/components/Window2Browser.tsx::openUrl` har qanday matnga shartsiz `https://` qo'shib yuborardi (`-hel` → `https://-hel`). `backend/main.py::browser_navigate` esa `url: str` ni hech qanday tekshirishsiz `live_browser.navigate` ga uzatardi. Natijada pastki darajadagi Playwright xatosi foydalanuvchiga to'g'ridan-to'g'ri ko'rsatilardi. Ikki chegarada ham tasdiqlash yo'q edi.

Dalil: `POST /api/browser/navigate` `-hel` bilan tuzatishdan oldin xom navigatsiya xatosini qaytargan; tuzatishdan keyin `422 {"detail":"Noto'g'ri host nomi"}`, `javascript:alert(1)` uchun `422 {"detail":"Faqat http va https sxemalari qo'llab-quvvatlanadi"}`. Playwright UI tekshiruvi: `ALERTS ["Noto'g'ri host nomi", '']`, `RAW_GOTO False`, `FRIENDLY True`, screenshot `url_ui.png`.

Tuzatish: Yangi `backend/url_validation.py::normalize_navigation_url` sxema, host, port, foydalanuvchi ma'lumoti, uzunlik va bo'sh joyni tekshiradi; `host:port` to'g'ri host sifatida taniladi. `backend/main.py` endi xatoda `HTTPException(422, ...)` qaytaradi va faqat normalizatsiyalangan URL'ni `live_browser.navigate` ga beradi. Frontend yaroqsiz sxemani oldindan rad etib, qisqa xabar chiqaradi; yakuniy nazorat backendda.

Tekshiruv: `pytest backend/tests/test_url_validation.py backend/tests/test_browser_navigation_api.py -q` → `13 passed` (asosiy to'plam bilan birga `24 passed`); API: `-hel`, `https://-hel`, `javascript:` → 422, `example.com` → `https://example.com/`, `localhost:3000` → `http://localhost:3000/`; UI: `RAW_GOTO False`, `FRIENDLY True`.

## 3. Noto'g'ri dastlabki gipoteza (rad etildi)

Alomat: Xom ko'rinishda spinner satrlari `\r⣻ ...\n\n` kabi ko'rinib, "yangi satr" sababi `\r` deb o'ylandi.

Ildiz sabab: Xato matnni `re.sub` bilan "tozalab" o'qish edi — bu `\x1b[3A`, `\x1b[K`, `\x1b[ND` boshqaruv ketma-ketliklarini o'chirib, noto'g'ri tasvir berardi.

Dalil: `chunks.json` dagi xom baytlar va `FRAMES_BEFORE 131 / BARE_AFTER 0` natijasi gipotezani rad etdi.

Tuzatish: Tahlil xom bo'laklar ustida qayta qilindi; kod yozishdan oldin haqiqiy PTY baytlari saqlab tekshirildi.

Tekshiruv: Uch gipotezadan H1 (navbatdagi promptlar) `SECOND_ECHOED False` bilan, H3 (xterm noto'g'ri chizadi) `running rows 0` bilan rad etildi; H2 (scrollback birlashtirish) `BAD_JOIN 0` bilan tasdiqlandi.
