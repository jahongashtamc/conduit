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

API_BASE = os.environ.get("CONDUIT_API_URL", "http://127.0.0.1:8000")

def _request(endpoint: str, method: str = "GET", data: dict = None):
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
        try:
            err_json = json.loads(err_msg)
            print(f"[CONDUIT ERROR {e.code}] {err_json.get('detail', err_msg)}", file=sys.stderr)
        except Exception:
            print(f"[CONDUIT ERROR {e.code}] {err_msg}", file=sys.stderr)
        sys.exit(1)
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
        
    print(f"\033[32m[YARATILDI]\033[0m Vazifa ID: \033[1;36m{task_id}\033[0m")
    print(f"  Subagent: \033[1m{subagent}\033[0m")
    print(f"  Kuzatish: \033[90mconduit status {task_id}\033[0m")
    print(f"  Kutish:   \033[90mconduit wait {task_id}\033[0m")
    return task_id

def cmd_wait(args):
    task_ids: List[str] = args.task_ids
    if not task_ids:
        print("[XATO] Kamida bitta task_id ko'rsatilishi kerak.", file=sys.stderr)
        sys.exit(1)
        
    print(f"\033[33m[KUTILMOQDA]\033[0m {len(task_ids)} ta vazifa kuzatilmoqda: {', '.join(task_ids)}")
    start_time = time.time()
    
    completed_tasks: Dict[str, Dict[str, Any]] = {}
    
    while len(completed_tasks) < len(task_ids):
        for tid in task_ids:
            if tid in completed_tasks:
                continue
            resp = _request(f"/api/tasks/{tid}")
            task_data = resp.get("task", resp) if isinstance(resp, dict) else {}
            status = task_data.get("status", "working")
            step = task_data.get("current_step", "planner")
            
            if status in ("PASS", "FAIL", "BLOCKED"):
                completed_tasks[tid] = task_data
                durations = task_data.get("step_durations", {})
                total_dur = task_data.get("total_duration", round(time.time() - start_time, 2))
                
                status_color = "\033[32m" if status == "PASS" else "\033[31m" if status == "FAIL" else "\033[33m"
                status_icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[BLOCKED]"
                print(f"  {status_color}{status_icon}\033[0m {tid} ({task_data.get('target_agent')}) | {total_dur}s")
                if task_data.get("evidence"):
                    print(f"     Dalil: {task_data.get('evidence')[:100]}")
                    
        if len(completed_tasks) < len(task_ids):
            time.sleep(1.0)
            if time.time() - start_time > 300:
                print("\n\033[31m[TIMEOUT]\033[0m 300s kutish vaqti tugadi.", file=sys.stderr)
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
    subagents = _request("/api/subagents")
    print("\n\033[1;36mCONDUIT RO'YXATGA OLINGAN SUBAGENTLAR:\033[0m")
    print(f"{'Nomi':<15} {'Holati':<10} {'Tavsifi':<40}")
    print("-" * 65)
    for ag in subagents:
        name = ag.get("name", "")
        status = ag.get("status", "unknown")
        desc = ag.get("role_desc_uz") or ag.get("role_desc_en", "")
        color = "\033[32m" if status == "active" else "\033[90m"
        print(f"{name:<15} {color}{status:<10}\033[0m {desc[:40]:<40}")
    print()

def cmd_kill_all(args):
    res = _request("/api/kill-all", method="POST")
    print("\033[31m[HAMMASINI TO'XTATISH]\033[0m", res.get("message", "Barcha jarayonlar to'xtatildi."))

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
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
        
    args.func(args)

if __name__ == "__main__":
    main()
