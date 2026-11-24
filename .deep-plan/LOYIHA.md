# LOYIHA

## 1. MVP talablari nima?

5 soatlik rejimda asosiy maqsad — foydalanuvchi ko'rgan haqiqiy muammolarni topib, ildiz sababini tuzatish va dalil keltirish. Eng kichik talablar: (1) real E2E vazifalari ishga tushib, haqiqiy artefakt yaratishi; (2) har bir FAIL sababi log va hisobotda aniq ko'rinishi; (3) sslash/xatoliklar yashirinmasligi; (4) regression testlari qo'shish; (5) test/doctor/build/gate yashil bo'lishi. Manbalar MANBALAR.md da.

## 2. Foydalanuvchi aynan nimani xohlaydi va qanday ishlashi kerak?

Foydalanuvchi: `5 soatli ish rejimiga ot va real muammolarni top hal qil dalillar keltir`. U tez hisobot emas, real tekshiruv va ishlaydigan tuzatish xohlaydi. Kutilayotgan oqim: audit → muammoni repro qilish → ildiz sabab → kod tuzatish → regression test → real chaqiruv bilan tasdiqlash → dalillar bilan hisobot. Faqat "testlar yashil" deyish qabul qilinmaydi.

## 3. Qismlar, oqim va eng kichik ishlaydigan qism

Oqim: `conduit.py` CLI → `backend/main.py` API → `backend/engine/kernel.py` va `cli_runner.py` → `backend/tools.py` / `app_adapter.py` → `backend/database.py` → frontend. Eng kichik ishlaydigan qism: bitta real vazifa `conduit run` orqali bajarilib, PASS bo'lsa haqiqiy artefakt yo'li qaytaradi; FAIL bo'lsa aniq sabab ko'rinadi. Bu ishlamasa, qolgan barcha funksiyalar shartli.

## 4. Har funksiya uchun eng qisqa to'g'ri yechim

Yangi MCP server, yangi framework yoki global konfiguratsiya qo'shmaymiz. Mavjud `tools.py`, `cli_runner.py`, `kernel.py` va `report_generator.py` ichida tuzatamiz. Tuzatishlar faqat repro qilingan muammolar bo'yicha bo'ladi; taxmin bilan kod o'zgartirilmaydi. Har tuzatishga regression test va real chaqiruv dalili qo'shish shart.

## 5. O'xshash mahsulotlar va ustunliklar

Claude Code subagentlari o'z konteksti va cheklangan tool'lari bilan ishlaydi; OpenAI function calling tool tavsifi va natijasini modelga qaytarishni talab qiladi; OpenCode ham tool'lar bilan ishlaydi. Conduit ustunligi — bularni bitta universal CLI/API orqali taqdim etish. **TAKLIF** (tasdiqlanmaguncha qo'shilmaydi): qo'shimcha evaluator yoki tashqi xizmat emas, faqat mavjud zanjirni mustahkamlash.

## 6. Kiberxavfsizlik

Foydalanuvchining global config/auth/MCP sozlamalariga tegmaymiz. Tool ruxsatlari `security_guard` va `CONDUIT_AGENT` orqali bajarish vaqtida tekshiriladi. Maxfiy kalitlar log va hisobotlarga yozilmaydi. Har qanday tashqi API xatosi (401 kabi) yashirilmay, aniq ko'rsatiladi. E2E testlari lokal resurslarga qaratiladi.

## 7. Tayyorlik mezonlari

`pytest backend/tests -q` yashil; `compileall`, `doctor`, `tsc`, `build`, `lint` 0; kamida bitta real E2E vazifasi haqiqiy artefakt bilan PASS; FAIL holatida sabab aniq; UI hisobot va galereya ishlaydi; `gate.py verify OK`; git toza va faqat rejadagi fayllar o'zgargan. Foydalanuvchi ko'rgan muammolar bo'yicha dalil va ochiq qolganlar ro'yxati hisobotda bo'ladi.
