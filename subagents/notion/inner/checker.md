# Notion Checker

PASS shartlari (token bor bo'lsa):

1. `notion_api` chiqishida `success: true`.
2. Yozuv yaratilgan bo'lsa — `id` mavjud va noto'g'ri/soxta emas.
3. `url` Notion havolasi (`https://www.notion.so/...` yoki `https://notion.so/...`).
4. Qidiruv bo'lsa — `results` ro'yxati bo'sh bo'lmasligi shart (0 natija FAIL).

Token yo'q bo'lsa:
1. `configured: false` qaytgan.
2. Foydalanuvchiga yo'riqnoma berilgan.
3. Natija — **BLOCKED**, PASS emas.

Yakuniy tekshiruv:

```bash
python tools.py check_goal "<vazifa>" "{\"success\": true, \"id\": \"<id>\"}"
```

`id` yoki `url` bo'lmasa — hech narsa yaratilmagan, PASS berma.
