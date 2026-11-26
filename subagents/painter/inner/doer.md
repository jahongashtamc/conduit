# Painter Doer

Bajarish qadamlari:

1. Ishchi papkada `tools.py` bor. Buyruq **aynan** shu shaklda:
   ```bash
   python tools.py gen_image "<tavsif>" <kenglik> <balandlik>
   ```
   - Tavsif qo'shtirnoq ichida; rang va shakl nomi o'zbekcha yoki inglizcha bo'lsin.
   - Standart o'lcham 512×512; foydalanuvchi boshqa o'lcham so'rasa — o'shani ber.
2. Buyruq chiqishida JSON keladi. Undan `success`, `image_path`, `bytes` ni o'qi.
3. `success: true` va `bytes > 0` bo'lsa — rasm haqiqatan yaratilgan.
4. `success: false` bo'lsa, `error` maydonini o'qi va sababini tuzat
   (masalan tavsif bo'sh bo'lsa — to'ldir; PIL yo'q bo'lsa — xato deb qayd et).
5. Natijani **o'zing** qayta tekshir: fayl mavjudmi va hajmi noldan katta emasmi.

Misol to'liq tsikl:

```bash
python tools.py gen_image "qizil kub, 1 ta" 512 512
```

Chiqish:
```json
{"success": true, "image_path": "C:\\...\\workspaces\\painter\\gen_12345.png",
 "width": 512, "height": 512, "bytes": 8432,
 "web_preview_url": "/static/screenshots/painter_gen_12345.png"}
```

Bu holatda dalil — `image_path` dagi haqiqiy PNG fayl.

TAQIQLANGAN: rasm yaratmasdan "tayyor" deb yozish; boshqa agentning rasmiga
havola berish; `image_path` ni o'zingdan to'qib yozish.
