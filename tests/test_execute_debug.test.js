// Test execute import with detailed logging
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Execute Import Debug', () => {
    
    test('should debug execute import functionality', async ({ page }) => {
        console.log('Debugging execute import...');
        
        // Capture all console messages
        const consoleLogs = [];
        page.on('console', msg => {
            consoleLogs.push(`${msg.type()}: ${msg.text()}`);
        });
        
        // Capture JavaScript errors
        const jsErrors = [];
        page.on('pageerror', error => {
            jsErrors.push(error.message);
        });
        
        // Track network requests
        const requests = [];
        const responses = [];
        
        page.on('request', request => {
            if (request.url().includes('ajax/')) {
                requests.push({
                    url: request.url(),
                    method: request.method()
                });
            }
        });
        
        page.on('response', async response => {
            if (response.url().includes('ajax/')) {
                try {
                    const body = await response.text();
                    responses.push({
                        url: response.url(),
                        status: response.status(),
                        body: body
                    });
                } catch (e) {
                    responses.push({
                        url: response.url(),
                        status: response.status(),
                        error: 'Could not read body'
                    });
                }
            }
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Go through import flow
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            
            // Expand region and import
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            const importButton = page.locator('.import-excel-btn').first();
            await importButton.click();
            await page.waitForTimeout(1000);
            
            // Upload file and analyze
            const fileInput = page.locator('#region-excel-file-input');
            const testFilePath = path.resolve('/Users/guldbach/google-ads-builder/test_cities.csv');
            await fileInput.setInputFiles(testFilePath);
            await page.waitForTimeout(500);
            
            const analyzeButton = page.locator('#slide-panel-save');
            await analyzeButton.click();
            await page.waitForTimeout(3000);
            
            // Now try to execute
            console.log('Testing execute functionality...');
            
            // Check if execute button exists and is clickable
            const executeButton = page.locator('#slide-panel-save');
            const buttonVisible = await executeButton.isVisible();
            const buttonEnabled = await executeButton.isEnabled();
            const buttonText = await executeButton.textContent();
            
            console.log('Execute button visible:', buttonVisible);
            console.log('Execute button enabled:', buttonEnabled);
            console.log('Execute button text:', buttonText);
            
            if (buttonVisible && buttonEnabled && buttonText.includes('Tilføj')) {
                console.log('Clicking execute button...');
                
                // Add a more specific event listener before clicking
                await page.evaluate(() => {
                    console.log('About to click execute button');
                    console.log('executeRegionImport function exists:', typeof window.executeRegionImport);
                    
                    // Test if we can call the function manually
                    const fileInput = document.getElementById('region-excel-file-input');
                    console.log('File input has file:', fileInput && fileInput.files.length > 0);
                });
                
                await executeButton.click();
                
                // Wait longer for execute to complete
                console.log('Waiting for execute to complete...');
                await page.waitForTimeout(5000);
                
                // Check what happened
                const panelVisible = await page.locator('#slide-panel-overlay').isVisible();
                console.log('Panel still visible after execute:', panelVisible);
                
            } else {
                console.log('Execute button not ready for click');
            }
            
        }
        
        console.log('\n=== CONSOLE LOGS ===');
        consoleLogs.forEach(log => console.log(log));
        
        console.log('\n=== JAVASCRIPT ERRORS ===');
        jsErrors.forEach(error => console.log('ERROR:', error));
        
        console.log('\n=== REQUESTS ===');
        requests.forEach((req, i) => {
            console.log(`${i + 1}. ${req.method} ${req.url}`);
        });
        
        console.log('\n=== RESPONSES ===');
        responses.forEach((res, i) => {
            console.log(`${i + 1}. ${res.status} ${res.url}`);
            if (res.body && res.body.includes('success')) {
                console.log(`   Success: ${res.body.includes('"success": true')}`);
            }
            if (res.error) {
                console.log(`   Error: ${res.error}`);
            }
        });
        
        expect(true).toBe(true);
    });
});