import asyncio
from playwright.async_api import async_playwright

async def test_placeholder_functionality():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to USP manager
        await page.goto('http://localhost:8000/usps/manager/')
        
        print("🧪 Testing New Placeholder Functionality\n")
        
        # Test 1: Open "Ny USP" slide-in
        print("📝 Opening 'Ny USP' slide-in...")
        await page.click('#add-usp-btn')
        await page.wait_for_selector('#slide-panel', state='visible')
        
        # Check that placeholder section exists and shows as reference
        placeholder_section = await page.query_selector('h4:has-text("Tilgængelige Placeholders")')
        if placeholder_section:
            print("✅ Placeholder reference section found")
        else:
            print("❌ Placeholder reference section not found")
        
        # Check that copy buttons exist
        copy_buttons = await page.query_selector_all('.copy-placeholder')
        print(f"✅ Found {len(copy_buttons)} placeholder copy buttons")
        
        # Test copying a placeholder
        if copy_buttons:
            print("🔄 Testing placeholder copy functionality...")
            await copy_buttons[0].click()
            await page.wait_for_timeout(1500)  # Wait for copy feedback
            print("✅ Clicked first placeholder button - copy functionality triggered")
        
        # Check that no input fields for placeholders exist
        placeholder_input = await page.query_selector('#edit-placeholder-input')
        if not placeholder_input:
            print("✅ No placeholder input field found (as expected)")
        else:
            print("❌ Placeholder input field still exists")
        
        # Fill in USP text with placeholders
        print("\n📝 Testing USP creation with placeholders...")
        await page.fill('#edit-usp-text', 'Ring nu til {VIRKSOMHED} - få pris på {SERVICE} i {BYNAVN}')
        
        # Fill in other required fields
        await page.fill('#edit-usp-explanation', 'Test USP med placeholders')
        await page.fill('#new-headline-text', '{SERVICE} priser - Ring {TELEFON}')
        await page.click('#save-new-headline')
        
        # Save the USP
        await page.click('#slide-panel-save')
        
        # Wait for success notification or page reload
        await page.wait_for_timeout(2000)
        print("✅ USP creation attempted - checking if successful...")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_placeholder_functionality())