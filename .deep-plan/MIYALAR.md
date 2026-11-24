# MIYALAR (multi-miya tekshiruvi)

## 1. Arxitektor

Muammolar: katalog, ruxsat, dalil tekshiruvi va UI alohida-alohida yaxshilangan, lekin ular bitta "natija shartnomasi"ga bog'lanmagan; `cli_runner` va `tools.py` o'rtasida vazifa konteksti faqat qisman (`CONDUIT_AGENT`, `CONDUIT_TASK_STARTED_AT`) uzatiladi. Bu sifat mezoni ikki joyda turlicha talqin qilinishiga yo'l qo'yadi. Tavsiya: bitta dalil kontrakti (captured_at, artifact_path, bytes, criteria) yagona manba sifatida qo'llanilsin; REJA 2-4-qadamlariga kiritildi.

## 2. Skeptik

Muammolar: foydalanuvchi konkret misol bermadi, "yomon" degan so'zni biz o'z dalillarimiz bilan talqin qilyapmiz; eski dalil PASS muammosi allaqachon tuzatilgan bo'lsa, bu reja takroriy ish bo'lib qolishi mumkin. Ikkinchi xavf: qayta urinishlar sifatni yaxshilamasdan token sarflaydi. Tavsiya: avval mavjud testlar bilan "tuzatilganmi yoki yo'qmi" ni tasdiqlash; qayta urinish chegarasi 2 va log majburiy; REJA 1 va 3-qadamlariga kiritildi.

## 3. Xavfsizlik

Muammolar: agentga yuborilgan FAIL sababi ichiga ishonchsiz tool chiqishi qo'shilsa, u keyingi qadamda buyruq sifatida talqin qilinishi mumkin; qayta urinishlar ruxsat darvozasini aylanib o'tishga imkon berishi mumkin. Tavsiya: ruxsat har urinishda qayta tekshirilsin, tool chiqishi faqat ma'lumot sifatida qaytarilsin, maxfiy qiymatlar loglanmasin; REJA 2-3-qadamlariga kiritildi.

## 4. Foydalanuvchi va UX

Muammolar: foydalanuvchi "ishlaydi" degan yashil holatni ko'rib, aslida eski yoki-noto'g'ri artefakt ko'rsatilishini sezmaydi; FAIL sababi ko'rinmasa, u yana "yomon ish" deb baholaydi. Tavsiya: UI yoki kamida hisobotda PASS/FAIL sababi va artefakt yo'li/qachan yaratilgani ko'rsinsin; REJA 4-qadamiga kiritildi.

## 5. Tester

Muammolar: faqat "fayl bor" testi etarli emas; eski fayl mtime bilan ajratilishi, bo'sh fayl, noto'g'ri tur va ruxsatsiz chaqiruv alohida sinovlari kerak. Ikkinchi muammo: real `conduit run` ishlatilmasa, testlar yashil bo'lib, foydalanuvchi ko'radigan oqim sinovdan qoladi. Tavsiya: unit testlarga qo'shimcha bitta real vazifa E2E va natijani ko'z bilan tekshirish; REJA 2 va 4-qadamlariga kiritildi.

## 6. Qaror

Kelishmovchiliklar: Skeptik bu rejani takroriy deb hisobladi; Arxitektor esa zaifliklar hali bitta shartnomaga bog'lanmaganligini ko'rsatdi. Qaror: takroriy kod yozmaymiz, avval mavjud tuzatishlarni test bilan tasdiqlaymiz (REJA 1), keyin faqat yetishmayotgan qismlarni qo'shamiz. Rad etildi: yangi MCP server, global config o'zgarishi, cheksiz retry, faqat promptga tayanish. Foydalanuvchiga qoldirilgan savol: hali konkret "yomon natija" misoli yo'q; u paydo bo'lsa, qabul mezonlari shunga qarab qayta tasdiqlanadi. Boshqa ochiq savol yo'q, chunki foydalanuvchi umumiy yondashuvni tanladi.
