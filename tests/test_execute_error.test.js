// Test to see exact execute error
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Execute Error Details', () => {
    
    test('should show exact execute error message', async ({ page }) => {
        console.log('Testing exact execute error...');
        
        // Capture exact response body
        page.on('response', async response => {
            if (response.url().includes('execute-excel-import-cities')) {
                try {
                    const body = await response.text();
                    console.log('=== EXECUTE RESPONSE ===');
                    console.log('Status:', response.status());
                    console.log('Body:', body);
                    console.log('========================');
                } catch (e) {
                    console.log('Could not read execute response body');
                }
            }
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Go through import flow
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            const importButton = page.locator('.import-excel-btn').first();
            await importButton.click();
            await page.waitForTimeout(1000);
            
            // Upload and analyze
            const fileInput = page.locator('#region-excel-file-input');
            const testFilePath = path.resolve('/Users/guldbach/google-ads-builder/test_cities.csv');
            await fileInput.setInputFiles(testFilePath);
            await page.waitForTimeout(500);
            
            const analyzeButton = page.locator('#slide-panel-save');
            await analyzeButton.click();
            await page.waitForTimeout(3000);
            
            // Execute
            const executeButton = page.locator('#slide-panel-save');
            const buttonText = await executeButton.textContent();
            
            if (buttonText.includes('Tilføj')) {
                console.log('Clicking execute button...');
                await executeButton.click();
                await page.waitForTimeout(3000);
            }
        }
        
        expect(true).toBe(true);
    });
});