# Slack Checker

PASS shartlari (token bor bo'lsa):

1. `slack_api` chiqishida `success: true` va `ok: true`.
2. Javobda `ts` (xabar vaqt belgisi) mavjud — bu xabar haqiqatan yuborilganini bildiradi.
3. `channel` maydoni so'ralgan kanalga mos.

Token yo'q bo'lsa:
1. `configured: false` qaytgan.
2. Foydalanuvchiga token sozlash yo'riqnomasi berilgan.
3. Natija — **BLOCKED**, PASS emas.

Yakuniy tekshiruv:

```bash
python tools.py check_goal "<vazifa>" "{\"ok\": true, \"ts\": \"<ts>\"}"
```

`ok: true` va `ts` ikkalasi bo'lmasa — xabar yuborilmagan, PASS berma.
