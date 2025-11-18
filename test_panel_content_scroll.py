#!/usr/bin/env python
"""
Detailed Playwright test to debug why panel content doesn't scroll properly
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def test_panel_content_scroll():
    """Test and debug panel content scrolling issues"""
    
    # Create test Excel file with many keywords to force scrollable content
    keywords = []
    for i in range(1, 51):  # 50 keywords to ensure lots of content
        keywords.append(f"test keyword {i},Broad Match")
    
    test_file_content = "Søgeord,Match Type\n" + "\n".join(keywords)
    
    test_file_path = '/tmp/test_keywords_large.csv'
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_file_content)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}  # Standard viewport
        )
        page = await context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda error: print(f"PAGE ERROR: {error}"))
        
        try:
            print("🔍 Loading negative keywords manager page...")
            await page.goto('http://localhost:8000/negative-keywords-manager/')
            await page.wait_for_load_state('networkidle')
            
            print("✅ Page loaded")
            
            # Expand VVS list
            vvs_section = page.locator('text=VVS Konkurrenter & DIY').first
            await vvs_section.click()
            await page.wait_for_timeout(1000)
            
            # Click Import Excel button
            import_button = page.locator('.import-excel-btn').first
            await import_button.click()
            await page.wait_for_timeout(1000)
            
            print("✅ Panel opened")
            await page.screenshot(path='debug-panel-opened-step1.png')
            
            # Check panel dimensions and structure
            panel_info = await page.evaluate('''
                () => {
                    const panel = document.getElementById('slide-panel');
                    const content = document.getElementById('slide-panel-content');
                    const overlay = document.getElementById('slide-panel-overlay');
                    
                    if (!panel || !content || !overlay) return { error: 'Missing elements' };
                    
                    const panelRect = panel.getBoundingClientRect();
                    const contentRect = content.getBoundingClientRect();
                    const overlayRect = overlay.getBoundingClientRect();
                    
                    return {
                        viewport: { width: window.innerWidth, height: window.innerHeight },
                        panel: {
                            rect: panelRect,
                            computed: {
                                height: window.getComputedStyle(panel).height,
                                overflow: window.getComputedStyle(panel).overflow,
                                overflowY: window.getComputedStyle(panel).overflowY,
                                display: window.getComputedStyle(panel).display,
                                position: window.getComputedStyle(panel).position
                            },
                            scrollHeight: panel.scrollHeight,
                            scrollTop: panel.scrollTop,
                            clientHeight: panel.clientHeight
                        },
                        content: {
                            rect: contentRect,
                            computed: {
                                height: window.getComputedStyle(content).height,
                                overflow: window.getComputedStyle(content).overflow,
                                overflowY: window.getComputedStyle(content).overflowY,
                                flex: window.getComputedStyle(content).flex
                            },
                            scrollHeight: content.scrollHeight,
                            scrollTop: content.scrollTop,
                            clientHeight: content.clientHeight
                        },
                        overlay: {
                            rect: overlayRect,
                            computed: {
                                position: window.getComputedStyle(overlay).position,
                                zIndex: window.getComputedStyle(overlay).zIndex
                            }
                        }
                    };
                }
            ''')
            
            print("📊 Panel structure analysis:")
            print(f"Viewport: {panel_info['viewport']}")
            print(f"Panel height: {panel_info['panel']['computed']['height']}")
            print(f"Panel overflow-y: {panel_info['panel']['computed']['overflowY']}")
            print(f"Panel scroll stats: height={panel_info['panel']['scrollHeight']}, client={panel_info['panel']['clientHeight']}, top={panel_info['panel']['scrollTop']}")
            print(f"Content height: {panel_info['content']['computed']['height']}")
            print(f"Content overflow-y: {panel_info['content']['computed']['overflowY']}")
            print(f"Content scroll stats: height={panel_info['content']['scrollHeight']}, client={panel_info['content']['clientHeight']}, top={panel_info['content']['scrollTop']}")
            
            # Upload large file
            file_input = page.locator('#list-excel-file-input')
            await file_input.set_input_files(test_file_path)
            await page.wait_for_timeout(1000)
            
            print("✅ Large file uploaded")
            await page.screenshot(path='debug-panel-file-uploaded.png')
            
            # Click analyze button to generate lots of content
            await page.evaluate('document.getElementById("slide-panel-save").click()')
            await page.wait_for_timeout(3000)  # Wait for analysis to complete
            
            print("✅ Analysis completed - checking content scroll")
            await page.screenshot(path='debug-panel-analysis-done.png')
            
            # Check content after analysis
            content_after_analysis = await page.evaluate('''
                () => {
                    const panel = document.getElementById('slide-panel');
                    const content = document.getElementById('slide-panel-content');
                    const analysisResults = document.getElementById('analysis-results');
                    
                    if (!panel || !content) return { error: 'Missing elements' };
                    
                    return {
                        panel: {
                            scrollHeight: panel.scrollHeight,
                            scrollTop: panel.scrollTop,
                            clientHeight: panel.clientHeight,
                            canScroll: panel.scrollHeight > panel.clientHeight
                        },
                        content: {
                            scrollHeight: content.scrollHeight,
                            scrollTop: content.scrollTop,
                            clientHeight: content.clientHeight,
                            canScroll: content.scrollHeight > content.clientHeight
                        },
                        analysisResults: analysisResults ? {
                            visible: !analysisResults.classList.contains('hidden'),
                            scrollHeight: analysisResults.scrollHeight,
                            clientHeight: analysisResults.clientHeight
                        } : null,
                        children: Array.from(content.children).map(child => ({
                            tagName: child.tagName,
                            className: child.className,
                            scrollHeight: child.scrollHeight,
                            clientHeight: child.clientHeight
                        }))
                    };
                }
            ''')
            
            print("📊 Content after analysis:")
            print(f"Panel can scroll: {content_after_analysis['panel']['canScroll']} (scroll: {content_after_analysis['panel']['scrollHeight']}, client: {content_after_analysis['panel']['clientHeight']})")
            print(f"Content can scroll: {content_after_analysis['content']['canScroll']} (scroll: {content_after_analysis['content']['scrollHeight']}, client: {content_after_analysis['content']['clientHeight']})")
            if content_after_analysis['analysisResults']:
                print(f"Analysis results visible: {content_after_analysis['analysisResults']['visible']}")
            
            # Test if save button is visible
            save_button_info = await page.evaluate('''
                () => {
                    const saveBtn = document.getElementById('slide-panel-save');
                    if (!saveBtn) return { error: 'Save button not found' };
                    
                    const rect = saveBtn.getBoundingClientRect();
                    const isVisible = rect.top >= 0 && 
                                    rect.left >= 0 && 
                                    rect.bottom <= window.innerHeight && 
                                    rect.right <= window.innerWidth;
                    
                    return {
                        rect: rect,
                        isVisible: isVisible,
                        isInViewport: rect.bottom <= window.innerHeight,
                        viewportHeight: window.innerHeight,
                        distanceFromBottom: window.innerHeight - rect.bottom
                    };
                }
            ''')
            
            print(f"💾 Save button visibility:")
            print(f"Is visible in viewport: {save_button_info['isVisible']}")
            print(f"Distance from bottom: {save_button_info['distanceFromBottom']}px")
            print(f"Button bottom: {save_button_info['rect']['bottom']}, Viewport height: {save_button_info['viewportHeight']}")
            
            # Try to scroll within panel content
            print("🔍 Attempting to scroll within panel content...")
            
            # Focus on panel content and try scrolling
            await page.locator('#slide-panel-content').click()
            
            # Try scrolling with keyboard
            await page.keyboard.press('PageDown')
            await page.wait_for_timeout(500)
            
            # Try scrolling with mouse wheel on content area
            content_element = page.locator('#slide-panel-content')
            await content_element.hover()
            
            # Mouse wheel scroll
            for i in range(5):
                await page.mouse.wheel(0, 200)
                await page.wait_for_timeout(100)
            
            await page.wait_for_timeout(1000)
            
            # Check scroll position after attempts
            final_scroll_info = await page.evaluate('''
                () => {
                    const panel = document.getElementById('slide-panel');
                    const content = document.getElementById('slide-panel-content');
                    const saveBtn = document.getElementById('slide-panel-save');
                    
                    const saveBtnRect = saveBtn.getBoundingClientRect();
                    
                    return {
                        panel_scrollTop: panel.scrollTop,
                        content_scrollTop: content.scrollTop,
                        saveButtonVisible: saveBtnRect.bottom <= window.innerHeight,
                        saveButtonPosition: saveBtnRect
                    };
                }
            ''')
            
            print(f"📊 After scroll attempts:")
            print(f"Panel scroll top: {final_scroll_info['panel_scrollTop']}")
            print(f"Content scroll top: {final_scroll_info['content_scrollTop']}")
            print(f"Save button visible: {final_scroll_info['saveButtonVisible']}")
            
            # Take final screenshot
            await page.screenshot(path='debug-panel-scroll-final.png')
            
            # Try to manually scroll to bottom
            print("🔍 Manually scrolling to bottom...")
            await page.evaluate('''
                () => {
                    const content = document.getElementById('slide-panel-content');
                    const panel = document.getElementById('slide-panel');
                    
                    // Try scrolling both elements to bottom
                    if (content) {
                        content.scrollTop = content.scrollHeight;
                    }
                    if (panel) {
                        panel.scrollTop = panel.scrollHeight;
                    }
                }
            ''')
            
            await page.wait_for_timeout(1000)
            await page.screenshot(path='debug-panel-manual-scroll.png')
            
            # Final check
            final_check = await page.evaluate('''
                () => {
                    const saveBtn = document.getElementById('slide-panel-save');
                    const rect = saveBtn.getBoundingClientRect();
                    return {
                        saveButtonVisible: rect.bottom <= window.innerHeight,
                        rect: rect,
                        viewportHeight: window.innerHeight
                    };
                }
            ''')
            
            print(f"🎯 Final check - Save button visible: {final_check['saveButtonVisible']}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path='debug-panel-error.png')
            
        finally:
            # Cleanup
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_panel_content_scroll())