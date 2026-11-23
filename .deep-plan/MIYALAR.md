# MIYALAR (multi-miya tekshiruvi)

Har bo'limda `Muammolar:` va `Tavsiya:` qatorlari bor.

## 1. Arxitektor: tuzilma, qismlar bog'lanishi, keyin kengaytirish. Reja qayerda noto'g'ri qurilgan?

Muammolar: klonlashni `workspace_manager.py` ichiga tiqish klonlarni agent workspace'lari bilan aralashtiradi; `acquisition.py` esa faqat scaffold yozadi. Tavsiya: mustaqil `backend/clone_manager.py` + registry JSON + `POST/GET/DELETE /api/clones` + `Window5Workspace` UI. Bu chegaralar aniq va keyin kengaytirishga imkon beradi.

## 2. Skeptik: reja qayerda buziladi? Nimani o'tkazib yubordik? Qaysi taxmin tekshirilmagan?

Muammolar: `git` binary yo'qligi, tarmoq uzilishi, katta repo va invalid URL rejani buzishi mumkin; shuningdek eski `.deep-plan/` hujjatlari yangi vazifaga tegishli emas edi. Tavsiya: `shutil.which('git')` tekshiruvi, `check=True` va xatolarni loglash, kichik `--depth 1` klon, barcha hujjatlarni qayta yozish, haqiqiy `morluto/rea` kloni bilan sinash.

## 3. Xavfsizlik: kiritish, ruxsat va maxfiy ma'lumotlar

Muammolar: URL orqali `file://`/`ssh://` sxemasi yoki `../` yo'l inyeksiyasi, shuningdek xato matnida token ko'rinishi xavfli. Tavsiya: faqat https, `resolve_safe_path`, symlink rad etish, `shell=False`, maxfiy naqshlarni redaktatsiya qilish, global sozlamalarga tegmaslik va `npx rea-agents setup` ni ishlatmaslik.

## 4. Foydalanuvchi va UX: natijani ko'rish va boshqarish

Muammolar: foydalanuvchi klonlash jarayonini ko'ra olmasa yoki ro'yxatni topolmasa, rejim "to'liq" bo'lmaydi. Tavsiya: `Klonalar` bo'limida URL, nom, holat, commit, log, ochish/yangilash/o'chirish tugmalari; Anime.js uchun mahalliy demo sahifasi va aniq xato xabarlari.

## 5. Tester: qanday dalil talab qilinadi?

Muammolar: faqat "fayl yaratildi" deyish yetarli emas; haqiqiy klon va oflayn kutubxona isbotlanishi kerak. Tavsiya: `git rev-parse HEAD` saqlanishi, `GET /api/clones` ro'yxati, `DELETE` dan keyin yo'qligi, `animejs` paketi va Timer demo fayllari mavjudligi, pytest/tsc/lint/build/doctor yashil, `gate.py verify OK`.

## 6. Qaror

Kelishmovchilik yo'q: 1-yondashuv tanlandi. Minimal forma va faqat git tool rad etildi. Yakuniy reja: mustaqil clone manager, xavfsiz API/UI, offline Anime.js v4, to'liq test va hujjatlar.
