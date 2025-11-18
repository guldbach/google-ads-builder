#!/usr/bin/env python
"""
Test script to debug Excel import analyze functionality
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def test_excel_import_analyze():
    """Test the Excel import analyze functionality"""
    
    # Create a simple test Excel file
    test_file_content = """Søgeord,Match Type
test keyword,Broad Match
another keyword,Exact Match
duplicate test,Phrase Match"""
    
    test_file_path = '/tmp/test_keywords.csv'
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_file_content)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Listen for console messages and network requests
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda error: print(f"PAGE ERROR: {error}"))
        page.on("response", lambda response: print(f"RESPONSE: {response.url} - {response.status}"))
        
        try:
            print("🔍 Loading negative keywords manager page...")
            await page.goto('http://localhost:8000/negative-keywords-manager/')
            await page.wait_for_load_state('networkidle')
            
            print("✅ Page loaded")
            
            # Scroll to VVS section and expand
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
            # Find and expand VVS list
            vvs_section = page.locator('text=VVS Konkurrenter & DIY').first
            await vvs_section.click()
            await page.wait_for_timeout(1000)
            
            print("✅ VVS section expanded")
            
            # Click Import Excel button
            import_button = page.locator('.import-excel-btn').first
            await import_button.click()
            await page.wait_for_timeout(1000)
            
            print("✅ Import Excel panel opened")
            
            # Take screenshot of panel
            await page.screenshot(path='debug-panel-after-open.png')
            
            # Wait for file input to be available
            file_input = page.locator('#list-excel-file-input')
            await file_input.wait_for(state='attached')
            
            print("✅ File input found")
            
            # Upload test file
            await file_input.set_input_files(test_file_path)
            await page.wait_for_timeout(1000)
            
            print("✅ File uploaded")
            
            # Find the save button (which should now say "Analyser")
            analyze_button = page.locator('#slide-panel-save')
            await analyze_button.wait_for(state='visible')
            
            # Check button text
            button_text = await analyze_button.inner_text()
            print(f"Button text: '{button_text}'")
            
            # Scroll panel to bottom to make button visible
            await page.evaluate('''
                () => {
                    const panel = document.querySelector('#slide-panel');
                    if (panel) {
                        panel.scrollTop = panel.scrollHeight;
                    }
                }
            ''')
            
            await page.wait_for_timeout(1000)
            
            print("🔍 Clicking Analyser button...")
            await page.evaluate('document.getElementById("slide-panel-save").click()')
            
            # Wait for response and check for errors
            await page.wait_for_timeout(5000)
            
            # Check if analysis results appeared
            analysis_content = page.locator('#analysis-results')
            if await analysis_content.count() > 0:
                print("✅ Analysis results found")
                analysis_text = await analysis_content.inner_text()
                print(f"Analysis content: {analysis_text}")
            else:
                print("❌ No analysis results found")
            
            # Take screenshot
            await page.screenshot(path='debug-analyze-test.png')
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path='debug-analyze-error.png')
            
        finally:
            # Cleanup
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_excel_import_analyze())