import os
import json

SUBAGENTS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "subagents"))

def create_dynamic_subagent(
    agent_id: str,
    app_name: str,
    category: str = "Productivity",
    role_description: str = ""
) -> bool:
    """
    Vazifa talab qilgan yangi subagent papkasi va fayllarini mavjud shablon asosida yaratadi:
    - subagents/<nom>/app.json
    - subagents/<nom>/role.md
    - subagents/<nom>/inner/planner.md, doer.md, checker.md
    - workspaces/<nom>/
    """
    clean_id = agent_id.strip().lower()
    target_dir = os.path.join(SUBAGENTS_ROOT, clean_id)
    inner_dir = os.path.join(target_dir, "inner")
    
    os.makedirs(inner_dir, exist_ok=True)
    
    # 1. app.json
    app_meta = {
        "id": clean_id,
        "name": app_name,
        "display_name_uz": f"{app_name} (Avto)",
        "display_name_en": f"{app_name} (Auto)",
        "role_desc_uz": role_description or f"{app_name} bilan bog'liq vazifalarni avtomatlashtirish",
        "role_desc_en": f"Automated tasks and workflows for {app_name}",
        "target_app": app_name,
        "status": "active",
        "icon": "Box",
        "version": "1.0.0"
    }
    with open(os.path.join(target_dir, "app.json"), "w", encoding="utf-8") as f:
        json.dump(app_meta, f, indent=2)

    # 2. role.md — never overwrite an existing agent's real tool list with the
    # generic template; that silently stripped roles like slack of their
    # dedicated tools (slack_api) after a dynamic re-registration.
    role_path = os.path.join(target_dir, "role.md")
    if os.path.exists(role_path):
        with open(role_path, "r", encoding="utf-8") as f:
            existing = f.read()
        if "## Ruxsat etilgan toollar" in existing:
            return True  # real role already configured — leave it alone
    role_content = f"""# Subagent: {app_name}

## Holat
Faol (Dinamik qo'shilgan)

## Vazifasi
{app_name} ilovasi bilan integratsiya va topshiriqlarni xavfsiz bajarish.

## Ruxsat etilgan toollar
- `screenshot`
- `interact_web`
- `run_process`
- `get_logs`
- `check_goal`
"""
    with open(os.path.join(target_dir, "role.md"), "w", encoding="utf-8") as f:
        f.write(role_content)

    # 3. inner/planner.md, doer.md, checker.md
    with open(os.path.join(inner_dir, "planner.md"), "w", encoding="utf-8") as f:
        f.write(f"# {app_name} Planner\n{app_name} vazifalari ketma-ketligini rejalashtirish.\n")

    with open(os.path.join(inner_dir, "doer.md"), "w", encoding="utf-8") as f:
        f.write(f"# {app_name} Doer\n{app_name} amallarini tools.py orqali bajarish.\n")

    with open(os.path.join(inner_dir, "checker.md"), "w", encoding="utf-8") as f:
        f.write(f"# {app_name} Checker\n{app_name} yakuniy dalili va natijalarini tekshirish.\n")

    # 4. Workspace yaratish
    from workspace_manager import get_agent_workspace
    get_agent_workspace(clean_id)

    # 5. Apps.json ga kiritish
    from apps_manager import add_app_to_registry
    add_app_to_registry(clean_id, app_name, category)

    # 6. Memoryga yozish
    try:
        import memory_manager
        memory_manager.append_decision(
            f"Yangi ilova va subagent qo'shildi: {app_name} ({clean_id}) - foydalanuvchi tasdig'i bilan."
        )
    except Exception:
        pass

    return True
