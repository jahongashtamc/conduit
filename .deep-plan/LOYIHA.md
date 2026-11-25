# LOYIHA

## 1. MVP talablari nima?

Asosiy muammo: so'ralgan natija o'rniga umumiy kub, tasodifiy grid yoki sintetik gradient chiqar edi. MVP: (1) vazifa matnidan rang, shakl, son, matn, material va fon olish; (2) Blender sahnasi va 2D rasm shu parametrlardan qurilishi; (3) sculptor/painter yo'nalishlari hardcoded qiymatlarni ishlatmasligi; (4) natijada `spec` ko'rinishi va artefakt haqiqiy bo'lishi; (5) ko'z bilan tekshiruv va regression testlar. Tekshiruv: `2 ta qizil kub + 1 ko'k shar, NEXUS matni, qora fon` talabi bilan yaratilgan PNG va render shu ko'rinishda bo'lishi.

## 2. Foydalanuvchi aynan nimani xohlaydi va qanday ishlashi kerak?

Foydalanuvchi: `hali ham yomon natiljalar` — testlar yashil bo'lsa ham chiqayotgan rasmlar va modellar uning talabiga javob bermaydi. Kutilayotgan oqim: foydalanuvchi «3 ta qizil shar» desa artefaktda aynan 3 ta qizil shar bo'lishi; «NEXUS» yoz desa matn ko'rinishi; fon qora desa fon qora/tungi ko'rinishi. Agent natijani faqat fayl mavjudligi bilan emas, talabga mosligi bilan tasdiqlashi kerak.

## 3. Qismlar, oqim va eng kichik ishlaydigan qism

Oqim: `task_goal` → `app_adapter.parse_visual_spec()` → `build_scene_script_from_goal()` / `tools.tool_gen_image()` → artefakt → `static/screenshots` → UI. Eng kichik ishlaydigan qism: bitta aniq talab bilan 2D rasm va bitta Blender render; ikkalasi ham ko'zga mos kelgach, katta sinov. Bu ishlamasa UI chiroyliligining ahamiyati yo'q.

## 4. Har funksiya uchun eng qisqa to'g'ri yechim

Yangi kutubxona yoki tashqi AI olamiz yo'q. Mavjud PIL va Blender/Cycles ishlatiladi; parser oddiy lug'at va regexlar bilan kengaytirildi. `cli_runner` allaqachon bor bo'lgan `doer` shoxlariga spec qiymatlarini uzatadi. Deterministik seed saqlanadi: bir xil talab = bir xil natija, lekin endi tasodifiy grid emas.

## 5. O'xshash mahsulotlar va ustunliklar

Tijorat image generatorlari tabiiy tilni tushunadi, lekin lokal, oflayn va tekshiriladigan emas. Conduit ustunligi: natija deterministik, spec qaytariladi, artefakt galereyada va hisobot ko'rinadi; global hisob/auth talab qilinmaydi. **TAKLIF** (tasdiqlanmaguncha qo'shilmaydi): UI da talab parametrlarini alohida ko'rsatish.

## 6. Kiberxavfsizlik

Foydalanuvchi matni kod sifatida bajarilmaydi; faqat rang/shakl/matn sifatida o'qiladi. Matn `repr()` bilan skriptga kiritiladi va HTML hisobotda escape qilinadi. Fayl yo'llari mavjudlik va hajm bo'yicha tekshiriladi. Global config/auth/MCP o'zgartirilmadi; xatolar loglanadi, jim yutilmaydi.

## 7. Tayyorlik mezonlari

Talab bo'yicha yaratilgan rasm va render ko'z bilan mos: ranglar, shakllar, son, matn va fon to'g'ri. Yangi testlar o'tadi, to'liq `pytest backend/tests -q` yashil, `compileall/doctor/tsc/build/lint 0`, UI 0 gap, `gate.py verify OK`. Faqat rejadagi fayllar o'zgargan bo'lishi kerak.
