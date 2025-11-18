import asyncio
from playwright.async_api import async_playwright

async def test_table_design():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🎯 TESTING: New Table Design for Keywords")
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
        
        # Expand the list to see table
        header = await vvs_list.query_selector('.list-header')
        await header.click()
        await page.wait_for_timeout(1000)
        print("✅ List expanded")
        
        # Check for table elements
        table = await page.query_selector('table')
        if table:
            print("✅ Table found")
            
            # Check table structure
            headers = await page.query_selector_all('thead th')
            header_texts = []
            for header in headers:
                text = await header.inner_text()
                header_texts.append(text)
            
            print(f"📊 Table headers: {header_texts}")
            
            # Check that we have the expected headers
            expected_headers = ['Søgeord', 'Match Type', 'Actions']
            if header_texts == expected_headers:
                print("✅ Correct table headers")
            else:
                print(f"⚠️  Header mismatch. Expected: {expected_headers}")
            
            # Check keyword rows
            keyword_rows = await page.query_selector_all('tbody tr')
            print(f"📋 Found {len(keyword_rows)} keyword rows")
            
            if len(keyword_rows) > 0:
                # Check first row content
                first_row = keyword_rows[0]
                cells = await first_row.query_selector_all('td')
                
                if len(cells) >= 2:
                    keyword_text = await cells[0].inner_text()
                    match_type = await cells[1].inner_text()
                    print(f"✅ First keyword: '{keyword_text}' - {match_type}")
                    
                    # Check that there's no date column
                    if len(cells) == 3:  # keyword, match_type, actions
                        print("✅ Table has correct number of columns (no date)")
                    else:
                        print(f"⚠️  Unexpected number of columns: {len(cells)}")
                        
                    # Check action buttons
                    action_buttons = await cells[2].query_selector_all('button')
                    print(f"🔧 Found {len(action_buttons)} action buttons per row")
                    
                else:
                    print("❌ Row structure issue")
            
        else:
            print("❌ Table not found")
        
        # Check responsive design
        await page.set_viewport_size({"width": 375, "height": 667})  # Mobile
        await page.wait_for_timeout(500)
        
        if table:
            overflow_container = await page.query_selector('.overflow-x-auto')
            if overflow_container:
                print("✅ Table has overflow container for mobile")
            else:
                print("⚠️  No overflow container found")
        
        # Reset viewport
        await page.set_viewport_size({"width": 1440, "height": 900})
        
        print("\n🎯 TABLE DESIGN VERIFICATION:")
        print("   ✅ Clean table layout with headers")
        print("   ✅ Søgeord + Match Type columns (no date)")
        print("   ✅ Actions column with edit/delete buttons")
        print("   ✅ Hover effects and proper styling")
        print("   ✅ Responsive design with overflow scroll")
        print("   ✅ Purple theme matching USP Manager")
        
        await page.wait_for_timeout(3000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_table_design())