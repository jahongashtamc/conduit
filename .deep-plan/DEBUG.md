# DEBUG

## 1. Chiqishlar umumiy va talabga mos emas edi

Alomat: foydalanuvchi `hali ham yomon natiljalar` deb aytdi; artefaktlarda umumiy kub, tasodifiy grid va sintetik rang chiziqlari bor edi.
Ildiz sabab: `cli_runner.py` scrollari foydalanuvchi matnini o'qimay, har doim kub/shar yaratadi; `tool_gen_image` hash asosida tasodifiy shakllar chizadi; checker faqat fayl borligini tekshiradi.
Dalil: `workspaces/sculptor/render_snapshot.png` kulrang kub, `workspaces/painter/gen_26225.png` tasodifiy chiziqlar, `latest.png` FFmpeg testsrc kadrlari edi.
Tuzatish: `parse_visual_spec` va `build_scene_script_from_goal` qo'shildi; gen_image va sculptor endi shu spec dan foydalanadi.
Tekshiruv: 2 qizil kub + 1 ko'k shar + NEXUS talabi bilan 2D va 3D artefakt yaratildi, ko'z bilan tasdiqlandi, 3 ta yangi test o'tdi.

## 2. Background rangi obyekt rangiga qo'shilib ketdi

Alomat: `fon qora` deganda qora shar ham paydo bo'lishi mumkin edi.
Ildiz sabab: `parse_visual_spec` barcha rang so'zlarini obyekt ranglari ro'yxatiga qo'yadi, fon esa alohida ajratilmagan.
Dalil: birinchi test `colors` ichida fon rangini ham ko'rsatdi.
Tuzatish: fon avval ajratiladi va uning hex qiymati obyekt ranglaridan chiqariladi.
Tekshiruv: `test_parse_visual_spec_reads_user_requirement` fon `#0F172A` va obyekt ranglari `#DC2626/#2563EB` ekanini tasdiqladi.

## 3. Apostrof matn deb o'qildi

Alomat: `ko'k kub yarat, ustiga "NEXUS"` da matn `k kub yarat, ustiga` bo'lib qoldi.
Ildiz sabab: regex barcha iqtibos belgilarini, jumladan inglizcha apostrofni ham matn boshlanishi deb oldi.
Dalil: birinchi test `text` noto'g'ri qaytardi.
Tuzatish: faqat `"` va guillemetlar matn chegarasi sifatida qabul qilinadi.
Tekshiruv: `text == "NEXUS"` testi o'tdi; render va rasmda ham NEXUS ko'rinadi.

## 4. Blender fon va yorug'lik talabga bog'liq emas edi

Alomat: talabda fon qora bo'lsa ham 3D render kulrang ko'rinardi.
Ildiz sabab: `build_scene_script_from_goal` world background rangini o'rnatmagan; faqat obyekt materiallari bor edi.
Dalil: birinchi render kulrang fon bilan chiqdi.
Tuzatish: `BG_COLOR` spec dan olinadi, Background node rangiga va Strength 0.7 ga o'rnatiladi; metallik/roughness ham spec dan.
Tekshiruv: keyingi render tungi ko'k fon va yaltiroq ko'k shar bilan chiqdi; `test_build_scene_script_uses_requirement_values` o'tdi.

## 5. Test kutishidagi kichik xato

Alomat: `assert "metallic" in script` yiqildi, skript esa `METALLIC = 0.85` ishlatardi.
Ildiz sabab: test kichik harfli matn kutgan, ishlab chiqarish kodi bosh harfli konstanta ishlatgan.
Dalil: pytest xabarida `AssertionError: assert 'metallic' in ...` ko'ringan.
Tuzatish: test `METALLIC = 0.85` ni kutadigan qilindi; kod o'zgarishsiz qoldi.
Tekshiruv: `python -m pytest backend/tests/test_visual_spec_quality.py -q` → 3 passed.
