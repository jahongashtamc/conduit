# Subagentlar — asosiy AI agentga bog'langan tool'lar

## 1. Rasmiy model (o'rganilgan manbalar)

| Fakt | Manba |
|------|-------|
| Subagent o'z kontekst oynasida, o'z system prompti va tool allowlisti bilan ishlaydi; natijani asosiy agentga qisqa xabar sifatida qaytaradi. | [Claude Code — Create custom subagents](https://code.claude.com/docs/en/subagents.md) |
| Asosiy agent faqat subagentning **qisqa tavsifi** asosida delegatsiya qiladi. Tavsiflar jami 15 000 token dan oshsa ogohlantirish chiqadi. | yuqoridagi manba |
| To'liq rol prompti faqat subagent ishga tushganda yuklanadi — asosiy kontekstga kirmaydi. | yuqoridagi manba |
| Subagent so'rovlari asosiy suhbat bilan **umumiy usage limit**ga hisoblanadi; arzon model tanlash xarajatni boshqaradi. | yuqoridagi manba |
| agy custom subagentlarni `.agents/agents/<name>.md` dan topadi; frontmatter: `name`, `description`, `tools`, `subagent`, `mainAgent`, `model`, `commandExecutionPolicy`. Noto'g'ri tool nomi subagentni osib qoldirishi mumkin. | [Antigravity — Custom subagents](https://antigravity.google/docs/subagents?tab=cli) |

O'qilgan sana: 2026-11-22.

## 2. Nexus/Conduit dagi amalga oshirish

Studio agent-agnostik bo'lgani uchun Claude Code'ning ichki `Agent` tool'i o'rniga
**universal CLI shartnomasi** ishlatiladi:

```text
conduit tools --json              # agentga bog'langan 16 tool katalogi
conduit budget --json             # qolgan token/narx
conduit run <id> "<vazifa>"       # tool chaqiruvi -> task_id
conduit wait <task_id>            # kutish
conduit result <task_id>          # dalil + artefaktlar
```

`GET /api/tools/catalog` shu katalogning API ko'rinishi. Har bir tool:

- `name` (`conduit_run_<id>`), `description` (asosiy kontekstga yuklanadigan qisqa matn),
- `input_schema` (`task` maydoni), `allowed_tools` (`role.md` dan),
- `context_tokens`, `estimated_execution_tokens`, `estimated_cost_usd`,
- `within_remaining_budget` — qolgan byudjetga mosligi.

Jami tavsif hajmi **334 token** (ogohlantirish chegarasi 15 000).
Ijro bahosi haqiqiy o'lchovlar bilan kalibrlangan: oddiy chaqiruv ~14k token,
ko'p-tool vazifa ~90k; minimal `15 000` olinadi.

## 3. Kontekst ierarxiyasi

1. **Asosiy agent** faqat qisqa tavsiflar ro'yxatini ko'radi (AGENTS/CLAUDE/GEMINI v3 yo'riqnomasi).
2. Delegatsiya qaroridan keyin `conduit run` chaqiriladi.
3. **Subagent** ishga tushganda uning to'liq `role.md` prompti yuklanadi; ruxsat etilgan
   toollar `security_guard.get_allowed_tools()` bilan tekshiriladi.
4. Subagent faqat qisqa natija + dalil yo'lini qaytaradi; katta log asosiy kontekstga kirmaydi.

## 4. Token va narxning ishlashi

- Har bir vazifa oxirida `resource_ledger` ga token/duration yoziladi.
- Provider stream-json'da usage e'lon qilsa, **oxirgi `result` hodisasi** olinadi;
  oraliq hodisalardagi cumulative qiymatlar qo'shilmaydi (ikki barobar hisob oldi oldingi xato edi).
- `conduit budget` va statusbar qolgan byudjetni ko'rsatadi (UI 15 s da yangilanadi).
- `POST /api/tasks` dagi BudgetGuard tanlangan tool uchun byudjet yetishmasa vazifani `BLOCKED` qiladi.

## 5. agy uchun native bog'lanish

`backend/native_subagents.py` 16 ta `.agents/agents/conduit_<id>.md` yozadi (faqat lokal).
Fayllar agy tomonidan o'zi topiladi; tasdiqlangan agy tool nomlarigina ro'yxatga olingan.
Global `~/.gemini` yoki `~/.claude` sozlamalariga tegilmadi.

## 6. Tasdiqlangan ish zanjiri

```text
Foydalanuvchi vazifasi -> terminal WS agent_prompt -> asosiy agy
  -> conduit tools --json (16 tool topildi)
  -> conduit run inst_image "..." -> task_e1bda0f0 / task_a0a9a52a
  -> conduit wait + conduit result -> PASS + artefakt
  -> Tasklar / jonli sahna / galereya yangilanadi
```

Dalillar: `DECISIONS.md`, `docs/FINAL_ACCEPTANCE.md`, `%TEMP%/opencode/nexus_final.png`.

## 7. Ovoz plagi (2026-11-24)

`backend/tools.py` ga 5 ta tool qo'shildi: `voice_speak`, `voice_clone`,
`voice_convert`, `voice_doctor`, `voice_catalog`. `subagents/voice/` (app.json +
role.md + inner) orqali `conduit run voice "<vazifa>"` ishlaydi. Katalog endi
21 tool; eski 16 tool soni yuqoridagi tasdiqlangan tarixiy natija hisoblanadi.

Bajarish zanjiri:

```text
conduit tools --json
  -> conduit run voice "Salom dunyo matnini qiz ovozida yarat"
  -> voice_doctor (sha256 tekshiruvi)
  -> voice_speak / voice_clone / voice_convert
  -> conduit result <task_id>  (WAV yo'li + sr + davomiylik)
```

Detallar: `docs/VOICE_PLUGIN.md`.
