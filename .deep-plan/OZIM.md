# O'ZIM

## 1. Bu ishni qilish uchun menda hozir nima yetishmaydi?

Tool'larning haqiqiy bajarilish mexanizmi haqida to'liq tasavvur yetishmaydi: qaysi tool qayerda chaqiriladi, kim ruxsat beradi, dalil qayerdan keladi. Shu sabab avval kodni o'qib, haqiqiy yugurish orqali dalil oldim: `check_goal '{}'` eski screenshot bilan PASS qaytardi.

## 2. Mutaxassis darajasiga yetish uchun nimani bilishim yoki ishlatishim kerak?

Subagent modelini rasmiy manbalardan o'qidim: alohida kontekst, aniq tool ruxsati, qisqa natija. Tool tavsiflari va soni model kontekstiga ta'sir qilishini bilishim kerak. Ichki koddagi `security_guard.get_allowed_tools`, `tool_registry`, `cli_runner` va `tools.py` o'rtasidagi bog'lanishni tushunishim shart.

## 3. Unumdorligimni qanday oshiraman (tayyor skill, MCP, kutubxona, skript)?

`deep-plan` darvozasi va uning `gate.py` skripti, mavjud pytest testlari, `python tools.py --help` katalogi, `backend/tool_registry.py` va Playwright tekshiruvlaridan foydalanaman. Yangi kutubxona yoki global MCP o'rnatmayman.

## 4. Bu loyiha uchun o'zim nimalarni avtomatlashtira olaman?

Tool katalogini qo'lda yozish o'rniga `tool_registry.py` va `security_guard` dan generatsiya qilaman; ruxsat tekshiruvini bitta funksiyaga jamlab, barcha tool'larga qo'llayman; dalil yangiligi testini regression test sifatida qo'shaman.

## 5. Jonsiz, yoqimsiz natijadan qanday qochaman? (rangsiz, animatsiyasiz oddiy 2D sayt, yomon UI)

Bu vazifa UI chiroyliligi haqida emas: sifat o'lchovi — haqiqiy dalil va to'g'ri rad etish. Shuning uchun PASS/FAIL natijalarini aniq ko'rsataman, eski fayl bilan yalgan PASS bermayman va foydalanuvchiga qaysi tool ishlayotganini ko'rsatadigan katalog chiqaraman.

## 6. Berilgan ishni qanday qilib to'liq va sifatli yetkazaman?

Avval katalog, keyin ruxsat darvozasi, keyin dalil tekshiruvi, keyin yo'riqnomaga kiritish va har biri uchun test. Har qadamda haqiqiy buyruq chiqishini olaman; xato chiqsa ildiz sababini topib, DEBUG.md ga yozaman.

## 7. Qaysi joyda foydalanuvchi yordami yoki ruxsati shart, qaysi joyda mustaqil ishlay olaman?

Reja va yondashuv foydalanuvchi tasdiqlashi shart (deep-plan/brainstorming darvozasi). Global o'rnatish, auth yoki MCP sozlamalariga tegish talab qilinganda ruxsat so'rayman. Loyiha ichidagi kod, test va hujjat o'zgarishlarini mustaqil bajaraman.

## 8. Kamchiliklar va ularni qoplash

yetishmaydi: tool'larning to'liq ro'yxati va chaqiruv yo'li -> qanday olaman: role.md, tool_registry.py va `python tools.py --help` ni solishtirdim -> holat: katalog generatsiya qilish rejalashtirildi
yetishmaydi: ruxsatni bajaruvchi tomonda tekshirish -> qanday olaman: `cli_runner` env va `tools.py` main ni o'qidim, `verify_tool_access` borligini aniqladim -> holat: env uzatish va chaqirish qo'shiladi
yetishmaydi: dalil yangiligi -> qanday olaman: `tool_check_goal` ni haqiqiy chaqirib eski `latest.png` PASS olganini tasdiqladim -> holat: mtime+mazmun tekshiruvi qo'shiladi
yetishmaydi: asosiy agentga to'liq yo'riqnomada tool nomlari -> qanday olaman: `_studio_guide_md` va AGENTS.md generatsiyasini o'qidim -> holat: katalog havolasi qo'shiladi
