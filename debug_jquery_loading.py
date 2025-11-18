import asyncio
from playwright.async_api import async_playwright

async def debug_jquery_loading():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🔧 DEBUGGING: jQuery and Script Loading")
        print("=" * 50)
        
        # Capture console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)  # Wait for all scripts to load
        
        print("✅ Page loaded")
        
        # Test jQuery availability
        jquery_loaded = await page.evaluate('typeof jQuery !== "undefined"')
        print(f"📚 jQuery loaded: {jquery_loaded}")
        
        dollar_loaded = await page.evaluate('typeof $ !== "undefined"')
        print(f"💲 $ available: {dollar_loaded}")
        
        # Test if our function is defined
        function_defined = await page.evaluate('typeof toggleListExpansion !== "undefined"')
        print(f"🔧 toggleListExpansion defined: {function_defined}")
        
        # Check what's available in global scope
        global_funcs = await page.evaluate('''
            Object.getOwnPropertyNames(window).filter(name => 
                typeof window[name] === 'function' && name.includes('toggle')
            )
        ''')
        print(f"🌍 Global toggle functions: {global_funcs}")
        
        # Check for script errors
        if console_messages:
            print(f"📝 Console messages:")
            for msg in console_messages:
                print(f"   {msg}")
        
        # Try to define function manually and test
        try:
            await page.evaluate('''
                window.toggleListExpansion = function(listId) {
                    console.log('Manual function called with ID:', listId);
                    const content = document.querySelector(`.keywords-content[data-list-id="${listId}"]`);
                    if (content) {
                        if (content.style.display === 'none' || !content.style.display) {
                            content.style.display = 'block';
                            console.log('Showing content');
                        } else {
                            content.style.display = 'none';
                            console.log('Hiding content');
                        }
                    } else {
                        console.log('Content element not found');
                    }
                };
            ''')
            
            print("🔧 Manual function definition successful")
            
            # Test the manual function
            await page.evaluate('toggleListExpansion(1)')
            await page.wait_for_timeout(1000)
            
            # Check if content is now visible
            content_visible = await page.evaluate('''
                const content = document.querySelector('.keywords-content[data-list-id="1"]');
                content ? content.style.display !== 'none' : false;
            ''')
            print(f"📂 Content visible after manual toggle: {content_visible}")
            
        except Exception as e:
            print(f"❌ Manual function test failed: {e}")
        
        await page.wait_for_timeout(3000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_jquery_loading())