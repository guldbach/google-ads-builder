import asyncio
from playwright.async_api import async_playwright

async def analyze_usp_manager_design():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("🎨 ANALYZING USP Manager Design for Color Matching")
        print("=" * 60)
        
        # Navigate to USP manager
        await page.goto('http://localhost:8000/usps/manager/')
        await page.wait_for_load_state('networkidle')
        print("✅ Loaded USP Manager")
        
        # Analyze hero section
        print("\n🏆 HERO SECTION ANALYSIS:")
        hero = await page.query_selector('.text-center.mb-12')
        if hero:
            hero_classes = await hero.get_attribute('class')
            print(f"   Hero classes: {hero_classes}")
            
            # Check background gradient
            hero_bg = await page.evaluate('''
                () => {
                    const hero = document.querySelector('.text-center.mb-12');
                    return hero ? getComputedStyle(hero).background : null;
                }
            ''')
            print(f"   Hero background: {hero_bg}")
        
        # Analyze icon container
        icon_container = await page.query_selector('.w-24.h-24')
        if icon_container:
            icon_classes = await icon_container.get_attribute('class')
            print(f"   Icon container classes: {icon_classes}")
        
        # Analyze quick actions
        print("\n⚡ QUICK ACTIONS ANALYSIS:")
        quick_actions = await page.query_selector('.bg-white.rounded-2xl.shadow-lg.p-6.mb-8')
        if quick_actions:
            qa_classes = await quick_actions.get_attribute('class')
            print(f"   Quick actions classes: {qa_classes}")
        
        # Analyze primary buttons
        primary_buttons = await page.query_selector_all('.bg-gradient-to-r.from-purple-600.to-pink-600')
        print(f"   Primary buttons found: {len(primary_buttons)}")
        if primary_buttons:
            btn_classes = await primary_buttons[0].get_attribute('class')
            print(f"   Primary button classes: {btn_classes}")
        
        # Analyze category sections
        print("\n📋 CATEGORY SECTIONS ANALYSIS:")
        categories = await page.query_selector_all('.category-section')
        print(f"   Categories found: {len(categories)}")
        
        if categories:
            cat_classes = await categories[0].get_attribute('class')
            print(f"   Category classes: {cat_classes}")
            
            # Check category header
            cat_header = await categories[0].query_selector('.category-header')
            if cat_header:
                header_style = await cat_header.get_attribute('style')
                print(f"   Category header style: {header_style}")
        
        # Analyze color schemes used
        print("\n🌈 COLOR SCHEME ANALYSIS:")
        
        # Check for all gradient patterns
        gradient_patterns = [
            '.from-purple-600.to-pink-600',
            '.from-blue-600.to-purple-600', 
            '.from-purple-100.via-blue-50.to-pink-100'
        ]
        
        for pattern in gradient_patterns:
            elements = await page.query_selector_all(pattern)
            if elements:
                print(f"   {pattern}: {len(elements)} elements")
        
        # Check title styling
        print("\n📝 TYPOGRAPHY ANALYSIS:")
        main_title = await page.query_selector('h1')
        if main_title:
            title_classes = await main_title.get_attribute('class')
            title_text = await main_title.inner_text()
            print(f"   Main title: '{title_text}'")
            print(f"   Title classes: {title_classes}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_usp_manager_design())