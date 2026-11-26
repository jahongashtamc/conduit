# Animator Doer

Bajarish qadamlari:

1. Keyframe JSON'ini tayyorla va buyruqni ishga tushir:

   ```bash
   python tools.py anim_render '[{"t":0,"color":"#101828"},{"t":1,"color":"#38bdf8"}]' 2.0
   ```

   Argumentlar tartibi: `keyframes_json` → `duration` (sekund).
   Natija har doim `workspaces/animator/animation.gif` (yoki `output_path` berilsa o'sha).

2. Chiqish JSON'ini o'qi:
   - `success: true` → `animation_path`, `frames`, `bytes`, `keyframes`.
   - `success: false` → `error`. `"Keyframe JSON noto'g'ri"` bo'lsa JSON sintaksisi
     buzilgan (qo'shtirnoqlar, vergullar). Qayta yoz va urin.

3. Tekshir: `frames > 0` va `bytes > 0`. 24 kadr = 2 sekund @ 12fps.

4. GIF haqiqatan harakatlanishini tasdiqlash (ixtiyoriy, kuchli dalil):

   ```bash
   ffprobe -v error -show_entries stream=nb_frames,width,height -of csv=p=0 "<animation_path>"
   ```

**Diqqat**: `anim_render` — rang o'tish animatsiyasi (GIF). 3D obyekt animatsiyasi
kerak bo'lsa bu tool emas: `blender_video` ishlatiladi (faqat sculptor/inst_blender
agentlarida ruxsat bor).

TAQIQLANGAN: faylni tekshirmasdan "animatsiya tayyor" deyish; mavjud bo'lmagan
GIF yo'lini ko'rsatish.
