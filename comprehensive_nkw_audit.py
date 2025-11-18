import asyncio
from playwright.async_api import async_playwright
import json

async def comprehensive_audit():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Enable console logging to catch JavaScript errors
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        # Catch JavaScript errors
        js_errors = []
        page.on("pageerror", lambda error: js_errors.append(str(error)))
        
        print("🔍 COMPREHENSIVE AUDIT: Negative Keywords Manager")
        print("=" * 60)
        
        try:
            # Navigate to the page
            response = await page.goto('http://localhost:8000/negative-keywords-manager/')
            print(f"✅ Page loaded with status: {response.status}")
            await page.wait_for_load_state('networkidle')
            
            # Check for JavaScript errors
            if js_errors:
                print("\n❌ JAVASCRIPT ERRORS FOUND:")
                for error in js_errors:
                    print(f"   🚨 {error}")
            else:
                print("✅ No JavaScript errors detected")
            
            # Check critical console messages
            error_messages = [msg for msg in console_messages if 'error' in msg.lower()]
            if error_messages:
                print("\n⚠️  CONSOLE ERRORS:")
                for msg in error_messages[:5]:  # Limit to first 5
                    print(f"   📝 {msg}")
            
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            return
        
        print("\n" + "=" * 60)
        print("🧪 DETAILED FUNCTIONALITY TESTING")
        print("=" * 60)
        
        # Test 1: Page Structure and Content
        print("\n📋 1. PAGE STRUCTURE & CONTENT:")
        
        # Check if page has content
        body_content = await page.evaluate('() => document.body.innerText.length')
        print(f"   📄 Page content length: {body_content} characters")
        
        if body_content < 100:
            print("   ❌ Page appears to be mostly empty")
            # Check for potential template errors
            error_indicators = await page.query_selector_all('.error, .exception, .traceback')
            if error_indicators:
                print("   🚨 Error indicators found on page")
        
        # Check title
        title = await page.title()
        print(f"   📑 Page title: '{title}'")
        
        # Check for hero section
        hero = await page.query_selector('h1')
        if hero:
            hero_text = await hero.inner_text()
            print(f"   🏆 Hero title found: '{hero_text}'")
        else:
            print("   ❌ No h1 element found")
        
        # Test 2: Critical UI Components
        print("\n🎨 2. UI COMPONENTS VERIFICATION:")
        
        # Check for main container
        main_container = await page.query_selector('.max-w-7xl')
        print(f"   📦 Main container: {'✅ Found' if main_container else '❌ Missing'}")
        
        # Check hero section styling
        hero_gradient = await page.query_selector('.bg-gradient-to-br.from-red-100')
        print(f"   🌈 Hero gradient: {'✅ Found' if hero_gradient else '❌ Missing'}")
        
        # Check statistics cards
        stat_cards = await page.query_selector_all('.grid .bg-white.rounded-2xl.shadow-lg')
        print(f"   📊 Statistics cards: {len(stat_cards)} found")
        
        if len(stat_cards) != 4:
            print(f"   ⚠️  Expected 4 cards, found {len(stat_cards)}")
        
        # Test 3: Interactive Elements
        print("\n🔘 3. INTERACTIVE ELEMENTS:")
        
        # Check quick action buttons
        buttons = {
            'create-list-btn': 'Create List',
            'import-excel-btn': 'Import Excel', 
            'download-template-btn': 'Download Template'
        }
        
        for btn_id, btn_name in buttons.items():
            btn = await page.query_selector(f'#{btn_id}')
            if btn:
                is_enabled = await btn.evaluate('el => !el.disabled')
                is_visible = await btn.is_visible()
                print(f"   🔘 {btn_name}: {'✅' if btn and is_enabled and is_visible else '❌'}")
            else:
                print(f"   🔘 {btn_name}: ❌ Not found")
        
        # Test 4: Slide Panel System
        print("\n📱 4. SLIDE PANEL TESTING:")
        
        # Check if slide panel exists
        slide_panel = await page.query_selector('#slide-panel')
        slide_overlay = await page.query_selector('#slide-panel-overlay')
        
        print(f"   📱 Slide panel element: {'✅ Found' if slide_panel else '❌ Missing'}")
        print(f"   🌫️  Slide overlay element: {'✅ Found' if slide_overlay else '❌ Missing'}")
        
        if slide_overlay:
            is_hidden = await slide_overlay.evaluate('el => el.classList.contains("hidden")')
            print(f"   👁️  Panel initially hidden: {'✅ Yes' if is_hidden else '❌ No'}")
        
        # Test panel opening
        if await page.query_selector('#create-list-btn'):
            print("   🔄 Testing panel opening...")
            try:
                await page.click('#create-list-btn')
                await page.wait_for_timeout(1000)  # Wait for animation
                
                panel_visible = await page.evaluate('''
                    () => {
                        const overlay = document.getElementById('slide-panel-overlay');
                        return overlay && !overlay.classList.contains('hidden');
                    }
                ''')
                print(f"   📱 Panel opens on click: {'✅ Success' if panel_visible else '❌ Failed'}")
                
                if panel_visible:
                    # Test form elements in panel
                    form_elements = await page.query_selector_all('#slide-panel input, #slide-panel select, #slide-panel textarea')
                    print(f"   📋 Form elements in panel: {len(form_elements)} found")
                    
                    # Test close button
                    close_btn = await page.query_selector('#slide-panel-close')
                    if close_btn:
                        await close_btn.click()
                        await page.wait_for_timeout(500)
                        panel_hidden = await page.evaluate('''
                            () => {
                                const overlay = document.getElementById('slide-panel-overlay');
                                return !overlay || overlay.classList.contains('hidden');
                            }
                        ''')
                        print(f"   ❌ Panel closes: {'✅ Success' if panel_hidden else '❌ Failed'}")
                
            except Exception as e:
                print(f"   ❌ Panel interaction failed: {e}")
        
        # Test 5: JavaScript Dependencies
        print("\n🔧 5. JAVASCRIPT DEPENDENCIES:")
        
        # Check jQuery
        jquery_loaded = await page.evaluate('() => typeof $ === "function"')
        print(f"   📚 jQuery loaded: {'✅ Yes' if jquery_loaded else '❌ No'}")
        
        # Check custom functions
        functions_to_check = [
            'openCreateListPanel',
            'openImportExcelPanel', 
            'toggleListExpansion',
            'filterLists',
            'addNewKeyword'
        ]
        
        for func_name in functions_to_check:
            func_exists = await page.evaluate(f'() => typeof {func_name} === "function"')
            print(f"   🔧 {func_name}: {'✅ Available' if func_exists else '❌ Missing'}")
        
        # Test 6: Data Loading
        print("\n📊 6. DATA LOADING:")
        
        # Check if statistics show actual data
        stat_values = []
        try:
            stat_cards = await page.query_selector_all('.text-3xl.font-bold')
            for card in stat_cards:
                value = await card.inner_text()
                stat_values.append(value.strip())
            
            print(f"   📈 Statistics values: {stat_values}")
            
            # Check if values look realistic
            if all(val == '0' for val in stat_values):
                print("   ⚠️  All statistics are 0 - might indicate no data or loading issues")
            
        except Exception as e:
            print(f"   ❌ Failed to read statistics: {e}")
        
        # Check if any keyword lists are displayed
        keyword_lists = await page.query_selector_all('.keyword-list-section')
        print(f"   📋 Keyword lists displayed: {len(keyword_lists)}")
        
        if len(keyword_lists) == 0:
            empty_state = await page.query_selector('.text-center.py-12')
            if empty_state:
                empty_text = await empty_state.inner_text()
                print(f"   📝 Empty state message: '{empty_text[:100]}...'")
        
        # Test 7: Search and Filter
        print("\n🔍 7. SEARCH & FILTER FUNCTIONALITY:")
        
        search_input = await page.query_selector('#search-lists')
        filter_select = await page.query_selector('#filter-category')
        reset_btn = await page.query_selector('#reset-filters-btn')
        
        print(f"   🔍 Search input: {'✅ Found' if search_input else '❌ Missing'}")
        print(f"   🗂️  Filter select: {'✅ Found' if filter_select else '❌ Missing'}")
        print(f"   🔄 Reset button: {'✅ Found' if reset_btn else '❌ Missing'}")
        
        # Test search functionality
        if search_input:
            try:
                await search_input.fill('test')
                await page.wait_for_timeout(500)
                print("   ✅ Search input accepts text")
            except Exception as e:
                print(f"   ❌ Search input failed: {e}")
        
        # Test 8: Network Requests
        print("\n🌐 8. NETWORK CONNECTIVITY:")
        
        # Test AJAX endpoints by making test requests
        endpoints_to_test = [
            '/ajax/create-negative-keyword-list/',
            '/download-negative-keywords-template/',
            '/ajax/import-negative-keywords-excel/'
        ]
        
        for endpoint in endpoints_to_test:
            try:
                status = await page.evaluate(f'''
                    fetch('{endpoint}', {{method: 'GET'}})
                    .then(r => r.status)
                    .catch(() => 0)
                ''')
                # 405 Method Not Allowed is expected for POST-only endpoints
                if status in [200, 405]:
                    print(f"   ✅ {endpoint}: Available")
                else:
                    print(f"   ❌ {endpoint}: Status {status}")
            except Exception as e:
                print(f"   ❌ {endpoint}: Error {e}")
        
        # Test 9: CSS and Styling
        print("\n🎨 9. STYLING VERIFICATION:")
        
        # Check if Tailwind classes are working
        test_element = await page.query_selector('.bg-gradient-to-r')
        if test_element:
            bg_color = await test_element.evaluate('el => getComputedStyle(el).background')
            has_gradient = 'gradient' in bg_color or 'linear' in bg_color
            print(f"   🌈 Tailwind gradients: {'✅ Working' if has_gradient else '❌ Not applied'}")
        
        # Check responsive classes
        responsive_elements = await page.query_selector_all('.md\\:')
        print(f"   📱 Responsive classes: {len(responsive_elements)} elements found")
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📋 AUDIT SUMMARY:")
        print("=" * 60)
        
        # Count issues found
        issues_found = []
        
        if js_errors:
            issues_found.append(f"JavaScript errors: {len(js_errors)}")
        
        if len(stat_cards) != 4:
            issues_found.append("Incorrect number of statistics cards")
        
        if not jquery_loaded:
            issues_found.append("jQuery not loaded")
        
        if len(keyword_lists) == 0:
            issues_found.append("No keyword lists displayed (might be normal if empty)")
        
        if issues_found:
            print("❌ ISSUES FOUND:")
            for issue in issues_found:
                print(f"   • {issue}")
        else:
            print("✅ NO CRITICAL ISSUES FOUND")
        
        print("\n🎯 RECOMMENDATIONS:")
        if not jquery_loaded:
            print("   • Ensure jQuery is properly loaded")
        if js_errors:
            print("   • Fix JavaScript errors for optimal functionality")
        if len(keyword_lists) == 0:
            print("   • Consider adding sample data or better empty state messaging")
        
        print(f"\n📊 CONSOLE MESSAGES ({len(console_messages)} total):")
        for msg in console_messages[-5:]:  # Show last 5 messages
            print(f"   {msg}")
        
        await page.wait_for_timeout(2000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(comprehensive_audit())