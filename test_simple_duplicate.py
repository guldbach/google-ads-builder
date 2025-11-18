#!/usr/bin/env python

from playwright.sync_api import sync_playwright

def test_duplicate_city_simple():
    """Simple test for duplicate city detection"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("🌐 Navigating to Geographic Regions Manager...")
            page.goto("http://localhost:8000/geographic-regions-manager/")
            page.wait_for_load_state('networkidle')
            
            print("🔍 Looking for region...")
            # Find the correct region by looking for the title
            region_title = page.locator('h3:has-text("dette er min nye region 2")')
            
            if region_title.is_visible():
                print("✅ Found region")
                
                # Click on the region title to expand it
                print("📂 Expanding region...")
                region_title.click()
                page.wait_for_timeout(1000)
                
                # Now look for the add city button
                add_btn = page.locator('[data-region-id="5"].add-city-btn')
                if add_btn.is_visible():
                    print("🔘 Add City button is now visible")
                    add_btn.click()
                    page.wait_for_timeout(1000)
                    
                    # Test duplicate detection
                    if page.locator('#add-city-name').is_visible():
                        print("📝 Form is open, testing duplicate...")
                        page.fill('#add-city-name', 'brønderslev')  # lowercase
                        page.click('button[type="submit"]')
                        page.wait_for_timeout(2000)
                        
                        # Look for error message
                        error_msg = page.locator('.text-red-600, .alert-error')
                        if error_msg.is_visible():
                            print(f"✅ Duplicate correctly detected: {error_msg.text_content()}")
                        else:
                            print("❌ No error message found")
                    else:
                        print("❌ Form did not open")
                else:
                    print("❌ Add City button not found or not visible")
                    # Debug: show what buttons are available
                    buttons = page.locator('button')
                    print(f"Available buttons: {buttons.count()}")
                    for i in range(min(5, buttons.count())):
                        btn_text = buttons.nth(i).text_content()
                        print(f"  Button {i}: '{btn_text}'")
            else:
                print("❌ Region not found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="debug_duplicate_test.png")
        
        finally:
            input("Press Enter to close browser...")
            browser.close()

if __name__ == "__main__":
    test_duplicate_city_simple()