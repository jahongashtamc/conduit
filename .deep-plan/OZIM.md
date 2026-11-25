# OZIM

## 1. Bu ishni qilish uchun menda hozir nima yetishmaydi?

Foydalanuvchi ko'zida natija yomonligini bildiradigan aniq sabab yetishmaydi edi; shuning uchun avval artefaktlarni ochib ko'rdim va umumiy kub/grid ekanini dalil bilan tasdiqladim.

## 2. Mutaxassis darajasiga yetish uchun nimani bilishim yoki ishlatishim kerak?

PIL chizish va Blender Python sahnasini bilishim, rang/shakl/matn parsingini to'g'ri ajratishim va natijani vizual tekshirishim kerak edi. Regexlardagi tillar farqi (qo'shtirnoq va apostrof) alohida sinov talab qildi.

## 3. Unumdorligimni qanday oshiraman (tayyor skill, MCP, kutubxona, skript)?

Mavjud `agent-studio` ko'z ko'rish yondashuvi va Playwright screenshot'dan foydalandim. Yangi kutubxona qo'shmadirim; faqat mavjud PIL/Blender va oldingi E2E skriptlarini qayta ishlatdim.

## 4. Bu loyiha uchun o'zim nimalarni avtomatlashtira olaman?

`parse_visual_spec` va `build_scene_script_from_goal` orqali talab parametrlarini avtomatik olish; testlar rasm va render mazmunini avtomatik tekshiradi. Shuning uchun har yangi talab qo'lda qayta chizilmaydi.

## 5. Jonsiz, yoqimsiz natijadan qanday qochaman? (rangsiz, animatsiyasiz oddiy 2D sayt, yomon UI)

Faqat mavjud fayl emas, ko'z bilan ko'rish: ranglar, son, matn va fon mosligini tekshirdim. 2D rasmda soyali kub/shar va kattaroq markaziy yozuv qo'shildi; 3D dagi metallik va fon rangi talabdan olinadi.

## 6. Berilgan ishni qanday qilib to'liq va sifatli yetkazaman?

Avval repro, keyin ildiz sabab, minimal kod o'zgarishi, real render/image, vizual tekshiruv, to'liq test va hujjatlar. Natijani faqat "test yashil" deb emas, skrinshot bilan tasdiqlayman.

## 7. Qaysi joyda foydalanuvchi yordami yoki ruxsati shart, qaysi joyda mustaqil ishlay olaman?

Uzbekcha/inglizcha rang va shakl so'zlari lug'atida yo'q so'z bo'lsa, foydalanuvchi aytib berishi kerak. Qolgan hamma joyda — kod, test, render va UI tekshiruvi — mustaqil ishlayman. Global config/auth/MCP ga tegmayman.

## 8. Kamchiliklar

yetishmaydi: yangi tillardagi rang nomlari -> qanday olaman: foydalanuvchi yoki rasmiy lug'at -> holat: hozircha faqat o'zbek/ingliz/hex; yetishmaydi: haqiqiy AI text-to-image modeli -> qanday olaman: foydalanuvchi ruxsati bilan qo'shish -> holat: qo'shilmadi, deterministik PIL yetarli; yetishmaydi: vizual quality metric -> qanday olaman: ko'z bilan tekshiruv + test -> holat: bajarildi.
