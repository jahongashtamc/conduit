# OZIM

## 1. Bu ishni qilish uchun menda hozir nima yetishmaydi?

Foydalanuvchi aniq misol keltirmadi: qaysi vazifa, qaysi artefakt va qaysi natija yomon ekani aytilmadi. Menda faqat koddagi dalillar bor: eski dalil bilan PASS bo'lgan `check_goal`, kalit so'zga ishonadigan validator, loglardagi eski backend va oldingi audit natijalari. Shuning uchun "taxmin qilib bitta tugmani tuzatish" emas, butun zanjirni obyektiv audit qilish kerak. Yetishmaydigan narsa: foydalanuvchi tomonidan ko'rsatilgan konkret yomon natija; uni so'radim, lekin u umumiy yondashuvni tanladi.

## 2. Mutaxassis darajasiga yetish uchun nimani bilishim yoki ishlatishim kerak?

Agent sifatini baholashda ground truth, evaluator-optimizer, tool tavsifi va ruxsat doirasi muhimligini rasmiy manbalardan o'qidim. Loyihada esa `cli_runner`, `tools.py`, `security_guard`, `tool_registry`, terminal session va testlar qanday bog'langanini o'qib tushundim. Mutaxassislik shu: "PASS" degan so'zga ishonmay, uni qanday dalil bilan olganini tekshirish.

## 3. Unumdorligimni qanday oshiraman (tayyor skill, MCP, kutubxona, skript)?

`deep-plan` darvozasi, mavjud pytest to'plami, `python tools.py list_tools`, `conduit tools --json`, `conduit doctor`, `gate.py check/verify` va Playwright/terminal kuzatuvlaridan foydalanaman. Yangi kutubxona yoki MCP server qo'shmayman: bu vazifa mavjud modullardagi zaif qarorlarni tuzatish. Parallel subagentlar avval ishlamagani uchun ularga qayta tayanmayman; multi-miyani o'zim ketma-ket, mustaqil yozaman.

## 4. Bu loyiha uchun o'zim nimalarni avtomatlashtira olaman?

Avtomatlashtirish: eski/bo'sh/soxta dalil uchun FAIL testlari, yangi artefakt uchun PASS testi, ruxsatsiz tool rad etilishi testi, qayta urinish chegarasi testi va oxirida to'liq `pytest backend/tests -q` + `doctor` + `tsc/build`. Qo'lda qiladigan yagona muhim ish: haqiqiy `conduit run` natijasini ko'z bilan tekshirib, UI'da ko'ringan dalil bilan hisobot dalili bir xil ekanini tasdiqlash.

## 5. Jonsiz, yoqimsiz natijadan qanday qochaman?

Jonsiz natija degani bu yerda "yashil test, lekin foydalanuvchi ko'radigan ish yomon". Buning oldini olish uchun faqat so'zlovchi xabar emas, haqiqiy artefakt (fayl, o'lcham, mtime, preview URL) talab qilaman. FAIL bo'lsa UI'da sabab ko'rinadi, agentga qayta urinish uchun aniq ko'rsatma bor. Real render/3D misolida eski 1920x1080 rasm yangi 960x540 o'rniga chiqib qolgani allaqachon dalil: shuning uchun artefakt yangiligi eng qattiq mezon bo'ladi.

## 6. Berilgan ishni qanday qilib to'liq va sifatli yetkazaman?

Avval darvoza hujjatlarini to'ldiraman, rejani ko'rsatib tasdiq olaman, keyin eng kichik qismdan boshlayman: fail-closed dalil tekshiruvi. Har qadamda test yozaman, xato chiqsa ildiz sababini DEBUG.md ga yozaman. Oxirida haqiqiy buyruqlar chiqishi bilan TEST.md ni to'ldiraman, `gate.py verify` OK bo'lmaguncha "tayyor" demayman. Hisobotda halol ravishda nima tekshirilgani va nima tekshirilmaganini ajrataman.

## 7. Qaysi joyda foydalanuvchi yordami yoki ruxsati shart, qaysi joyda mustaqil ishlay olaman?

Foydalanuvchi ruxsatisiz: kod o'qish, test yozish, mavjud modullarda sifat darvozalarini tuzatish, hujjatlarga yozish, commit qilish (oldingi ish tartibi bo'yicha). Ruxsat shart: global config/auth/MCP ga tegish, boshqa foydalanuvchi agent sessiyasini o'chirish, tashqi CLI o'rnatish, kuchli parallel agent yoki pul sarflaydigan xizmat ishlatish. Foydalanuvchi "umumiy hammasi" deb keng yo'l bergani uchun konkret misol so'ramay, o'z dalillarim bilan ishlayman.

## 8. Kamchiliklar

yetishmaydi: foydalanuvchining konkret yomon natijasi -> qanday olaman: mavjud log, test va artefaktlardan obyektiv dalil yig'aman, kerak bo'lsa hisobotda so'rayman -> holat: obyekt dalillar topildi (eski dalil PASS, kalit so'z validator), ammo foydalanuvchi misoli hali yo'q.
yetishmaydi: barcha vazifa turlari uchun qabul mezonlari -> qanday olaman: mavjud role.md, tool_registry va testlar asosida kichik mezon matritsasi tuzaman -> holat: REJA 1-qadamida.
yetishmaydi: parallel multi-miya agentlari -> qanday olaman: oldingi urinish kesilgani uchun besh miyani ketma-ket mustaqil yozaman -> holat: MIYALAR.md da bajarildi.
