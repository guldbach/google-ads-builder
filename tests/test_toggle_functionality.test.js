// Test for region toggle functionality
const { test, expect } = require('@playwright/test');

test.describe('Region Toggle Functionality', () => {
    
    test('should test region expand/collapse functionality', async ({ page }) => {
        console.log('Testing region toggle functionality...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Listen for JavaScript errors
        const consoleMessages = [];
        page.on('console', msg => {
            consoleMessages.push(`${msg.type()}: ${msg.text()}`);
        });
        
        // Look for region headers
        const regionHeaders = page.locator('.region-header');
        const regionCount = await regionHeaders.count();
        
        console.log('Found regions:', regionCount);
        
        if (regionCount > 0) {
            // Get the first region
            const firstRegion = regionHeaders.first();
            
            // Check if onclick attribute exists
            const onclickValue = await firstRegion.getAttribute('onclick');
            console.log('Onclick attribute:', onclickValue);
            
            // Check initial state - cities content should be hidden
            const regionId = await page.evaluate(() => {
                const firstRegionElement = document.querySelector('.geographic-region-section');
                return firstRegionElement ? firstRegionElement.getAttribute('data-region-id') : null;
            });
            
            console.log('Region ID:', regionId);
            
            if (regionId) {
                const citiesContent = page.locator(`.cities-content[data-region-id="${regionId}"]`);
                const isVisibleBefore = await citiesContent.isVisible();
                console.log('Cities content visible before click:', isVisibleBefore);
                
                // Click the header
                await firstRegion.click();
                await page.waitForTimeout(1000);
                
                // Check if it's visible now
                const isVisibleAfter = await citiesContent.isVisible();
                console.log('Cities content visible after click:', isVisibleAfter);
                
                // Check for JavaScript errors
                console.log('Console messages:', consoleMessages);
                
                // Verify toggle worked
                if (isVisibleBefore === false && isVisibleAfter === true) {
                    console.log('✅ Toggle functionality works correctly!');
                } else {
                    console.log('❌ Toggle functionality not working');
                    console.log('Before:', isVisibleBefore, 'After:', isVisibleAfter);
                    
                    // Check if toggleRegionExpansion function exists
                    const functionExists = await page.evaluate(() => {
                        return typeof window.toggleRegionExpansion;
                    });
                    console.log('toggleRegionExpansion function type:', functionExists);
                    
                    // Try calling the function manually
                    try {
                        await page.evaluate((id) => {
                            console.log('Trying to call toggleRegionExpansion with ID:', id);
                            window.toggleRegionExpansion(id);
                        }, parseInt(regionId));
                    } catch (e) {
                        console.log('Error calling toggleRegionExpansion:', e.message);
                    }
                }
            }
        } else {
            console.log('No regions found to test');
        }
    });
});