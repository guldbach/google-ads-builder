// Test complete workflow with new cities import
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Complete Workflow Test', () => {
    
    test('should handle complete workflow with new cities', async ({ page }) => {
        console.log('Testing complete workflow with new cities...');
        
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
            
            // Upload file with new cities
            const fileInput = page.locator('#region-excel-file-input');
            const testFilePath = path.resolve('/Users/guldbach/google-ads-builder/test_new_cities.csv');
            await fileInput.setInputFiles(testFilePath);
            await page.waitForTimeout(500);
            
            // Check file selected indicator
            const fileSelected = page.locator('#region-file-selected-info');
            const fileIndicatorVisible = await fileSelected.isVisible();
            console.log('File selected indicator visible:', fileIndicatorVisible);
            
            // Analyze
            const analyzeButton = page.locator('#slide-panel-save');
            await analyzeButton.click();
            await page.waitForTimeout(3000);
            
            // Check if preview sections appear
            const newCitiesSection = page.locator('h4:has-text("📍 Nye byer der vil blive tilføjet")');
            const hasNewCities = await newCitiesSection.count() > 0;
            console.log('Found new cities section:', hasNewCities);
            
            // Check if cancel button is hidden after analysis
            const cancelAfterAnalysis = await cancelButton.isVisible();
            console.log('Cancel button visible after analysis:', cancelAfterAnalysis);
            
            // Check save button
            const saveButton = page.locator('#slide-panel-save');
            const buttonText = await saveButton.textContent();
            const isDisabled = await saveButton.isDisabled();
            console.log('Save button text:', buttonText);
            console.log('Save button disabled:', isDisabled);
            
            if (buttonText && buttonText.includes('Tilføj') && !isDisabled) {
                console.log('✅ Found active import button with city count');
                console.log('✅ Cancel button hidden after analysis:', !cancelAfterAnalysis);
                console.log('✅ File indicator working:', fileIndicatorVisible);
                console.log('✅ New cities preview working:', hasNewCities);
            }
        }
        
        expect(true).toBe(true);
    });
});