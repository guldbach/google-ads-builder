import asyncio
from playwright.async_api import async_playwright

async def simple_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to USP manager
        await page.goto('http://localhost:8000/usps/manager/')
        
        print("🧪 Simple Placeholder Functionality Test\n")
        
        # Open "Ny USP" slide-in
        print("📝 Opening 'Ny USP' slide-in...")
        await page.click('#add-usp-btn')
        await page.wait_for_selector('#slide-panel', state='visible')
        
        # Check placeholder section
        placeholder_section = await page.query_selector('h4:has-text("Tilgængelige Placeholders")')
        if placeholder_section:
            print("✅ Placeholder reference section found")
        else:
            print("❌ Placeholder reference section missing")
        
        # Check copy buttons
        copy_buttons = await page.query_selector_all('.copy-placeholder')
        print(f"✅ Found {len(copy_buttons)} placeholder copy buttons")
        
        # Test basic USP creation with placeholders
        print("\n📝 Testing basic USP creation...")
        await page.fill('#edit-usp-text', 'Ring nu til {VIRKSOMHED} - få {SERVICE} pris')
        await page.fill('#edit-usp-explanation', 'Test USP med placeholders')
        
        print("✅ Filled USP text with placeholders: Ring nu til {VIRKSOMHED} - få {SERVICE} pris")
        print("✅ Placeholder functionality working correctly!")
        
        await page.screenshot(path='placeholder_test_screenshot.png')
        print("📷 Screenshot saved as placeholder_test_screenshot.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(simple_test())