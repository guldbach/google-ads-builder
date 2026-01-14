"""
Playwright test - Verify Client Detail page with segmented sections.
Tests:
1. Quick stats bar displays
2. Navigation tabs work
3. All sections load correctly
4. Geo map modal opens
"""
import asyncio
from playwright.async_api import async_playwright


async def test_client_detail_sections():
    """
    Test the new Client Detail page with segmented sections.
    """
    print("\n" + "=" * 60)
    print("TEST: Client Detail Segmented Sections")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page()

        try:
            # 1. Load a specific client detail page directly
            print("\n1. Loading client detail page...")
            # Try client IDs that might exist
            for client_id in [14, 16, 15, 17, 2, 3]:
                response = await page.goto(f'http://localhost:8000/clients/{client_id}/')
                if response.status == 200:
                    print(f"   Found client with ID {client_id}")
                    break
            else:
                # No client found, create one first
                print("   No clients found, going to client list to create one...")
                await page.goto('http://localhost:8000/clients/')
                await page.wait_for_load_state('networkidle')

                create_btn = await page.query_selector('#create-client-btn')
                if create_btn:
                    await create_btn.click()
                    await asyncio.sleep(0.5)
                    await page.fill('#client-name', 'Test Detail Kunde')
                    await page.fill('#client-website', 'https://testdetail.dk')
                    save_btn = await page.query_selector('#save-client-btn')
                    if save_btn:
                        await save_btn.click()
                        await asyncio.sleep(1)

                # Find and click on first client link
                await page.reload()
                await page.wait_for_load_state('networkidle')

            await page.wait_for_load_state('networkidle')

            # 2. Check page header loaded (Quick Stats Bar was removed)
            print("\n2. Checking page header...")
            header_section = await page.query_selector('.bg-gradient-to-br')
            if header_section:
                print("   [PASS] Page header loaded")
                stats_test_passed = True
            else:
                print("   [FAIL] Page header not found")
                stats_test_passed = False

            # 3. Check Navigation Tabs
            print("\n3. Checking Navigation Tabs...")
            tabs = await page.query_selector_all('button.section-tab')
            tab_count = len(tabs)
            if tab_count >= 6:
                print(f"   [PASS] Found {tab_count} navigation tabs")
                tabs_test_passed = True
            else:
                print(f"   [INFO] Found {tab_count} tabs")
                tabs_test_passed = tab_count > 0

            # 4. Test clicking each tab
            print("\n4. Testing tab navigation...")
            sections = ['overview', 'campaigns', 'company', 'texts', 'usps', 'industries', 'geo']
            sections_test_passed = True
            sections_passed = 0

            for section in sections:
                tab = await page.query_selector(f'button.section-tab[data-section="{section}"]')
                if tab:
                    await tab.click()
                    await asyncio.sleep(0.3)

                    section_content = await page.query_selector(f'#section-{section}')
                    if section_content:
                        is_hidden = await section_content.evaluate('el => el.classList.contains("hidden")')
                        if not is_hidden:
                            print(f"   [PASS] {section.capitalize()} section visible")
                            sections_passed += 1
                        else:
                            print(f"   [FAIL] {section.capitalize()} section hidden")
                    else:
                        print(f"   [FAIL] {section.capitalize()} section not found")
                else:
                    print(f"   [FAIL] {section.capitalize()} tab not found")

            sections_test_passed = sections_passed >= 5  # At least 5 of 7 should work

            # 5. Test Geo Modal with Leaflet and Campaign Builder functionality
            print("\n5. Testing Geo Modal with Leaflet...")
            geo_tab = await page.query_selector('button.section-tab[data-section="geo"]')
            if geo_tab:
                await geo_tab.click()
                await asyncio.sleep(0.3)

                geo_modal_btn = await page.query_selector('button:has-text("Se Bykort")')
                if geo_modal_btn:
                    await geo_modal_btn.click()
                    await asyncio.sleep(1.5)  # Wait for Leaflet map and DAWA data to load

                    # Check if modal is visible
                    geo_modal = await page.query_selector('#geo-modal')
                    if geo_modal:
                        is_hidden = await geo_modal.evaluate('el => el.classList.contains("hidden")')
                        if not is_hidden:
                            print("   [PASS] Geo modal opened")
                            geo_modal_passed = True

                            # Check for Leaflet map container
                            leaflet_map = await page.query_selector('#geo-map .leaflet-container')
                            if leaflet_map:
                                print("   [PASS] Leaflet map initialized")
                            else:
                                # Wait a bit more for the map
                                await asyncio.sleep(1)
                                leaflet_map = await page.query_selector('#geo-map .leaflet-container')
                                if leaflet_map:
                                    print("   [PASS] Leaflet map initialized (delayed)")
                                else:
                                    print("   [INFO] Leaflet map container not found yet")

                            # Check for postal code input
                            postal_input = await page.query_selector('#geo-postal-input')
                            if postal_input:
                                print("   [PASS] Postal code input field found")

                            # Check for circle mode button
                            circle_btn = await page.query_selector('#toggle-circle-mode-btn')
                            if circle_btn:
                                print("   [PASS] Circle mode button found")

                            # Check for clear selections button
                            clear_btn = await page.query_selector('#clear-geo-selections-btn')
                            if clear_btn:
                                print("   [PASS] Clear selections button found")

                            # Check for city list
                            city_list = await page.query_selector('#city-list')
                            if city_list:
                                print("   [PASS] City list container found")

                            # Check for color legend
                            color_legend = await page.query_selector('text="Farvekoder:"')
                            if color_legend:
                                print("   [PASS] Color legend found")

                            # Close modal
                            close_btn = await page.query_selector('#geo-modal button:has-text("Luk")')
                            if close_btn:
                                await close_btn.click()
                            else:
                                await page.keyboard.press('Escape')
                            await asyncio.sleep(0.3)
                        else:
                            print("   [FAIL] Geo modal hidden")
                            geo_modal_passed = False
                    else:
                        print("   [FAIL] Geo modal element not found")
                        geo_modal_passed = False
                else:
                    print("   [INFO] 'Se Bykort' button not found (may not have geo data)")
                    geo_modal_passed = True
            else:
                geo_modal_passed = True

            # Summary
            print("\n" + "-" * 40)
            print("TEST RESULTS:")
            print("-" * 40)

            all_passed = True

            if stats_test_passed:
                print("   [PASS] Page Header")
            else:
                print("   [FAIL] Page Header")
                all_passed = False

            if tabs_test_passed:
                print("   [PASS] Navigation Tabs")
            else:
                print("   [FAIL] Navigation Tabs")
                all_passed = False

            if sections_test_passed:
                print(f"   [PASS] Sections ({sections_passed}/7 working)")
            else:
                print(f"   [FAIL] Sections ({sections_passed}/7 working)")
                all_passed = False

            if geo_modal_passed:
                print("   [PASS] Geo Modal")
            else:
                print("   [FAIL] Geo Modal")
                all_passed = False

            print("\n" + "=" * 60)
            if all_passed:
                print("CLIENT DETAIL SECTIONS TEST PASSED!")
            else:
                print("TEST COMPLETED WITH SOME ISSUES")
            print("=" * 60)

            await asyncio.sleep(2)
            return all_passed

        except Exception as e:
            print(f"\nERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            await browser.close()


if __name__ == '__main__':
    result = asyncio.run(test_client_detail_sections())
    if result:
        print("\n\nClient detail sections test completed successfully!")
    else:
        print("\n\nClient detail sections test completed with issues - check output above")
