# O'ZIM (o'zimni tekshirish)

## 1. Vazifani qanchalik tushunaman?
Foydalanuvchi Nexus/Conduit studiyasiga minimal emas, **to'liq GitHub klonlash rejimi** qo'shishni xohlaydi. Aniq URL: `https://github.com/morluto/rea.git`. Shuningdek `https://animejs.com/documentation/timer` dagi Timer va boshqa animatsiya imkoniyatlarini to'liq kutubxona sifatida studiyaga oflayn yuklab qo'yish kerak. Foydalanuvchi 1-yondashuvni va dizayn hujjatini `ha` bilan tasdiqladi.

## 2. Dastlabki taxminim va uni tekshirish
Dastlab loyihada klonlash bor deb taxmin qilgan edim. `backend/engine/acquisition.py` faqat `LICENSE` va `conduit_tool.json` yozadi, hech qanday `git clone` chaqiruvi yo'q. `backend/tools.py::tool_run_process()` `shell=True` va fire-and-forget bo'lib, klonlash uchun yaroqsiz. Shuning uchun mustaqil `backend/clone_manager.py` yozish to'g'ri.

## 3. Qanday vositalar bor?
`git` binary mavjud (`/api/connections`), `shutil.which`, `subprocess.run(shell=False)`, `workspace_manager.resolve_safe_path()`, FastAPI, WS, pytest/Playwright, xterm.js va Next.js mavjud. Tashqi paket sifatida faqat `animejs@4` ni `vendor/libraries/animejs/` ichiga o'rnatish kerak; global o'rnatish yo'q.

## 4. Eng kichik to'g'ri yechim
`clones/registry.json` + xavfsiz URL tekshiruvi + `git clone --depth 1` + ro'yxat/ochish/o'chirish + `Window5Workspace` da `Klonalar` bo'limi. Anime.js uchun rasmiy npm paketini mahalliy papkaga olib, Timer demosini yozish. Yangi DB jadvali kerak emas.

## 5. Xavf va uni qoplash
Xavflar: path traversal, xavfli URL sxemalari, maxfiy kalitlarning logga tushishi, klon papkasini noto'g'ri o'chirish. Qoplash: faqat `https://`, `resolve_safe_path()`, symlink tekshiruvi, `check=True` va loglarda faqat xato turi, hech qanday token yo'q. Global git/auth/MCP o'zgartirilmaydi, `npx rea-agents setup` chaqirilmaydi.

## 6. Tashqi manbalar
Anime.js rasmiy hujjatlari va GitHub repo, git clone hujjatlari, OWASP/SSRF/MDN URL, pytest/FastAPI/Playwright/Next.js hujjatlari o'qildi. Manbalar `MANBALAR.md` da.

## 7. Tayyorlik mezonlari
`https://github.com/morluto/rea.git` haqiqatdan klonlanadi, HEAD saqlanadi, ro'yxat/ochish/o'chirish ishlaydi; Anime.js oflayn paket + Timer demo bor; `pytest`, `compileall`, `doctor`, `tsc`, `lint`, `build` yashil; API/WEB 200; `gate.py verify` OK; faqat ko'zlangan fayllar o'zgargan.

## 8. Kamchiliklar va ularni qoplash
yetishmaydi: mavjud klonlash kodi -> qanday olaman: acquisition.py va workspace_manager ni o'qidim -> holat: haqiqiy klonlash yo'qligi tasdiqlandi
yetishmaydi: Anime.js Timer API tafsiloti -> qanday olaman: rasmiy animejs.com/documentation/timer sahifasini o'qidim -> holat: createTimer va metodlar ro'yxati olindi
yetishmaydi: xavfsiz klonlash chegaralari -> qanday olaman: OWASP, MDN URL va git hujjatlarini o'qidim -> holat: https-only va resolve_safe_path qaror qilindi
