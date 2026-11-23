# LOYIHA

## 1. MVP talablari nima?

To'liq klonlash rejimi: HTTPS GitHub URL'ni tekshirib, `git clone --depth 1` bilan loyiha ichidagi `clones/` papkaga klonlash, ro'yxat/holat/log, qayta yangilash va o'chirish. Shuningdek Anime.js v4 to'liq kutubxonasi (Timer, SVG, WAAPI, Easings, Utilities) + mahalliy demo `vendor/libraries/animejs/` ichida, CDN'siz. Hech qanday global git/auth/MCP sozlamasi o'zgartirilmaydi, `npx rea-agents setup` chaqirilmaydi.

## 2. Foydalanuvchi aniq nima xohlaydi?

Foydalanuvchi `minimal clone amas butunlay clonlash rejimini qosh` dedi va ikkita aniq manzil berdi: `https://github.com/morluto/rea.git` hamda `https://animejs.com/documentation/timer`. U animatsiya va shunga o'xshash narsalarni "butunlay kutubxona qilib studio ga yuklab qoyish"ni xohlaydi. Ya'ni haqiqiy klonlash va oflayn kutubxona, stub emas. U `1` deb to'liq menejer + oflayn kutubxona yondashuvini tanladi va keyin `ha` deb tasdiqladi.

## 3. Qismlar, oqim va eng kichik ishlaydigan qism

Oqim: UI `Klonalar` bo'limi → `POST /api/clones` → `backend/clone_manager.py` URL validatsiyasi → `subprocess.run(['git','clone','--depth','1',...])` → `clones/registry.json` + WS progress → frontend ro'yxat. Anime.js: `npm pack animejs@4` yoki `git clone --depth 1 https://github.com/juliangarnier/anime` orqali `vendor/libraries/animejs/` ga import, keyin mahalliy demo. Eng kichik ishlaydigan qism: bitta URL uchun haqiqiy klonlash + ro'yxat ko'rsatish.

## 4. Eng qisqa to'g'ri yechim

Yangi DB jadvali kiritmaymiz: registry JSON yetarli. `backend/workspace_manager.py::resolve_safe_path()` bilan yo'l xavfsizligi, `shutil.which('git')` bilan mavjudlik, shell'siz subprocess. `backend/tools.py::tool_run_process()` ishlatilmaydi (shell=True, fire-and-forget). Xatolar loglanadi va UI'ga ko'rinadi.

## 5. O'xshash mahsulotlar va ustunliklar

GitHub Desktop va VS Code built-in Git klonlashni qo'llab-quvvatlaydi, lekin studiya ichida agentlar bilan bog'lanmaydi. **TAKLIF** (tasdiqlanmaguncha qo'shilmaydi): klonlangan repo'ni subagent workspace sifatida bog'lash. Hozirgi talab: mustaqil klon menejeri va oflayn Anime.js kutubxonasi.

## 6. Xavfsizlik

Faqat `https://` sxemasi; `file://`, `ssh://`, `javascript:` rad etiladi. `clones/` ichidagi yo'l `resolve_safe_path()` bilan tekshiriladi, path traversal va symlink chiqishi taqiqlanadi. Komanda massiv bilan, shell'siz bajariladi. Maxfiy kalitlar loglanmaydi. Global konfiguratsiya/auth/MCP o'zgarishsiz.

## 7. Tayyorlik mezonlari

`real clone` API bilan morluto/rea klonlanadi, HEAD saqlanadi; Anime.js oflayn paket + Timer demo ishlaydi; `pytest`, `compileall`, `doctor`, `tsc`, `lint`, `build` yashil; API/WEB 200; `gate.py verify` OK; faqat ko'zlangan fayllar o'zgargan; lokal commit (push yo'q).
