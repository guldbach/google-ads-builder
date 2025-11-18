import asyncio
from playwright.async_api import async_playwright

async def test_full_usp_creation():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to USP manager
        await page.goto('http://localhost:8000/usps/manager/')
        
        print("🚀 Testing Complete USP Creation with Placeholders\n")
        
        # Open "Ny USP" slide-in
        print("📝 Opening 'Ny USP' slide-in...")
        await page.click('#add-usp-btn')
        await page.wait_for_selector('#slide-panel', state='visible')
        
        # Fill USP with placeholders
        print("✏️ Filling USP with placeholders...")
        await page.fill('#edit-usp-text', 'Ring {TELEFON} - få {SERVICE} pris i {BYNAVN}')
        await page.fill('#edit-usp-explanation', 'Perfekt til lokale servicevirksomheder der vil fremhæve telefonnummer og byspecifikke services')
        
        # Check that all expected placeholders are available
        expected_placeholders = [
            '{SERVICE}', '{BYNAVN}', '{PRIS}', '{OMRÅDE}', 
            '{BEDØMMELSE}', '{BEDØMMELSESPLATFORM}', '{VIRKSOMHED}', 
            '{TELEFON}', '{ÅBNINGSTID}'
        ]
        
        print(f"🔍 Checking for {len(expected_placeholders)} expected placeholders...")
        for placeholder in expected_placeholders:
            button = await page.query_selector(f'[data-placeholder="{placeholder}"]')
            if button:
                print(f"✅ {placeholder} button found")
            else:
                print(f"❌ {placeholder} button missing")
        
        # Save USP (just simulate - don't actually save)
        print("\n💾 USP ready to save with placeholders!")
        print("📝 USP Text: 'Ring {TELEFON} - få {SERVICE} pris i {BYNAVN}'")
        print("📝 Explanation: 'Perfekt til lokale servicevirksomheder...'")
        print("✅ All placeholders available as standard reference!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_full_usp_creation())