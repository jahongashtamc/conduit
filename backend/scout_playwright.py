"""
Conduit Scout Playwright Engine
Professional, production-grade browser automation module:
- Playwright Chromium engine
- Smart waiting & DOM mutation handling
- Automatic cookie & modal dismissers
- Multi-tab support
- Resumable chunked file downloader (HTTP Range)
- Console & network error tracking
- CAPTCHA / Login detection with human-intervention gate (BLOCKED: "odam kerak")
- Zero-secret security policy (no password requests or storage)
"""

import os
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Callable
import httpx

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error as PlaywrightError
except ImportError:
    async_playwright = None
    Browser = None
    BrowserContext = None
    Page = None
    PlaywrightError = Exception

POPUP_DISMISS_SELECTORS = [
    # Common cookie accept buttons
    "button#onetrust-accept-btn-handler",
    "button[id*='cookie']",
    "button[class*='cookie']",
    "button:has-text('Accept all')",
    "button:has-text('Accept All')",
    "button:has-text('Accept cookies')",
    "button:has-text('Roziman')",
    "button:has-text('Qabul qilish')",
    "button:has-text('I agree')",
    "button:has-text('Got it')",
    "button:has-text('Allow all')",
    "button:has-text('Dismiss')",
    # Common dialog closes
    "button[aria-label='Close']",
    "button[aria-label='Yopish']",
    ".modal-close",
    "[data-action='close']",
]

CAPTCHA_LOGIN_INDICATORS = [
    "g-recaptcha",
    "cf-turnstile",
    "hcaptcha",
    "arkose",
    "recaptcha",
    "input[type='password']",
    "form[action*='login']",
    "form[action*='signin']",
]

class ResumableDownloader:
    """
    Katta fayllarni boshqariladigan (chunked, pause-and-resume, SHA256 tekshiruvli)
    HTTP Range so'rovlari orqali yuklab olish sinfi.
    """
    def __init__(self, chunk_size: int = 1024 * 1024): # 1MB chunks
        self.chunk_size = chunk_size
        self._is_paused = False

    async def download_file(
        self,
        url: str,
        dest_path: str,
        expected_sha256: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        pause_event: Optional[asyncio.Event] = None
    ) -> Dict[str, Any]:
        """
        Faylni to'xtatib davom ettirish (pause/resume) imkoniyati bilan yuklaydi.
        """
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        part_path = dest_path + ".part"

        # Qisman yuklangan qism hajmini aniqlash
        downloaded_bytes = 0
        if os.path.exists(part_path):
            downloaded_bytes = os.path.getsize(part_path)

        headers = {}
        if downloaded_bytes > 0:
            headers["Range"] = f"bytes={downloaded_bytes}-"

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            # Boshlang'ich head yoki range so'rovi
            async with client.stream("GET", url, headers=headers) as response:
                total_bytes = downloaded_bytes
                if response.status_code == 206: # Partial Content
                    content_range = response.headers.get("Content-Range", "")
                    if "/" in content_range:
                        try:
                            total_bytes = int(content_range.split("/")[-1])
                        except ValueError:
                            total_bytes = downloaded_bytes + int(response.headers.get("Content-Length", 0))
                elif response.status_code == 200:
                    # Server Range qo'llab-quvvatlamasa, qaytadan boshlaymiz
                    downloaded_bytes = 0
                    total_bytes = int(response.headers.get("Content-Length", 0))
                    if os.path.exists(part_path):
                        os.remove(part_path)
                elif response.status_code == 416: # Range Not Satisfiable (allaqachon yuklangan bo'lishi mumkin)
                    total_bytes = downloaded_bytes
                else:
                    return {
                        "success": False,
                        "error": f"HTTP status xatosi: {response.status_code}",
                        "downloaded_bytes": downloaded_bytes
                    }

                # Yozish rejimi (ab agar 206 bo'lsa, wb agar 200 bo'lsa)
                mode = "ab" if downloaded_bytes > 0 else "wb"
                with open(part_path, mode) as f:
                    async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                        if pause_event and pause_event.is_set():
                            return {
                                "success": False,
                                "status": "PAUSED",
                                "message": "Yuklash to'xtatildi (Paused). Davom ettirish mumkin.",
                                "downloaded_bytes": downloaded_bytes,
                                "total_bytes": total_bytes,
                                "part_file": part_path
                            }

                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        if progress_callback and total_bytes > 0:
                            pct = (downloaded_bytes / total_bytes) * 100.0
                            progress_callback(downloaded_bytes, total_bytes, pct)

        # Yuklash yakunlandi, .part faylni asosiy fayl nomiga o'tkazish
        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.rename(part_path, dest_path)

        # SHA256 checksum hisoblash
        hasher = hashlib.sha256()
        with open(dest_path, "rb") as f:
            for b in iter(lambda: f.read(65536), b""):
                hasher.update(b)
        actual_sha256 = hasher.hexdigest()

        hash_verified = True
        if expected_sha256:
            hash_verified = (actual_sha256.lower() == expected_sha256.lower())

        return {
            "success": hash_verified,
            "status": "COMPLETED" if hash_verified else "HASH_MISMATCH",
            "file_path": dest_path,
            "downloaded_bytes": downloaded_bytes,
            "sha256": actual_sha256,
            "hash_verified": hash_verified,
            "error": None if hash_verified else f"SHA256 mos kelmadi: kutilgan {expected_sha256}, olingan {actual_sha256}"
        }


class ScoutBrowserEngine:
    """
    Playwright asosidagi Scout brauzer avtonom mexanizmi.
    """
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self.tabs: List[Page] = []
        self.active_page: Optional[Page] = None
        self.console_logs: List[str] = []
        self.network_errors: List[str] = []
        self.downloader = ResumableDownloader()

    async def initialize(self):
        if not async_playwright:
            raise RuntimeError("Playwright moduli o'rnatilmagan!")
        if not self._playwright:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            # Dastlabki yorliq
            page = await self._context.new_page()
            self._setup_page_listeners(page)
            self.tabs.append(page)
            self.active_page = page

    def _setup_page_listeners(self, page: Page):
        page.on("console", lambda msg: self.console_logs.append(f"[{msg.type.upper()}] {msg.text}"))
        page.on("requestfailed", lambda req: self.network_errors.append(f"REQ FAILED: {req.method} {req.url} - {req.failure}"))

    async def new_tab(self, url: Optional[str] = None) -> Page:
        if not self._context:
            await self.initialize()
        page = await self._context.new_page()
        self._setup_page_listeners(page)
        self.tabs.append(page)
        self.active_page = page
        if url:
            await self.navigate(url)
        return page

    async def switch_tab(self, index: int) -> Optional[Page]:
        if 0 <= index < len(self.tabs):
            self.active_page = self.tabs[index]
            await self.active_page.bring_to_front()
            return self.active_page
        return None

    async def close_tab(self, index: Optional[int] = None):
        target = self.tabs[index] if index is not None and 0 <= index < len(self.tabs) else self.active_page
        if target:
            if target in self.tabs:
                self.tabs.remove(target)
            await target.close()
            self.active_page = self.tabs[0] if self.tabs else None

    async def dismiss_popups(self):
        """Pop-up, modal va cookie ogohlantirishlarini avtomatik yopadi."""
        if not self.active_page:
            return
        for selector in POPUP_DISMISS_SELECTORS:
            try:
                el = await self.active_page.query_selector(selector)
                if el and await el.is_visible():
                    await el.click(timeout=1000)
                    await asyncio.sleep(0.2)
            except Exception:
                pass

    async def check_captcha_or_login(self) -> Optional[str]:
        """
        CAPTCHA yoki Login talabini aniqlaydi.
        Agar aniqlansa, xavfsizlik uchun BLOCKED holatini qaytaradi.
        """
        if not self.active_page:
            return None
        html = await self.active_page.content()
        html_lower = html.lower()
        for ind in CAPTCHA_LOGIN_INDICATORS:
            if ind in html_lower:
                return f"BLOCKED: 'Odam kerak' - Sahifada autentifikatsiya yoki CAPTCHA aniqlandi ({ind}). Xavfsizlik qoidasi: parollar so'ralmaydi va saqlanmaydi."
        return None

    async def navigate(self, url: str, max_retries: int = 2) -> Dict[str, Any]:
        """
        Aqlli kutish, avto-pop-up tozalash va xatolikda qayta urinish bilan navigatsiya.
        """
        if not self.active_page:
            await self.initialize()

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                response = await self.active_page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(0.5)
                await self.dismiss_popups()

                # CAPTCHA tekshiruvi
                blocked_reason = await self.check_captcha_or_login()
                if blocked_reason:
                    return {
                        "success": False,
                        "blocked": True,
                        "status": "BLOCKED",
                        "reason": blocked_reason,
                        "url": url
                    }

                title = await self.active_page.title()
                return {
                    "success": True,
                    "status": response.status if response else 200,
                    "title": title,
                    "url": self.active_page.url,
                    "attempt": attempt,
                    "console_errors_count": len(self.console_logs),
                    "network_errors_count": len(self.network_errors)
                }
            except PlaywrightError as e:
                last_error = str(e)
                await asyncio.sleep(1.0)

        return {
            "success": False,
            "error": f"Navigatsiya xatoligi ({max_retries} urinishdan so'ng): {last_error}",
            "url": url
        }

    async def get_text_content(self, selector: str = "body") -> str:
        if not self.active_page:
            return ""
        try:
            el = await self.active_page.query_selector(selector)
            return await el.inner_text() if el else ""
        except Exception:
            return ""

    async def take_screenshot_if_needed(self, output_path: str) -> str:
        """
        Faqat kerak bo'lganda (dalil yoki muammo yuz berganda) skrinshot oladi.
        """
        if not self.active_page:
            return ""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        await self.active_page.screenshot(path=output_path, full_page=False)
        return output_path

    async def close(self):
        for t in self.tabs:
            try:
                await t.close()
            except Exception:
                pass
        self.tabs.clear()
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
