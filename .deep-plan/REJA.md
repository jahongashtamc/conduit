# REJA

## 1. Real E2E audit va muammo tasdiqlash

Nima qilinadi va qaysi fayllar: ishga tushirilgan `e2e5h.py` natijasini o'qish; `backend/main.py`, `backend/engine/kernel.py`, `backend/engine/cli_runner.py`, `backend/tools.py` va DB loglarini solishtirish; har muammo uchun aniq alomat, sabab va dalil yozish.

Tugash sharti: kamida bitta real muammo E2E yoki log bilan tasdiqlangan; test fixture'laridan kelgan shovqin mahsulot muammosi deb olinmagan; `.deep-plan/DEBUG.md` da dalil bor.

Eng sodda variant: yangi fayl yaratmay, mavjud E2E skripti va DB so'rovlari bilan ishlash; faqat tasdiqlangan muammolarni ro'yxatga olish.

## 2. Ildiz sabablarni tuzatish

Nima qilinadi va qaysi fayllar: faqat tasdiqlangan muammolar bo'yicha `backend/tools.py`, `backend/engine/cli_runner.py`, `backend/engine/kernel.py`, `backend/main.py` yoki `backend/report_generator.py` ga minimal o'zgartirish kiritish.

Tugash sharti: har tuzatishda alomat yo'qoladi va oldingi xatti-harakat qaytmaydi; xatolar logda ko'rinadi; hech qanday soxta PASS qolmaydi.

Eng sodda variant: mavjud funksiyalarni kengaytirish; yangi framework, MCP yoki global konfiguratsiya qo'shmaslik.

## 3. Regression testlari qo'shish

Nima qilinadi va qaysi fayllar: `backend/tests/` ichiga har tuzatish uchun bitta aniq test qo'shish; fake artefakt, timeout va xato holatlarini ham qamrab olish.

Tugash sharti: har yangi test tuzatishdan oldin yiqiladi yoki muammoni fosh qiladi; tuzatishdan keyin o'tadi; `pytest backend/tests -q` yashil.

Eng sodda variant: mavjud test fayllariga qisqa test funksiyalari qo'shish; yangi test infrastrukturasi yaratmaslik.

## 4. Real chaqiruv va UI tekshiruvi

Nima qilinadi va qaysi fayllar: `conduit run`, `conduit status`, `conduit result`, API va Playwright orqali haqiqiy natija olish; artefakt fayli va hisobot matnini tekshirish.

Tugash sharti: kamida bitta vazifa haqiqiy artefakt bilan PASS yoki aniq sabab bilan FAIL; UI da galereya/hisobot ko'rinadi; konsol xatosi yo'q.

Eng sodda variant: mavjud E2E va Playwright skriptlarini qayta ishlatish; qo'lda tasdiqlash.

## 5. Hujjat va darvoza

Nima qilinadi va qaysi fayllar: `.deep-plan/TEST.md`, `DEBUG.md`, `PROGRESS.md`, `DECISIONS.md`, `.agents/time-log.md` yangilash; `gate.py verify` ishga tushirish.

Tugash sharti: barcha test buyruqlari haqiqiy chiqish bilan yozilgan; topilgan xatolar ildiz sababi bilan DEBUG da; `verify OK`.

Eng sodda variant: mavjud hujjatlarga fakt qo'shish; shablon va ortiqcha matn yozmaslik.

## 6. Integratsiya

Nima qilinadi va qaysi fayllar: `git diff --check`, alohida branch, commit va `main` ga `--no-ff` merge; `git status` tozaligini tasdiqlash.

Tugash sharti: faqat rejadagi fayllar o'zgargan; commit va merge muvaffaqiyatli; push foydalanuvchi ruxsatisiz amalga oshirilmaydi.

Eng sodda variant: oldingi vazifalardagi kabi per-command git identity ishlatish, global config o'zgartirmaslik.

TASDIQ: HA
