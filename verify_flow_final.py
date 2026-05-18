import asyncio
from playwright.async_api import async_playwright
import time
import os

async def verify_flow():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1280, 'height': 720})

        print("Connecting to http://localhost:5000...")
        await page.goto('http://localhost:5000')

        # Wait for page to load
        await page.wait_for_selector('#no-cd')
        await page.screenshot(path='/home/jules/verification/step1_initial.png')
        print("Captured initial state (No CD).")

        # Trigger Play
        print("Triggering /play via API...")
        await page.evaluate("fetch('/play', {method: 'POST'})")

        # Wait for UI update (metadata)
        print("Waiting for metadata update...")
        try:
            await page.wait_for_selector('text=Random Access Memories', timeout=10000)
            print("Metadata updated successfully.")
        except Exception as e:
            print(f"Timeout or error waiting for metadata: {e}")
            # Check if player is visible at least
            is_visible = await page.is_visible('#player')
            print(f"Player visible: {is_visible}")

        await page.screenshot(path='/home/jules/verification/step2_after_play.png')

        # Trigger Pause
        print("Triggering /pause...")
        await page.evaluate("fetch('/pause', {method: 'POST'})")
        await asyncio.sleep(2)
        await page.screenshot(path='/home/jules/verification/step3_after_pause.png')

        await browser.close()

if __name__ == "__main__":
    if not os.path.exists('/home/jules/verification'):
        os.makedirs('/home/jules/verification')
    asyncio.run(verify_flow())
