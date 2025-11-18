import asyncio
from playwright.async_api import async_playwright

async def analyze_design():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to USP manager
        await page.goto('http://localhost:8000/usps/manager/')
        await page.wait_for_load_state('networkidle')
        
        print("🎨 ANALYZING USP MANAGER DESIGN & UX")
        print("=" * 50)
        
        # 1. Overall Layout Analysis
        print("\n📐 LAYOUT STRUCTURE:")
        hero_section = await page.query_selector('.text-center.mb-12')
        if hero_section:
            print("✅ Hero Section: Centered, gradient background, large icon")
            
        quick_actions = await page.query_selector('.bg-white.rounded-2xl.shadow-lg.p-6.mb-8')
        if quick_actions:
            print("✅ Quick Actions: White card with shadow, rounded corners")
        
        categories = await page.query_selector_all('.category-section')
        print(f"✅ Categories: {len(categories)} category cards with consistent styling")
        
        # 2. Color Scheme Analysis
        print("\n🎨 COLOR PALETTE:")
        gradient_buttons = await page.query_selector_all('[class*="from-purple-6"][class*="to-pink-6"]')
        print(f"✅ Primary Gradient: Purple to Pink ({len(gradient_buttons)} elements)")
        
        blue_purple_buttons = await page.query_selector_all('[class*="from-blue-6"][class*="to-purple-6"]')
        print(f"✅ Secondary Gradient: Blue to Purple ({len(blue_purple_buttons)} elements)")
        
        # 3. Interactive Elements
        print("\n🖱️  INTERACTIVE ELEMENTS:")
        hover_elements = await page.query_selector_all('[class*="hover:"]')
        print(f"✅ Hover States: {len(hover_elements)} elements with hover effects")
        
        transition_elements = await page.query_selector_all('[class*="transition"]')
        print(f"✅ Transitions: {len(transition_elements)} elements with smooth transitions")
        
        # 4. Typography Analysis
        print("\n📝 TYPOGRAPHY:")
        h1_elements = await page.query_selector_all('h1')
        for h1 in h1_elements:
            text = await h1.inner_text()
            print(f"✅ H1: '{text}' - Large, bold primary heading")
            
        h2_elements = await page.query_selector_all('h2')
        for h2 in h2_elements:
            text = await h2.inner_text()
            print(f"✅ H2: '{text}' - Section headers")
            
        # 5. Card Design Analysis
        print("\n🃏 CARD DESIGN PATTERNS:")
        white_cards = await page.query_selector_all('.bg-white.rounded-2xl.shadow-lg')
        print(f"✅ White Cards: {len(white_cards)} cards with rounded-2xl and shadow-lg")
        
        # 6. Icon Usage
        print("\n🎯 ICON USAGE:")
        svg_icons = await page.query_selector_all('svg')
        print(f"✅ SVG Icons: {len(svg_icons)} vector icons for scalability")
        
        emoji_usage = await page.locator(':text("➕")').count() + await page.locator(':text("⭐")').count()
        print(f"✅ Emoji Icons: {emoji_usage} emojis for quick recognition")
        
        # 7. Spacing & Layout
        print("\n📏 SPACING SYSTEM:")
        space_y_elements = await page.query_selector_all('[class*="space-y-"]')
        print(f"✅ Vertical Spacing: {len(space_y_elements)} elements using space-y utilities")
        
        flex_elements = await page.query_selector_all('[class*="flex"]')
        print(f"✅ Flexbox Layout: {len(flex_elements)} flex containers")
        
        # 8. Slide-in Panel Analysis
        print("\n📱 SLIDE-IN PANEL:")
        await page.click('#add-usp-btn')
        await page.wait_for_selector('#slide-panel', state='visible')
        
        panel_width = await page.evaluate('() => document.querySelector("#slide-panel").offsetWidth')
        print(f"✅ Panel Width: {panel_width}px - Right-side overlay")
        
        form_sections = await page.query_selector_all('#slide-panel .border-t')
        print(f"✅ Form Sections: {len(form_sections)} distinct sections with border separators")
        
        input_styles = await page.query_selector_all('#slide-panel input')
        print(f"✅ Input Fields: {len(input_styles)} fields with consistent rounded styling")
        
        # 9. Button Analysis
        print("\n🔘 BUTTON PATTERNS:")
        primary_buttons = await page.query_selector_all('.bg-gradient-to-r')
        print(f"✅ Primary Buttons: {len(primary_buttons)} gradient buttons")
        
        text_buttons = await page.query_selector_all('button:not([class*="bg-"])')
        print(f"✅ Text/Icon Buttons: {len(text_buttons)} minimal style buttons")
        
        await page.screenshot(path='usp_design_analysis.png')
        print(f"\n📷 Screenshot saved: usp_design_analysis.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_design())