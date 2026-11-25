# MIYALAR (multi-miya tekshiruvi)

## 1. Arxitektor: tuzilma, bog'lanish, keyin kengaytirish. Reja qayerda noto'g'ri qurilgan?

Muammolar: `parse_visual_spec` va `build_scene_script_from_goal` ikki joyda (app_adapter va tools) ishlatiladi; kelajakda yangi shakl qo'shish ikki joyga ta'sir qiladi. Sculptor va painter alohida shoxlar, lekin bir xil spec dan foydalanadi.
Tavsiya: spec lug'atini markaziy joyda saqlash (hozircha app_adapter), `cli_runner` faqat undan foydalanadi; yangi shakl qo'shishda ikki test yangilanadi.

## 2. Skeptik: reja qayerda buziladi? Nimani o'tkazib yubordik? Qaysi taxmin tekshirilmagan?

Muammolar: parser faqat o'zbek/ingliz kalit so'zlari va hex ranglarni biladi; «to'q qizil» kabi sifatlar `qizil` sifatida o'qiladi. Render va 2D rasm bir xil ko'rinmaydi: Blender metallik va yorug'lik tufayli boshqacha ko'rinadi.
Tavsiya: bunday hollarda spec matnida `colors` qaytariladi va foydalanuvchi(view) ko'rib tasdiqlaydi; testlarda ranglar soni va matn mavjudligi tekshiriladi, piksel aniqligi emas.

## 3. Xavfsizlik: hujum yuzasi, maxfiy ma'lumot, ruxsatlar. Qanday suiiste'mol qilish mumkin?

Muammolar: foydalanuvchi matni `repr()` bilan skriptga kiritiladi, lekin juda uzun matn render vaqtida katta yozuv yaratishi mumkin. HTML hisobot oldin XSS xavfiga ega edi.
Tavsiya: matn 60 belgi bilan cheklangan; HTML escape qilingan; global config/auth/MCP tegilmadi. Uzun matn chegarasi test bilan mustahkamlanadi.

## 4. Foydalanuvchi va UX: tushunarlimi, jonlimi, xato holatida nima ko'radi?

Muammolar: oldin foydalanuvchi «yomon natija» deganda faqat fayl borligini ko'rardi, talab mosligini emas. Yangi render fon va matn hali ham kichik ko'rinishi mumkin.
Tavsiya: artefaktlar galereyada ko'rinadi, `doer_out_summary` da shakl/rang/son/matn ochiq yoziladi; natija yomon bo'lsa foydalanuvchi skrinshot yuborib aniq aytadi.

## 5. Tester: buni qanday sindiraman? Qabul mezoni va chegara holatlari qaysilar?

Muammolar: `ko'k` dagi apostrof matn sifatida o'qilingan; `fon qora` obyekt rangi qo'shib yuborgan; test `metallic` kichik harfini kutgan. Bularning hammasi haqiqiy test xatolari edi.
Tavsiya: testlar qo'shildi: background chiqariladi, faqat ikki qo'shtirnoq matn, `METALLIC = 0.85` kutilyapti, 3 ta shakl va `spec` qaytarilishi tekshiriladi.

## 6. Qaror: kelishmovchiliklar, REJA.md ga kiritilgan o'zgarishlar va foydalanuvchiga qoldirilgan savollar

Kelishmovchilik yo'q: barcha miyalar markaziy spec va real artefakt zarurligiga kelishdi. Rad etilgan variant: tashqi text-to-image modeli — foydalanuvchi ruxsati yo'q va global config o'zgarardi. Foydalanuvchiga savol: yangi til/rang nomlari kerak bo'lsa, ularni aniq yozib bersin.
