# MIYALAR (multi-miya tekshiruvi)

## 1. Arxitektor

Muammolar: video va Figma yo'llari aslida mavjud kuchli modullarga ulanmagan; DEEPSEARCH rejim sifatida yo'q; report endpoint ID turini noto'g'ri uzatadi. Tavsiya: to'rt yo'nalishni ham mavjud modullar ustiga qayta ulash, yangi arxitektura yaratmaslik.

## 2. Skeptik

Muammolar: "testlar yashil" degan da'vo foydalanuvchi kuzatgan muammoni isbotlamaydi; deepx timeout testi real vaqt talab qiladi; Figma va GitHub tokenlari yo'q. Tavsiya: har bir tuzatishga real yoki mock repro dalil va regressiya testi qo'shish, token yo'qligini halol xato qilish.

## 3. Xavfsizlik

Muammolar: tokenlarni log yoki natijaga yozish xavfi; video kirish yo'li foydalanuvchi matnidan keladi; GitHub 401 ni yutish. Tavsiya: token faqat env, yo'llar workspace ichida tekshiriladi, 401 va boshqa xatolar aniq qaytariladi.

## 4. Foydalanuvchi va UX

Muammolar: foydalanuvchi noto'g'ri MP4, noto'g'ri Figma ma'lumoti va "Vazifa topilmadi" xabarini ko'radi; deepx 4 daqiqa osilib qoladi. Tavsiya: natijada haqiqiy fayl yo'li, aniq FAIL sababi va rejim holati ko'rinadigan bo'lishi.

## 5. Tester

Muammolar: eski testlar sun'iy video va hardcode Figma natijasini qabul qiladi; report uchun raqamli ID testi yo'q; sekin swarm uchun timeout testi yo'q. Tavsiya: haqiqiy kichik klip, mock Figma REST, mock sekin agent va raqamli ID bo'yicha yangi testlar qo'shish.

## 6. Qaror

Muammolar: kelishmovchilik yo'q: barcha miyalarning asosiy xavoti bir xil — kod yo'qlarini matn bilan yashirish. Tavsiyalar qabul qilindi: rejaga qattiq timeout, halol xato, real artefakt testlari va token xavfsizligi kiritildi. Foydalanuvchiga qoldiriladigan savol yo'q; aniq misol va asosiy tuzatishlar uning so'zlaridan olingan.
