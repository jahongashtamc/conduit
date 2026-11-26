# Painter Checker

PASS faqat quyidagi shartlar **hammasi** bajarilganda beriladi:

1. `gen_image` chiqishida `success: true` bo'lgan.
2. `image_path` da ko'rsatilgan fayl diskda **haqiqatan mavjud**:
   `python -c "import os; print(os.path.getsize(r'<image_path>'))"` — soni 0 dan katta.
3. Fayl kengaytmasi `.png` (yoki `.jpg`) va o'lchamlar so'ralganiga mos
   (`width`/`height` maydonlari).
4. Tavsif foydalanuvchi so'ragan rang/shaklga mos (chiqishdagi `spec.colors`,
   `spec.shapes`, `spec.count` maydonlarini solishtir).

Yakuniy tekshiruv buyrug'i:

```bash
python tools.py check_goal "<vazifa matni>" "{\"image_path\": \"<path>\", \"bytes\": <son>}"
```

Qaysi shart bajarilmasa — aniq sabab bilan FAIL va qaysi qadam qayta
bajarilishi kerakligini yoz.
