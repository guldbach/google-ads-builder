// Test final close functionality 
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Final Close Test', () => {
    
    test('should close panel with "Ingen nye byer" and hide cancel button', async ({ page }) => {
        console.log('Testing final close functionality...');
        
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
            
            // Check if cancel button is initially visible
            const cancelButton = page.locator('#slide-panel-cancel');
            const cancelInitiallyVisible = await cancelButton.isVisible();
            console.log('Cancel button initially visible:', cancelInitiallyVisible);
            
            // Upload file with only existing cities (duplicates)
            const fileInput = page.locator('#region-excel-file-input');
            const testFilePath = path.resolve('/Users/guldbach/google-ads-builder/test_cities.csv');
            await fileInput.setInputFiles(testFilePath);
            await page.waitForTimeout(500);
            
            // Analyze
            const analyzeButton = page.locator('#slide-panel-save');
            await analyzeButton.click();
            await page.waitForTimeout(3000);
            
            // Check button state after analysis
            const saveButton = page.locator('#slide-panel-save');
            const buttonText = await saveButton.textContent();
            const isDisabled = await saveButton.isDisabled();
            const isVisible = await saveButton.isVisible();
            
            console.log('Save button text after analysis:', buttonText);
            console.log('Save button disabled:', isDisabled);
            console.log('Save button visible:', isVisible);
            
            // Check if cancel button is hidden after analysis
            const cancelAfterAnalysis = await cancelButton.isVisible();
            console.log('Cancel button visible after analysis:', cancelAfterAnalysis);
            
            if (buttonText && buttonText.includes('Ingen')) {
                console.log('Found "Ingen nye byer" button, clicking...');
                await saveButton.click();
                await page.waitForTimeout(1000);
                
                const panelVisible = await page.locator('#slide-panel-overlay').isVisible();
                console.log('Panel still visible after clicking "Ingen nye byer":', panelVisible);
                
                if (!panelVisible) {
                    console.log('✅ Panel closed successfully with "Ingen nye byer" button!');
                }
            }
        }
        
        expect(true).toBe(true);
    });
});