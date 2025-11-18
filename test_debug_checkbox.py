#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def test_debug_checkbox():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"🖥️ BROWSER: {msg.text}"))
        
        print("🔗 Navigating to negative keywords manager...")
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        await page.wait_for_timeout(2000)
        
        print("🔍 Looking for testliste...")
        # Find testliste specifically
        testliste_container = page.locator('[data-list-id="5"]').first
        
        # Get data attribute
        is_active_attr = await testliste_container.get_attribute('data-is-active')
        print(f"📋 Database data-is-active: {is_active_attr}")
        
        # Click edit button
        edit_button = testliste_container.locator('[title="Redigér liste"]').first
        await edit_button.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        
        print("🖱️ Clicking edit button...")
        await edit_button.click(force=True)
        
        # Wait for panel and debug output
        await page.wait_for_timeout(2000)
        
        # Check actual checkbox state
        checkbox = page.locator('#edit-list-active')
        checkbox_checked = await checkbox.is_checked()
        print(f"✅ Final checkbox state: {'✅ Checked' if checkbox_checked else '❌ Unchecked'}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_debug_checkbox())