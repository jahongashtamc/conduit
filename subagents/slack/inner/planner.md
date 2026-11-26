# Slack Planner

Slack vazifasini aniq buyruqqa aylantir:

1. **Amal turi**: xabar yuborish (`post`), kanallar ro'yxati (`list`),
   kanal tarixi (`history`).
2. **Kanal**: `#general`, `#dev` yoki kanal ID (`C01234ABCDE`).
3. **Matn**: yuboriladigan xabar mazmuni.

Reja oxirida buyruq:

```bash
python tools.py slack_api <amal> "<kanal>" "<matn>"
```

Misollar:
```bash
python tools.py slack_api post "#general" "Deploy tugadi"
python tools.py slack_api list
```

**Muhim**: `SLACK_BOT_TOKEN` env o'zgaruvchisi kerak (bot token, `xoxb-...`).
Token yo'q bo'lsa tool halol xato qaytaradi — foydalanuvchidan token so'ra.
