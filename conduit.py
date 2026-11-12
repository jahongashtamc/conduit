#!/usr/bin/env python3
"""
Conduit AI CLI - Terminal Interface for Subagent Orchestration
Commands:
  conduit run <subagent> "<vazifa>"  -> Dispatches task and immediately returns task_id
  conduit wait <id...>              -> Waits for one or more tasks to complete
  conduit status <id>               -> Displays detailed status and logs of a task
  conduit list                      -> Lists registered subagents
  conduit kill-all                  -> Emergency terminates all processes
"""

import sys
import os
import json
import time
import argparse
import urllib.request
import urllib.error
from typing import List, Dict, Any

API_BASE = os.environ.get("CONDUIT_API") or os.environ.get("CONDUIT_API_URL") or "http://127.0.0.1:8000"


def _emit(args, data: dict, human: str = ""):
    """--json berilsa JSON chiqaradi (agent o'qishi uchun), aks holda odam uchun matn."""
    if getattr(args, "json", False):
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(human)

def _request(endpoint: str, method: str = "GET", data: dict = None, raise_on_error: bool = True):
    url = f"{API_BASE}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        
    try:
        with urllib.request.urlopen(req, data=body, timeout=60) as resp:
            content = resp.read().decode("utf-8")
            if content:
                return json.loads(content)
            return {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        detail = err_msg
        try:
            detail = json.loads(err_msg).get("detail", err_msg)
        except Exception:
            pass
        if raise_on_error:
            print(f"[CONDUIT ERROR {e.code}] {detail}", file=sys.stderr)
            sys.exit(1)
        return {"status": "error", "http_status": e.code, "error": str(detail)}
    except urllib.error.URLError as e:
        print(f"[CONDUIT CONNECTION ERROR] Cannot reach backend at {API_BASE}: {e.reason}", file=sys.stderr)
        print("Iltimos, Conduit backend (FastAPI 127.0.0.1:8000) ishlab turganligini tekshiring.", file=sys.stderr)
        sys.exit(1)

def cmd_run(args):
    subagent = args.subagent.lower()
    task_prompt = args.task
    
    payload = {
        "prompt": task_prompt,
        "target_agent": subagent
    }
    
    res = _request("/api/tasks", method="POST", data=payload)
    task_id = res.get("task_id") or (res.get("task") or {}).get("task_id")
    
    if not task_id:
        print("\033[31m[XATO]\033[0m Vazifa yaratilmadi:", res, file=sys.stderr)
        sys.exit(1)
    
    _emit(args, {"ok": True, "task_id": task_id, "subagent": subagent},
          f"\033[32m[YARATILDI]\033[0m Vazifa ID: \033[1;36m{task_id}\033[0m\n"
          f"  Subagent: \033[1m{subagent}\033[0m\n"
          f"  Kuzatish: \033[90mconduit status {task_id}\033[0m\n"
          f"  Kutish:   \033[90mconduit wait {task_id}\033[0m")
    return task_id

def cmd_wait(args):
    task_ids: List[str] = args.task_ids
    if not task_ids:
        print("[XATO] Kamida bitta task_id ko'rsatilishi kerak.", file=sys.stderr)
        sys.exit(1)
        
    print(f"\033[33m[KUTILMOQDA]\033[0m {len(task_ids)} ta vazifa kuzatilmoqda: {', '.join(task_ids)}")
    start_time = time.time()
    
    completed_tasks: Dict[str, Dict[str, Any]] = {}
    missing = set()
    last_step: Dict[str, str] = {}
    last_beat = 0.0

    while len(completed_tasks) < len(task_ids):
        for tid in task_ids:
            if tid in completed_tasks or tid in missing:
                continue
            resp = _request(f"/api/tasks/{tid}", raise_on_error=False)
            if resp.get("status") == "error":
                # The task does not exist: stop watching it instead of looping
                # until the global timeout.
                missing.add(tid)
                print(f"  \033[31m[YO'Q]\033[0m {tid}", file=sys.stderr)
                continue
            task_data = resp.get("task", resp) if isinstance(resp, dict) else {}
            status = task_data.get("status", "working")
            step = task_data.get("current_step", "planner")

            # Show progress so a 2-minute planner phase never looks frozen.
            if last_step.get(tid) != step:
                last_step[tid] = step
                elapsed = round(time.time() - start_time, 1)
                print(f"  \033[90m...\033[0m {tid} bosqich: {step} ({elapsed}s)")
            
            if status in ("PASS", "FAIL", "BLOCKED"):
                completed_tasks[tid] = task_data
                total_dur = task_data.get("total_duration")
                if not isinstance(total_dur, (int, float)):
                    total_dur = round(time.time() - start_time, 2)
                
                status_color = "\033[32m" if status == "PASS" else "\033[31m" if status == "FAIL" else "\033[33m"
                status_icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[BLOCKED]"
                print(f"  {status_color}{status_icon}\033[0m {tid} ({task_data.get('target_agent')}) | {total_dur}s")
                if task_data.get("evidence"):
                    print(f"     Dalil: {task_data.get('evidence')[:100]}")

        if len(missing) == len(task_ids):
            print("\n\033[31m[XATO]\033[0m Hech qanday vazifa topilmadi.", file=sys.stderr)
            sys.exit(1)

        if len(completed_tasks) < len(task_ids):
            time.sleep(1.0)
            # Heartbeat every 15s so the operator knows it is still alive.
            if time.time() - last_beat > 15:
                last_beat = time.time()
                pending = [t for t in task_ids if t not in completed_tasks and t not in missing]
                if pending:
                    print(f"  \033[90m[KUTILMOQDA] {round(time.time() - start_time)}s ... {', '.join(pending)}\033[0m")
            if time.time() - start_time > 600:
                print("\n\033[31m[TIMEOUT]\033[0m 600s kutish vaqti tugadi.", file=sys.stderr)
                sys.exit(1)
                
    print("\n" + "="*60)
    print("\033[1;36mYAKUNIY XULOSA (Barcha vazifalar yakunlandi):\033[0m")
    all_passed = True
    for tid, t in completed_tasks.items():
        st = t.get("status")
        ag = t.get("target_agent", "")
        ev = t.get("evidence", "Dalil yo'q")
        color = "\033[32m" if st == "PASS" else "\033[31m"
        print(f"  {color}{st:<8}\033[0m {tid:<16} [{ag:<10}] {ev[:50]}")
        if st != "PASS":
            all_passed = False
    print("="*60)
    
    if all_passed:
        sys.exit(0)
    else:
        sys.exit(1)

def cmd_status(args):
    task_id = args.task_id
    resp = _request(f"/api/tasks/{task_id}")
    task_data = resp.get("task", resp) if isinstance(resp, dict) else {}
    logs = resp.get("logs", [])

    if getattr(args, "json", False):
        print(json.dumps({"task": task_data, "logs": logs[-10:]}, ensure_ascii=False, indent=2))
        return

    st = task_data.get("status", "unknown")
    color = "\033[32m" if st == "PASS" else "\033[31m" if st == "FAIL" else "\033[33m"
    
    print(f"\n\033[1mVAZIFA:\033[0m {task_data.get('task_id')} | Holat: {color}{st}\033[0m | Subagent: \033[1m{task_data.get('target_agent')}\033[0m")
    print(f"Topshiriq: \"{task_data.get('prompt')}\"")
    print(f"Bosqich:   {task_data.get('current_step')} | Umumiy vaqt: {task_data.get('total_duration', 0)}s")
    if task_data.get("evidence"):
        print(f"Dalil:     {task_data.get('evidence')}")
    if task_data.get("screenshot_url"):
        print(f"Skrinshot: {task_data.get('screenshot_url')}")
        
    durations = task_data.get("step_durations", {})
    if durations:
        print(f"Qadamlar:  Planner={durations.get('planner', 0)}s, Doer={durations.get('doer', 0)}s, Checker={durations.get('checker', 0)}s")
        
    if logs:
        print(f"\n\033[90mSo'nggi loglar ({len(logs)} ta):\033[0m")
        for l in logs[-5:]:
            ts = (l.get('timestamp') or '').split('T')[-1][:8]
            print(f"  \033[90m{ts}\033[0m [{l.get('level')}] {l.get('message')}")
    print()

def cmd_list(args):
    payload = _request("/api/subagents")
    # The API returns {"subagents": [...]} (older builds returned a bare list),
    # so unwrap defensively before iterating.
    if isinstance(payload, dict):
        subagents = payload.get("subagents") or payload.get("agents") or []
    elif isinstance(payload, list):
        subagents = payload
    else:
        subagents = []

    print("\n\033[1;36mCONDUIT RO'YXATGA OLINGAN SUBAGENTLAR:\033[0m")
    if not subagents:
        print("\033[33mHech qanday subagent topilmadi\033[0m")
        print()
        return
    if getattr(args, "json", False):
        print(json.dumps({"subagents": subagents}, ensure_ascii=False, indent=2))
        return
    print(f"{'Nomi':<15} {'Holati':<10} {'Turi':<12} {'Tavsifi':<40}")
    print("-" * 80)
    for ag in subagents:
        name = ag.get("name") or ag.get("id", "")
        status = ag.get("status", "unknown")
        atype = ag.get("type") or "role"
        desc = ag.get("role_desc_uz") or ag.get("role_desc_en") or ""
        color = "\033[32m" if status == "active" else "\033[90m"
        print(f"{name:<15} {color}{status:<10}\033[0m {atype:<12} {desc[:40]:<40}")
    print()

def cmd_kill_all(args):
    res = _request("/api/kill-all", method="POST")
    _emit(args, {"ok": True, "message": res.get("message", "Barcha jarayonlar to'xtatildi.")},
          "\033[31m[HAMMASINI TO'XTATISH]\033[0m " + res.get("message", "Barcha jarayonlar to'xtatildi."))


def cmd_result(args):
    """Vazija natijasi: holat + dalil + shu agentning yangi artefaktlari."""
    task_id = args.task_id
    resp = _request(f"/api/tasks/{task_id}")
    task_data = resp.get("task", resp) if isinstance(resp, dict) else {}
    agent = (task_data.get("target_agent") or "").lower()
    created = task_data.get("created_at") or ""

    artifacts = []
    try:
        all_items = _request("/api/artifacts?limit=200")
        if isinstance(all_items, dict):
            all_items = all_items.get("artifacts") or all_items.get("items") or []
        # Vazifa yaratilganidan keyin yaratilgan shu agent fayllari
        import datetime
        try:
            t0 = datetime.datetime.fromisoformat(created.replace("Z", "+00:00")).timestamp()
        except Exception:
            t0 = 0
        for it in all_items:
            if agent and it.get("agent", "").lower() != agent:
                continue
            if t0 and it.get("modified", 0) < t0 - 5:
                continue
            artifacts.append(it)
    except SystemExit:
        pass

    out = {
        "task_id": task_id,
        "status": task_data.get("status"),
        "target_agent": agent,
        "evidence": task_data.get("evidence"),
        "screenshot_url": task_data.get("screenshot_url"),
        "artifacts": [
            {"path": a.get("path"), "agent": a.get("agent"), "bytes": a.get("bytes"), "kind": a.get("kind")}
            for a in artifacts[:20]
        ],
    }
    if getattr(args, "json", False):
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    color = "\033[32m" if task_data.get("status") == "PASS" else "\033[31m" if task_data.get("status") == "FAIL" else "\033[33m"
    print(f"\n\033[1mNATIJA:\033[0m {task_id} | Holat: {color}{task_data.get('status')}\033[0m | Agent: \033[1m{agent}\033[0m")
    if task_data.get("evidence"):
        print(f"Dalil: {task_data['evidence']}")
    if task_data.get("screenshot_url"):
        print(f"Skrinshot: {task_data['screenshot_url']}")
    if artifacts:
        print(f"\nArtefaktlar ({len(artifacts)} ta, eng yangilari):")
        for a in artifacts[:10]:
            print(f"  \033[36m{a.get('path')}\033[0m ({a.get('bytes', 0)} bayt, {a.get('kind')})")
    else:
        print("\033[90mArtefakt topilmadi.\033[0m")
    print()


def cmd_screenshot(args):
    """Brauzer oynasining joriy kadrini faylga saqlaydi."""
    import urllib.error
    out_path = os.path.abspath(args.out or "conduit_screenshot.jpg")
    url = f"{API_BASE}/api/browser/frame"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": f"Brauzer ochilmagan (HTTP {e.code})"}))
        else:
            print("\033[31m[XATO]\033[0m Brauzer oynasi ochilmagan. Avval 'conduit browser <url>' yoki scout vazifasini ishga tushiring.", file=sys.stderr)
        sys.exit(1)
    with open(out_path, "wb") as f:
        f.write(data)
    _emit(args, {"ok": True, "file": out_path, "bytes": len(data)},
          f"\033[32m[SAQLANDI]\033[0m {out_path} ({len(data)} bayt)")


def cmd_browser(args):
    """Brauzer oynasini berilgan URL'ga yo'naltiradi."""
    res = _request("/api/browser/navigate", method="POST", data={"url": args.url})
    ok = bool(res.get("success"))
    _emit(args, {"ok": ok, "url": args.url, "state": res.get("state")},
          ("\033[32m[BRAUZER]\033[0m " if ok else "\033[31m[XATO]\033[0m ") + args.url)
    if not ok:
        sys.exit(1)

def cmd_doctor(args):
    """Tizim salomatligini bir buyruqda tekshirish."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
    import doctor
    checks, all_ok = doctor.run_doctor(verbose=True)
    sys.exit(0 if all_ok else 1)

DEMO_TASKS = {
    "scout":     "Open https://example.com and take a screenshot",
    "sculptor":  "Blender'da oddiy 3d kub modelini yarat va render ol",
    "designer":  "Figma spec va dizayn tokenlarini sinxronizatsiya qil",
    "animator":  "Oddiy keyframe animatsiya yarat",
    "editor":    "3 soniyalik intro video klip yarat",
    "painter":   "Rangli tekstura pattern yarat",
    "inspector": "Tizim salomatligini tekshir (health probe)",
    "sentinel":  "Loyiha xavfsizlik tekshiruvini o'tkaz",
    "notion":    "Notion integratsiyasini tekshir",
    "slack":     "Slack integratsiyasini tekshir",
    "superagent":"Oddiy MVP: salom dunyo veb-sahifasi yarat",
}

def cmd_demo(args):
    """Bir agentga tayyor demo vazifa beradi va natijani kutadi."""
    agent = (args.agent or "scout").lower()
    if agent not in DEMO_TASKS:
        print(f"\033[31m[XATO]\033[0m '{agent}' demo yo'q. Mavjudlar: {', '.join(DEMO_TASKS)}", file=sys.stderr)
        sys.exit(1)
    prompt = DEMO_TASKS[agent]
    print(f"\033[36m[DEMO]\033[0m {agent}: {prompt}")
    res = _request("/api/tasks", method="POST", data={"prompt": prompt, "target_agent": agent})
    tid = res.get("task_id")
    if not tid:
        print("\033[31m[XATO]\033[0m Vazifa yaratilmadi.", file=sys.stderr)
        sys.exit(1)
    print(f"\033[32m[YARATILDI]\033[0m {tid} — kutilmoqda...")

    # Wait inline (reuse cmd_wait logic via direct polling).
    import time as _t
    start = _t.time()
    last_step = ""
    while _t.time() - start < 600:
        _t.sleep(4)
        resp = _request(f"/api/tasks/{tid}", raise_on_error=False)
        if resp.get("status") == "error":
            print("\033[31m[XATO]\033[0m Vazifa yo'qolgan.", file=sys.stderr)
            sys.exit(1)
        t = resp.get("task", resp) if isinstance(resp, dict) else {}
        step = t.get("current_step", "")
        if step != last_step:
            last_step = step
            print(f"  \033[90mbosqich: {step} ({round(_t.time()-start)}s)\033[0m")
        if t.get("status") in ("PASS", "FAIL", "BLOCKED"):
            color = "\033[32m" if t["status"] == "PASS" else "\033[31m"
            print(f"  {color}[{t['status']}][0m {round(_t.time()-start)}s")
            if t.get("evidence"):
                print(f"     Dalil: {t['evidence'][:120]}")
            sys.exit(0 if t["status"] == "PASS" else 1)
    print("\033[31m[TIMEOUT]\033[0m 600s.", file=sys.stderr)
    sys.exit(1)

def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        prog="conduit",
        description="Conduit AI CLI Orchestrator - Terminal Interface for Subagent Operations"
    )
    subparsers = parser.add_subparsers(dest="command", help="Conduit buyruqlari")
    
    # run
    p_run = subparsers.add_parser("run", help="Subagentga vazifa berish va darrov task_id qaytarish")
    p_run.add_argument("subagent", help="Ijrochi subagent nomi (scout, sculptor, inspector, painter, animator, editor, designer)")
    p_run.add_argument("task", help="Vazifa matni (prompt)")
    p_run.set_defaults(func=cmd_run)
    
    # wait
    p_wait = subparsers.add_parser("wait", help="Bir yoki bir nechta vazifa tugashini kutish")
    p_wait.add_argument("task_ids", nargs="+", help="Kutiladigan vazifa ID lari (masalan: task_1 task_2)")
    p_wait.set_defaults(func=cmd_wait)
    
    # status
    p_status = subparsers.add_parser("status", help="Vazifa holati va dalilini tekshirish")
    p_status.add_argument("task_id", help="Vazifa ID raqami")
    p_status.set_defaults(func=cmd_status)
    
    # list
    p_list = subparsers.add_parser("list", help="Mavjud subagentlar ro'yxatini ko'rish")
    p_list.set_defaults(func=cmd_list)
    
    # kill-all
    p_kill = subparsers.add_parser("kill-all", help="Barcha ishlayotgan subagent jarayonlarini to'xtatish")
    p_kill.set_defaults(func=cmd_kill_all)

    p_doc = subparsers.add_parser("doctor", help="Tizim salomatligini tekshirish (MVP tayyorlik)")
    p_doc.set_defaults(func=cmd_doctor)

    p_demo = subparsers.add_parser("demo", help="Agentga tayyor demo vazifa berish va natijani ko'rish")
    p_demo.add_argument("agent", nargs="?", default="scout", help="Agent nomi (scout, painter, editor...)")
    p_demo.set_defaults(func=cmd_demo)

    # result
    p_res = subparsers.add_parser("result", help="Vazifa natijasi: dalil + chiqqan artefakt fayllar yo'li")
    p_res.add_argument("task_id", help="Vazifa ID raqami")
    p_res.set_defaults(func=cmd_result)

    # screenshot
    p_shot = subparsers.add_parser("screenshot", help="Brauzer oynasi kadrini faylga saqlash")
    p_shot.add_argument("out", nargs="?", default=None, help="Saqlanadigan fayl yo'li (default: conduit_screenshot.jpg)")
    p_shot.set_defaults(func=cmd_screenshot)

    # browser
    p_br = subparsers.add_parser("browser", help="Brauzer oynasini URL'ga yo'naltirish")
    p_br.add_argument("url", help="Ochiladigan URL (masalan: https://example.com)")
    p_br.set_defaults(func=cmd_browser)

    parser.add_argument("--json", action="store_true", help="Chiqishni JSON qilib berish (agentlar uchun)")

    # --json istalgan pozitsiyada ishlashi uchun (conduit list --json ham,
    # conduit --json list ham) avval argv'dan ajratib olamiz.
    raw_argv = sys.argv[1:]
    json_flag = "--json" in raw_argv
    raw_argv = [a for a in raw_argv if a != "--json"]

    args = parser.parse_args(raw_argv)
    args.json = json_flag
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
