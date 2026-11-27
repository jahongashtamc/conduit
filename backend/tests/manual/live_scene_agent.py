"""Jonli sahna (D bosqich) sinovi: /ws/task/{task_id} orqali qadam hodisalari
va preview kadrlar kelishini tekshiradi. Backend jonli bo'lishi shart."""
import asyncio
import json
import urllib.request

URI = "ws://127.0.0.1:8000/ws/task/{task_id}"
API = "http://127.0.0.1:8000"


def api(path, method="GET", data=None):
    req = urllib.request.Request(f"{API}{path}", method=method)
    req.add_header("Content-Type", "application/json")
    body = json.dumps(data).encode() if data else None
    with urllib.request.urlopen(req, body, timeout=30) as r:
        return json.loads(r.read().decode())


async def main():
    import websockets
    # 1) Vazifa yaratamiz (claude engine, inspector — tez va real)
    resp = api("/api/tasks", "POST", {
        "prompt": "Tizim salomatligini tekshir: backend /api/health so'rovi OK bo'lsin",
        "subagent": "inspector",
    })
    task_id = resp.get("task_id") or resp.get("task", {}).get("id")
    print(f"[1] Vazifa yaratildi: {task_id}")

    events = {"snapshot": 0, "step": 0, "log": 0, "preview_frame": 0, "other": 0}
    previews = []
    async with websockets.connect(URI.format(task_id=task_id), max_size=10 * 1024 * 1024) as ws:
        deadline = asyncio.get_event_loop().time() + 180
        done = False
        while asyncio.get_event_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=10)
            except asyncio.TimeoutError:
                continue
            except Exception as exc:
                print(f"[ws] yopildi: {exc}")
                break
            msg = json.loads(raw)
            t = msg.get("type", "?")
            if t == "snapshot":
                events["snapshot"] += 1
                print(f"[2] snapshot: status={msg['task'].get('status')}, loglar={len(msg.get('logs', []))}")
            elif t == "preview_frame":
                events["preview_frame"] += 1
                fr = msg.get("frame", {})
                previews.append(fr.get("source"))
                print(f"[3] preview_frame #{events['preview_frame']}: source={fr.get('source')}, {len(fr.get('data', '')) // 1024}KB")
            elif t in ("log", "brain_event", "heart_transition", "subagent_activated", "task_completed"):
                events["step"] += 1
                if t == "task_completed":
                    print(f"[4] task_completed: status={msg.get('status')}")
                    done = True
                elif t == "log":
                    events["log"] += 1
            else:
                events["other"] += 1
            if done:
                break

    print("\n=== NATIJA ===")
    print(json.dumps(events, indent=2))
    ok = events["snapshot"] >= 1 and events["step"] >= 1
    print(f"JONLI SAHNA: {'OK' if ok else 'XATO'} (preview kadrlar: {events['preview_frame']}, manbalar: {set(previews) or '-'})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
