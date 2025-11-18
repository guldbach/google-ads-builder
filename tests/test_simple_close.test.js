// Simple test to check if openSlidePanel logs appear
const { test, expect } = require('@playwright/test');

test.describe('Simple Close Test', () => {
    
    test('should check if openSlidePanel function logs appear', async ({ page }) => {
        console.log('Testing if openSlidePanel logs appear...');
        
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
            
            console.log('About to click import button...');
            const importButton = page.locator('.import-excel-btn').first();
            await importButton.click();
            await page.waitForTimeout(2000); // Wait longer for logs
            
            // Check if panel opened
            const slidePanel = page.locator('#slide-panel-overlay');
            const isVisible = await slidePanel.isVisible();
            console.log('Panel visible:', isVisible);
            
            if (isVisible) {
                // Wait a bit more and then try manual close
                await page.waitForTimeout(1000);
                console.log('Trying to call closeSlidePanel manually...');
                
                await page.evaluate(() => {
                    console.log('About to call window.closeSlidePanel');
                    if (window.closeSlidePanel) {
                        window.closeSlidePanel();
                        console.log('closeSlidePanel called');
                    } else {
                        console.log('closeSlidePanel function not found');
                    }
                });
                
                await page.waitForTimeout(1000);
                
                const stillVisible = await slidePanel.isVisible();
                console.log('Panel still visible after manual close:', stillVisible);
            }
        }
        
        expect(true).toBe(true);
    });
});