#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright

async def test_checkbox_initial_state():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🔗 Navigating to negative keywords manager...")
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        
        # Wait for page to load
        await page.wait_for_timeout(2000)
        
        print("🔍 Looking for all negative keyword lists...")
        
        # Find all list containers and check their is_active status
        list_containers = page.locator('[data-list-id]')
        count = await list_containers.count()
        
        print(f"📊 Found {count} keyword lists")
        
        for i in range(count):
            container = list_containers.nth(i)
            
            # Get data attributes
            list_id = await container.get_attribute('data-list-id')
            is_active_attr = await container.get_attribute('data-is-active')
            
            # Get list name
            list_name_element = container.locator('h3').first
            list_name = await list_name_element.text_content()
            
            print(f"\n📋 List: {list_name} (ID: {list_id})")
            print(f"🏷️ Database is_active: {is_active_attr}")
            
            # Find edit button and click it
            try:
                edit_button = container.locator('[title="Redigér liste"]').first
                await edit_button.scroll_into_view_if_needed()
                await page.wait_for_timeout(300)
                await edit_button.click(force=True)
                
                # Wait for panel to open
                await page.wait_for_timeout(1000)
                
                # Check if panel opened
                slide_panel = page.locator('#slide-panel')
                if not await slide_panel.is_visible():
                    print("❌ Could not open edit panel")
                    continue
                    
                # Check checkbox state
                checkbox = page.locator('#edit-list-active')
                if await checkbox.is_visible():
                    checkbox_checked = await checkbox.is_checked()
                    print(f"✅ UI Checkbox state: {'✅ Checked' if checkbox_checked else '❌ Unchecked'}")
                    
                    # Compare database vs UI
                    database_active = is_active_attr == 'true'
                    if checkbox_checked == database_active:
                        print(f"🎉 MATCH: Database and UI are in sync!")
                    else:
                        print(f"❌ MISMATCH: Database={database_active}, UI={checkbox_checked}")
                        
                else:
                    print("❌ Checkbox not found in edit panel")
                
                # Close panel
                close_button = page.locator('#slide-panel-close')
                if await close_button.is_visible():
                    await close_button.click()
                    await page.wait_for_timeout(500)
                    
            except Exception as e:
                print(f"❌ Error testing list {list_name}: {e}")
                # Try to close any open panels
                close_button = page.locator('#slide-panel-close')
                if await close_button.is_visible():
                    await close_button.click()
                    await page.wait_for_timeout(500)
        
        await browser.close()
        
        print("\n🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_checkbox_initial_state())