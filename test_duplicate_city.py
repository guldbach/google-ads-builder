#!/usr/bin/env python

from playwright.sync_api import sync_playwright

def test_duplicate_city_prevention():
    """Test that duplicate city names are properly prevented (case-insensitive)"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("🌐 Navigating to Geographic Regions Manager...")
            page.goto("http://localhost:8000/geographic-regions-manager/")
            page.wait_for_load_state('networkidle')
            
            print("🔍 Finding 'dette er min nye region 2'...")
            region_elements = page.locator('.geographic-region-section')
            target_region = None
            
            for i in range(region_elements.count()):
                element = region_elements.nth(i)
                region_name = element.locator('h3').text_content().strip()
                if 'dette er min nye region 2' in region_name.lower():
                    target_region = element
                    print(f"✅ Found region: {region_name}")
                    break
            
            if not target_region:
                print("❌ Could not find target region")
                return
            
            # Test 1: Try to add "brønderslev" (lowercase) - should be rejected
            print("\n🧪 Test 1: Trying to add 'brønderslev' (lowercase)...")
            add_city_button = target_region.locator('button').filter(has_text='Tilføj By')
            add_city_button.click()
            
            page.wait_for_selector('#add-city-name', state='visible')
            
            # Fill in the city name (lowercase to test case-insensitive detection)
            page.fill('#add-city-name', 'brønderslev')
            page.fill('#add-city-postal-code', '9700')  # Add postal code this time
            
            # Submit the form
            page.click('button[type="submit"]')
            
            # Wait for response
            page.wait_for_timeout(1000)
            
            # Check if error message appears
            error_visible = page.locator('.text-red-600').is_visible()
            if error_visible:
                error_text = page.locator('.text-red-600').text_content()
                print(f"✅ Duplicate correctly rejected: {error_text}")
            else:
                print("❌ Duplicate was not rejected - this is a problem!")
            
            # Close the modal
            page.click('button:has-text("Annuller")')
            page.wait_for_timeout(500)
            
            # Test 2: Try to add "BRØNDERSLEV" (uppercase) - should also be rejected
            print("\n🧪 Test 2: Trying to add 'BRØNDERSLEV' (uppercase)...")
            add_city_button.click()
            page.wait_for_selector('#add-city-name', state='visible')
            
            page.fill('#add-city-name', 'BRØNDERSLEV')
            page.fill('#add-city-postal-code', '')  # No postal code to test name-only duplicate
            
            page.click('button[type="submit"]')
            page.wait_for_timeout(1000)
            
            error_visible = page.locator('.text-red-600').is_visible()
            if error_visible:
                error_text = page.locator('.text-red-600').text_content()
                print(f"✅ Duplicate correctly rejected: {error_text}")
            else:
                print("❌ Duplicate was not rejected - this is a problem!")
            
            # Test 3: Try to add a genuinely new city - should work
            print("\n🧪 Test 3: Trying to add 'Aalborg' (new city)...")
            page.fill('#add-city-name', 'Aalborg')
            page.fill('#add-city-postal-code', '9000')
            
            page.click('button[type="submit"]')
            page.wait_for_timeout(2000)
            
            # Check if city appears in the list
            city_list = target_region.locator('.city-item')
            aalborg_found = False
            for i in range(city_list.count()):
                city_text = city_list.nth(i).text_content()
                if 'Aalborg' in city_text:
                    aalborg_found = True
                    print(f"✅ New city successfully added: {city_text.strip()}")
                    break
            
            if not aalborg_found:
                print("❌ New city was not added - unexpected!")
                
            print("\n🏁 Test completed!")
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            page.screenshot(path="duplicate_city_test_error.png")
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_duplicate_city_prevention()