# SKANER

Avtomatik faktlar `gate.py scan` dan. Pastdagi bo'limlarni agent o'zi kodni o'qib to'ldiradi.

<!-- AUTO:START -->
## Avtomatik faktlar

- Fayllar (skaner qilingan): 815
- Tillar (fayl soni / qator): .py 116/20502, .tsx 24/8648, .ts 4/520, .js 3/78, .sh 1/72, .css 1/276
- Manifest va sozlama fayllari: .gitignore, README.md, backend\requirements.txt, frontend\package.json, frontend\tsconfig.json
- Kirish nuqtalari (taxminiy): backend\main.py
- Eng katta fayllar: backend\main.py (1549), backend\database.py (1444), backend\engine\cli_runner.py (1432), frontend\src\components\Window2Browser.tsx (1006), backend\engine\kernel.py (985)
- Test fayllari: 37
- CI (.github/workflows): bor
- Git: oxirgi commit: 95afdc3 docs: mark final deep-plan gate steps complete; o'zgartirilgan fayllar: 1
- TODO/FIXME/HACK/XXX belgilari: 0
- MAXFIY QIYMAT GUMONI: 4 ta (qiymat ko'rsatilmaydi):
  - API kalit (sk-...): backend\inspector_executor.py:80
  - API kalit (sk-...): backend\inspector_executor.py:82
  - API kalit (sk-...): backend\tests\test_security.py:49
  - API kalit (sk-...): backend\tests\test_security.py:51
- Xavfli naqshlar (qo'lda tekshirish kerak):
  - jim except (xatoni yutadi): 30 ta, masalan conduit.py:53, conduit.py:341, conduit.py:475
  - eval/exec: 6 ta, masalan backend\live_browser.py:82, backend\live_browser.py:85, backend\live_browser_session.py:86
  - shell=True / os.system: 5 ta, masalan .opencode\skills\webapp-testing\scripts\with_server.py:68, .opencode\skills\webapp-testing\scripts\with_server.py:71, backend\app_adapter.py:139
  - SQL satrni birlashtirish: 5 ta, masalan backend\database.py:1420, backend\pipeline.py:132, backend\pipeline.py:146
  - innerHTML / dangerouslySetInnerHTML: 1 ta, masalan frontend\src\components\Window1Terminal.tsx:130
<!-- AUTO:END -->

## 1. Tuzilma va asosiy oqim

Yangi xususiyat uchun asosiy oqim: foydalanuvchi `Window5Workspace.tsx` dagi `Klonalar` bo'limida HTTPS Git manzilini kiritadi; frontend `POST /api/clones` ga yuboradi; `backend/main.py` `clone_manager.validate_git_url` bilan sxemani tekshiradi va `clone_manager.clone_repository` orqali `subprocess.run([...], shell=False, check=True, capture_output=True, text=True)` chaqiradi; klon `clones/<id>/` ichiga yoziladi, `clones/registry.json` ga id, url, commit pin, holat va log saqlanadi; `GET /api/clones` ro'yxatni, `DELETE /api/clones/{id}` esa xavfsiz o'chirishni bajaradi. Yo'llar `workspace_manager.resolve_safe_path()` va symlink tekshiruvi bilan himoyalanadi. Anime.js kutubxonasi `vendor/libraries/animejs/` ichiga mahalliy npm paket sifatida o'rnatiladi, Timer/SVG/WAAPI/Easings bo'yicha hujjat va mahalliy demo yaratiladi, CDN ishlatilmaydi.

## 2. Zaif va xavfli joylar

Avtomatik skanerdagi 4 ta `sk-...` gumoni qizil chizish testlaridagi fixture'lar, haqiqiy kalit emas. 30 ta jim except, 6 eval/exec, 5 shell=True, 5 SQL satr birlashtirish va 1 innerHTML (xterm ichki renderi) mavjud, ammo ular yangi klon xususiyatining doirasiga kirmaydi; yangi kodda ular qo'llanilmaydi. Xavflar: noto'g'ri URL sxemasi (`file://`, `ssh://`, `javascript:`), `../` bilan yo'l chiqishi, noto'g'ri papkani o'chirish, maxfiy ma'lumotning logga tushishi. Himoya: faqat `https://`, `resolve_safe_path`, symlink tekshiruvi, `shell=False`, `check=True`, xato turini loglash, global git/auth/MCP ga tegmaslik va `npx rea-agents setup` ni ishga tushirmaslik.

## 3. Test va sifat holati

Joriy holat: oldingi vazifa uchun `pytest backend/tests -q` natijasi `148 passed, 2 skipped, 4 warnings in 283.02s`, `compileall 0`, `doctor 0 FAIL`, `tsc 0`, `build 0`, `lint 0`, API/WEB 200 edi. Yangi xususiyat uchun testlar yozilgach natijalar ushbu bo'limga haqiqiy chiqish bilan qo'shiladi: URL validatsiyasi, klon yaratish/ro'yxat/o'chirish, xato holatlari, Anime.js oflayn fayllari mavjudligi va UI tekshiruvi.

## 4. Bilmaydigan va tekshirilmagan joylar

Barcha 815 fayl to'liq o'qilmadi; global git config/auth va MCP sozlamalari o'zgartirilmadi hamda sinab ko'rilmadi; ixtiyoriy 7 CLI o'rnatilmagan; boshqa AI agentlarning uzoq muddatli TUI ishi sinab ko'rilmadi; `npm audit` dagi postcss/next zaifliklari Next 16 ga major migratsiyagacha kechiktirildi (`docs/SKILLS_AND_AUDIT.md`). Shaxsiy repository yoki token bilan klonlash sinab ko'rilmadi — faqat ochiq HTTPS repositorylar mo'ljallangan.
