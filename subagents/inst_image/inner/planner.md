# PIL Image Instrument Planner

Vazifani tool chaqiruviga aylantir:

1. **Nima kerak**: foydalanuvchi qanday artefakt so'rayapti (rasm / video / 3D render /
   skrinshot / dizayn ma'lumoti).
2. **Tool tanlash**: bu agent faqat bitta asosiy dvigatel bilan ishlaydi —
   `gen_image`. Boshqa tool chaqirish taqiqlangan.
3. **Argumentlar**: quyidagi sintaksisga aniq moslashtir:
   ```bash
   python tools.py gen_image "<tavsif>" <kenglik> <balandlik> [out.png]
   ```
4. **Chiqish fayli**: qayerda saqlanadi va nomi nima.

Pillow (PIL) bilan deterministik PNG rasm yaratadi: rang, shakl va son tavsifdan ajratiladi (seed = tavsif hash → har safar bir xil natija).

Tavsifda rang nomi (qizil, ko'k, yashil, sariq, oq, qora) va shakl (kub, shar, doira, uchburchak, yulduz) bo'lishi kerak. Son: "3 ta" yoki "uchta". Standart o'lcham 512×512.

Misol:

```bash
python tools.py gen_image "qizil kub, 1 ta" 512 512
```

Reja oxirida **bitta aniq buyruq** bo'lsin — model uni o'zgartirmasdan bajaradi.
