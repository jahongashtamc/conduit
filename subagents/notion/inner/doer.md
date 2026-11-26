# Notion Doer

Bajarish qadamlari:

1. Buyruqni ishga tushir:

   ```bash
   python tools.py notion_api <amal> "<payload_json>"
   ```

   `payload_json` — JSON satri, qo'shtirnoq ichida, ichki kalitlar ikki qo'shtirnoq bilan.

2. Chiqish JSON'ini o'qi:
   - `success: true` → `id` (sahifa/yozuv ID), `url` (Notion havolasi), `results`.
   - `success: false` → `error` maydoni.

3. Token yo'q bo'lsa:

   ```json
   {"success": false, "configured": false,
    "error": "NOTION_TOKEN sozlanmagan..."}
   ```

   Foydalanuvchiga ayt: "notion.so/my-integrations → New integration → token
   (`secret_...`) → sahifani integration bilan ulashish → `NOTION_TOKEN` ga qo'ying."

4. Muvaffaqiyatli bo'lsa — `id` va `url` ni dalil sifatida yoz.

TAQIQLANGAN: token yo'qligida "yaratildi" deyish; `id`/`url` ni o'zingdan to'qish.
