# OZIM

## 1. Bu ishni qilish uchun menda hozir nima yetishmaydi?

Foydalanuvchi ko'rgan muammoning aniq qaysi E2E holatida yuz berishini hali to'liq bilmayman. Shuning uchun avval real vazifalar va loglar asosida repro qilishim kerak. E2E skripti ishga tushirildi, natijasini kutib, taxmin qilmay tahlil qilaman.

## 2. Mutaxassis darajasiga yetish uchun nimani bilishim yoki ishlatishim kerak?

Conduitning CLI, API, kernel, subagent va tool qatlamlarining bog'lanishini bilishim kerak. Rasmiy manbalardan agent mezonlari va tool interfeysi talablarini o'qidim. Ichki kodni o'qib, har muammoni qaysi qatlamda ekanini aniqlayman.

## 3. Unumdorligimni qanday oshiraman?

Mavjud E2E skripti, pytest, doctor, Playwright va DB so'rovlaridan foydalanaman. Har bir tuzatishdan oldin eng arzon testni ishga tushuraman. Katta o'zgartirish o'rniga bitta ildiz sababni tuzatib, darhol tekshiraman.

## 4. Bu loyiha uchun o'zim nimalarni avtomatlashtira olaman?

E2E vazifa yaratish, holatni so'rash, loglarni o'qish va artefaktlarni tekshirish skriptlarini ishlataman. Regression testlari avtomatik ishlaydi. Qo'lda faqat natijani o'qish va noaniq holatlarni izohlash qoladi.

## 5. Jonsiz, yoqimsiz natijadan qanday qochaman?

Faqat sun'iy yoki hardcode natija qabul qilmayman: video haqiqiy klipdan, Figma real API ma'lumotidan, hisobot real iqtiboslardan bo'lishi kerak. UI da bo'sh hisobot yoki soxta PASS ko'rsatish jonsiz natija hisoblanadi. Har natijada haqiqiy fayl yo'li va sabab bo'lishi shart.

## 6. Berilgan ishni qanday qilib to'liq va sifatli yetkazaman?

Har muammoni repro qilish → ildiz sabab → tuzatish → regression test → real chaqiruv → dalil tartibida bajaraman. Testlar yashil bo'lsa ham foydalanuvchi natijasini o'zim tekshiraman. Oxirida aniq hisobot va ochiq qolganlar ro'yxatini beraman.

## 7. Qaysi joyda foydalanuvchi yordami yoki ruxsati shart?

Global config/auth/MCP, tashqi API kalitlari, kuchli o'chirish yoki push kabi harakatlarda ruxsat shart. Ichki kod, testlar va lokal DB ustida ishlashda mustaqil harakat qilaman. Eski papkadagi boshqa agent sessiyasini o'chirish uchun ham ruxsat kerak.

## 8. Kamchiliklar

yetishmaydi: foydalanuvchi ko'rgan muammoning aniq E2E misoli -> qanday olaman: real vazifa va loglar bilan repro qilaman -> holat: E2E ishga tushirildi, natija kutilmoqda; yetishmaydi: FIGMA_TOKEN va GitHub autentifikatsiyasi -> qanday olaman: mavjud xato xabarlarini halol ko'rsataman, global sozlamaga tegmayman -> holat: xato ochiq ko'rinadi.
