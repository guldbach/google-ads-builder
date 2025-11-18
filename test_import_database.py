#!/usr/bin/env python
"""
Test script to verify keywords are actually saved to the database after Execute Import
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def test_database_import():
    """Test that Execute Import actually saves keywords to the database"""
    
    # Use the real Excel file created by create_test_excel.py
    test_file_path = '/tmp/test_keywords_real.xlsx'
    
    # Verify file exists
    if not os.path.exists(test_file_path):
        print(f"❌ Excel file not found: {test_file_path}")
        print("Run: python create_test_excel.py first")
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Listen for console messages and network requests
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("response", lambda response: print(f"RESPONSE: {response.url} - {response.status}"))
        
        try:
            print("🔍 Loading negative keywords manager page...")
            await page.goto('http://localhost:8000/negative-keywords-manager/')
            await page.wait_for_load_state('networkidle')
            
            # Count keywords in VVS list BEFORE import
            await page.locator('text=VVS Konkurrenter & DIY').first.click()
            await page.wait_for_timeout(1000)
            
            # Get keyword count before import from the circular badge
            keywords_before_elem = page.locator('.keyword-list-section[data-list-id="1"] span.rounded-full').first
            keywords_before_text = await keywords_before_elem.inner_text()
            keywords_before_count = int(keywords_before_text.strip()) if keywords_before_text.strip().isdigit() else 0
            print(f"📊 Keywords in list BEFORE import: {keywords_before_count}")
            
            # Click Import Excel button
            import_button = page.locator('.import-excel-btn').first
            await import_button.click()
            await page.wait_for_timeout(1000)
            
            # Upload test file
            file_input = page.locator('#list-excel-file-input')
            await file_input.set_input_files(test_file_path)
            await page.wait_for_timeout(1000)
            
            # Click analyze button
            await page.evaluate('document.getElementById("slide-panel-save").click()')
            await page.wait_for_timeout(3000)
            
            # Check all checkboxes to select all keywords for import
            checkboxes = page.locator('input[name="keywords_to_add"]')
            checkbox_count = await checkboxes.count()
            print(f"📋 Found {checkbox_count} keywords to select")
            
            for i in range(checkbox_count):
                await checkboxes.nth(i).check()
                await page.wait_for_timeout(100)
            
            # Click Execute Import button
            await page.locator('#slide-panel-save').click()
            print("✅ Execute Import clicked")
            
            # Wait for panel to close and page to refresh
            await page.wait_for_timeout(5000)
            
            # Count keywords AFTER import
            await page.wait_for_load_state('networkidle')
            
            # Click VVS section again to expand it
            await page.locator('text=VVS Konkurrenter & DIY').first.click()
            await page.wait_for_timeout(1000)
            
            # Get keyword count after import from the circular badge
            keywords_after_elem = page.locator('.keyword-list-section[data-list-id="1"] span.rounded-full').first
            keywords_after_text = await keywords_after_elem.inner_text()
            keywords_after_count = int(keywords_after_text.strip()) if keywords_after_text.strip().isdigit() else 0
            print(f"📊 Keywords in list AFTER import: {keywords_after_count}")
            
            # Calculate difference
            keywords_added = keywords_after_count - keywords_before_count
            print(f"➕ Keywords added to database: {keywords_added}")
            
            if keywords_added > 0:
                print("✅ SUCCESS: Keywords were successfully saved to the database!")
            else:
                print("❌ FAILURE: No keywords were added to the database")
            
            # Take a screenshot for verification
            await page.screenshot(path='import_verification.png')
            print("📸 Screenshot saved as import_verification.png")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path='import_test_error.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_database_import())