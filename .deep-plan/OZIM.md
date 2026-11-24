# OZIM

## 1. Bu ishni qilish uchun menda hozir nima yetishmaydi?

Foydalanuvchining haqiqiy Figma fayli va tokeni, haqiqiy video kliplari ham yo'q. DeepSearch uchun GitHub tokeni yo'q, shuning uchun 401 keladi. Ammo bu kamchiliklar kodni to'g'ri tuzatishga to'sqinlik qilmaydi: mavjud FFmpeg, mock HTTP va vaqtli testlar bilan mexanizmni isbotlash mumkin.

## 2. Mutaxassis darajasiga yetish uchun nimani bilishim yoki ishlatishim kerak?

FFmpeg concat/trim/setpts/atrim filtrlari, Figma REST endpoint'lari, GitHub search autentifikatsiyasi, asyncio.wait_for va DB ID turlarini bilishim kerak. Bularning hammasi rasmiy manbalardan o'qildi va MANBALAR.md ga yozildi.

## 3. Unumdorligimni qanday oshiraman (tayyor skill, MCP, kutubxona, skript)?

Mavjud `tools.py`, `kernel.py`, `cli_runner.py`, `report_generator.py` va FFmpeg binary ishlataman. Yangi kutubxona yoki global MCP qo'shmayman; testlar uchun `tmp_path` va `unittest.mock` etarli.

## 4. Bu loyiha uchun o'zim nimalarni avtomatlashtira olaman?

Video kirish fayllarini avtomatik topish, FFmpeg buyrug'ini tuzish, Figma xatosini standart `needs_config` javobiga aylantirish, deepx bosqichiga qattiq timeout qo'yish va hisobot ID sini normalizatsiya qilishni avtomatlashtiraman.

## 5. Jonsiz, yoqimsiz natijadan qanday qochaman?

Sun'iy gradient video o'rniga haqiqiy klipdan olingan kadrlar, aniq kesim va audio bilan MP4; hardcode Figma spec o'rniga real yoki halol `needs_config`; soxta `Sertifikatlangan` o'rniga haqiqiy audit natijasi; "Vazifa topilmadi" o'rniga haqiqiy hisobot.

## 6. Berilgan ishni qanday qilib to'liq va sifatli yetkazaman?

Har bir nuqson uchun avval repro dalil, keyin kod tuzatish, keyin regression test va nihoyat to'liq `backend/tests` + doctor/build/do'kon tekshiruvi. Faqat test yashiligi bilan to'xtamayman, real chaqiruv natijasini ham ko'rsataman.

## 7. Qaysi joyda foydalanuvchi yordami yoki ruxsati shart, qaysi joyda mustaqil ishlay olaman?

Figma va GitHub haqiqiy API chaqiruvi uchun foydalanuvchi tokeni kerak; ularsiz halol xato qaytaraman. Video uchun haqiqiy klip kerak; ularsiz xato qaytaraman. Qolgan barcha kod tuzatish va testlarni mustaqil bajaraman, global config/auth/MCP ga tegmayman.

## 8. Kamchiliklar

yetishmaydi: FIGMA_TOKEN -> qanday olaman: foydalanuvchi o'zi muhitga qo'yadi -> holat: yo'q, needs_config test bilan qoplanadi. yetishmaydi: GITHUB_TOKEN -> qanday olaman: foydalanuvchi qo'yadi yoki 401 halol ko'rsatiladi -> holat: yo'q, 401 xato sifatida qaytariladi. yetishmaydi: haqiqiy video klipi -> qanday olaman: FFmpeg bilan lokal test klipi yarataman -> holat: test bilan qoplanadi.
