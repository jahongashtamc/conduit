# Editor Doer

Bajarish qadamlari:

1. Ishchi papkada `tools.py` bor. Montaj buyrug'i:

   ```bash
   python tools.py video_render "<klip1>" ["<klip2>" ...] --out "<natija.mp4>" <davomiylik_soniya>
   ```

   - Klip yo'llari **qo'shtirnoq ichida** — probel va kirill harflar uchun shart.
   - `--out` berilmasa natija `workspaces/editor/montage.mp4` ga tushadi.
   - Davomiylik — har bir klippan olinadigan sekund (masalan `2.0`). `0` bersangiz
     butun klip ishlatiladi.
   - Audio: oxirgi argument sifatida audio fayl yo'li (`music.mp3`).

2. Chiqish JSON'ini o'qi:
   - `success: true` → `video_path`, `inputs`, `frames`, `fps`, `bytes` maydonlari.
   - `success: false` → `error` maydonidagi sababni o'qi va tuzat.
     Eng ko'p uchraydigan sabab: kirish fayli topilmadi (yo'l xato yozilgan).

3. **Klip mavjudligini oldindan tekshir** (montajdan oldin, vaqtni tejaydi):

   ```bash
   python -c "import os,sys; [print(p, os.path.isfile(p), os.path.getsize(p) if os.path.isfile(p) else 0) for p in sys.argv[1:]]" "klip1.mp4" "klip2.mp4"
   ```

4. `frames > 0` va `bytes > 0` bo'lishi shart — aks holda video buzuq.

5. Natijani tekshir (ffprobe bilan haqiqiy davomiylik):

   ```bash
   ffprobe -v error -show_entries format=duration -of csv=p=0 "<video_path>"
   ```

TAQIQLANGAN: klip yo'qligida soxta video yaratishga urinish; `video_path` ni
o'zingdan to'qib yozish; faylni tekshirmasdan "tayyor" deyish.

## Muammolarni bartaraf etish

| Xato | Sabab | Yechim |
|---|---|---|
| `Haqiqiy montaj uchun kamida bitta mavjud kirish video fayli kerak` | Yo'l xato yoki fayl yo'q | `python -c "import os; print(os.path.isfile(r'<yo\'l>'))"` bilan tekshir |
| `FFmpeg topilmadi` | PATH'da ffmpeg yo'q | `python tools.py get_logs` bilan tekshir, foydalanuvchiga xabar ber |
| `ffmpeg xato` | Kod deklanmaydi yoki buzuq fayl | `error` oxiridagi ffmpeg matnini o'qi |
