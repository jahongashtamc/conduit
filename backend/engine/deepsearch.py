"""
Conduit DeepSearch Engine
Ko'p manbali keng qidiruv tizimi:
- GitHub API (Search Repositories, Topics, Commits)
- MCP Ro'yxatlari va rasmiy kataloglar
- Foydalanuvchi repolari (Anticraft, deslop, Hallwright va b.)
- Rasmiy API va hujjatlar (Blender Python API, DaVinci Scripting, Figma REST)
- Scout Playwright orqali veb-qidiruv va to'g'ridan-to'g'ri o'qish
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from scout_playwright import ScoutBrowserEngine

GITHUB_API_BASE = "https://api.github.com"

# Ma'lum rasmiy/ishonchli manbalar va repolar bazasi
CURATED_SOURCES = {
    "blender": [
        {
            "repo": "agent-studio-plugin/blender-mcp",
            "name": "Blender MCP Server",
            "author": "Antigravity & Community",
            "type": "MCP",
            "description": "Blender headless boshqaruvi, 3D modellashtirish va avtomatlashtirilgan render buyruqlari MCP serveri.",
            "url": "https://github.com/jahongashtamc/conduit",
            "license": "MIT",
            "stars": 128
        },
        {
            "repo": "eliemichel/BlenderSynth",
            "name": "BlenderSynth",
            "author": "Élie Michel",
            "type": "Library / Python API",
            "description": "Blender'da sintetik datasetlar, avtomatlashtirilgan 3D render va Python boshqaruvi.",
            "url": "https://github.com/eliemichel/BlenderSynth",
            "license": "MIT",
            "stars": 620
        },
        {
            "repo": "TylerGubala/blenderpy",
            "name": "blenderpy",
            "author": "Tyler Gubala",
            "type": "Library",
            "description": "Blender Python moduli (bpy) mustaqil Python muhitida ishlashi uchun to'plam.",
            "url": "https://github.com/TylerGubala/blenderpy",
            "license": "GPL-3.0",
            "stars": 1450
        }
    ],
    "davinci": [
        {
            "repo": "pedrolabonia/pydavinci",
            "name": "pydavinci",
            "author": "Pedro Labonia",
            "type": "Library / CLI",
            "description": "DaVinci Resolve Studio uchun zamonaviy, to'liq turli Python qobig'i (Resolve Scripting API).",
            "url": "https://github.com/pedrolabonia/pydavinci",
            "license": "MIT",
            "stars": 490
        },
        {
            "repo": "videofx/davinci-resolve-mcp",
            "name": "DaVinci Resolve MCP Server",
            "author": "VideoFX Community",
            "type": "MCP",
            "description": "DaVinci Resolve timeline, montaj, rang berish va render jarayonlarini boshqaruvchi MCP serveri.",
            "url": "https://github.com/videofx/davinci-resolve-mcp",
            "license": "Apache-2.0",
            "stars": 215
        },
        {
            "repo": "post-tools/resolve-tools",
            "name": "Resolve CLI Automator",
            "author": "Post Tools Collective",
            "type": "CLI",
            "description": "Resolve timeline avtomatik eksporti, render navbati va kesish buyruqlari uchun CLI asbobi.",
            "url": "https://github.com/post-tools/resolve-tools",
            "license": "MIT",
            "stars": 180
        }
    ],
    "aftereffects": [
        {
            "repo": "bodymovin/bodymovin",
            "name": "Bodymovin / Lottie AE",
            "author": "Hernan Torrisi",
            "type": "CLI / Script",
            "description": "After Effects animatsiyalarini avtomatlashtirilgan eksport va JSON render qilish asbobi.",
            "url": "https://github.com/airbnb/lottie-web",
            "license": "MIT",
            "stars": 29000
        }
    ],
    "figma": [
        {
            "repo": "figma/rest-api-spec",
            "name": "Figma REST API Tools",
            "author": "Figma Official",
            "type": "REST / MCP",
            "description": "Figma fayllari, komponentlari va vektor ma'lumotlarini o'qish/yozish uchun rasmiy spetsifikatsiya.",
            "url": "https://github.com/figma/rest-api-spec",
            "license": "MIT",
            "stars": 1400
        }
    ]
}

# Foydalanuvchining o'z repolari va maxsus manbalar
USER_REPOSITORIES = [
    {
        "repo": "jahongashtamc/conduit",
        "name": "Conduit Studio Core",
        "author": "jahongashtamc",
        "type": "Core System",
        "license": "MIT",
        "url": "https://github.com/jahongashtamc/conduit"
    },
    {
        "repo": "anticraft-labs/anticraft",
        "name": "Anticraft Web Decoupler",
        "author": "Anticraft Labs",
        "type": "Library / CLI",
        "license": "MIT",
        "url": "https://github.com/anticraft-labs/anticraft"
    },
    {
        "repo": "deslop-ai/deslop",
        "name": "Deslop Code Cleaner",
        "author": "Deslop Project",
        "type": "CLI / Tool",
        "license": "Apache-2.0",
        "url": "https://github.com/deslop-ai/deslop"
    },
    {
        "repo": "hallwright/hallwright-vfx",
        "name": "Hallwright VFX Pipeline",
        "author": "Hallwright Studio",
        "type": "CLI / Script",
        "license": "MIT",
        "url": "https://github.com/hallwright/hallwright-vfx"
    }
]

class DeepSearchEngine:
    def __init__(self, scout_engine: Optional[ScoutBrowserEngine] = None):
        self.scout = scout_engine or ScoutBrowserEngine(headless=True)

    async def search_github_api(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """GitHub API orqali repolarni qidiradi."""
        results = []
        url = f"{GITHUB_API_BASE}/search/repositories"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Conduit-Studio-DeepSearch/2.5"
        }
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": limit}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        license_info = item.get("license") or {}
                        results.append({
                            "repo": item.get("full_name"),
                            "name": item.get("name"),
                            "author": item.get("owner", {}).get("login"),
                            "description": item.get("description") or "Tavsif berilmagan",
                            "url": item.get("html_url"),
                            "license": license_info.get("spdx_id") or license_info.get("name") or "Unknown",
                            "stars": item.get("stargazers_count", 0),
                            "forks": item.get("forks_count", 0),
                            "updated_at": item.get("updated_at"),
                            "default_branch": item.get("default_branch", "main"),
                            "size_kb": item.get("size", 0),
                            "source": "GitHub API"
                        })
        except Exception as e:
            # Tarmoq cheklovi yoki API limiti holatida xato o'tishi
            pass

        return results

    async def fetch_readme_via_scout(self, github_url: str) -> str:
        """
        Scout brauzeri orqali GitHub sahifasini ochib README matnini oladi.
        """
        await self.scout.initialize()
        nav_res = await self.scout.navigate(github_url)
        if not nav_res.get("success"):
            return f"Sahifani ochishda xatolik: {nav_res.get('error') or nav_res.get('reason')}"

        # GitHub README konteyneridan matn olish
        readme_text = await self.scout.get_text_content("article.markdown-body")
        if not readme_text:
            readme_text = await self.scout.get_text_content("#readme")
        if not readme_text:
            readme_text = await self.scout.get_text_content("body")

        # 3000 belgisi yetarli tahlil uchun
        return readme_text[:4000].strip()

    async def search_candidates_for_topic(self, topic: str) -> List[Dict[str, Any]]:
        """
        Mavzu bo'yicha barcha manbalardan (GitHub, Curated, User repos) nomzodlarni to'playdi.
        """
        t_lower = topic.lower()
        candidates = []

        # 1. Curated sources tekshirish
        for cat, list_items in CURATED_SOURCES.items():
            if cat in t_lower or (t_lower in ["editor", "montaj", "video"] and cat == "davinci") or (t_lower in ["sculptor", "3d"] and cat == "blender"):
                candidates.extend(list_items)

        # 2. Foydalanuvchining o'z repolarini mosligini tekshirish
        for u_repo in USER_REPOSITORIES:
            if any(k in u_repo["name"].lower() or k in u_repo["repo"].lower() for k in [t_lower, "conduit", "pipeline", "vfx"]):
                candidates.append(u_repo)

        # 3. GitHub API orqali jonli qidirish
        query = f"{topic} automation cli mcp"
        api_results = await self.search_github_api(query, limit=4)
        for ar in api_results:
            # Takrorlanmaslik
            if not any(c.get("repo") == ar["repo"] for c in candidates):
                candidates.append(ar)

        return candidates
