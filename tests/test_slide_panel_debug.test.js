// Debug slide panel close functionality
const { test, expect } = require('@playwright/test');

test.describe('Slide Panel Debug', () => {
    
    test('should debug slide panel close functionality', async ({ page }) => {
        console.log('Debugging slide panel close functionality...');
        
        // Listen for all console messages
        page.on('console', msg => {
            console.log(`[BROWSER LOG] ${msg.type()}: ${msg.text()}`);
        });
        
        // Listen for all console errors
        page.on('pageerror', err => {
            console.log(`[BROWSER ERROR] ${err.name}: ${err.message}`);
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Open slide panel
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            const importButton = page.locator('.import-excel-btn').first();
            console.log('Opening slide panel...');
            await importButton.click();
            await page.waitForTimeout(1000);
            
            // Check if panel is open
            const slidePanel = page.locator('#slide-panel-overlay');
            const isVisible = await slidePanel.isVisible();
            console.log('Slide panel visible:', isVisible);
            
            if (isVisible) {
                // Check if close button exists
                const closeButton = page.locator('#slide-panel-close');
                const closeButtonExists = await closeButton.isVisible();
                console.log('Close button exists:', closeButtonExists);
                
                // Check if cancel button exists
                const cancelButton = page.locator('#slide-panel-cancel');
                const cancelButtonExists = await cancelButton.isVisible();
                console.log('Cancel button exists:', cancelButtonExists);
                
                // Check window.closeSlidePanel function
                const hasPanelFunction = await page.evaluate(() => {
                    return typeof window.closeSlidePanel === 'function';
                });
                console.log('window.closeSlidePanel function exists:', hasPanelFunction);
                
                // Try manual close
                console.log('Attempting manual close...');
                await page.evaluate(() => {
                    if (typeof window.closeSlidePanel === 'function') {
                        console.log('Calling window.closeSlidePanel()');
                        window.closeSlidePanel();
                    } else {
                        console.log('window.closeSlidePanel is not a function');
                    }
                });
                
                await page.waitForTimeout(1000);
                
                const stillVisible = await slidePanel.isVisible();
                console.log('Panel still visible after manual close:', stillVisible);
                
                // Check for CSS classes
                const panelClasses = await page.locator('#slide-panel').getAttribute('class');
                const overlayClasses = await page.locator('#slide-panel-overlay').getAttribute('class');
                console.log('Panel classes:', panelClasses);
                console.log('Overlay classes:', overlayClasses);
                
            } else {
                console.log('❌ Slide panel did not open');
            }
        }
        
        expect(true).toBe(true);
    });
});