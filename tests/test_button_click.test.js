// Test actual button clicks
const { test, expect } = require('@playwright/test');

test.describe('Button Click Test', () => {
    
    test('should test actual button clicks', async ({ page }) => {
        console.log('Testing actual button clicks...');
        
        // Listen for console messages
        page.on('console', msg => {
            console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Open slide panel
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            const importButton = page.locator('.import-excel-btn').first();
            await importButton.click();
            await page.waitForTimeout(1000);
            
            // Check if panel is open
            const slidePanel = page.locator('#slide-panel-overlay');
            const isVisible = await slidePanel.isVisible();
            console.log('Slide panel visible:', isVisible);
            
            if (isVisible) {
                // Try clicking close button with force
                console.log('Clicking close button with force...');
                const closeButton = page.locator('#slide-panel-close');
                await closeButton.click({ force: true });
                await page.waitForTimeout(1000);
                
                const stillVisible1 = await slidePanel.isVisible();
                console.log('Panel still visible after force close:', stillVisible1);
                
                if (stillVisible1) {
                    // Re-open and try cancel button
                    console.log('Trying cancel button...');
                    const cancelButton = page.locator('#slide-panel-cancel');
                    await cancelButton.click({ force: true });
                    await page.waitForTimeout(1000);
                    
                    const stillVisible2 = await slidePanel.isVisible();
                    console.log('Panel still visible after cancel:', stillVisible2);
                    
                    if (stillVisible2) {
                        // Try escape key
                        console.log('Trying escape key...');
                        await page.keyboard.press('Escape');
                        await page.waitForTimeout(1000);
                        
                        const stillVisible3 = await slidePanel.isVisible();
                        console.log('Panel still visible after escape:', stillVisible3);
                    }
                }
            }
        }
        
        expect(true).toBe(true);
    });
});