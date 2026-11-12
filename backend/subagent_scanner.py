import os
import json
from typing import List, Dict, Any

SUBAGENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "subagents"))

def scan_subagents() -> List[Dict[str, Any]]:
    if not os.path.exists(SUBAGENTS_DIR):
        return []

    subagents = []
    for entry in os.scandir(SUBAGENTS_DIR):
        if entry.is_dir():
            folder_path = entry.path
            agent_id = entry.name

            app_json_path = os.path.join(folder_path, "app.json")
            role_md_path = os.path.join(folder_path, "role.md")
            inner_dir = os.path.join(folder_path, "inner")

            meta = {}
            if os.path.exists(app_json_path):
                try:
                    with open(app_json_path, "r", encoding="utf-8-sig") as f:
                        meta = json.load(f)
                except Exception as e:
                    print(f"Error reading {app_json_path}: {e}")

            role_content = ""
            if os.path.exists(role_md_path):
                try:
                    with open(role_md_path, "r", encoding="utf-8") as f:
                        role_content = f.read()
                except Exception as e:
                    print(f"Error reading {role_md_path}: {e}")

            # Check inner steps
            planner_exists = os.path.exists(os.path.join(inner_dir, "planner.md"))
            doer_exists = os.path.exists(os.path.join(inner_dir, "doer.md"))
            checker_exists = os.path.exists(os.path.join(inner_dir, "checker.md"))

            subagents.append({
                "id": meta.get("id", agent_id),
                "name": meta.get("name", agent_id.capitalize()),
                "display_name_uz": meta.get("display_name_uz", agent_id.capitalize()),
                "display_name_en": meta.get("display_name_en", agent_id.capitalize()),
                "role_desc_uz": meta.get("role_desc_uz", ""),
                "role_desc_en": meta.get("role_desc_en", ""),
                "target_app": meta.get("target_app", "General"),
                "status": meta.get("status", "later"),
                "icon": meta.get("icon", "Bot"),
                "version": meta.get("version", "1.0.0"),
                "role_summary": role_content[:200] if role_content else "",
                "has_planner": planner_exists,
                "has_doer": doer_exists,
                "has_checker": checker_exists
            })

    # Sort so active ones (scout, inspector) are at the top
    subagents.sort(key=lambda a: (0 if a.get("status") == "active" else 1, a.get("id")))
    return subagents
