# Editor Checker

PASS faqat quyidagilar **hammasi** bajarilganda beriladi:

1. `video_render` chiqishida `success: true`.
2. `video_path` dagi fayl diskda mavjud va hajmi 0 dan katta:
   ```bash
   python -c "import os; p=r'<video_path>'; print(os.path.isfile(p), os.path.getsize(p))"
   ```
3. `frames > 0` — video haqiqiy kadrlardan iborat (0 bo'lsa kodlanmagan).
4. `inputs` ro'yxatida **barcha** so'ralgan kliplar bor (bittasi tushib qolsa FAIL).
5. Haqiqiy davomiylik ffprobe bilan tasdiqlansin:
   ```bash
   ffprobe -v error -show_entries format=duration -of csv=p=0 "<video_path>"
   ```
   Son 0 dan katta bo'lishi shart.
6. So'ralgan audio berilgan bo'lsa, `audio` maydoni `null` emas.

Yakuniy tekshiruv:

```bash
python tools.py check_goal "<vazifa>" "{\"video_path\": \"<path>\", \"frames\": <son>, \"bytes\": <son>}"
```

Qaysi shart bajarilmasa — aniq sabab bilan FAIL. "Video chiqdi" degan gap
dalil emas: yo'l, kadr soni va hajm ko'rsatilishi shart.
