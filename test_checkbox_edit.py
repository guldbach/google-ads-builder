#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import time

async def test_checkbox_edit():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🔗 Navigating to negative keywords manager...")
        await page.goto('http://localhost:8000/negative-keywords-manager/')
        
        # Wait for page to load
        await page.wait_for_timeout(2000)
        
        print("🔍 Looking for 'testliste' list...")
        # Find the list with name "testliste"
        testliste_element = page.locator('text=testliste').first
        await testliste_element.wait_for()
        
        # Find the edit button for testliste
        print("✏️ Finding edit button for testliste...")
        # Look for edit button more directly
        edit_button = page.locator('[title="Redigér liste"][onclick*="editList"]').first
        
        # Scroll to the element and click
        print("🖱️ Scrolling to and clicking edit button...")
        await edit_button.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        await edit_button.click(force=True)
        
        # Wait for slide panel to open
        await page.wait_for_timeout(1000)
        
        # Check if slide panel is open
        slide_panel = page.locator('#slide-panel')
        await slide_panel.wait_for(state='visible')
        print("✅ Edit slide panel opened")
        
        # Find the checkbox
        checkbox = page.locator('#edit-list-active')
        await checkbox.wait_for()
        
        # Check current state
        is_checked_before = await checkbox.is_checked()
        print(f"📋 Current checkbox state: {'✅ Checked' if is_checked_before else '❌ Unchecked'}")
        
        # Toggle checkbox
        print("🔄 Toggling checkbox...")
        await checkbox.click()
        
        # Verify checkbox changed
        is_checked_after_toggle = await checkbox.is_checked()
        print(f"📋 After toggle: {'✅ Checked' if is_checked_after_toggle else '❌ Unchecked'}")
        
        # Save changes
        print("💾 Saving changes...")
        save_button = page.locator('#slide-panel-save')
        await save_button.click()
        
        # Wait for save and panel close
        await page.wait_for_timeout(3000)
        
        # Check that we're back to main page
        await page.wait_for_selector('#keyword-lists-container')
        print("🏠 Back to main page")
        
        # Open edit panel again to verify the change persisted
        print("🔄 Opening edit panel again to verify persistence...")
        edit_button = page.locator('[title="Redigér liste"][onclick*="editList"]').first
        await edit_button.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        await edit_button.click(force=True)
        
        # Wait for slide panel
        await page.wait_for_timeout(1000)
        await slide_panel.wait_for(state='visible')
        
        # Check checkbox state again
        checkbox = page.locator('#edit-list-active')
        final_state = await checkbox.is_checked()
        print(f"📋 Final state after save: {'✅ Checked' if final_state else '❌ Unchecked'}")
        
        # Verify the change persisted
        if final_state == is_checked_after_toggle:
            print("🎉 SUCCESS: Checkbox state persisted correctly!")
            success = True
        else:
            print("❌ FAILED: Checkbox state did not persist")
            success = False
        
        # Test toggling back
        print("🔄 Testing toggle back...")
        await checkbox.click()
        final_toggle_state = await checkbox.is_checked()
        print(f"📋 After second toggle: {'✅ Checked' if final_toggle_state else '❌ Unchecked'}")
        
        # Save again
        save_button = page.locator('#slide-panel-save')
        await save_button.click()
        await page.wait_for_timeout(3000)
        
        # Final verification
        print("🔍 Final verification...")
        edit_button = page.locator('[title="Redigér liste"][onclick*="editList"]').first
        await edit_button.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        await edit_button.click(force=True)
        
        await page.wait_for_timeout(1000)
        checkbox = page.locator('#edit-list-active')
        very_final_state = await checkbox.is_checked()
        print(f"📋 Very final state: {'✅ Checked' if very_final_state else '❌ Unchecked'}")
        
        if very_final_state == final_toggle_state:
            print("🎉 SUCCESS: Both toggles worked correctly!")
        else:
            print("❌ FAILED: Second toggle did not persist")
            success = False
            
        # Close panel
        close_button = page.locator('#slide-panel-close')
        await close_button.click()
        
        await browser.close()
        
        return success

if __name__ == "__main__":
    success = asyncio.run(test_checkbox_edit())
    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)