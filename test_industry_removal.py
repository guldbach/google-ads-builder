#!/usr/bin/env python

from playwright.sync_api import sync_playwright

def test_geographic_regions_no_industry():
    """Test at geographic regions manager virker uden industry felter"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("🌐 Navigating to Geographic Regions Manager...")
            page.goto("http://localhost:8000/geographic-regions-manager/")
            page.wait_for_load_state('networkidle')
            
            # Check that page loads without errors
            title = page.locator('h1:has-text("Geografiske Regioner")').text_content()
            print(f"✅ Page loaded: {title}")
            
            # Check that there's no industry filter dropdown
            industry_filter = page.locator('#filter-industry')
            if industry_filter.count() == 0:
                print("✅ Industry filter dropdown successfully removed")
            else:
                print("❌ Industry filter dropdown still exists")
            
            # Check that there's no industry statistics
            industry_stats = page.locator('.stat-card:has-text("Brancher")')
            if industry_stats.count() == 0:
                print("✅ Industry statistics card successfully removed")
            else:
                print("❌ Industry statistics card still exists")
            
            # Test region display works without errors
            regions = page.locator('.geographic-region-section')
            regions_count = regions.count()
            print(f"✅ Found {regions_count} regions displayed")
            
            if regions_count > 0:
                # Test that region expansion works
                first_region = regions.first()
                region_name = first_region.locator('h3').text_content()
                print(f"✅ Testing expansion of region: {region_name}")
                
                first_region.locator('.region-header').click()
                page.wait_for_timeout(1000)
                
                # Check if cities content is visible
                cities_content = first_region.locator('.cities-content')
                if cities_content.is_visible():
                    print("✅ Region expansion works correctly")
                else:
                    print("❌ Region expansion not working")
            
            print("\n🏁 Industry removal test completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            page.screenshot(path="industry_removal_test_error.png")
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_geographic_regions_no_industry()