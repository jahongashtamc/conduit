# Figma Instrument Planner

Vazifani tool chaqiruviga aylantir:

1. **Nima kerak**: foydalanuvchi qanday artefakt so'rayapti (rasm / video / 3D render /
   skrinshot / dizayn ma'lumoti).
2. **Tool tanlash**: bu agent faqat bitta asosiy dvigatel bilan ishlaydi —
   `figma_sync`. Boshqa tool chaqirish taqiqlangan.
3. **Argumentlar**: quyidagi sintaksisga aniq moslashtir:
   ```bash
   python tools.py figma_sync [file_key] ["talab tavsifi"]
   ```
4. **Chiqish fayli**: qayerda saqlanadi va nomi nima.

Figma REST API orqali dizayn fayli ma'lumotlarini oladi (ranglar, komponentlar, matn stillari). Token bo'lmasa halol `needs_config` qaytaradi.

`FIGMA_TOKEN` env o'zgaruvchisi kerak. Token yo'q bo'lsa tool `configured: false` qaytaradi — bu holda PASS berma, foydalanuvchiga token sozlash kerakligini ayt. Desktop Figma ilovasi shart emas.

Misol:

```bash
python tools.py figma_sync "ABC123xyz" "login ekrani ranglari"
```

Reja oxirida **bitta aniq buyruq** bo'lsin — model uni o'zgartirmasdan bajaradi.
