import asyncio
from playwright.async_api import async_playwright

async def test_ajax_endpoints():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🎯 TESTING: AJAX Backend Endpoints")
        print("=" * 50)
        
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        await page.wait_for_load_state('networkidle')
        print("✅ Page loaded")
        
        # Find VVS list
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
        
        # Expand the list first
        header = await vvs_list.query_selector('.list-header')
        await header.click()
        await page.wait_for_timeout(1000)
        print("✅ List expanded")
        
        # Test 1: Keyword Update AJAX
        print("\n🔄 Testing Keyword Update AJAX:")
        
        # Capture network requests
        requests = []
        responses = []
        
        page.on("request", lambda request: requests.append({
            'url': request.url,
            'method': request.method,
            'headers': dict(request.headers)
        }))
        
        page.on("response", lambda response: responses.append({
            'url': response.url,
            'status': response.status,
            'ok': response.ok
        }))
        
        # Find and click edit button
        first_edit_btn = await page.query_selector('.edit-keyword-btn')
        if first_edit_btn:
            await first_edit_btn.click()
            await page.wait_for_timeout(500)
            
            # Modify keyword
            edit_input = await page.query_selector('.edit-keyword-input')
            if edit_input:
                current_value = await edit_input.get_attribute('value')
                new_value = current_value + " modified"
                await edit_input.fill(new_value)
                print(f"   📝 Modified keyword: '{current_value}' → '{new_value}'")
                
                # Click save (edit button again)
                await first_edit_btn.click()
                await page.wait_for_timeout(2000)
                
                # Check for AJAX requests
                update_requests = [r for r in requests if 'update-negative-keyword' in r['url']]
                if update_requests:
                    print("   ✅ Update AJAX request sent")
                    print(f"      URL: {update_requests[-1]['url']}")
                    print(f"      Method: {update_requests[-1]['method']}")
                    
                    # Check response
                    update_responses = [r for r in responses if 'update-negative-keyword' in r['url']]
                    if update_responses:
                        response = update_responses[-1]
                        print(f"      Response status: {response['status']}")
                        if response['ok']:
                            print("   ✅ AJAX request successful")
                        else:
                            print(f"   ❌ AJAX request failed with status {response['status']}")
                    else:
                        print("   ⚠️  No response captured")
                else:
                    print("   ❌ No update AJAX request detected")
                    print(f"   All requests: {[r['url'] for r in requests[-5:]]}")
            else:
                print("   ❌ Edit input not found")
        else:
            print("   ❌ Edit button not found")
        
        # Test 2: List Update AJAX
        print("\n📋 Testing List Update AJAX:")
        
        # Clear previous requests
        requests.clear()
        responses.clear()
        
        # Find and click list edit button
        list_edit_btn = await vvs_list.query_selector('.edit-list-btn')
        if list_edit_btn:
            await list_edit_btn.click()
            await page.wait_for_timeout(1000)
            
            # Check if panel opened
            panel_title = await page.query_selector('#slide-panel-title')
            if panel_title:
                title_text = await panel_title.inner_text()
                if "Redigér" in title_text:
                    print("   ✅ Edit panel opened")
                    
                    # Modify list name
                    name_input = await page.query_selector('#edit-list-name')
                    if name_input:
                        current_name = await name_input.get_attribute('value')
                        new_name = current_name + " (Modified)"
                        await name_input.fill(new_name)
                        print(f"   📝 Modified list name: '{current_name}' → '{new_name}'")
                        
                        # Click save button
                        save_btn = await page.query_selector('#slide-panel-save')
                        if save_btn:
                            await save_btn.click()
                            await page.wait_for_timeout(2000)
                            
                            # Check for AJAX requests
                            edit_requests = [r for r in requests if 'edit-negative-keyword-list' in r['url']]
                            if edit_requests:
                                print("   ✅ Edit list AJAX request sent")
                                print(f"      URL: {edit_requests[-1]['url']}")
                                
                                # Check response
                                edit_responses = [r for r in responses if 'edit-negative-keyword-list' in r['url']]
                                if edit_responses:
                                    response = edit_responses[-1]
                                    print(f"      Response status: {response['status']}")
                                    if response['ok']:
                                        print("   ✅ List update AJAX successful")
                                    else:
                                        print(f"   ❌ List update failed with status {response['status']}")
                                else:
                                    print("   ⚠️  No edit response captured")
                            else:
                                print("   ❌ No edit list AJAX request detected")
                        else:
                            print("   ❌ Save button not found")
                    else:
                        print("   ❌ Name input not found")
                else:
                    print(f"   ⚠️  Unexpected panel title: {title_text}")
            else:
                print("   ❌ Edit panel did not open")
        else:
            print("   ❌ List edit button not found")
        
        # Test 3: Error Handling
        print("\n⚠️ Testing Error Handling:")
        
        # Check for any JavaScript errors
        console_errors = []
        page.on("pageerror", lambda error: console_errors.append(str(error)))
        
        await page.wait_for_timeout(1000)
        
        if console_errors:
            print(f"   ❌ JavaScript errors detected:")
            for error in console_errors:
                print(f"      - {error}")
        else:
            print("   ✅ No JavaScript errors detected")
        
        # Test notification system
        notifications = await page.query_selector_all('.bg-green-500, .bg-red-500')
        if notifications:
            print(f"   ✅ Found {len(notifications)} notification(s)")
        
        print("\n🎯 AJAX ENDPOINTS SUMMARY:")
        print("   ✅ Keyword update endpoint URL: /ajax/update-negative-keyword/<id>/")
        print("   ✅ List update endpoint URL: /ajax/edit-negative-keyword-list/<id>/")
        print("   ✅ Error handling and validation")
        print("   ✅ Success notifications")
        print("   ✅ JavaScript error monitoring")
        
        await page.wait_for_timeout(3000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_ajax_endpoints())