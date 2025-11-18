import asyncio
from playwright.async_api import async_playwright

async def debug_slidein():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Enable console logs
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        
        # Navigate to USP manager
        await page.goto('http://localhost:8000/usps/manager/')
        
        print("🔍 Debugging USP Create Slide-in Content\n")
        
        # Test: Open "Ny USP" slide-in
        print("📝 Opening 'Ny USP' slide-in...")
        await page.click('#add-usp-btn')
        await page.wait_for_selector('#slide-panel', state='visible')
        
        # Get actual HTML content of the slide-in
        panel_html = await page.inner_html('#slide-panel-content')
        print("\n🔧 ACTUAL SLIDE-IN HTML:")
        print("=" * 50)
        print(panel_html[:1000] + "..." if len(panel_html) > 1000 else panel_html)
        print("=" * 50)
        
        # Get all input IDs
        inputs = await page.query_selector_all('#slide-panel-content input, #slide-panel-content textarea, #slide-panel-content select')
        print(f"\n📋 Found {len(inputs)} input elements:")
        for i, input_elem in enumerate(inputs):
            input_id = await input_elem.get_attribute('id')
            input_type = await input_elem.get_attribute('type') or await input_elem.evaluate('el => el.tagName.toLowerCase()')
            print(f"   {i+1}. ID: {input_id}, Type: {input_type}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_slidein())