# LOYIHA

## 1. MVP talablari nima?

Foydalanuvchi shikoyati: "bug'lar juda ko'p, toollar va terminal qismi barcha
funksiyalar talabga javob bermaydi". MVP: (1) har bir tool (`list_tools` 22 ta)
haqiqiy chaqiruvda ishlashi va **haqiqiy artefakt** qaytarishi; (2) terminal
(PTY/xterm) barcha asosiy amallarni bajarishi: buyruq, kirill matn, xato,
Ctrl+C bekor qilish, tarix, ko'p qatorli chiqish, resize, qayta ulanish;
(3) barcha API endpointlar 5xx bermasligi va noto'g'ri kiritishni rad etishi;
(4) UI 0 konsol xatosi va 0 gorizontal overflow bilan ishlashi; (5) subagent
zanjiri (routing -> doer -> checker) haqiqiy fayl bilan PASS berishi.
Tekshiruv: har qatlam uchun dalil jadvali (TEST.md).

## 2. Foydalanuvchi aynan nimani xohlaydi va qanday ishlashi kerak?

Foydalanuvchi terminalni ochsa, buyruq yozsa — ishlashi kerak; Ctrl+C bilan
uzoq buyruqni to'xtata olishi; kirill matn yozishi. `conduit run <agent>` bersa
— haqiqiy artefakt chiqishi. Xato bo'lsa — aniq sabab, 500 emas.

## 3. Qismlar, oqim va eng kichik ishlaydigan qism

Qatlamlar: (a) xom PTY (pywinpty), (b) WS qatlami, (c) xterm.js UI, (d) tools.py,
(e) FastAPI endpointlar, (f) router -> cli_runner -> subagent. Eng kichik
ishlaydigan qism: xom PTY'da Ctrl+C. U ishlamasa terminal "o'lik" bo'ladi.

## 4. Har funksiya uchun eng qisqa to'g'ri yechim

Yangi kutubxona yo'q. pywinpty'ning `sendintr()` va `PYWINPTY_BACKEND=1`
(ConPTY) ishlatiladi. Kodlash uchun `encoding="utf-8"` + bola muhitiga
`PYTHONIOENCODING`. Artefakt tekshiruvi uchun fayl mavjudligi + hajm.

## 5. O'xshash mahsulotlar va ustunliklar

ConPTY — Windows'ning rasmiy PTY API'si (Windows 10 1809+). Alternativa
`pywinpty` (o'ralgan) yoki `conpty` to'g'ridan-to'g'ri. Conduit afzalligi:
deterministik tekshiruv (fayl + hajm + check_goal), UI monitoring.

## 6. Kiberxavfsizlik

Shell inyeksiyasi: agent buyrug'i tokenlar bo'yicha tekshiriladi
(`;&|`$()<>\n` taqiqlangan). URL: faqat http/https, foydalanuvchi/parol
taqiqlangan, TLD tekshiriladi. Terminal javoblari (DA/DSR) filtrlangan.
Fayl yo'llari workspace chegarasida.

## 7. Tayyorlik mezonlari

Har topilgan nuqson: (a) haqiqiy reproduksiya, (b) ildiz sabab yozilgan,
(c) regressiya testi (mutation bilan tekshirilgan), (d) to'liq to'plam yashil,
(e) jonli dalil. `gate.py verify` OK.
