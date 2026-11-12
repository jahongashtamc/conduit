"""Conduit DeepSearch — real, multi-source search.

Every source here is a live network lookup; nothing is a hand-written list of
repositories that may no longer exist. Sources:

1. GitHub repository search (REST, live)
2. GitHub code search (REST, live) — finds real usage examples
3. npm registry search (live)
4. PyPI simple index (live)
5. Local project files + learned lessons (offline, always available)

Each hit is normalised into the same candidate shape so DeepX can score it.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import urllib.parse
from typing import Any, Dict, List, Optional

import httpx

GITHUB_API = "https://api.github.com"
NPM_API = "https://registry.npmjs.org/-/v1/search"
PYPI_API = "https://pypi.org/pypi/{name}/json"

LOGGER = logging.getLogger("conduit.deepsearch")

USER_AGENT = "Conduit-Studio-DeepSearch/3.0"
TIMEOUT = 12.0


def _normalise_license(value: Any) -> str:
    if not value:
        return "Unknown"
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("spdx_id") or value.get("name") or "Unknown"
    return "Unknown"


class DeepSearchEngine:
    """Collects candidate tools/libraries for a topic from several live sources."""

    def __init__(self, workspace_root: Optional[str] = None) -> None:
        self.workspace_root = workspace_root or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    # ------------------------------------------------------------------ GitHub
    async def search_github_repos(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """Live GitHub repository search."""
        headers = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": limit}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"{GITHUB_API}/search/repositories", headers=headers, params=params)
                if resp.status_code != 200:
                    LOGGER.warning(
                        "GitHub repo qidiruvi HTTP %s qaytardi (query=%r)",
                        resp.status_code, query,
                    )
                    return []
                items = resp.json().get("items", [])
        except Exception as exc:
            LOGGER.warning("GitHub repo qidiruvi xato berdi (query=%r): %s", query, exc)
            return []

        out = []
        for item in items:
            out.append(
                {
                    "repo": item.get("full_name"),
                    "name": item.get("name"),
                    "author": (item.get("owner") or {}).get("login", ""),
                    "description": item.get("description") or "No description",
                    "url": item.get("html_url"),
                    "license": _normalise_license(item.get("license")),
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "updated_at": item.get("updated_at"),
                    "language": item.get("language"),
                    "topics": item.get("topics") or [],
                    "open_issues": item.get("open_issues_count", 0),
                    "archived": bool(item.get("archived")),
                    "default_branch": item.get("default_branch", "main"),
                    "size_kb": item.get("size", 0),
                    "type": "Repository",
                    "source": "github_repos",
                }
            )
        return out

    async def search_github_code(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Live GitHub code search — shows how a topic is actually used in code."""
        headers = {
            "Accept": "application/vnd.github.text-match+json",
            "User-Agent": USER_AGENT,
        }
        params = {"q": query, "per_page": limit}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"{GITHUB_API}/search/code", headers=headers, params=params)
                if resp.status_code != 200:
                    LOGGER.warning(
                        "GitHub kod qidiruvi HTTP %s qaytardi (query=%r)",
                        resp.status_code, query,
                    )
                    return []
                data = resp.json()
        except Exception as exc:
            LOGGER.warning("GitHub kod qidiruvi xato berdi (query=%r): %s", query, exc)
            return []

        out = []
        for item in data.get("items", []):
            repo = item.get("repository") or {}
            snippets = item.get("text_matches") or []
            snippet = (snippets[0].get("fragment") or "") if snippets else ""
            out.append(
                {
                    "repo": repo.get("full_name"),
                    "name": item.get("name"),
                    "author": (repo.get("owner") or {}).get("login", ""),
                    "description": re.sub(r"\s+", " ", snippet)[:180] or "Code example",
                    "url": item.get("html_url"),
                    "license": "Unknown",
                    "stars": repo.get("stargazers_count", 0),
                    "path": item.get("path"),
                    "type": "Code example",
                    "source": "github_code",
                }
            )
        return out

    # ---------------------------------------------------------------- registries
    async def search_npm(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        params = {"text": query, "size": limit}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(NPM_API, params=params)
                if resp.status_code != 200:
                    LOGGER.warning(
                        "npm qidiruvi HTTP %s qaytardi (query=%r)", resp.status_code, query
                    )
                    return []
                objects = resp.json().get("objects", [])
        except Exception as exc:
            LOGGER.warning("npm qidiruvi xato berdi (query=%r): %s", query, exc)
            return []

        out = []
        for obj in objects:
            pkg = obj.get("package", {})
            links = pkg.get("links", {})
            out.append(
                {
                    "repo": f"npm:{pkg.get('name')}",
                    "name": pkg.get("name"),
                    "author": (pkg.get("author") or {}).get("name", "") if isinstance(pkg.get("author"), dict) else str(pkg.get("author") or ""),
                    "description": (pkg.get("description") or "")[:200],
                    "url": links.get("npm") or links.get("homepage") or "",
                    "license": pkg.get("license") or "Unknown",
                    "stars": 0,
                    "version": pkg.get("version"),
                    "updated_at": pkg.get("date"),
                    "type": "npm package",
                    "source": "npm",
                }
            )
        return out

    async def search_pypi(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """PyPI has no search API; probe likely names derived from the query."""
        words = [w for w in re.split(r"[^a-zA-Z0-9]+", query.lower()) if len(w) > 2]
        guesses = []
        if words:
            guesses.append("".join(words[:2]))
            guesses.append("-".join(words[:2]))
            guesses.extend(words[:3])
        guesses = list(dict.fromkeys(guesses))[:limit]

        out: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for name in guesses:
                try:
                    resp = await client.get(PYPI_API.format(name=urllib.parse.quote(name)))
                    if resp.status_code != 200:
                        continue
                    info = resp.json().get("info", {})
                    out.append(
                        {
                            "repo": f"pypi:{info.get('name', name)}",
                            "name": info.get("name", name),
                            "author": info.get("author") or info.get("author_email") or "",
                            "description": (info.get("summary") or "")[:200],
                            "url": info.get("home_page") or info.get("project_url") or "",
                            "license": info.get("license") or "Unknown",
                            "stars": 0,
                            "version": info.get("version"),
                            "type": "PyPI package",
                            "source": "pypi",
                        }
                    )
                except Exception as exc:
                    LOGGER.warning("PyPI probe xato berdi (name=%r): %s", name, exc)
                    continue
        return out

    # -------------------------------------------------------------------- local
    def search_local(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches this project's own sources and learned lessons (offline)."""
        terms = [t for t in re.split(r"[^a-zA-Z0-9_]+", query.lower()) if len(t) > 3][:6]
        if not terms:
            return []

        hits: List[Dict[str, Any]] = []
        roots = [os.path.join(self.workspace_root, d) for d in ("backend", "subagents", "skills", "research", "tools")]
        seen = 0
        for root in roots:
            if not os.path.isdir(root):
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in {"__pycache__", "node_modules", ".next", ".git"}]
                for fname in filenames:
                    if not fname.endswith((".py", ".md", ".json")):
                        continue
                    seen += 1
                    if seen > 600:
                        break
                    path = os.path.join(dirpath, fname)
                    try:
                        text = open(path, encoding="utf-8", errors="ignore").read().lower()
                    except Exception as exc:
                        LOGGER.warning("Lokal fayl o'qilmadi (%s): %s", path, exc)
                        continue
                    matched = [t for t in terms if t in text]
                    if len(matched) >= 2:
                        rel = os.path.relpath(path, self.workspace_root)
                        hits.append(
                            {
                                "repo": f"file:///{rel.replace(os.sep, '/')}",
                                "name": os.path.basename(path),
                                "author": "Conduit workspace",
                                "description": f"Local match on: {', '.join(matched)}",
                                "url": f"file:///{rel.replace(os.sep, '/')}",
                                "license": "Project",
                                "stars": 0,
                                "type": "Local source",
                                "relevance": len(matched) / max(len(terms), 1),
                                "source": "local",
                            }
                        )
                    if len(hits) >= limit:
                        return hits
        return hits

    # ------------------------------------------------------------------- public
    async def search_candidates_for_topic(self, topic: str, limit: int = 12) -> List[Dict[str, Any]]:
        """Runs every source in parallel and merges de-duplicated candidates."""
        results = await asyncio.gather(
            self.search_github_repos(topic, limit=8),
            self.search_github_code(topic, limit=4),
            self.search_npm(topic, limit=4),
            self.search_pypi(topic, limit=3),
            return_exceptions=True,
        )

        merged: List[Dict[str, Any]] = []
        for batch in results:
            if isinstance(batch, Exception):
                continue
            merged.extend(batch)

        local = self.search_local(topic, limit=4)
        merged.extend(local)

        # De-duplicate by repo key, keeping the entry with more signal.
        by_key: Dict[str, Dict[str, Any]] = {}
        for cand in merged:
            key = (cand.get("repo") or cand.get("url") or "").lower()
            if not key:
                continue
            prev = by_key.get(key)
            if prev is None or (cand.get("stars", 0) > prev.get("stars", 0)):
                by_key[key] = cand

        ordered = sorted(
            by_key.values(),
            key=lambda c: (c.get("stars", 0), c.get("relevance", 0)),
            reverse=True,
        )
        return ordered[:limit]

    async def fetch_readme(self, repo_full_name: str) -> str:
        """Fetches a README through the GitHub API (no browser needed)."""
        headers = {"Accept": "application/vnd.github.raw+json", "User-Agent": USER_AGENT}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"{GITHUB_API}/repos/{repo_full_name}/readme", headers=headers)
                if resp.status_code == 200:
                    return resp.text[:8000]
                LOGGER.warning(
                    "README HTTP %s qaytardi (repo=%r)", resp.status_code, repo_full_name
                )
        except Exception as exc:
            LOGGER.warning("README olinmadi (repo=%r): %s", repo_full_name, exc)
        return ""
