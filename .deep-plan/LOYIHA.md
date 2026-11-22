# LOYIHA

## 1. Shu turdagi loyihani bozorda MVP qilish uchun minimal talablar qanday? [QIDIRUV: manbalarni MANBALAR.md ga yoz]

Ishlaydigan terminal bridge (PTY → WebSocket → xterm.js), asosiy AI agentning `conduit run` orqali subagentga vazifa topshirishi, qisqa natijaning UI'da ko'rinishi, token/byudjet hisobi, xato holatlarida tushunarli xabar, 0 placeholder, avtomat testlar va toza git daraxti. Manbalar: MANBALAR.md 1-bo'lim.

## 2. Foydalanuvchi aynan nimani xohlayapti va qanday ishlashi kerak? [FOYDALANUVCHIDAN SO'RA]

Foydalanuvchi: `shablon emas demo emas expert darajasidagi tolliq ish`. Aniq ikki xato: terminal `Running command...` zinapoyasi va browser `-hel` kabi noto'g'ri URL'da xom `page.goto` xatosi. Kutilayotgan holat: terminal toza, xatolar tushunarli, asosiy agent ishlab turgan holda subagentlarni chaqiradi. Savol berilmadi — foydalanuvchi o'zi o'qib tuzatishni topshirdi.

## 3. Loyiha qismlarga qanday bo'linadi va qismlar qanday bog'lanadi? Avval ko'rsatib tasdiq olinadigan, ishlaydigan eng kichik qism qaysi? Foydalanuvchiga yoqmasa, qancha ish bekor ketadi? [Bog'lanishni yoz; kichik qismdan boshla]

`backend/terminal_session.py` PTY chiqishini o'qiydi → `collapse_spinner_frames` va xom bo'laklar buferi → `WS /ws/terminal` → `Window1Terminal.tsx` xterm.js. `Window2Browser.tsx` → `POST /api/browser/navigate` → `url_validation.normalize_navigation_url` → `live_browser.navigate`. Eng kichik qism: URL validatsiyasi (sofreferensiya) va xom scrollback replay. Taxmin 30 daqiqa; yoqmasa faqat shu ikki joy qaytariladi.

## 4. Har funksiya uchun eng qisqa to'g'ri yechim qaysi? Tayyor kutubxona yoki vosita bormi? [Yuzlab qator yozishdan oldin tayyorini qidir]

Yangi paket yo'q: Python `re`, `urllib.parse`, FastAPI `HTTPException`, mavjud Playwright va xterm.js ishlatildi. Spinner uchun TUI kadrlarini o'zgarishsiz qoldirib, faqat xom bo'laklarni `\"\".join` bilan qayta o'ynash; URL uchun bitta sof funksiya + 422.

## 5. Bozorda o'xshashlari bormi? Qaysi ustunliklarni taklif qila olaman? [QIDIRUV: manbalarni MANBALAR.md ga yoz. Ustunliklar faqat TAKLIF, foydalanuvchi tasdiqlamaguncha qo'shilmaydi]

Bor: Claude Code subagents, Antigravity CLI subagents, OpenCode. **TAKLIF** (tasdiqlanmagan): har qandai CLI agentga universal bog'langan 16 ta subagent, `conduit run` + byudjet va jonli sahna. Foydalanuvchi tasdiqlamaguncha qo'shilmadi.

## 6. Kiberxavfsizlik tomondan nimalar qilinishi kerak? [QIDIRUV + yonalish faylidagi ro'yxat]

Kiritishni chegara nuqtasida tekshirish (sxema, host, port, userinfo, uzunlik), xom Playwright xatosini UI'ga chiqarmaslik, maxfiy qiymatlarni loglamaslik, global sozlamalarga tegmaslik, sun'iy URL bilan SSRF yo'qligi (faqat http/https, localhost faqat aniq ruxsat). Manbalar: MANBALAR.md 6-bo'lim.

## 7. 'Tayyor' deyish mezoni nima? [Ishga tushadimi? Ko'rinishi jonlimi? Ortiqcha narsa qolmadimi? Zerikarli, jonsiz joy yo'qmi?]

`pytest` yashil, `compileall/doctor/tsc/lint/build` 0, API/WEB 200, live replay `BAD_JOIN 0`, UI'da `RAW_GOTO False`, terminal `running rows 0`, `gate.py verify OK`, git daraxtida faqat maqsadli o'zgarishlar. Qo'shimcha placeholder/TODO yo'q.
