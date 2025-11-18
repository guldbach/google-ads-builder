import asyncio
from playwright.async_api import async_playwright

async def debug_script_errors():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Capture all console messages and errors
        console_messages = []
        js_errors = []
        
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda error: js_errors.append(str(error)))
        
        print("🔍 DEBUGGING: Script Errors and Console Output")
        print("=" * 60)
        
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(3000)  # Wait for all scripts to execute
        
        print("✅ Page loaded and scripts executed")
        
        # Check for JavaScript errors
        if js_errors:
            print(f"\n❌ JavaScript Errors ({len(js_errors)}):")
            for i, error in enumerate(js_errors):
                print(f"   {i+1}. {error}")
        else:
            print("\n✅ No JavaScript errors detected")
        
        # Check console messages
        if console_messages:
            print(f"\n📝 Console Messages ({len(console_messages)}):")
            for i, msg in enumerate(console_messages):
                print(f"   {i+1}. {msg}")
        else:
            print("\n📝 No console messages")
        
        # Check what functions are actually defined
        defined_functions = await page.evaluate('''
            Object.getOwnPropertyNames(window).filter(name => 
                typeof window[name] === 'function'
            ).slice(0, 20)  // First 20 functions
        ''')
        print(f"\n🔧 Sample defined functions: {defined_functions}")
        
        # Try to see the actual script content
        script_content = await page.evaluate('''
            Array.from(document.scripts).map(script => ({
                src: script.src || 'inline',
                content: script.src ? null : script.innerHTML.slice(0, 200) + '...'
            }))
        ''')
        
        print(f"\n📜 Scripts on page:")
        for i, script in enumerate(script_content):
            if script['src'] == 'inline' and 'toggleListExpansion' in (script['content'] or ''):
                print(f"   {i+1}. Inline script with toggleListExpansion found")
                print(f"      Content preview: {script['content']}")
            else:
                print(f"   {i+1}. {script['src']}")
        
        await page.wait_for_timeout(2000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_script_errors())