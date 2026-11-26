# Designer Planner

Figma dizayn vazifasini aniq rejaga aylantir:

1. **Manba**: Figma fayl kaliti (`file_key`) berilganmi yoki foydalanuvchi
   fayl nomini aytganmi.
2. **Nima kerak**: ranglar palitrasi / tipografiya / komponentlar / to'liq spec.
3. **Chiqish formati**: JSON spec (`workspaces/designer/figma_spec.json`) yoki
   qisqa hisobot.

Reja oxirida buyruq:

```bash
python tools.py figma_sync "<file_key>" "<talab tavsifi>"
```

Misol: `python tools.py figma_sync "ABC123xyz" "login ekrani ranglarini ol"`

**Muhim**: `FIGMA_TOKEN` env o'zgaruvchisi kerak. Token yo'q bo'lsa tool
`configured: false` qaytaradi — bu holda foydalanuvchidan token so'ra,
o'zingdan dizayn ma'lumoti to'qima.

Figma'da **MCP toollarini chaqirish taqiqlangan** — faqat `tools.py figma_sync`
ishlatiladi.
