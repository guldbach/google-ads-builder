import asyncio
from playwright.async_api import async_playwright

async def test_simple_ajax():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🎯 TESTING: Simple AJAX Update Test")
        print("=" * 40)
        
        # Capture console messages and errors
        console_messages = []
        requests = []
        responses = []
        
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("request", lambda request: requests.append({
            'url': request.url,
            'method': request.method
        }))
        page.on("response", lambda response: responses.append({
            'url': response.url,
            'status': response.status
        }))
        
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        await page.wait_for_load_state('networkidle')
        print("✅ Page loaded")
        
        # Find VVS list and expand
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
            # Expand list
            header = await vvs_list.query_selector('.list-header')
            await header.click()
            await page.wait_for_timeout(1000)
            print("✅ VVS list expanded")
            
            # Find and click first edit button
            edit_btn = await page.query_selector('.edit-keyword-btn')
            if edit_btn:
                await edit_btn.click()
                await page.wait_for_timeout(500)
                print("✅ Edit mode activated")
                
                # Check for edit input
                edit_input = await page.query_selector('.edit-keyword-input')
                if edit_input:
                    # Modify text slightly
                    current_value = await edit_input.get_attribute('value')
                    await edit_input.fill(current_value + " TEST")
                    print(f"✅ Modified keyword: '{current_value}' → '{current_value} TEST'")
                    
                    # Click save (same button)
                    await edit_btn.click()
                    await page.wait_for_timeout(3000)  # Wait for AJAX
                    
                    # Check requests
                    update_requests = [r for r in requests if 'update-negative-keyword' in r['url']]
                    if update_requests:
                        last_request = update_requests[-1]
                        print(f"✅ AJAX request sent: {last_request['method']} {last_request['url']}")
                        
                        # Check response
                        update_responses = [r for r in responses if 'update-negative-keyword' in r['url']]
                        if update_responses:
                            last_response = update_responses[-1]
                            print(f"✅ Response status: {last_response['status']}")
                            
                            if last_response['status'] == 200:
                                print("🎉 AJAX update successful!")
                            else:
                                print(f"❌ AJAX failed with status {last_response['status']}")
                        else:
                            print("⚠️  No response captured")
                    else:
                        print("❌ No AJAX request detected")
                        print(f"Recent requests: {[r['url'] for r in requests[-3:]]}")
                else:
                    print("❌ Edit input not found")
            else:
                print("❌ Edit button not found")
        else:
            print("❌ VVS list not found")
        
        # Print any console messages
        if console_messages:
            print("\n📝 Console messages:")
            for msg in console_messages:
                print(f"   {msg}")
        
        await page.wait_for_timeout(2000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_simple_ajax())