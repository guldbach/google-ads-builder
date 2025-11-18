#!/usr/bin/env python
"""
Test script to verify scroll behavior in slide panel
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def test_panel_scroll():
    """Test that scroll works correctly in panel and doesn't affect body"""
    
    # Create a large test Excel file to trigger scrollable content
    test_file_content = """Søgeord,Match Type
test keyword 1,Broad Match
test keyword 2,Exact Match
test keyword 3,Phrase Match
test keyword 4,Broad Match
test keyword 5,Exact Match
test keyword 6,Phrase Match
test keyword 7,Broad Match
test keyword 8,Exact Match
test keyword 9,Phrase Match
test keyword 10,Broad Match
test keyword 11,Broad Match
test keyword 12,Exact Match
test keyword 13,Phrase Match
test keyword 14,Broad Match
test keyword 15,Exact Match
test keyword 16,Phrase Match
test keyword 17,Broad Match
test keyword 18,Exact Match
test keyword 19,Phrase Match
test keyword 20,Broad Match
test keyword 21,Broad Match
test keyword 22,Exact Match
test keyword 23,Phrase Match
test keyword 24,Broad Match
test keyword 25,Exact Match"""
    
    test_file_path = '/tmp/test_keywords.csv'
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_file_content)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Listen for console messages
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda error: print(f"PAGE ERROR: {error}"))
        
        try:
            print("🔍 Loading negative keywords manager page...")
            await page.goto('http://localhost:8000/negative-keywords-manager/')
            await page.wait_for_load_state('networkidle')
            
            # Get initial body scroll position
            initial_body_scroll = await page.evaluate('window.pageYOffset')
            print(f"Initial body scroll: {initial_body_scroll}")
            
            # Expand VVS list
            vvs_section = page.locator('text=VVS Konkurrenter & DIY').first
            await vvs_section.click()
            await page.wait_for_timeout(1000)
            
            # Click Import Excel button
            import_button = page.locator('.import-excel-btn').first
            await import_button.click()
            await page.wait_for_timeout(1000)
            
            print("✅ Panel opened")
            
            # Check if body has overflow-hidden class
            body_classes = await page.evaluate('document.body.className')
            print(f"Body classes after panel open: {body_classes}")
            
            # Upload test file
            file_input = page.locator('#list-excel-file-input')
            await file_input.set_input_files(test_file_path)
            await page.wait_for_timeout(1000)
            
            # Click analyze button
            await page.evaluate('document.getElementById("slide-panel-save").click()')
            await page.wait_for_timeout(3000)
            
            print("✅ Analysis complete")
            
            # Test scroll behavior inside panel
            print("🔍 Testing panel scroll...")
            
            # Try to scroll within panel
            panel_content = page.locator('#slide-panel-content')
            await panel_content.hover()
            
            # Get initial panel scroll position
            panel_scroll_before = await page.evaluate('''
                () => {
                    const content = document.getElementById('slide-panel-content');
                    return content ? content.scrollTop : 0;
                }
            ''')
            
            # Scroll down in panel
            await page.mouse.wheel(0, 500)
            await page.wait_for_timeout(500)
            
            # Check panel scroll position after scrolling
            panel_scroll_after = await page.evaluate('''
                () => {
                    const content = document.getElementById('slide-panel-content');
                    return content ? content.scrollTop : 0;
                }
            ''')
            
            # Check if body scroll changed
            body_scroll_after = await page.evaluate('window.pageYOffset')
            
            print(f"Panel scroll before: {panel_scroll_before}")
            print(f"Panel scroll after: {panel_scroll_after}")
            print(f"Body scroll before: {initial_body_scroll}")
            print(f"Body scroll after: {body_scroll_after}")
            
            # Verify scroll behavior
            if panel_scroll_after > panel_scroll_before:
                print("✅ Panel content scrolled correctly")
            else:
                print("❌ Panel content did not scroll")
                
            if body_scroll_after == initial_body_scroll:
                print("✅ Body scroll was blocked correctly")
            else:
                print("❌ Body scroll was not blocked")
            
            # Test closing panel
            print("🔍 Testing panel close...")
            close_button = page.locator('#slide-panel-close')
            await close_button.click()
            await page.wait_for_timeout(500)
            
            # Check if overflow-hidden was removed
            body_classes_after_close = await page.evaluate('document.body.className')
            print(f"Body classes after panel close: {body_classes_after_close}")
            
            if 'overflow-hidden' not in body_classes_after_close:
                print("✅ Body scroll restored correctly")
            else:
                print("❌ Body scroll not restored")
            
            # Take final screenshot
            await page.screenshot(path='debug-scroll-test.png')
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path='debug-scroll-error.png')
            
        finally:
            # Cleanup
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_panel_scroll())