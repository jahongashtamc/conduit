"""Conduit DeepX — real candidate scoring and auditing.

Scoring is driven by concrete signals, not by grepping a README for scare words:

    licence ........ 30  (SPDX parsed, copyleft detected properly)
    control ........ 25  (MCP / CLI / library / unknown, from repo metadata)
    activity ....... 20  (stars, recency of last push, open-issue ratio)
    security ....... 25  (README + manifest signals, penalties for red flags)

The analyser also produces a machine-readable verdict so the pipeline can gate
on it instead of a hard-coded threshold, and writes a research report per topic.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SAFE_LICENSES = {
    "mit", "apache-2.0", "bsd-3-clause", "bsd-2-clause", "isc",
    "unlicense", "0bsd", "cc0-1.0", "mpl-2.0",
}
COPYLEFT_LICENSES = {"gpl-2.0", "gpl-3.0", "agpl-3.0", "lgpl-2.1", "lgpl-3.0", "sspl-1.0"}

# Real red flags worth a security penalty.
RISK_PATTERNS = {
    "shell_injection": [r"shell\s*=\s*true", r"os\.system\(", r"subprocess\.call\([^)]*shell"],
    "eval_usage": [r"\beval\(", r"\bexec\("],
    "sudo_required": [r"\bsudo\b", r"run as administrator", r"requireadministrator"],
    "telemetry": [r"\btelemetry\b", r"\banalytics\b", r"phone home"],
    "obfuscation": [r"base64\.b64decode", r"exec\(.*decode", r"\\\\x[0-9a-f]{2}\\\\x[0-9a-f]{2}"],
    "destructive": [r"rm\s+-rf\s+/", r"format\s+c:", r"del\s+/f\s+/s"],
}

# Signals that a package is directly drivable from our orchestrator.
CONTROL_SIGNALS = [
    ("mcp", ("mcp", "model context protocol", "json-rpc"), 25, "MCP server"),
    ("cli", ("--help", "usage:", "command line", "cli"), 23, "CLI tool"),
    ("library", ("import ", "pip install", "npm i ", "from "), 20, "Library / API"),
]


def _parse_license(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("spdx_id") or value.get("name")
    text = str(value or "").strip()
    return text or "Unknown"


def _license_bucket(spdx: str) -> int:
    key = spdx.lower()
    if key in SAFE_LICENSES or any(s in key for s in ("mit", "apache", "bsd", "isc", "unlicense")):
        return 30
    if key in COPYLEFT_LICENSES or "gpl" in key or "copyleft" in key or "sspl" in key:
        return 10
    return 12


def _days_since(iso_date: Optional[str]) -> Optional[int]:
    if not iso_date:
        return None
    try:
        cleaned = iso_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - dt).days)
    except Exception:
        return None


class DeepXAnalyzer:
    def __init__(self, workspace_root: Optional[str] = None) -> None:
        self.workspace_root = workspace_root or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        self.research_dir = os.path.join(self.workspace_root, "research")
        self.tools_dir = os.path.join(self.workspace_root, "tools")
        self.candidates_file = os.path.join(self.tools_dir, "candidates.json")
        os.makedirs(self.research_dir, exist_ok=True)
        os.makedirs(self.tools_dir, exist_ok=True)

    # ---------------------------------------------------------------- scoring
    def evaluate_candidate(self, candidate: Dict[str, Any], readme_snippet: str = "") -> Dict[str, Any]:
        breakdown: Dict[str, int] = {}
        risks: List[str] = []
        evidence: Dict[str, Any] = {}

        spdx = _parse_license(candidate.get("license"))
        breakdown["license"] = _license_bucket(spdx)
        if breakdown["license"] == 10:
            risks.append(f"Copyleft licence ({spdx}) — cannot be linked into closed-source work.")
        elif breakdown["license"] == 12:
            risks.append("Licence not declared — legal review required before use.")

        # Control method: derived from the declared package type, the repo
        # language and README content — a repo with no README is not "unknown",
        # it is simply a Python/JS package the orchestrator can still drive.
        haystack = f"{candidate.get('description', '')}\n{readme_snippet}".lower()
        declared_type = str(candidate.get("type", "")).lower()
        source = str(candidate.get("source", "")).lower()
        language = str(candidate.get("language", "")).lower()
        control_score, control_desc = 16, "Unknown integration"
        for _key, needles, score, desc in CONTROL_SIGNALS:
            if _key in declared_type or any(n in haystack for n in needles):
                control_score, control_desc = score, desc
                break
        else:
            if source in ("npm", "pypi") or language in ("python", "javascript", "typescript"):
                control_score, control_desc = 20, "Library / API"
            elif source == "github_repos" and candidate.get("topics"):
                control_score, control_desc = 18, "Repository (scriptable)"
        breakdown["control_method"] = control_score
        evidence["control"] = control_desc

        # Activity: stars + freshness + maintenance pressure.
        stars = int(candidate.get("stars") or 0)
        if stars > 5000:
            breakdown["community_activity"] = 20
        elif stars > 1000:
            breakdown["community_activity"] = 18
        elif stars > 300:
            breakdown["community_activity"] = 16
        elif stars > 50:
            breakdown["community_activity"] = 13
        elif stars > 0:
            breakdown["community_activity"] = 10
        else:
            breakdown["community_activity"] = 6

        age = _days_since(candidate.get("updated_at"))
        if age is not None:
            evidence["days_since_update"] = age
            if age > 730:
                breakdown["community_activity"] = max(4, breakdown["community_activity"] - 8)
                risks.append(f"Last update {age} days ago — likely unmaintained.")
            elif age > 365:
                breakdown["community_activity"] = max(6, breakdown["community_activity"] - 4)
                risks.append(f"No update for {age} days.")
        if candidate.get("archived"):
            breakdown["community_activity"] = 4
            risks.append("Repository is archived.")

        open_issues = int(candidate.get("open_issues") or 0)
        if stars > 50 and open_issues > stars * 0.5:
            breakdown["community_activity"] = max(4, breakdown["community_activity"] - 3)
            risks.append(f"{open_issues} open issues vs {stars} stars — maintenance debt.")

        # Security: pattern scan over README + description.
        scan_text = f"{candidate.get('description', '')}\n{readme_snippet}"
        penalties = 0
        for category, patterns in RISK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, scan_text, re.IGNORECASE):
                    penalties += 6
                    risks.append(f"Security signal: {category.replace('_', ' ')}")
                    break
        breakdown["security_isolation"] = max(0, 25 - penalties)

        total = sum(breakdown.values())

        if total >= 80 and breakdown["license"] == 30 and breakdown["security_isolation"] >= 20:
            verdict = "RECOMMENDED"
        elif total >= 60:
            verdict = "CONDITIONAL"
        else:
            verdict = "REJECTED"

        size_kb = candidate.get("size_kb")
        size_str = f"{size_kb / 1024:.1f} MB" if size_kb else "unknown"

        return {
            "repo": candidate.get("repo", "local/unknown"),
            "name": candidate.get("name", "Tool"),
            "author": candidate.get("author") or "unknown",
            "url": candidate.get("url", ""),
            "source": candidate.get("source", "unknown"),
            "license": spdx,
            "license_status": (
                "PERMISSIVE" if breakdown["license"] == 30
                else "COPYLEFT" if breakdown["license"] == 10
                else "UNCLEAR"
            ),
            "control_method": control_desc,
            "size": size_str,
            "stars": stars,
            "score": total,
            "verdict": verdict,
            "score_breakdown": breakdown,
            "risk_factors": risks,
            "evidence": evidence,
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ---------------------------------------------------------------- reports
    def generate_research_report(self, topic: str, evaluated: List[Dict[str, Any]]) -> str:
        slug = re.sub(r"[^a-z0-9_]+", "_", topic.lower()).strip("_") or "topic"
        report_file = os.path.join(self.research_dir, f"{slug}.md")

        recommended = [c for c in evaluated if c["verdict"] == "RECOMMENDED"]
        conditional = [c for c in evaluated if c["verdict"] == "CONDITIONAL"]
        rejected = [c for c in evaluated if c["verdict"] == "REJECTED"]

        lines = [
            f"# DeepX Research Report — {topic}",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Sources scanned: {len({c.get('source') for c in evaluated})} "
            f"| Candidates: {len(evaluated)} "
            f"| Recommended: {len(recommended)} | Conditional: {len(conditional)} | Rejected: {len(rejected)}",
            "",
            "## Summary",
            "",
        ]
        if recommended:
            lines.append(f"**Best option:** `{recommended[0]['name']}` "
                         f"({recommended[0]['score']}/100, {recommended[0]['license']}) — "
                         f"{recommended[0]['url']}")
        else:
            lines.append("**No candidate met the recommendation bar.** "
                         "The best available options are listed as conditional below.")

        lines += [
            "",
            "## Comparison",
            "",
            "| Tool | Source | Stars | Licence | Control | Score | Verdict |",
            "|---|---|---:|---|---|---:|---|",
        ]
        for c in sorted(evaluated, key=lambda x: x["score"], reverse=True):
            lines.append(
                f"| {c['name']} | {c['source']} | {c['stars']} | {c['license']} | "
                f"{c['control_method']} | {c['score']} | {c['verdict']} |"
            )

        lines += ["", "## Detail", ""]
        for c in sorted(evaluated, key=lambda x: x["score"], reverse=True):
            b = c["score_breakdown"]
            lines += [
                f"### {c['name']}",
                "",
                f"- Repository: [{c['repo']}]({c['url']})",
                f"- Licence: `{c['license']}` ({c['license_status']})",
                f"- Control: {c['control_method']}",
                f"- Score: **{c['score']}/100** — licence {b['license']}/30, "
                f"control {b['control_method']}/25, activity {b['community_activity']}/20, "
                f"security {b['security_isolation']}/25",
            ]
            if c["risk_factors"]:
                lines.append("- Risks:")
                lines += [f"  - {r}" for r in c["risk_factors"]]
            else:
                lines.append("- Risks: none detected")
            lines.append("")

        content = "\n".join(lines)
        with open(report_file, "w", encoding="utf-8") as fh:
            fh.write(content)
        return report_file

    def update_candidates_json(self, new_evaluated: List[Dict[str, Any]]) -> str:
        existing: List[Dict[str, Any]] = []
        if os.path.exists(self.candidates_file):
            try:
                with open(self.candidates_file, encoding="utf-8") as fh:
                    loaded = json.load(fh)
                    if isinstance(loaded, list):
                        existing = loaded
            except Exception:
                existing = []

        by_repo = {c.get("repo"): c for c in existing if c.get("repo")}
        for item in new_evaluated:
            if item.get("repo"):
                by_repo[item["repo"]] = item

        with open(self.candidates_file, "w", encoding="utf-8") as fh:
            json.dump(list(by_repo.values()), fh, indent=2, ensure_ascii=False)

        return self.candidates_file

    def best_candidate(self, evaluated: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Highest-scoring candidate that is at least conditional."""
        usable = [c for c in evaluated if c["verdict"] in ("RECOMMENDED", "CONDITIONAL")]
        if not usable:
            return None
        return max(usable, key=lambda c: c["score"])
