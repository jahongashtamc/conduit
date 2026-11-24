# MIYALAR (multi-miya tekshiruvi)

## 1. Arxitektor

Muammolar: E2E natijasi kelmaguncha qaysi qatlam buzilgani noma'lum; test va mahsulot loglari aralashib, noto'g'ri muammo topish xavfi bor. Tavsiya: avval CLI→API→kernel→tools zanjirini real vazifa bilan ajratib ko'rsatish, keyin tuzatish.

## 2. Skeptik

Muammolar: "testlar yashil" deyish foydalanuvchi muammosini isbotlamaydi; Bloklangan vazifalar ko'p, lekin ularning aksariyati test fixture. Tavsiya: har muammoni repro qilish, test kelib chiqishini tekshirish va faqat dalilli muammolarni tuzatish.

## 3. Xavfsizlik

Muammolar: tashqi API xatolari yashirinsa, hisobot noto'g'ri ishonch beradi; maxfiy tokenlar logga tushishi xavfi bor. Tavsiya: 401 kabi xatolarni ochiq ko'rsatish, global config/auth/MCP ga tegmaslik, maxfiy qiymatlarni chiqarmaslik.

## 4. Foydalanuvchi va UX

Muammolar: foydalanuvchi "yomon ishlayapti" desa, qaysi natija yomonligini UI aniq aytmasligi mumkin; PASS/FAIL sababi ko'rinmasa ishonch yo'q. Tavsiya: natija va FAIL sababini hisobot hamda UI da aniq ko'rsatish, soxta preview ishlatmaslik.

## 5. Tester

Muammolar: eski testlar mexanik holatni tekshiradi; sun'iy artefakt bilan PASS olish mumkin; timeout testlari kutilgan xato loglarini qoldiradi. Tavsiya: haqiqiy fayl mavjudligi, mazmun va xato holatlarini tekshiradigan regression testlar qo'shish; kutilgan loglarni izohlash.

## 6. Qaror

Kelishmovchilik: tez tuzatish vs repro kutish. Qaror: repro kutish tanlandi, chunki foydalanuvchi aniq dalil talab qildi. REJA ga qo'shilganlar: real E2E natijasini kutish, test shovqinini ajratish, har tuzatishga regression test va real chaqiruv dalili qo'shish. Foydalanuvchiga yuboriladigan savol yo'q — u 5 soat ishlashni va o'zimiz topishni buyurdi.
