#!/usr/bin/env python
"""
Test script to verify Execute Import functionality works end-to-end
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def test_execute_import():
    """Test the complete Execute Import workflow"""
    
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
        page.on("pageerror", lambda error: print(f"PAGE ERROR: {error}"))
        page.on("response", lambda response: print(f"RESPONSE: {response.url} - {response.status}"))
        
        # Enable JavaScript debugging
        await page.add_init_script('''
            window.addEventListener('error', (e) => {
                console.log('JS ERROR:', e.message, 'at', e.filename + ':' + e.lineno);
            });
        ''')
        
        try:
            print("🔍 Loading negative keywords manager page...")
            await page.goto('http://localhost:8000/negative-keywords-manager/')
            await page.wait_for_load_state('networkidle')
            
            # Expand VVS list
            vvs_section = page.locator('text=VVS Konkurrenter & DIY').first
            await vvs_section.click()
            await page.wait_for_timeout(1000)
            
            # Click Import Excel button
            import_button = page.locator('.import-excel-btn').first
            await import_button.click()
            await page.wait_for_timeout(1000)
            
            print("✅ Panel opened")
            
            # Upload test file
            file_input = page.locator('#list-excel-file-input')
            await file_input.set_input_files(test_file_path)
            await page.wait_for_timeout(1000)
            
            print("✅ File uploaded")
            
            # Click analyze button
            await page.evaluate('document.getElementById("slide-panel-save").click()')
            await page.wait_for_timeout(3000)
            
            print("✅ Analysis completed")
            
            # Check if button text changed to "Udfør Import"
            button_text = await page.locator('#slide-panel-save').inner_text()
            print(f"Button text after analysis: '{button_text}'")
            
            # Take screenshot before execute
            await page.screenshot(path='debug-before-execute.png')
            
            # Try to click Execute Import button
            print("🔍 Clicking Execute Import...")
            
            if '✅ Udfør Import' in button_text:
                await page.locator('#slide-panel-save').click()
                print("✅ Execute Import button clicked")
                
                # Wait for response and check for success/error
                await page.wait_for_timeout(5000)
                
                # Take screenshot after execute attempt
                await page.screenshot(path='debug-after-execute.png')
                
                # Check if panel closed (success) or still open (error)
                panel_visible = await page.locator('#slide-panel-overlay').is_visible()
                print(f"Panel still visible after execute: {panel_visible}")
                
                if not panel_visible:
                    print("✅ Panel closed - import likely successful!")
                    # Check if page was refreshed by looking for the same elements
                    await page.wait_for_timeout(2000)
                    vvs_section_after = page.locator('text=VVS Konkurrenter & DIY').first
                    is_visible = await vvs_section_after.is_visible()
                    print(f"VVS section visible after refresh: {is_visible}")
                else:
                    print("❌ Panel still open - check for error messages")
                    
            else:
                print("❌ Button text did not change to 'Udfør Import'")
                print(f"Current button text: '{button_text}'")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path='debug-execute-error.png')
            
        finally:
            # Don't remove the real Excel file - keep it for multiple tests
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_execute_import())