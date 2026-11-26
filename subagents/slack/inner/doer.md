# Slack Doer

Bajarish qadamlari:

1. Buyruqni ishga tushir:

   ```bash
   python tools.py slack_api <amal> "<kanal>" "<matn>"
   ```

2. Chiqish JSON'ini o'qi:
   - `success: true` → `ok: true`, `ts` (xabar vaqt belgisi), `channel`.
   - `success: false` → `error` maydoni.

3. Token yo'q bo'lsa:

   ```json
   {"success": false, "configured": false,
    "error": "SLACK_BOT_TOKEN sozlanmagan..."}
   ```

   Foydalanuvchiga ayt: "api.slack.com/apps → Create App → OAuth & Permissions →
   Bot Token Scopes (`chat:write`, `channels:read`) → Install → `xoxb-...` tokenini
   `SLACK_BOT_TOKEN` ga qo'ying."

4. Muvaffaqiyatli yuborilgan bo'lsa — `ts` va `channel` ni dalil sifatida yoz.

TAQIQLANGAN: token yo'qligida "yuborildi" deyish; `ts` ni o'zingdan to'qish.
