import asyncio
from playwright.async_api import async_playwright

async def test_simple_nkw():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🚫 Simple Test for Negative Keywords Manager")
        print("=" * 50)
        
        # Navigate to the manager
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        await page.wait_for_load_state('networkidle')
        
        print("✅ Siden indlæst succesfuldt")
        
        # Check if page title is correct
        title = await page.title()
        print(f"📄 Page Title: {title}")
        
        # Check if main elements are present
        hero = await page.query_selector('h1')
        if hero:
            hero_text = await hero.inner_text()
            print(f"🏆 Hero Title: {hero_text}")
        
        # Check quick action buttons
        create_btn = await page.query_selector('#create-list-btn')
        import_btn = await page.query_selector('#import-excel-btn')
        template_btn = await page.query_selector('#download-template-btn')
        
        print(f"🔘 Create Button: {'✅ Found' if create_btn else '❌ Missing'}")
        print(f"📊 Import Button: {'✅ Found' if import_btn else '❌ Missing'}")
        print(f"📥 Template Button: {'✅ Found' if template_btn else '❌ Missing'}")
        
        # Check slide panel exists
        slide_panel = await page.query_selector('#slide-panel')
        slide_overlay = await page.query_selector('#slide-panel-overlay')
        
        print(f"📱 Slide Panel: {'✅ Found' if slide_panel else '❌ Missing'}")
        print(f"🌫️  Slide Overlay: {'✅ Found' if slide_overlay else '❌ Missing'}")
        
        # Check if panel is initially hidden
        if slide_overlay:
            is_hidden = await slide_overlay.evaluate('el => el.classList.contains("hidden")')
            print(f"👁️  Panel Hidden: {'✅ Yes' if is_hidden else '❌ No'}")
        
        # Test JavaScript function exists
        js_function_test = await page.evaluate('() => typeof openCreateListPanel === "function"')
        print(f"🔧 JavaScript Function: {'✅ Available' if js_function_test else '❌ Missing'}")
        
        # Test jQuery is loaded
        jquery_test = await page.evaluate('() => typeof $ === "function"')
        print(f"📚 jQuery Loaded: {'✅ Yes' if jquery_test else '❌ No'}")
        
        print("\n🎯 TEST RESULTAT:")
        if create_btn and slide_panel and js_function_test and jquery_test:
            print("✅ Alle nødvendige komponenter er til stede")
            
            print("\n🔄 Testing panel åbning manuelt...")
            try:
                # Manually trigger the panel opening function
                await page.evaluate('openCreateListPanel()')
                
                # Wait a bit for animation
                await page.wait_for_timeout(500)
                
                # Check if panel is now visible
                panel_visible = await page.evaluate('''
                    () => {
                        const overlay = document.getElementById('slide-panel-overlay');
                        return overlay && !overlay.classList.contains('hidden');
                    }
                ''')
                
                print(f"📱 Panel Åbnet: {'✅ Success' if panel_visible else '❌ Failed'}")
                
                if panel_visible:
                    print("🎉 JavaScript funktionalitet virker korrekt!")
                
            except Exception as e:
                print(f"❌ Fejl ved test af panel åbning: {e}")
        else:
            print("❌ Manglende komponenter - se detaljer ovenfor")
        
        # Wait a moment before closing
        await page.wait_for_timeout(2000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_simple_nkw())