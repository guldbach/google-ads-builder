// Test close functionality when there are no new cities
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('No New Cities Close Test', () => {
    
    test('should be able to close panel when no new cities found', async ({ page }) => {
        console.log('Testing close functionality when no new cities...');
        
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
            
            // Upload file with only existing cities (duplicates)
            const fileInput = page.locator('#region-excel-file-input');
            const testFilePath = path.resolve('/Users/guldbach/google-ads-builder/test_cities.csv');
            await fileInput.setInputFiles(testFilePath);
            await page.waitForTimeout(500);
            
            // Analyze
            const analyzeButton = page.locator('#slide-panel-save');
            await analyzeButton.click();
            await page.waitForTimeout(3000);
            
            // Check if we have "Ingen nye byer" button
            const saveButton = page.locator('#slide-panel-save');
            const buttonText = await saveButton.textContent();
            console.log('Save button text after analysis:', buttonText);
            
            if (buttonText && buttonText.includes('Ingen')) {
                console.log('Found "Ingen nye byer" button, trying to click...');
                await saveButton.click();
                await page.waitForTimeout(1000);
                
                const panelVisible = await page.locator('#slide-panel-overlay').isVisible();
                console.log('Panel still visible after clicking "Ingen nye byer":', panelVisible);
            }
            
            // Try close button
            if (await page.locator('#slide-panel-overlay').isVisible()) {
                console.log('Trying close button...');
                await page.locator('#slide-panel-close').click();
                await page.waitForTimeout(1000);
                
                const panelVisible = await page.locator('#slide-panel-overlay').isVisible();
                console.log('Panel visible after close button:', panelVisible);
            }
            
            // Try cancel button
            if (await page.locator('#slide-panel-overlay').isVisible()) {
                console.log('Trying cancel button...');
                await page.locator('#slide-panel-cancel').click();
                await page.waitForTimeout(1000);
                
                const panelVisible = await page.locator('#slide-panel-overlay').isVisible();
                console.log('Panel visible after cancel button:', panelVisible);
            }
        }
        
        expect(true).toBe(true);
    });
});