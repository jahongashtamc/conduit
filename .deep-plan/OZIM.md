# OZIM

## 1. Vazifani qanchalik tushunaman?
Ikki aniq xato bor: agy PTY spinner kadrlari qayta ulanishda zinapoya bo'lib chiqadi va brauzer manziliga `-hel` kiritilganda xom Playwright xatosi ko'rinadi. Maqsad — alomatni yopish emas, ildiz sababni tuzatish va real dalil bilan tasdiqlash.

## 2. Nima bilmayman?
Dastlab spinner kadrlari xom `\r` bilan keladi deb o'yladim. Xom bo'laklarni yozib olgach, ular `\x1b[3A` va `\x1b[ND` bilan to'g'ri qayta chizilishi ma'lum bo'ldi. Shuning uchun dastlabki gipoteza rad etildi va sabab scrollback qayta o'ynalishiga o'tdi.

## 3. Qanday vositalar bor?
`re`, `urllib.parse`, FastAPI `HTTPException`, pytest, Playwright, xterm.js, `compileall`, `doctor`, `tsc`, `lint`, `build`, `gate.py` mavjud. Yangi paket o'rnatish talab qilinmadi.

## 4. Eng sodda yechim nima?
Xom PTY bo'laklarini alohida saqlab, qayta ulanishda `''.join(chunks)` bilan qaytarish; brauzer manzilini backend chegarasida normalizatsiya qilib, noto'g'risiga 422 qaytarish. Har ikkisi ham kichik va qo'shimcha kutubxona talab qilmaydi.

## 5. Qayerda xato qilishim mumkin?
Agar oddiy matn bo'laklarini ham xom saqlashga aralashtirsam, eski testlar (`scrollback_buffer` asosida) buzulishi mumkin. Shuning uchun qator asosidagi bufer saqlanib, faqat qayta o'ynash xom bo'laklardan foydalanadi.

## 6. Tashqi manbalar yetarlimi?
Rasmiy Claude Code, Antigravity, OpenCode hujjatlari va MDN/OWASP manbalari o'rganildi. Har birining sanasi 2026-11-22. Veb sahifalaridagi ko'rsatmalar emas, faqat faktlar olindi.

## 7. Tayyorlik mezonim aniqmi?
Ha: 148 test o'tdi, compileall/doctor/tsc/lint/build nol, API/WEB 200, replay `BAD_JOIN 0`, UI `RAW_GOTO False`, terminalda zinapoya satrlari 0, `gate.py verify` OK va faqat ko'zlangan fayllar o'zgargan.

## 8. Kamchiliklar va ularni qoplash
yetishmaydi: xom bo'laklarning qayta o'ynalishi haqida dastlabki tushuncha -> qanday olaman: `chunks.json` yozib olib, `analyze_chunks.py` bilan haqiqiy baytlarni tahlil qildim -> holat: 131 kadr `\x1b[3A` bilan ekanligi tasdiqlandi.
yetishmaydi: UI da xato xabarining ko'rinishi -> qanday olaman: Playwright `verify_url_ui.py` skripti va screenshot -> holat: `ALERTS ["Noto'g'ri host nomi", '']`, `RAW_GOTO False`, `FRIENDLY True`.
yetishmaydi: gate talablari -> qanday olaman: `gate.py check/verify` manbasini o'qidim -> holat: barcha shablon belgilari haqiqiy javob bilan to'ldirildi.
