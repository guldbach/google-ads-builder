// Test to see actual server response
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Detailed Import Response', () => {
    
    test('should show detailed server response during import', async ({ page }) => {
        console.log('Testing detailed server response...');
        
        // Capture all network requests
        const requests = [];
        const responses = [];
        
        page.on('request', request => {
            if (request.url().includes('analyze-excel-import-cities')) {
                requests.push({
                    url: request.url(),
                    method: request.method(),
                    headers: request.headers() || {},
                    postData: request.postData()
                });
            }
        });
        
        page.on('response', async response => {
            if (response.url().includes('analyze-excel-import-cities')) {
                try {
                    const responseText = await response.text();
                    responses.push({
                        url: response.url(),
                        status: response.status(),
                        statusText: response.statusText(),
                        headers: response.headers() || {},
                        body: responseText
                    });
                } catch (e) {
                    responses.push({
                        url: response.url(),
                        status: response.status(),
                        error: 'Could not read response body'
                    });
                }
            }
        });
        
        // Capture console logs
        const consoleLogs = [];
        page.on('console', msg => {
            consoleLogs.push(`${msg.type()}: ${msg.text()}`);
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Expand region and click import
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            const importButton = page.locator('.import-excel-btn').first();
            await importButton.click();
            await page.waitForTimeout(1000);
            
            // Upload file
            const fileInput = page.locator('#region-excel-file-input');
            const testFilePath = path.resolve('/Users/guldbach/google-ads-builder/test_cities.csv');
            await fileInput.setInputFiles(testFilePath);
            await page.waitForTimeout(500);
            
            // Click analyze and wait for response
            const analyzeButton = page.locator('#slide-panel-save');
            await analyzeButton.click();
            
            // Wait for network request to complete
            await page.waitForTimeout(3000);
            
            console.log('\n=== REQUESTS ===');
            requests.forEach((req, i) => {
                console.log(`Request ${i + 1}:`);
                console.log('URL:', req.url);
                console.log('Method:', req.method);
                console.log('Headers:', JSON.stringify(req.headers, null, 2));
            });
            
            console.log('\n=== RESPONSES ===');
            responses.forEach((res, i) => {
                console.log(`Response ${i + 1}:`);
                console.log('Status:', res.status, res.statusText);
                console.log('Headers:', JSON.stringify(res.headers, null, 2));
                console.log('Body:', res.body);
                console.log('---');
            });
            
            console.log('\n=== CONSOLE LOGS ===');
            consoleLogs.forEach(log => {
                console.log(log);
            });
            
            // Check final panel content
            const finalContent = await page.locator('#slide-panel-content').innerHTML();
            console.log('\n=== FINAL PANEL CONTENT (first 500 chars) ===');
            console.log(finalContent.substring(0, 500) + '...');
            
        } else {
            console.log('No regions found');
        }
    });
});