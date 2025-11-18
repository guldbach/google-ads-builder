// Debug JavaScript loading issues
const { test, expect } = require('@playwright/test');

test.describe('JavaScript Debug', () => {
    
    test('should debug JavaScript loading and function availability', async ({ page }) => {
        console.log('Debugging JavaScript loading...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Check if jQuery is loaded
        const jqueryStatus = await page.evaluate(() => {
            return {
                jqueryExists: typeof window.$ !== 'undefined',
                jqueryVersion: window.$ ? window.$.fn.jquery : 'not loaded'
            };
        });
        console.log('jQuery Status:', jqueryStatus);
        
        // Check function existence
        const functionStatus = await page.evaluate(() => {
            return {
                toggleRegionExpansion: typeof window.toggleRegionExpansion,
                initializeToggleFunction: typeof window.initializeToggleFunction,
                toggleFunction: typeof toggleRegionExpansion
            };
        });
        console.log('Function Status:', functionStatus);
        
        // Try to manually call initializeToggleFunction
        try {
            await page.evaluate(() => {
                if (typeof window.initializeToggleFunction === 'function') {
                    console.log('Calling initializeToggleFunction manually...');
                    window.initializeToggleFunction();
                    console.log('toggleRegionExpansion after manual init:', typeof window.toggleRegionExpansion);
                } else {
                    console.log('initializeToggleFunction not found');
                }
            });
        } catch (e) {
            console.log('Error calling initializeToggleFunction:', e.message);
        }
        
        // Check function status after manual init
        const functionStatusAfter = await page.evaluate(() => {
            return {
                toggleRegionExpansion: typeof window.toggleRegionExpansion
            };
        });
        console.log('Function Status After Manual Init:', functionStatusAfter);
        
        // Check for any JavaScript errors
        const jsErrors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                jsErrors.push(msg.text());
            }
        });
        
        // Wait a bit for any errors to appear
        await page.waitForTimeout(2000);
        
        if (jsErrors.length > 0) {
            console.log('JavaScript Errors:', jsErrors);
        } else {
            console.log('No JavaScript errors detected');
        }
        
        // Check if region headers have onclick attributes
        const headerInfo = await page.evaluate(() => {
            const headers = Array.from(document.querySelectorAll('.region-header'));
            return headers.map(header => ({
                onclick: header.getAttribute('onclick'),
                hasClickHandler: !!header.onclick
            }));
        });
        console.log('Region Header Info:', headerInfo);
    });
});