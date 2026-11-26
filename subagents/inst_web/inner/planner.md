# Web Instrument Planner

Vazifani tool chaqiruviga aylantir:

1. **Nima kerak**: foydalanuvchi qanday artefakt so'rayapti (rasm / video / 3D render /
   skrinshot / dizayn ma'lumoti).
2. **Tool tanlash**: bu agent faqat bitta asosiy dvigatel bilan ishlaydi —
   `screenshot / interact_web / web_search`. Boshqa tool chaqirish taqiqlangan.
3. **Argumentlar**: quyidagi sintaksisga aniq moslashtir:
   ```bash
   python tools.py screenshot <url> [out.jpg]
python tools.py interact_web <url>
python tools.py web_search "<so'rov>"
   ```
4. **Chiqish fayli**: qayerda saqlanadi va nomi nima.

Brauzer va qidiruv: sahifa skrinshoti (Playwright), sahifa konsoli/tarmoq tekshiruvi, DuckDuckGo orqali veb qidiruv.

Vazifada URL bo'lsa — `screenshot` yoki `interact_web`. URL bo'lmasa — `web_search`. Conduit dashboardi (localhost:3000) skrinshot qilish taqiqlangan.

Misol:

```bash
python tools.py screenshot "https://example.com" example.jpg
python tools.py web_search "python asyncio tutorial"
```

Reja oxirida **bitta aniq buyruq** bo'lsin — model uni o'zgartirmasdan bajaradi.
