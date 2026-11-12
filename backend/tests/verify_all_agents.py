"""Barcha rol-agentlarni real vazifa bilan ketma-ket sinash (ertalabgacha tekshiruv)."""
import json
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:8000"

TASKS = {
    "scout": "example.com sahifasini ochib, sarlavhasini aniqlash",
    "inspector": "backend /api/health so'rovini yuborib holatini tekshirish",
    "sentinel": "workspaces/painter papkasidagi fayllarda maxfiy kalitlar bor-yo'qligini tekshirish",
    "sculptor": "sfera 3d modelini yaratib render olish",
    "designer": "dizayn tokenlarini figma_sync orqali olish va ranglar ro'yxatini chiqarish",
    "animator": "2 soniyali sferani aylantiruvchi keyframe animatsiya yaratish",
    "editor": "3 soniyali qisqa test video yaratish",
    "painter": "o'rmon yashil tekstura rasm yaratish",
    "notion": "notion integratsiya holatini tekshirish",
    "slack": "slack integratsiya holatini tekshirish",
    "superagent": "kichik misol: ikkita fayl yaratish rejasi tuzish",
}


def req(method: str, path: str, payload: dict = None, timeout: int = 30):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def wait_task(tid: str, max_s: int = 900):
    t0 = time.time()
    last_step = ""
    while time.time() - t0 < max_s:
        try:
            t = req("GET", f"/api/tasks/{tid}").get("task", {})
        except Exception as exc:
            print(f"    [so'rov xato: {exc}]", flush=True)
            time.sleep(15)
            continue
        st, step = t.get("status"), t.get("current_step")
        if (st, step) != (None, last_step):
            print(f"    {int(time.time()-t0)}s: {st} | {step}", flush=True)
            last_step = step
        if st in ("PASS", "FAIL", "BLOCKED"):
            return st, t
        time.sleep(15)
    return "TIMEOUT", {}


def main():
    agents = sys.argv[1:] or list(TASKS)
    results = {}
    for agent in agents:
        print(f"\n=== {agent}: {TASKS[agent][:60]}", flush=True)
        try:
            resp = req("POST", "/api/tasks", {
                "prompt": TASKS[agent], "target_agent": agent,
                "execution_mode": "standard",
            })
            tid = resp.get("task", resp).get("task_id")
        except Exception as exc:
            results[agent] = f"CREATE-ERROR: {exc}"
            continue
        st, t = wait_task(tid)
        dur = t.get("total_duration") or round(time.time() - time.time(), 1)
        ev = (t.get("evidence") or "")[:110].replace("\n", " ")
        results[agent] = f"{st} ({t.get('total_duration')}s): {ev}"
        print(f"  -> {results[agent]}", flush=True)

    print("\n===== YAKUNIY NATIJALAR =====", flush=True)
    ok = 0
    for a, r in results.items():
        mark = "PASS" if r.startswith("PASS") else "XATO"
        if r.startswith("PASS"):
            ok += 1
        print(f"[{mark}] {a}: {r}", flush=True)
    print(f"\n{ok}/{len(results)} PASS", flush=True)


if __name__ == "__main__":
    main()
