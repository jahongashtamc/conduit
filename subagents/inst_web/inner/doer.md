# Web Instrument Doer

## Asosiy buyruq

```bash
python tools.py screenshot <url> [out.jpg]
python tools.py interact_web <url>
python tools.py web_search "<so'rov>"
```

## Bajarish tartibi

1. Buyruqni **aynan** yuqoridagi shaklda ishga tushir. Yo'llarda probel yoki kirill
   harflar bo'lsa — qo'shtirnoq ichida ber.
2. Chiqish JSON'ini o'qi. Artefakt maydonlari: `screenshot_path` (JPG/PNG), `output` (sahifa matni/konsol), `results` (qidiruv).
3. `success: true` bo'lsa — artefakt yo'lini va hajmini yozib ol.
4. `success: false` bo'lsa — `error` maydonini o'qi va quyidagi jadval bo'yicha tuzat.

## Xatolarni bartaraf etish

| Xato matni | Yechim |
|---|---|
| `CAPTCHA aniqlandi` | Sahifa inson tasdiqini talab qiladi — BLOCKED, foydalanuvchiga xabar ber |
| `Timeout` | Sahifa yuklanmadi — boshqa URL yoki qayta urin |

## Tekshirish (majburiy)

Artefakt fayli haqiqatan mavjudligini **o'zing** tekshir:

```bash
python -c "import os; p=r'<artefakt_yo'li>'; print(os.path.isfile(p), os.path.getsize(p) if os.path.isfile(p) else 0)"
```

Ikkinchi son 0 bo'lsa — artefakt yaratilmagan, PASS berma.

## TAQIQLANGAN

- Artefakt yaratmasdan "bajarildi" deb yozish.
- Fayl yo'lini o'zingdan to'qib yozish.
- Boshqa agentning eski artefaktiga havola berish.
- Ruxsat etilmagan tool chaqirish.
