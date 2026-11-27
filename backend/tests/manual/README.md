# Qo'lda yurgiziladigan sinov skriptlari

Bu fayllar **pytest testlari emas**. Ular haqiqiy AI agent CLI (agy, claude,
codex) va tirik backend talab qiladi — CI'da deterministik emas, shuning
uchun `tests/` dan chiqarilgan: `test_*.py` nomi bilan turgani "qamrov bor"
degan yolg'on taassurot berardi, holbuki pytest ularni yig'a olmasdi ham.

## Nima bilan qoplanadi (bular pytest, CI'da ishlaydi)

| Qamrov | pytest fayli |
|---|---|
| PTY: prompt, echo, Ctrl+C, resize, scrollback, close, heartbeat | `tests/test_pty_live.py` |
| PTY backend tanlovi (ConPTY) | `tests/test_pty_backend.py` |
| Jonli sahna: snapshot / preview_frame / task_completed / ping | `tests/test_live_scene_ws.py` |
| CLI kontraktlari (`status --json`, `list --json`, 404) | `tests/test_five_hour_findings.py` |
| URL/terminal/voice regressiyalari | `tests/test_url_validation.py`, `tests/test_utf8_subprocess.py` |

## Bu yerda nima qoladi va nima uchun

| Skript | Nimani tekshiradi | Nima uchun CI'da emas |
|---|---|---|
| `pty_terminal_agy.py` | agy TUI ochiladi, markerli so'rovga javob beradi, Ctrl+C promptga qaytaradi | Haqiqiy agy CLI + model chaqiruvi kerak (tarmoq, kvota, ~3 daqiqa) |
| `pty_claude.py` | claude interaktiv sessiyasi + `{"type":"close"}` jarayon daraxtini o'ldiradi | claude CLI o'rnatilgan va autentifikatsiya qilingan bo'lishi shart |
| `pty_env_conduit.py` | PTY ichida `CONDUIT_API`/`CONDUIT_SESSION` va `conduit list --json` | `conduit` global PATH'da bo'lishi kerak (CI'da faqat repo ildizida) |
| `live_scene_agent.py` | Agent bilan to'liq vazifa → jonli sahna hodisalari | Agent CLI'siz vazifa tugamaydi; endi `test_live_scene_ws.py` shartnomani qoplaydi |
| `e2e_agy_studio.py` | Terminalda agy → `conduit run` → artefakt galereyasi | To'liq stack + model; qo'lda E2E |
| `acceptance_h.py` | Har bir agent uchun yakuniy qabul sinovi | Har agent uchun model chaqiruvi |

## Ishga tushirish

Tirik backend (8000-port) va kerakli CLI o'rnatilgan bo'lishi shart:

```powershell
# alohida oynada backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000   # backend/ ichida

# keyin skript
python backend/tests/manual/pty_terminal_agy.py
python backend/tests/manual/pty_claude.py
python backend/tests/manual/acceptance_h.py claude_code   # yoki: agy, codex_cli
python backend/tests/manual/e2e_agy_studio.py
```

`live_scene_agent.py` va `acceptance_h.py` natijani PASS/FAIL sifatida
qaytaradi (`exit code 0/1`), qolganlari jadval chop etadi — `[OK]`/`[XATO]`.
