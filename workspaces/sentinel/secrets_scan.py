import os
import re

PATTERNS = [
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
    (r'sk-[A-Za-z0-9]{20,}', 'OpenAI / Secret Key'),
    (r'ghp_[A-Za-z0-9]{20,}', 'GitHub Personal Access Token'),
    (r'gho_[A-Za-z0-9]{20,}', 'GitHub OAuth Token'),
    (r'glpat-[A-Za-z0-9_\-]{20,}', 'GitLab Personal Access Token'),
    (r'xox[baprs]-[0-9A-Za-z\-]{10,}', 'Slack Token'),
    (r'(?i)(?:api_key|apikey|secret_key|private_key|auth_token)\s*[:=]\s*["\']([A-Za-z0-9_\-\.]{16,})["\']', 'Generic Secret Key'),
    (r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----', 'Private Key')
]

painter_dir = r"C:\Users\Kapitan\conduit\workspaces\painter"
results = []
checked_files = []

for root, dirs, files in os.walk(painter_dir):
    for f in files:
        if f.endswith(('.png', '.pyc', '.jpg', '.jpeg', '.gif')):
            continue
        filepath = os.path.join(root, f)
        checked_files.append(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as handle:
                content = handle.read()
                for pat, label in PATTERNS:
                    matches = re.findall(pat, content)
                    if matches:
                        results.append({
                            "file": filepath,
                            "type": label,
                            "matches": matches
                        })
        except Exception as e:
            results.append({"file": filepath, "error": str(e)})

print("CHECKED_FILES_COUNT:", len(checked_files))
for cf in checked_files:
    print("CHECKED:", cf)

print("LEAKS_FOUND:", len(results))
for r in results:
    print("LEAK:", r)
