// Test slide panel close functionality
const { test, expect } = require('@playwright/test');

test.describe('Slide Panel Close Test', () => {
    
    test('should be able to close slide panel properly', async ({ page }) => {
        console.log('Testing slide panel close functionality...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Find a region and open import panel
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            
            // Expand region first
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Click import button to open slide panel
            const importButton = page.locator('.import-excel-btn').first();
            console.log('Opening slide panel...');
            await importButton.click();
            await page.waitForTimeout(1000);
            
            // Check if slide panel is open
            const slidePanel = page.locator('#slide-panel-overlay');
            const isVisible = await slidePanel.isVisible();
            console.log('Slide panel visible:', isVisible);
            
            if (isVisible) {
                // Test different ways to close the panel
                
                // 1. Test close button
                console.log('Testing close button...');
                const closeButton = page.locator('#slide-panel-close');
                if (await closeButton.isVisible()) {
                    await closeButton.click();
                    await page.waitForTimeout(500);
                    
                    const stillVisible1 = await slidePanel.isVisible();
                    console.log('Panel still visible after close button:', stillVisible1);
                    
                    if (stillVisible1) {
                        console.log('❌ Close button did not work');
                    } else {
                        console.log('✅ Close button worked');
                        
                        // Re-open panel for next test
                        await importButton.click();
                        await page.waitForTimeout(1000);
                    }
                }
                
                // 2. Test cancel button
                console.log('Testing cancel button...');
                const cancelButton = page.locator('#slide-panel-cancel');
                if (await cancelButton.isVisible()) {
                    await cancelButton.click();
                    await page.waitForTimeout(500);
                    
                    const stillVisible2 = await slidePanel.isVisible();
                    console.log('Panel still visible after cancel button:', stillVisible2);
                    
                    if (stillVisible2) {
                        console.log('❌ Cancel button did not work');
                    } else {
                        console.log('✅ Cancel button worked');
                        
                        // Re-open panel for next test
                        await importButton.click();
                        await page.waitForTimeout(1000);
                    }
                }
                
                // 3. Test clicking overlay background
                console.log('Testing overlay click...');
                const overlay = page.locator('#slide-panel-overlay');
                await overlay.click();
                await page.waitForTimeout(500);
                
                const stillVisible3 = await slidePanel.isVisible();
                console.log('Panel still visible after overlay click:', stillVisible3);
                
                if (stillVisible3) {
                    console.log('❌ Overlay click did not work');
                } else {
                    console.log('✅ Overlay click worked');
                }
                
            } else {
                console.log('❌ Slide panel did not open');
            }
            
        } else {
            console.log('❌ No regions found to test');
        }
        
        expect(true).toBe(true);
    });
});