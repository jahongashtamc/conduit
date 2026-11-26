# Notion Planner

Notion vazifasini aniq buyruqqa aylantir:

1. **Amal turi**: qidiruv (`search`), sahifa yaratish (`create_page`),
   ma'lumotlar bazasiga yozuv (`create_db_row`), sahifa o'qish (`read_page`).
2. **Manzil**: sahifa ID yoki ma'lumotlar bazasi ID (`32 belgi, tirelar bilan`).
3. **Kontent**: sarlavha va matn (Notion block formati).

Reja oxirida buyruq:

```bash
python tools.py notion_api <amal> "<payload_json>"
```

Misollar:
```bash
python tools.py notion_api search "{\"query\":\"loyiha\"}"
python tools.py notion_api read_page "{\"page_id\":\"abc123...\"}"
```

**Muhim**: `NOTION_TOKEN` env o'zgaruvchisi kerak (`secret_...` yoki `ntn_...`).
Token yo'q bo'lsa tool halol xato qaytaradi.
