import asyncio
from playwright.async_api import async_playwright

async def debug_nkw_issues():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Capture all console messages and errors
        console_messages = []
        js_errors = []
        network_failures = []
        
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda error: js_errors.append(str(error)))
        page.on("response", lambda response: network_failures.append(f"{response.status} - {response.url}") if response.status >= 400 else None)
        
        print("🐛 DEBUGGING: Negative Keywords Manager Issues")
        print("=" * 60)
        
        try:
            # Step 1: Navigate and check basic loading
            print("\n📍 STEP 1: Page Loading")
            response = await page.goto('http://localhost:8000/negative-keywords-manager/')
            print(f"   Status Code: {response.status}")
            
            await page.wait_for_load_state('networkidle')
            print("   ✅ Page loaded successfully")
            
            # Check if page content exists
            body_text = await page.evaluate('() => document.body.innerText')
            if len(body_text) < 100:
                print(f"   ⚠️  Page content seems minimal: {len(body_text)} characters")
                print(f"   First 200 chars: {body_text[:200]}")
            
            # Step 2: Check for errors
            print("\n🚨 STEP 2: Error Detection")
            if js_errors:
                print(f"   JavaScript Errors ({len(js_errors)}):")
                for error in js_errors:
                    print(f"     • {error}")
            else:
                print("   ✅ No JavaScript errors")
            
            if network_failures:
                print(f"   Network Failures ({len(network_failures)}):")
                for failure in network_failures:
                    print(f"     • {failure}")
            else:
                print("   ✅ No network failures")
            
            # Step 3: Check DOM structure
            print("\n🏗️  STEP 3: DOM Structure Check")
            
            # Check critical elements
            critical_elements = {
                'hero-title': 'h1',
                'main-container': '.max-w-7xl',
                'create-button': '#create-list-btn',
                'slide-panel': '#slide-panel',
                'slide-overlay': '#slide-panel-overlay'
            }
            
            for name, selector in critical_elements.items():
                element = await page.query_selector(selector)
                print(f"   {name}: {'✅ Found' if element else '❌ Missing'}")
            
            # Step 4: Test JavaScript environment
            print("\n🔧 STEP 4: JavaScript Environment")
            
            # Check jQuery
            jquery_check = await page.evaluate('''
                () => {
                    try {
                        return {
                            loaded: typeof $ === 'function',
                            version: typeof $.fn !== 'undefined' ? $.fn.jquery : 'unknown'
                        };
                    } catch (e) {
                        return { loaded: false, error: e.message };
                    }
                }
            ''')
            print(f"   jQuery: {'✅ Loaded' if jquery_check.get('loaded') else '❌ Missing'}")
            if jquery_check.get('version'):
                print(f"     Version: {jquery_check['version']}")
            if jquery_check.get('error'):
                print(f"     Error: {jquery_check['error']}")
            
            # Check custom functions
            custom_functions = ['openCreateListPanel', 'closeSlidePanel', 'forceClosePanel']
            for func in custom_functions:
                func_exists = await page.evaluate(f'() => typeof {func} === "function"')
                print(f"   {func}: {'✅ Available' if func_exists else '❌ Missing'}")
            
            # Step 5: Test actual interaction
            print("\n🖱️  STEP 5: Interaction Testing")
            
            # Test button clicking
            create_btn = await page.query_selector('#create-list-btn')
            if create_btn:
                print("   Testing create button click...")
                
                # Get button properties
                btn_visible = await create_btn.is_visible()
                btn_enabled = await create_btn.is_enabled()
                btn_box = await create_btn.bounding_box()
                
                print(f"     Visible: {btn_visible}")
                print(f"     Enabled: {btn_enabled}")
                print(f"     Position: {btn_box}")
                
                if btn_visible and btn_enabled:
                    try:
                        # Try clicking the button
                        await create_btn.click(timeout=5000)
                        await page.wait_for_timeout(1000)
                        print("     ✅ Button clicked successfully")
                        
                        # Check if panel opened
                        panel_state = await page.evaluate('''
                            () => {
                                const overlay = document.getElementById('slide-panel-overlay');
                                const panel = document.getElementById('slide-panel');
                                return {
                                    overlay_exists: !!overlay,
                                    overlay_hidden: overlay ? overlay.classList.contains('hidden') : true,
                                    panel_exists: !!panel,
                                    panel_transformed: panel ? panel.classList.contains('translate-x-full') : true
                                };
                            }
                        ''')
                        
                        print(f"     Panel state: {panel_state}")
                        
                        if not panel_state['overlay_hidden']:
                            print("     ✅ Panel opened successfully")
                            
                            # Test closing
                            print("   Testing panel closing...")
                            
                            # Try ESC key
                            await page.keyboard.press('Escape')
                            await page.wait_for_timeout(500)
                            
                            panel_closed = await page.evaluate('''
                                () => {
                                    const overlay = document.getElementById('slide-panel-overlay');
                                    return !overlay || overlay.classList.contains('hidden');
                                }
                            ''')
                            
                            if panel_closed:
                                print("     ✅ Panel closed with ESC key")
                            else:
                                print("     ⚠️  ESC key didn't close panel")
                                
                                # Try force close function
                                await page.evaluate('forceClosePanel()')
                                await page.wait_for_timeout(500)
                                
                                force_closed = await page.evaluate('''
                                    () => {
                                        const overlay = document.getElementById('slide-panel-overlay');
                                        return !overlay || overlay.classList.contains('hidden');
                                    }
                                ''')
                                
                                print(f"     Force close: {'✅ Success' if force_closed else '❌ Failed'}")
                        
                        else:
                            print("     ❌ Panel didn't open")
                            
                    except Exception as e:
                        print(f"     ❌ Button click failed: {e}")
                else:
                    print(f"     ❌ Button not clickable (visible: {btn_visible}, enabled: {btn_enabled})")
            else:
                print("   ❌ Create button not found")
            
            # Step 6: Check AJAX functionality
            print("\n🌐 STEP 6: AJAX Endpoints Test")
            
            endpoints = [
                '/ajax/create-negative-keyword-list/',
                '/download-negative-keywords-template/'
            ]
            
            for endpoint in endpoints:
                try:
                    response = await page.evaluate(f'''
                        fetch('{endpoint}', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                            }},
                            body: JSON.stringify({{}})
                        }})
                        .then(r => ({{status: r.status, ok: r.ok}}))
                        .catch(e => ({{error: e.message}}))
                    ''')
                    
                    if 'error' in response:
                        print(f"   {endpoint}: ❌ {response['error']}")
                    else:
                        print(f"   {endpoint}: ✅ Status {response['status']}")
                        
                except Exception as e:
                    print(f"   {endpoint}: ❌ Exception {e}")
            
            # Step 7: Check CSS/Styling
            print("\n🎨 STEP 7: Styling Verification")
            
            # Check if Tailwind is working
            test_gradient = await page.evaluate('''
                () => {
                    const el = document.querySelector('.bg-gradient-to-r');
                    if (el) {
                        const styles = getComputedStyle(el);
                        return {
                            background: styles.background,
                            backgroundImage: styles.backgroundImage
                        };
                    }
                    return null;
                }
            ''')
            
            if test_gradient and ('gradient' in test_gradient.get('background', '') or 'gradient' in test_gradient.get('backgroundImage', '')):
                print("   ✅ Tailwind gradients working")
            else:
                print("   ⚠️  Tailwind gradients may not be working")
                print(f"     Background styles: {test_gradient}")
            
            # Final summary
            print("\n" + "=" * 60)
            print("📊 ISSUE SUMMARY:")
            
            issues = []
            if js_errors:
                issues.append(f"JavaScript errors: {len(js_errors)}")
            if network_failures:
                issues.append(f"Network failures: {len(network_failures)}")
            if not jquery_check.get('loaded'):
                issues.append("jQuery not loaded")
            
            if issues:
                print("❌ ISSUES FOUND:")
                for issue in issues:
                    print(f"   • {issue}")
            else:
                print("✅ No critical issues detected")
            
            print("\n📝 CONSOLE OUTPUT:")
            for msg in console_messages[-10:]:  # Last 10 messages
                print(f"   {msg}")
            
        except Exception as e:
            print(f"❌ Critical error during debugging: {e}")
        
        await page.wait_for_timeout(3000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_nkw_issues())