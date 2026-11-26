# FFmpeg Video Instrument Planner

Vazifani tool chaqiruviga aylantir:

1. **Nima kerak**: foydalanuvchi qanday artefakt so'rayapti (rasm / video / 3D render /
   skrinshot / dizayn ma'lumoti).
2. **Tool tanlash**: bu agent faqat bitta asosiy dvigatel bilan ishlaydi —
   `video_render`. Boshqa tool chaqirish taqiqlangan.
3. **Argumentlar**: quyidagi sintaksisga aniq moslashtir:
   ```bash
   python tools.py video_render "<klip1>" ["<klip2>" ...] --out "<natija.mp4>" <davomiylik>
   ```
4. **Chiqish fayli**: qayerda saqlanadi va nomi nima.

FFmpeg bilan haqiqiy kirish kliplaridan MP4 montaj qiladi. Kirish fayllari bo'lmasa soxta video yaratmaydi — halol FAIL qaytaradi.

Yo'llarda probel va kirill harflar bo'lsa, **albatta** qo'shtirnoq ichida ber. `--out` chiqish fayli yo'li. Davomiylik — har bir klippan olinadigan sekund. `anim_render` ham mavjud (keyframe GIF/MP4).

Misol:

```bash
python tools.py video_render "C:\Kliplar\a.mp4" "C:\Kliplar\b.mp4" --out "C:\Kliplar\montaj.mp4" 2.0
```

Reja oxirida **bitta aniq buyruq** bo'lsin — model uni o'zgartirmasdan bajaradi.
