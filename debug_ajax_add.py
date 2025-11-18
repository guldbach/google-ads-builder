import asyncio
from playwright.async_api import async_playwright

async def debug_ajax_add():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🔍 DEBUGGING: AJAX Add Keyword")
        print("=" * 40)
        
        # Capture all network activity
        requests = []
        responses = []
        console_messages = []
        
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("request", lambda request: requests.append({
            'method': request.method,
            'url': request.url,
            'post_data': request.post_data if request.method == 'POST' else None
        }))
        page.on("response", lambda response: responses.append({
            'url': response.url,
            'status': response.status,
            'ok': response.ok
        }))
        
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        await page.wait_for_load_state('networkidle')
        print("✅ Page loaded")
        
        # Clear previous requests
        requests.clear()
        responses.clear()
        console_messages.clear()
        
        # Find VVS list and expand it
        vvs_list = None
        lists = await page.query_selector_all('.keyword-list-section')
        
        for list_element in lists:
            name = await list_element.query_selector('h3')
            if name:
                name_text = await name.inner_text()
                if 'VVS' in name_text:
                    vvs_list = list_element
                    break
        
        if vvs_list:
            header = await vvs_list.query_selector('.list-header')
            await header.click()
            await page.wait_for_timeout(1000)
            print("✅ VVS list expanded")
            
            # Get list ID for debugging
            list_id = await vvs_list.get_attribute('data-list-id')
            print(f"📋 List ID: {list_id}")
            
            # Find form elements
            keyword_input = await page.query_selector(f'.new-keyword-text[data-list-id="{list_id}"]')
            add_button = await page.query_selector(f'.add-keyword-btn[data-list-id="{list_id}"]')
            
            if keyword_input and add_button:
                # Fill and submit
                test_keyword = "debug test"
                await keyword_input.fill(test_keyword)
                print(f"📝 Filled keyword: '{test_keyword}'")
                
                await add_button.click()
                print("🖱️  Clicked add button")
                
                # Wait for response
                await page.wait_for_timeout(5000)
                
                # Analyze network activity
                print(f"\n🌐 Network Activity:")
                add_requests = [r for r in requests if 'add-negative-keyword' in r['url']]
                
                if add_requests:
                    req = add_requests[-1]
                    print(f"   📤 Request: {req['method']} {req['url']}")
                    print(f"   📋 Post data: {req['post_data']}")
                    
                    add_responses = [r for r in responses if 'add-negative-keyword' in r['url']]
                    if add_responses:
                        resp = add_responses[-1]
                        print(f"   📥 Response: {resp['status']} {'✅' if resp['ok'] else '❌'}")
                    else:
                        print("   ❌ No response found")
                else:
                    print("   ❌ No add-keyword request found")
                    print(f"   All requests: {[r['url'] for r in requests]}")
                
                # Check console messages
                if console_messages:
                    print(f"\n📝 Console Messages:")
                    for msg in console_messages:
                        print(f"   {msg}")
                else:
                    print("\n📝 No console messages")
                
                # Try to manually call the JavaScript functions
                print(f"\n🔧 Manual Function Test:")
                
                try:
                    # Test if addKeywordToTable function exists
                    func_exists = await page.evaluate('typeof addKeywordToTable')
                    print(f"   addKeywordToTable function type: {func_exists}")
                    
                    if func_exists == 'function':
                        # Try calling it manually
                        test_data = {
                            'id': 999,
                            'text': 'manual test',
                            'match_type': 'phrase'
                        }
                        
                        await page.evaluate(f"""
                            addKeywordToTable({list_id}, {test_data});
                        """)
                        print("   ✅ Manual function call successful")
                        
                        await page.wait_for_timeout(1000)
                        
                        # Check if row was added
                        manual_rows = await page.query_selector_all('.keywords-content tbody tr')
                        print(f"   📊 Rows after manual add: {len(manual_rows)}")
                    
                except Exception as e:
                    print(f"   ❌ Manual function test failed: {e}")
                
            else:
                print("❌ Form elements not found")
        else:
            print("❌ VVS list not found")
        
        await page.wait_for_timeout(3000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_ajax_add())