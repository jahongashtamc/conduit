# Designer Checker

PASS shartlari:

**Token bor bo'lsa:**
1. `figma_sync` chiqishida `success: true` va `configured: true`.
2. Dizayn ma'lumoti bo'sh emas: `colors` yoki `components` ro'yxati mavjud.
3. `spec_path` berilgan bo'lsa, fayl diskda mavjud va hajmi 0 dan katta.

**Token yo'q bo'lsa:**
1. `configured: false` yoki `status: "needs_config"` qaytgan.
2. Foydalanuvchiga token sozlash yo'riqnomasi aniq berilgan.
3. Bu holda **PASS emas, BLOCKED** — vazifa bajarilmagan, sabab halol ko'rsatilgan.

Yakuniy tekshiruv:

```bash
python tools.py check_goal "<vazifa>" "{\"file_key\": \"<key>\", \"configured\": <true|false>}"
```

Soxta dizayn ma'lumoti — eng og'ir xato. Token yo'qligini yashirmang.
