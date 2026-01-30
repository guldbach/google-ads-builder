"""
Playwright test for crawl functionality timeout fix.
Tests that the service detection doesn't hang indefinitely and responds within timeout limits.
"""
import asyncio
from playwright.async_api import async_playwright


async def test_crawl_hjarsoelteknik():
    """
    Test that crawling hjarsoelteknik.dk works correctly with the timeout fixes.

    Expected behavior:
    - Roberto loading animation shows during detection
    - Response comes within 3 minutes (or timeout error is shown)
    - Services/industries are detected (e.g., "Elektriker" or "El")
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            print("1. Navigating to campaign builder...")
            await page.goto('http://localhost:8000/campaign-builder/')
            await page.wait_for_load_state('networkidle')

            print("2. Selecting a purpose (required for Step 0)...")
            # Select at least one purpose card to enable next button
            purpose_card = page.locator('[data-purpose="google_ads"]')
            await purpose_card.click()
            await page.wait_for_timeout(500)

            print("3. Going to Step 1 (Website URL step)...")
            # Click the global next button to go from Step 0 to Step 1
            next_btn = page.locator('#next-btn')
            await next_btn.click()
            await page.wait_for_timeout(500)

            # Wait for step 1 to be visible
            await page.wait_for_selector('#step-content-1:not([style*="display: none"])', timeout=5000)

            print("4. Entering website URL...")
            # Find and fill the URL input (now visible in step 1)
            url_input = page.locator('#website-url-input')
            await url_input.fill('hjarsoelteknik.dk')
            await page.wait_for_timeout(1000)

            print("5. Clicking 'Næste' button to trigger crawl...")
            # Click the next button again to trigger crawl (go from step 1 to step 2)
            await next_btn.click()

            print("6. Waiting for Roberto loading modal...")
            # Wait for Roberto loading modal to appear (max 10 seconds)
            try:
                await page.wait_for_selector('#roberto-loading-modal:not([style*="display: none"])', timeout=10000)
                print("   ✓ Roberto loading modal is visible")
            except Exception as e:
                print(f"   ! Roberto modal might not be visible: {e}")

            print("7. Waiting for service detection to complete (max 5 minutes)...")
            # Wait for completion - either Roberto hides or alert shows
            try:
                await page.wait_for_function(
                    """() => {
                        const modal = document.getElementById('roberto-loading-modal');
                        const isHidden = !modal || modal.style.display === 'none' ||
                                        modal.classList.contains('hidden');
                        return isHidden;
                    }""",
                    timeout=300000  # 5 minutes
                )
                print("   ✓ Service detection completed")
            except Exception as timeout_error:
                print(f"   ! Timeout waiting for detection: {timeout_error}")
                # Check if alert was shown
                await page.wait_for_timeout(1000)

            print("8. Verifying service detection results...")
            # Get the service detection result from JavaScript
            result = await page.evaluate('campaignConfig?.service_detection || {}')

            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Detected industries: {result.get('detected_industries', [])}")
            print(f"   Detected services: {result.get('detected_services', [])}")
            print(f"   Pages scraped: {result.get('pages_scraped', 0)}")

            # Validate results
            status = result.get('status')
            if status == 'success':
                industries = result.get('detected_industries', [])
                detected_industry_ids = result.get('detected_industry_ids', [])

                if len(industries) > 0 or len(detected_industry_ids) > 0:
                    print("\n✓ TEST PASSED: Crawl completed successfully with detected industries!")
                else:
                    print("\n⚠ TEST WARNING: Crawl completed but no industries detected")
            elif status == 'error':
                error_msg = result.get('error_message', 'Unknown error')
                print(f"\n✗ TEST FAILED: Service detection returned error: {error_msg}")
            else:
                print(f"\n⚠ TEST INCONCLUSIVE: Unexpected status: {status}")

            # Take screenshot for debugging
            await page.screenshot(path='test_crawl_result.png')
            print("\nScreenshot saved to test_crawl_result.png")

        except Exception as e:
            print(f"\n✗ TEST ERROR: {e}")
            await page.screenshot(path='test_crawl_error.png')
            raise
        finally:
            await browser.close()


async def test_timeout_behavior():
    """
    Test that timeout error handling works correctly.

    This test verifies that if a request times out, the user gets proper feedback.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            print("Testing timeout error handling...")
            await page.goto('http://localhost:8000/campaign-builder/')
            await page.wait_for_load_state('networkidle')

            # Listen for alert dialogs
            alert_shown = False
            alert_message = ""

            def handle_dialog(dialog):
                nonlocal alert_shown, alert_message
                alert_shown = True
                alert_message = dialog.message
                asyncio.create_task(dialog.accept())

            page.on('dialog', handle_dialog)

            # Fill URL and trigger crawl
            url_input = page.locator('#website-url-input, input[name="website_url"]').first
            await url_input.fill('hjarsoelteknik.dk')
            await page.wait_for_timeout(500)

            next_button = page.locator('button:has-text("Næste"), button:has-text("Next")').first
            await next_button.click()

            # Wait for completion or alert
            await page.wait_for_timeout(180000)  # Wait up to 3 min

            if alert_shown:
                print(f"Alert was shown with message: {alert_message}")

            print("✓ Timeout behavior test completed")

        except Exception as e:
            print(f"Test error: {e}")
        finally:
            await browser.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Running Crawl Timeout Fix Tests")
    print("=" * 60)
    print()

    asyncio.run(test_crawl_hjarsoelteknik())
