# FFmpeg Video Instrument Doer

## Asosiy buyruq

```bash
python tools.py video_render "<klip1>" ["<klip2>" ...] --out "<natija.mp4>" <davomiylik>
```

## Bajarish tartibi

1. Buyruqni **aynan** yuqoridagi shaklda ishga tushir. Yo'llarda probel yoki kirill
   harflar bo'lsa — qo'shtirnoq ichida ber.
2. Chiqish JSON'ini o'qi. Artefakt maydonlari: `video_path` (MP4), `inputs`, `frames`, `fps`, `bytes`, `web_preview_url`.
3. `success: true` bo'lsa — artefakt yo'lini va hajmini yozib ol.
4. `success: false` bo'lsa — `error` maydonini o'qi va quyidagi jadval bo'yicha tuzat.

## Xatolarni bartaraf etish

| Xato matni | Yechim |
|---|---|
| `kamida bitta mavjud kirish video fayli kerak` | Yo'l xato yoki fayl yo'q. Tekshir: python -c "import os; print(os.path.isfile(r'<yo\'l>'))" |
| `FFmpeg topilmadi` | ffmpeg PATH'da yo'q — foydalanuvchiga xabar ber |

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
