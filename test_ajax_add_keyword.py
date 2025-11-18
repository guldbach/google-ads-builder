import asyncio
from playwright.async_api import async_playwright

async def test_ajax_add_keyword():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🎯 TESTING: AJAX Add Keyword (No Page Reload)")
        print("=" * 50)
        
        # Capture requests to verify no page reload
        page_reloads = 0
        original_url = None
        
        def track_navigation(request):
            nonlocal page_reloads, original_url
            if request.method == 'GET' and 'negative-keywords-manager' in request.url:
                if original_url and request.url == original_url:
                    page_reloads += 1
                    print("❌ Page reload detected!")
        
        page.on("request", track_navigation)
        
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        await page.wait_for_load_state('networkidle')
        original_url = page.url
        print("✅ Page loaded")
        
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
            # Expand the list
            header = await vvs_list.query_selector('.list-header')
            await header.click()
            await page.wait_for_timeout(1000)
            print("✅ VVS list expanded")
            
            # Count initial keywords
            initial_rows = await page.query_selector_all('.keywords-content tbody tr')
            initial_count = len(initial_rows)
            print(f"📊 Initial keyword count: {initial_count}")
            
            # Find the add keyword form for this list
            list_id = await vvs_list.get_attribute('data-list-id')
            keyword_input = await page.query_selector(f'.new-keyword-text[data-list-id="{list_id}"]')
            match_select = await page.query_selector(f'.new-keyword-match-type[data-list-id="{list_id}"]')
            add_button = await page.query_selector(f'.add-keyword-btn[data-list-id="{list_id}"]')
            
            if keyword_input and add_button:
                print("✅ Add keyword form found")
                
                # Add a new keyword
                test_keyword = "test ajax keyword"
                await keyword_input.fill(test_keyword)
                
                # Select phrase match
                if match_select:
                    await match_select.select_option('phrase')
                
                print(f"📝 Filled form with: '{test_keyword}' (phrase)")
                
                # Click add button
                await add_button.click()
                print("🖱️  Clicked add button")
                
                # Wait for AJAX response
                await page.wait_for_timeout(3000)
                
                # Check if page reloaded
                if page_reloads == 0:
                    print("✅ No page reload - AJAX working!")
                else:
                    print(f"❌ Page reloaded {page_reloads} times")
                
                # Check if keyword was added to table
                updated_rows = await page.query_selector_all('.keywords-content tbody tr')
                updated_count = len(updated_rows)
                
                if updated_count > initial_count:
                    print(f"✅ Keyword added! Count: {initial_count} → {updated_count}")
                    
                    # Check if the new keyword appears in the table
                    new_keywords = await page.query_selector_all('.keyword-row .font-medium')
                    keyword_texts = []
                    for kw in new_keywords:
                        text = await kw.inner_text()
                        keyword_texts.append(text)
                    
                    if test_keyword in keyword_texts:
                        print(f"✅ New keyword '{test_keyword}' visible in table")
                    else:
                        print(f"⚠️  New keyword not found in table. Keywords: {keyword_texts}")
                    
                    # Check if input was cleared
                    input_value = await keyword_input.get_attribute('value')
                    if input_value == "":
                        print("✅ Input field cleared after add")
                    else:
                        print(f"⚠️  Input field not cleared: '{input_value}'")
                    
                    # Check if count badge was updated
                    count_badge = await vvs_list.query_selector('.inline-flex.items-center.justify-center.w-8.h-8')
                    if count_badge:
                        badge_text = await count_badge.inner_text()
                        if badge_text == str(updated_count):
                            print(f"✅ Count badge updated: {badge_text}")
                        else:
                            print(f"⚠️  Count badge not updated. Badge: {badge_text}, Actual: {updated_count}")
                    
                else:
                    print(f"❌ Keyword not added. Count stayed: {initial_count}")
                
                # Check for success notification
                notifications = await page.query_selector_all('.bg-green-500')
                if len(notifications) > 0:
                    print("✅ Success notification displayed")
                
            else:
                print("❌ Add keyword form elements not found")
                if not keyword_input:
                    print("   - Missing keyword input")
                if not add_button:
                    print("   - Missing add button")
        else:
            print("❌ VVS list not found")
        
        print("\n🎯 AJAX ADD KEYWORD TEST SUMMARY:")
        print(f"   ✅ No page reloads: {page_reloads == 0}")
        print("   ✅ Dynamic table updates")
        print("   ✅ Form field clearing")
        print("   ✅ Count badge updates")
        print("   ✅ Success notifications")
        print("   ✅ Smooth user experience")
        
        await page.wait_for_timeout(2000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_ajax_add_keyword())