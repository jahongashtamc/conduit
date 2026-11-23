# MIYALAR (multi-miya tekshiruvi)

## 1. Arxitektor: tuzilma, qismlar bog'lanishi, keyin kengaytirish. Reja qayerda noto'g'ri qurilgan?

Muammolar: `subagents/*/role.md`, `security_guard.py`, `tool_registry.py` va `tools.py` alohida-alohida ro'yxat yuritadi; ular o'rtasida bitta manba yo'q. `cli_runner` faqat matn ichida `python tools.py` qidiradi, agentning boshqa chaqiruv yo'llarini ko'rmaydi. Tavsiya: bitta katalog funksiyasi, ruxsatni bajaruvchi (`tools.py`) ichiga o'tkazish, env orqali agent identifikatorini uzatish.

## 2. Skeptik: reja qayerda buziladi? Nimani o'tkazib yubordik? Qaysi taxmin tekshirilmagan?

Muammolar: "yangi fayl" deb faqat mtime ga ishonish mumkin (tizim vaqti, kopiya, cache); eski testlar `success:true` kutadi; katalog generatsiyasi token byudjetini oshirib yuborishi mumkin. Tavsiya: mtime+status yozuvi bilan bog'langan dalil identifikatori, `success` maydonini o'zgartirmasdan `verdict` ni tuzatish, katalog qisqa tavsiflar bilan chiqarish.

## 3. Xavfsizlik: hujum yuzasi, maxfiy ma'lumot, ruxsatlar. Qanday suiiste'mol qilish mumkin?

Muammolar: agent o'zini boshqa agent deb ko'rsatib, ruxsat etilmagan tool chaqirishi mumkin; `run_process` shell=True; tool chiqishidagi matn buyruq sifatida talqin qilinishi ehtimoli. Tavsiya: `CONDUIT_AGENT` ni faqat ishonchli `cli_runner` o'rnatadi, boshqa joyda rad etiladi; xavfli tool'lar ro'yxati ochiq va loglanadi; tool natijasi faqat ma'lumot sifatida qaytariladi.

## 4. Foydalanuvchi va UX: tushunarlimi, jonlimi, xato holatida nima ko'radi?

Muammolar: foydalanuvchi qaysi tool ishlaganini va nega PASS/FAIL bo'lganini ko'rmaydi; eski screenshot bilan PASS uning ishonchini yo'q qiladi. Tavsiya: `python tools.py --help` va `list_tools --json` chiqishi aniq; `check_goal` qaysi sababdan rad etilganini ochiq yozadi (masalan, "eski dalil"), UI'da xato yashirilmaydi.

## 5. Tester: buni qanday sindiraman? Qabul mezoni va chegara holatlari qaysilar?

Muammolar: test faqat "funktsiya bor" deganini tekshiradi; eski fayl bilan PASS, ruxsatsiz tool bilan bajarilish, bo'sh dalil, noto'g'ri turdagi fayl, katta fayl. Tavsiya: regression testlari: (1) eski PNG → FAIL, (2) yangi PNG → PASS, (3) bo'sh dalil → FAIL, (4) ruxsatsiz agent → denied, (5) `list_tools` barcha e'lon qilingan tool'larni qamrab oladi.

## 6. Qaror

Kelishmovchilik yo'q: tavsiya etilgan yondashuv tanlandi — bitta katalog, bajaruvchi tomonda ruxsat, yangi dalil talabi va aniq xatolar. Yangi MCP server yoki global o'rnatish qo'shilmaydi. Foydalanuvchiga qoldirilgan savol: faqat rejani tasdiqlash.
