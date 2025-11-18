// Debug JavaScript syntax error
const { test, expect } = require('@playwright/test');

test.describe('Debug JS Error', () => {
    
    test('should find exact location of syntax error', async ({ page }) => {
        console.log('Debugging JavaScript syntax error...');
        
        // Capture all JavaScript errors with more detail
        const jsErrors = [];
        page.on('pageerror', error => {
            jsErrors.push({
                message: error.message,
                stack: error.stack,
                name: error.name
            });
            console.log(`[JS ERROR] ${error.name}: ${error.message}`);
            if (error.stack) {
                console.log(`[STACK] ${error.stack}`);
            }
        });
        
        page.on('console', msg => {
            if (msg.type() === 'error') {
                console.log(`[CONSOLE ERROR] ${msg.text()}`);
                console.log(`[CONSOLE LOCATION] ${msg.location()}`);
            }
        });
        
        // Navigate and wait for all errors
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForTimeout(3000);
        
        // Check for specific script parsing
        const scriptErrors = await page.evaluate(() => {
            const errors = [];
            const scripts = document.querySelectorAll('script');
            
            scripts.forEach((script, index) => {
                if (script.textContent && script.textContent.includes('<')) {
                    errors.push({
                        index,
                        hasAngleBrackets: true,
                        content: script.textContent.substring(0, 200) + '...'
                    });
                }
            });
            
            return errors;
        });
        
        console.log('Script errors found:', scriptErrors.length);
        scriptErrors.forEach(error => {
            console.log(`Script ${error.index}:`, error.content);
        });
        
        expect(true).toBe(true);
    });
});