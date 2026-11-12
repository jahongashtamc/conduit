import os
import json
import shutil
import psutil
from typing import List, Dict, Any

APPS_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps.json"))

def get_apps_status() -> List[Dict[str, Any]]:
    if not os.path.exists(APPS_JSON_PATH):
        return []

    try:
        with open(APPS_JSON_PATH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            apps = data.get("apps", [])
    except Exception as e:
        print(f"Error loading apps.json: {e}")
        return []

    # Get all running process names once
    running_processes = set()
    try:
        for proc in psutil.process_iter(['name']):
            try:
                pname = proc.info.get('name')
                if pname:
                    running_processes.add(pname.lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"Error checking processes: {e}")

    result = []
    for app in apps:
        app_id = app.get("id")
        name = app.get("name")
        exe_name = app.get("executable", "").lower()
        common_paths = app.get("common_paths", [])
        icon = app.get("icon", "Box")
        category = app.get("category", "General")
        default_status = app.get("default_status", "not installed")

        # Check if process is currently running
        is_running = False
        if exe_name and exe_name in running_processes:
            is_running = True

        # Check if installed
        is_installed = False
        if is_running:
            is_installed = True
        else:
            # Check PATH
            if exe_name and shutil.which(exe_name):
                is_installed = True
            else:
                # Check common paths
                for p in common_paths:
                    expanded = os.path.expandvars(p)
                    if os.path.exists(expanded):
                        is_installed = True
                        break

        # If not detected on disk, use fallback from default_status
        if not is_installed and default_status == "ready":
            is_installed = True

        # Status mapping: Faol / O'rnatilmagan / Keyinroq
        is_enabled = app.get("enabled", True)
        if not is_enabled:
            status_badge = "Keyinroq"
        elif is_installed:
            status_badge = "Faol"
        else:
            status_badge = "O'rnatilmagan"

        status = "running" if is_running else ("ready" if is_installed else "not installed")

        supported_formats = []
        try:
            import app_adapter
            supported_formats = app_adapter.SUPPORTED_FORMATS.get(app_id, [app.get("extension")] if app.get("extension") else [".txt"])
            tpl = app.get("run_template") or app_adapter.RUN_TEMPLATES.get(app_id, "")
        except Exception:
            tpl = app.get("run_template", "")

        result.append({
            "id": app_id,
            "name": name,
            "category": category,
            "status": status,
            "status_badge": status_badge,
            "enabled": is_enabled,
            "is_installed": is_installed,
            "is_running": is_running,
            "icon": icon,
            "executable": app.get("executable"),
            "exe_path": app.get("exe_path") or (common_paths[0] if common_paths else app.get("executable", "")),
            "run_template": tpl,
            "extension": app.get("extension", ""),
            "supported_formats": supported_formats
        })

    return result

def toggle_app_enabled(app_id: str, enabled: bool) -> bool:
    """Ilovani yoqish/o'chirish holatini o'zgartiradi."""
    try:
        if not os.path.exists(APPS_JSON_PATH):
            return False
        with open(APPS_JSON_PATH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        
        updated = False
        for a in data.get("apps", []):
            if a.get("id") == app_id:
                a["enabled"] = enabled
                updated = True
                break
        
        if updated:
            with open(APPS_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        return False
    except Exception as e:
        print(f"Error toggling app: {e}")
        return False

def add_app_to_registry(
    app_id: str,
    name: str,
    category: str = "Productivity",
    executable: str = "",
    exe_path: str = "",
    run_template: str = "",
    extension: str = ""
) -> bool:
    """Yangi ilovani apps.json fayliga rasman qo'shadi."""
    try:
        if not os.path.exists(APPS_JSON_PATH):
            data = {"apps": []}
        else:
            with open(APPS_JSON_PATH, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        
        apps = data.get("apps", [])
        if any(a.get("id") == app_id for a in apps):
            return True
        
        apps.append({
            "id": app_id,
            "name": name,
            "category": category,
            "icon": "Box",
            "executable": executable or f"{app_id}.exe",
            "exe_path": exe_path or executable or f"{app_id}.exe",
            "common_paths": [exe_path] if exe_path else [f"%ProgramFiles%\\{name}\\{app_id}.exe"],
            "run_template": run_template,
            "extension": extension,
            "enabled": True,
            "default_status": "ready"
        })
        data["apps"] = apps
        with open(APPS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error adding app to registry: {e}")
        return False

