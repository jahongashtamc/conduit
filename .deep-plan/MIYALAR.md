# MIYALAR (multi-miya tekshiruvi)

Har bo'limda `Muammolar:` va `Tavsiya:` satrlari bor. Reja qoralamasi mustaqil nuqtai nazarlardan tanqid qilindi.

## 1. Arxitektor: tuzilma, qismlar bog'lanishi, keyin kengaytirish. Reja qayerda noto'g'ri qurilgan?

Muammolar: xom bo'laklar buferi qo'shilganda `scrollback_buffer` bilan ikki xil tarix yuzaga keladi; faqat birini tozalash eski kadrlarni qoldiradi. `collapse_spinner_frames` haqiqiy agy kadrlariga tegmaydi, shuning uchun uning o'zi zinapoyani tuzatmaydi.

Tavsiya: ikki buferni bitta `_clear_scrollback()` orqali tozala; replay faqat xom bo'laklardan bo'lsin; qator buferi faqat matn qidirish uchun qolsin. Arxitektura aniq: PTY → WS → xterm.js, URL esa API chegarasida tekshiriladi.

## 2. Skeptik: reja qayerda buziladi? Nimani o'tkazib yubordik? Qaysi taxmin tekshirilmagan?

Muammolar: dastlabki gipoteza " spinner kadrlari `\r` bilan keladi" noto'g'ri edi; haqiqiy kadrlarda `\x1b[3A` borligi xom bo'laklarda tasdiqlandi. Yana bir xato: test payloadlarida braille belgilar `?` bo'lib yozilgan bo'lishi mumkin.

Tavsiya: har qadamda haqiqiy chiqishni saqla; test fayllarining baytlarini tekshir; UI da peak sinovida bandlik warning chiqsa, u agent ishlayotganining dalili deb hisobla, xato emas.

## 3. Xavfsizlik: kiritilgan ma'lumot, ruxsat, maxfiylik.

Muammolar: `-hel` kabi matn to'g'ridan-to'g'ri Playwright'ga berilgan; `javascript:`/`file:` sxemalari ham o'tishi mumkin edi; xato matni foydalanuvchiga xom stack trace sifatida chiqardi.

Tavsiya: backendda sxema, host, port, foydalanuvchi ma'lumoti va uzunlikni tekshir; xavfli sxemalarni 422 bilan rad et; xato xabarini qisqa va tushunarli qil; global konfiguratsiya va maxfiy kalitlarga tegma.

## 4. Foydalanuvchi va UX: xato xabari va terminal ko'rinishi.

Muammolar: terminal zinapoya bilan to'lib, foydalanuvchi "bu faqat debug" deb o'yladi; brauzerda qizil xom `page.goto` matni professional emas.

Tavsiya: terminal bitta satrda qayta chizilishi kerak; brauzer xatosi "Noto'g'ri host nomi" kabi qisqa bo'lishi kerak; muvaffaqiyatli normalizatsiya ham ko'rinib turishi uchun javobda `url` qaytariladi.

## 5. Tester: qanday qilib buzilganini ushlaymiz?

Muammolar: faqat bir martalik ko'rish etarli emas; qayta ulanish (reconnect) paytida replay buziladi, lekin live oqim toza ko'rinadi.

Tavsiya: replay testi qo'sh (`test_scrollback_replay_preserves_cursor_up_frames`), URL uchun parametrli test va API 422 testi qo'sh; jonli tekshiruvda `BAD_JOIN 0`, `GOOD_JOIN 345`, `RAW_GOTO False`, `FRIENDLY True` olinishi shart.

## 6. Qaror: kelishmovchiliklar va rejaga kiritilgan o'zgarishlar.

Muammolar: dastlab regex bilan spinner kadrlarni o'zgartirish taklif qilindi; bu noto'g'ri edi, chunki kadrlar allaqachon to'g'ri qayta chiziladi. Asl muammo scrollback replayida edi.

Tavsiya: yakuniy yechim — xom bo'laklar buferi + `"".join` replay, backend URL validatsiyasi, frontend dastlabki filtr (`QIDIRUV YO'Q` emas, real kod). Bu yechimga barcha besh nuqtai nazar rozilik bergan.
