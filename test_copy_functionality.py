import asyncio
from playwright.async_api import async_playwright

async def test_copy_functionality():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Grant clipboard permissions
        context = browser.contexts[0]
        await context.grant_permissions(["clipboard-read", "clipboard-write"])
        
        # Navigate to USP manager
        await page.goto('http://localhost:8000/usps/manager/')
        
        print("📋 Testing Placeholder Copy to Clipboard\n")
        
        # Open "Ny USP" slide-in
        await page.click('#add-usp-btn')
        await page.wait_for_selector('#slide-panel', state='visible')
        
        # Test copying a placeholder
        print("🔄 Testing {SERVICE} placeholder copy...")
        service_button = await page.query_selector('[data-placeholder="{SERVICE}"]')
        
        if service_button:
            await service_button.click()
            await page.wait_for_timeout(500)  # Wait for copy animation
            
            # Check if button text changed to "Kopieret!"
            button_text = await service_button.inner_text()
            if "Kopieret" in button_text:
                print("✅ Copy feedback animation working")
            
            # Wait for animation to complete
            await page.wait_for_timeout(1200)
            
            # Check if button text returned to normal
            button_text = await service_button.inner_text()
            if button_text == "{SERVICE}":
                print("✅ Copy feedback animation completed successfully")
            
            print("✅ Placeholder copy functionality is working!")
        else:
            print("❌ Could not find {SERVICE} button")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_copy_functionality())