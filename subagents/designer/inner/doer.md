# Designer Doer

Bajarish qadamlari:

1. Buyruqni ishga tushir:

   ```bash
   python tools.py figma_sync "<file_key>" "<talab tavsifi>"
   ```

   `file_key` bo'sh bo'lsa ham ishlaydi (foydalanuvchining Figma fayllarini qidiradi).

2. Chiqish JSON'ini o'qi. Maydonlar:
   - `success: true` → `colors` (palitra), `typography` (matn stillari),
     `components` (komponentlar), `spec_path` (saqlangan JSON).
   - `configured: false` → token yo'q.
   - `success: false` → `error` maydonidagi sabab.

3. Token yo'q bo'lsa (eng ko'p uchraydigan holat):

   ```json
   {"success": false, "status": "needs_config",
    "error": "FIGMA_TOKEN topilmadi..."}
   ```

   Bu holda **PASS berma**. Foydalanuvchiga aniq ayt:
   "Figma → Settings → Security → Personal access tokens → Generate new token,
   keyin `FIGMA_TOKEN` muhit o'zgaruvchisiga qo'ying."

4. Token bor bo'lsa — ranglar va tipografiyani `workspaces/designer/` ichiga JSON
   sifatida saqla va foydalanuvchiga qisqa hisobot ber.

TAQIQLANGAN: token yo'qligida soxta rang/komponent yozish; Figma MCP toollarini
chaqirish (faqat `tools.py figma_sync` ruxsat etilgan).
