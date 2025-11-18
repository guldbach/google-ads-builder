import asyncio
from playwright.async_api import async_playwright

async def debug_expand_collapse():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🔍 DEBUGGING: Expand/Collapse Functionality")
        print("=" * 50)
        
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        await page.wait_for_load_state('networkidle')
        print("✅ Page loaded")
        
        # Look for VVS list
        vvs_lists = await page.query_selector_all('.keyword-list-section')
        vvs_list = None
        
        for list_element in vvs_lists:
            list_name = await list_element.query_selector('h3')
            if list_name:
                name_text = await list_name.inner_text()
                if 'VVS' in name_text:
                    vvs_list = list_element
                    print(f"✅ Found VVS list: {name_text}")
                    break
        
        if not vvs_list:
            print("❌ VVS list not found")
            await browser.close()
            return
        
        # Check initial state
        list_id = await vvs_list.get_attribute('data-list-id')
        print(f"📋 List ID: {list_id}")
        
        # Find keywords content section
        keywords_content = await page.query_selector(f'.keywords-content[data-list-id="{list_id}"]')
        if keywords_content:
            is_visible = await keywords_content.is_visible()
            print(f"📂 Keywords content initially visible: {is_visible}")
        else:
            print("❌ Keywords content section not found")
        
        # Check if toggleListExpansion function exists
        function_exists = await page.evaluate('''
            typeof window.toggleListExpansion === 'function'
        ''')
        print(f"🔧 window.toggleListExpansion function exists: {function_exists}")
        
        # Try to click on the header to expand
        try:
            header = await vvs_list.query_selector('.list-header')
            print("🖱️  Clicking on list header...")
            await header.click()
            await page.wait_for_timeout(1000)
            
            # Check state after click
            if keywords_content:
                is_visible_after = await keywords_content.is_visible()
                print(f"📂 Keywords content visible after click: {is_visible_after}")
            
            # Check icon rotation
            icon = await vvs_list.query_selector('.expansion-icon svg')
            if icon:
                has_rotation = await icon.evaluate('el => el.classList.contains("rotate-180")')
                print(f"🔄 Icon has rotation class: {has_rotation}")
            
        except Exception as e:
            print(f"❌ Click test failed: {e}")
        
        # Check for any JavaScript errors
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        
        # Try calling the function directly
        try:
            result = await page.evaluate(f'window.toggleListExpansion({list_id})')
            await page.wait_for_timeout(500)
            print("🔧 Function called directly")
            
        except Exception as e:
            print(f"❌ Direct function call failed: {e}")
        
        # Check final state
        if keywords_content:
            final_visible = await keywords_content.is_visible()
            print(f"📂 Final keywords content visible: {final_visible}")
        
        if console_messages:
            print(f"📝 Console messages: {console_messages}")
        
        await page.wait_for_timeout(3000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_expand_collapse())