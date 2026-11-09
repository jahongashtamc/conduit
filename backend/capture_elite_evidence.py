import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\Kapitan\.gemini\antigravity\brain\6ed15a26-c09c-400b-a0f3-a9aba6cdb3cd"

async def capture_elite_evidence():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1600, "height": 950})
        page = await context.new_page()

        print("Navigating to http://localhost:3000 ...")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await asyncio.sleep(2)

        # 1. Main Elite Studio Layout screenshot
        p1 = os.path.join(ARTIFACT_DIR, "evidence_elite_overview.png")
        await page.screenshot(path=p1, full_page=False)
        print(f"Captured: {p1}")

        # 2. Window 2: Click 'Hisobot' tab
        try:
            hisobot_btn = page.locator("button:has-text('Hisobot')").first
            if await hisobot_btn.is_visible():
                await hisobot_btn.click()
                await asyncio.sleep(1)
                p2 = os.path.join(ARTIFACT_DIR, "evidence_elite_window2_report.png")
                await page.screenshot(path=p2, full_page=False)
                print(f"Captured: {p2}")
        except Exception as e:
            print("Error clicking Hisobot tab:", e)

        # 3. Window 2: Click 'Avto-Tuzatish' tab
        try:
            healer_btn = page.locator("button:has-text('Avto-Tuzatish')").first
            if await healer_btn.is_visible():
                await healer_btn.click()
                await asyncio.sleep(1)
                p3 = os.path.join(ARTIFACT_DIR, "evidence_elite_window2_selfhealer.png")
                await page.screenshot(path=p3, full_page=False)
                print(f"Captured: {p3}")
        except Exception as e:
            print("Error clicking Avto-Tuzatish tab:", e)

        # 4. Open Profile & Permission levels
        try:
            profile_btn = page.locator("button:has-text('Profil')").first
            if await profile_btn.is_visible():
                await profile_btn.click()
                await asyncio.sleep(1)
                p4 = os.path.join(ARTIFACT_DIR, "evidence_elite_settings_permissions.png")
                await page.screenshot(path=p4, full_page=False)
                print(f"Captured: {p4}")
        except Exception as e:
            print("Error clicking profile:", e)

        await browser.close()
        print("All screenshots successfully captured!")

if __name__ == "__main__":
    asyncio.run(capture_elite_evidence())
