import urllib.request
import json
import sys
import os

sys.path.insert(0, r"C:\Users\Kapitan\.gemini\antigravity\scratch\conduit\backend")
import database

# 1. Create skill
sk_req = urllib.request.Request(
    'http://127.0.0.1:8000/api/skills',
    data=json.dumps({
        'name': "SEO Metama'lumotlarni tahlil qilish",
        'description': "Web sahifaning title, meta description va OpenGraph teglari sifatini audit qiladi.",
        'prompt_template': "Berilgan sahifa kodidagi SEO teglarni ajratib ol va audit hisoboti tuz.",
        'target_subagents': ["scout"],
        'trigger_keywords': ["seo", "meta", "og", "audit"],
        'force': True
    }).encode(),
    headers={'Content-Type': 'application/json'}
)
sk_res = json.loads(urllib.request.urlopen(sk_req).read())
print("Created skill:", sk_res["id"], sk_res["name"])

# Test skill
test_req = urllib.request.Request(
    f"http://127.0.0.1:8000/api/skills/{sk_res['id']}/test",
    data=json.dumps({"test_prompt": "https://antigravity.dev sayti metateglarini tekshir"}).encode(),
    headers={"Content-Type": "application/json"}
)
test_res = json.loads(urllib.request.urlopen(test_req).read())
print("Test result:", test_res["status"], test_res["result_preview"])

# 2. Create Dangerous Approval
database.create_approval(
    approval_id="appr_dang_rm",
    task_id="task_audit_01",
    agent_id="inspector",
    action_type="file_delete",
    risk_description="Tizimdagi kesh va eski log fayllarini butunlay o'chirish (rm -rf /cache /logs)",
    details={"command": "rm -rf /cache /logs"}
)
print("Created dangerous approval: appr_dang_rm")
