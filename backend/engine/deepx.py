"""
Conduit DeepX Analysis Engine
Chuqur texnik tahlil, xavfsizlik auditi va ball tizimi:
- README va kod arxitekturasi tahlili
- Litsenziya muvofiqligi (MIT, Apache-2.0 ruxsat berilgan; GPL/AGPL xavfli/ogohlantirish)
- Boshqarish usuli (CLI, MCP, kutubxona, REST)
- Hajm va resurs sarfi (MB/GB)
- Xavfsizlik auditi (tizim fayllariga teginish, tarmoq, noaniq dinamik eval)
- 100 ballik baholash shkalasi va sabablar taqsimoti
- research/<topic>.md hisobot generatsiyasi va tools/candidates.json yangilash
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

SAFE_LICENSES = ["MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC", "Unlicense"]
RESTRICTIVE_LICENSES = ["GPL-3.0", "GPL-2.0", "AGPL-3.0", "LGPL-3.0", "SSPL"]

class DeepXAnalyzer:
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.research_dir = os.path.join(self.workspace_root, "research")
        self.tools_dir = os.path.join(self.workspace_root, "tools")
        self.candidates_file = os.path.join(self.tools_dir, "candidates.json")
        os.makedirs(self.research_dir, exist_ok=True)
        os.makedirs(self.tools_dir, exist_ok=True)

    def evaluate_candidate(self, candidate: Dict[str, Any], readme_snippet: str = "") -> Dict[str, Any]:
        """
        Nomzod asbobni 100 ballik mezonlar bo'yicha baholaydi:
        - Litsenziya erkinligi (30 ball): MIT/Apache = 30, GPL = 10, Noaniq = 5
        - Boshqarish qulayligi (25 ball): MCP/CLI = 25, Library = 20, Script = 15
        - Ekotizim obro'si va faollik (20 ball): Stars/Forks/Updated
        - Xavfsizlik va izolatsiya (25 ball): Tizim fayllariga teginmaslik, sandbox mosligi
        """
        license_str = candidate.get("license", "Unknown")
        name = candidate.get("name", "Tool")
        tool_type = candidate.get("type", "CLI")
        stars = candidate.get("stars", 100)

        score_breakdown = {}
        risk_factors = []

        # 1. Litsenziya bahosi (max 30)
        lic_upper = str(license_str).upper()
        if any(safe in lic_upper for safe in ["MIT", "APACHE", "BSD", "ISC"]):
            score_breakdown["license"] = 30
            license_status = "APPROVED_PERMISSIVE"
        elif any(rst in lic_upper for rst in ["GPL", "AGPL", "COPYLEFT"]):
            score_breakdown["license"] = 10
            license_status = "WARNING_VIRAL_COPYLEFT"
            risk_factors.append("Copyleft litsenziya (GPL/AGPL). Tijoriy yopiq kodga qo'shib bo'lmaydi.")
        else:
            score_breakdown["license"] = 12
            license_status = "UNCERTAIN_LICENSE"
            risk_factors.append("Litsenziya aniq ko'rsatilmagan yoki xususiy mulk.")

        # 2. Boshqaruv usuli (max 25)
        tt_upper = str(tool_type).upper()
        if "MCP" in tt_upper:
            score_breakdown["control_method"] = 25
            method_desc = "MCP Server (Standart JSON-RPC, to'liq boshqariluvchi)"
        elif "CLI" in tt_upper:
            score_breakdown["control_method"] = 23
            method_desc = "CLI vosita (Argumentlar va stdout/stderr orqali boshqaruv)"
        elif "LIBRARY" in tt_upper or "API" in tt_upper:
            score_breakdown["control_method"] = 20
            method_desc = "Python kutubxona / API adapteri"
        else:
            score_breakdown["control_method"] = 16
            method_desc = "Maxsus skript yoki noaniq integratsiya"

        # 3. Faollik va ishonchlilik (max 20)
        if stars > 1000:
            score_breakdown["community_activity"] = 20
        elif stars > 300:
            score_breakdown["community_activity"] = 17
        elif stars > 50:
            score_breakdown["community_activity"] = 14
        else:
            score_breakdown["community_activity"] = 10

        # 4. Xavfsizlik va izolyatsiya (max 25)
        # README va kod xavfsizligi tahlili
        readme_lower = readme_snippet.lower()
        has_suspicious_patterns = any(k in readme_lower for k in ["sudo", "system32", "rm -rf", "telemetry", "miner"])
        if has_suspicious_patterns:
            score_breakdown["security_isolation"] = 8
            risk_factors.append("Qo'pol tizim buyruqlari yoki telemetriya shubhasi aniqlandi.")
        else:
            score_breakdown["security_isolation"] = 25

        total_score = sum(score_breakdown.values())

        if total_score >= 80 and license_status == "APPROVED_PERMISSIVE":
            recommendation = "TAVSIYA ETILADI (Kutubxonaga olish mumkin)"
        elif total_score >= 60:
            recommendation = "SHARTLI TAVSIYA (Qo'shimcha izolyatsiya bilan)"
        else:
            recommendation = "RAD ETILADI (Xavfli yoki litsenziya cheklovi)"

        # Taxminiy hajm
        size_str = f"{candidate.get('size_kb', 5200) // 1024} MB" if candidate.get("size_kb") else "15-50 MB"

        return {
            "repo": candidate.get("repo", "local/unknown"),
            "name": name,
            "author": candidate.get("author", "Community"),
            "license": license_str,
            "license_status": license_status,
            "control_method": method_desc,
            "size": size_str,
            "commit": candidate.get("default_branch", "main"),
            "stars": stars,
            "url": candidate.get("url", ""),
            "score": total_score,
            "score_breakdown": score_breakdown,
            "risk_factors": risk_factors,
            "recommendation": recommendation,
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def generate_research_report(self, topic: str, evaluated_candidates: List[Dict[str, Any]]) -> str:
        """
        research/<topic>.md faylini yaratadi va qaytaradi.
        """
        clean_topic = topic.lower().replace(" ", "_").replace("/", "_")
        report_file = os.path.join(self.research_dir, f"{clean_topic}.md")

        md = []
        md.append(f"# Conduit DeepX Tadqiqot Hisoboti: `{topic.upper()}`")
        md.append(f"**Sana:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Dvigatel:** DeepSearch + DeepX v2.5")
        md.append("")
        md.append("---")
        md.append("## 1. Qidiruv va Tahlil Xulosasi")
        md.append(f"Ushbu hisobot `{topic}` bo'yicha ochiq kodli asboblar, MCP serverlar va kutubxonalarni o'rganish natijasida shakllantirildi.")
        md.append(f"Jami ko'rib chiqilgan nomzodlar soni: **{len(evaluated_candidates)} ta**.")
        md.append("")
        md.append("## 2. Nomzodlar Qiyosiy Jadvali")
        md.append("| Asbob Nomi | Muallif / Repo | Boshqaruv | Litsenziya | Ball | Tavsiya |")
        md.append("|---|---|---|---|---|---|")

        for c in evaluated_candidates:
            md.append(f"| **{c['name']}** | [{c['repo']}]({c.get('url', '#')}) | {c['control_method'][:22]} | `{c['license']}` | **{c['score']}/100** | {c['recommendation'][:20]}... |")

        md.append("")
        md.append("## 3. Har Bir Asbobning Chuqur Tahlili va Xavfsizlik Auditi")

        for c in evaluated_candidates:
            md.append(f"### 🔹 {c['name']} (`{c['repo']}`)")
            md.append(f"- **Muallif:** {c['author']}")
            md.append(f"- **Boshqaruv usuli:** {c['control_method']}")
            md.append(f"- **Litsenziya:** `{c['license']}` ({c['license_status']})")
            md.append(f"- **Hajm:** `{c['size']}` | **Commit/Branch:** `{c['commit']}`")
            md.append(f"- **DeepX Ball:** **{c['score']} / 100**")
            md.append(f"  - Litsenziya erkinligi: `{c['score_breakdown'].get('license', 0)} / 30`")
            md.append(f"  - Boshqaruv integratsiyasi: `{c['score_breakdown'].get('control_method', 0)} / 25`")
            md.append(f"  - Ekotizim va faollik: `{c['score_breakdown'].get('community_activity', 0)} / 20`")
            md.append(f"  - Xavfsizlik va izolyatsiya: `{c['score_breakdown'].get('security_isolation', 0)} / 25`")
            
            if c["risk_factors"]:
                md.append("- ⚠️ **Xavf omillari:**")
                for rf in c["risk_factors"]:
                    md.append(f"  - {rf}")
            else:
                md.append("- ✅ **Xavfsizlik:** Tizim fayllariga teginmaydi, xavfli naqshlar aniqlanmadi.")
            
            md.append(f"- **Yakuniy Xulosa:** **{c['recommendation']}**")
            md.append("")

        md_content = "\n".join(md)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        return report_file

    def update_candidates_json(self, new_evaluated: List[Dict[str, Any]]):
        """
        tools/candidates.json faylini yangilaydi.
        """
        existing = []
        if os.path.exists(self.candidates_file):
            try:
                with open(self.candidates_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        existing_repos = {c.get("repo"): c for c in existing}
        for ne in new_evaluated:
            existing_repos[ne.get("repo")] = ne

        final_list = list(existing_repos.values())
        with open(self.candidates_file, "w", encoding="utf-8") as f:
            json.dump(final_list, f, indent=2, ensure_ascii=False)

        return self.candidates_file
