#!/usr/bin/env python
"""
Debug script to check why Import Excel button is not clickable
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_import_button():
    """Debug the Import Excel button issue"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False to see what happens
        context = await browser.new_context()
        page = await context.new_page()
        
        # Listen for console messages and errors
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda error: print(f"PAGE ERROR: {error}"))
        
        try:
            print("🔍 Loading negative keywords manager page...")
            await page.goto('http://localhost:8000/negative-keywords-manager/')
            await page.wait_for_load_state('networkidle')
            
            print("✅ Page loaded")
            
            # Scroll down to see lists
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
            # Find VVS list
            vvs_section = page.locator('text=VVS Konkurrenter & DIY').first
            if not await vvs_section.is_visible():
                print("❌ VVS section not found")
                return
            
            print("✅ Found VVS section, clicking to expand...")
            await vvs_section.click()
            await page.wait_for_timeout(1000)
            
            # Take screenshot before testing button
            await page.screenshot(path='debug-button-before.png')
            
            # Find the import button
            import_button = page.locator('.import-excel-btn').first
            if not await import_button.is_visible():
                print("❌ Import button not visible")
                return
                
            print("✅ Import button found and visible")
            
            # Check if button is enabled
            is_enabled = await import_button.is_enabled()
            print(f"Button enabled: {is_enabled}")
            
            # Get button position and size
            box = await import_button.bounding_box()
            print(f"Button position: {box}")
            
            # Check if any overlapping elements
            overlapping = await page.evaluate('''
                () => {
                    const btn = document.querySelector('.import-excel-btn');
                    if (!btn) return "Button not found";
                    
                    const rect = btn.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    
                    const elementAtCenter = document.elementFromPoint(centerX, centerY);
                    
                    return {
                        buttonRect: rect,
                        elementAtCenter: elementAtCenter?.tagName + ' ' + (elementAtCenter?.className || ''),
                        isButtonClickable: btn === elementAtCenter || btn.contains(elementAtCenter)
                    };
                }
            ''')
            print(f"Button clickability check: {overlapping}")
            
            # Test if jQuery event listener is attached
            has_listener = await page.evaluate('''
                () => {
                    const btn = document.querySelector('.import-excel-btn');
                    if (!btn) return "No button";
                    
                    // Check if jQuery events are attached
                    const events = $._data(btn, 'events');
                    return {
                        hasJQueryEvents: !!events,
                        eventTypes: events ? Object.keys(events) : [],
                        hasClickEvent: events && events.click ? events.click.length : 0
                    };
                }
            ''')
            print(f"jQuery event listeners: {has_listener}")
            
            print("🔍 Testing button click...")
            
            # Try clicking the button
            try:
                await import_button.click()
                await page.wait_for_timeout(2000)
                print("✅ Button clicked successfully")
                
                # Wait a moment for animation
                await page.wait_for_timeout(500)
                
                # Check if panel opened
                panel_visible = await page.locator('#slide-panel-overlay').is_visible()
                print(f"Panel opened: {panel_visible}")
                
                # Check panel element visibility too
                panel_element_visible = await page.locator('#slide-panel').is_visible()
                print(f"Panel element visible: {panel_element_visible}")
                
                # Get the actual CSS classes
                overlay_classes = await page.locator('#slide-panel-overlay').get_attribute('class')
                panel_classes = await page.locator('#slide-panel').get_attribute('class')
                print(f"Final overlay classes: {overlay_classes}")
                print(f"Final panel classes: {panel_classes}")
                
                # Check bounding boxes
                overlay_box = await page.locator('#slide-panel-overlay').bounding_box()
                panel_box = await page.locator('#slide-panel').bounding_box()
                print(f"Overlay bounding box: {overlay_box}")
                print(f"Panel bounding box: {panel_box}")
                
                # Check computed styles
                panel_styles = await page.evaluate('''
                    () => {
                        const panel = document.getElementById('slide-panel');
                        const overlay = document.getElementById('slide-panel-overlay');
                        const panelStyles = window.getComputedStyle(panel);
                        const overlayStyles = window.getComputedStyle(overlay);
                        return {
                            panel: {
                                display: panelStyles.display,
                                position: panelStyles.position,
                                right: panelStyles.right,
                                top: panelStyles.top,
                                width: panelStyles.width,
                                height: panelStyles.height,
                                zIndex: panelStyles.zIndex,
                                transform: panelStyles.transform,
                                opacity: panelStyles.opacity
                            },
                            overlay: {
                                display: overlayStyles.display,
                                position: overlayStyles.position,
                                zIndex: overlayStyles.zIndex,
                                opacity: overlayStyles.opacity
                            }
                        };
                    }
                ''')
                print(f"Computed styles: {panel_styles}")
                
                if panel_visible:
                    await page.screenshot(path='debug-panel-opened.png')
                else:
                    await page.screenshot(path='debug-panel-not-opened.png')
                    
            except Exception as e:
                print(f"❌ Click failed: {e}")
                
            # Take final screenshot
            await page.screenshot(path='debug-button-after.png')
            
        except Exception as e:
            print(f"❌ Debug failed: {e}")
            await page.screenshot(path='debug-error.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_import_button())