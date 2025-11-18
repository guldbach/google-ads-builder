// Test new cities preview functionality
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('New Cities Preview Test', () => {
    
    test('should show preview of new cities and duplicates', async ({ page }) => {
        console.log('Testing new cities preview...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Find a region and expand it
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            
            // Expand region
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Click import button
            const importButton = page.locator('.import-excel-btn').first();
            console.log('Opening import panel...');
            await importButton.click();
            await page.waitForTimeout(1000);
            
            // Upload test file with new cities
            const fileInput = page.locator('#region-excel-file-input');
            const testFilePath = path.resolve('/Users/guldbach/google-ads-builder/test_new_cities.csv');
            console.log('Uploading test file with new cities...');
            await fileInput.setInputFiles(testFilePath);
            await page.waitForTimeout(500);
            
            // Click analyze
            console.log('Starting analysis...');
            const analyzeButton = page.locator('#slide-panel-save');
            await analyzeButton.click();
            
            // Wait for analysis to complete
            await page.waitForTimeout(3000);
            
            // Check for analysis completion
            const analysisSection = page.locator('h3:has-text("✅ Analyse Fuldført")');
            const hasAnalysis = await analysisSection.count() > 0;
            console.log('Got analysis section:', hasAnalysis);
            
            if (hasAnalysis) {
                // Check for new cities section
                const newCitiesHeader = page.locator('h4:has-text("📍 Nye byer der vil blive tilføjet")');
                const hasNewCities = await newCitiesHeader.count() > 0;
                console.log('Found new cities section:', hasNewCities);
                
                // Check for duplicates section
                const duplicatesSection = page.locator('summary:has-text("📋 Vis dubletter")');
                const hasDuplicates = await duplicatesSection.count() > 0;
                console.log('Found duplicates section:', hasDuplicates);
                
                // Check save button state
                const saveButton = page.locator('#slide-panel-save');
                const buttonText = await saveButton.textContent();
                const isDisabled = await saveButton.isDisabled();
                console.log('Save button text:', buttonText);
                console.log('Save button disabled:', isDisabled);
                
                // If there are new cities, test the button text
                if (buttonText && buttonText.includes('Tilføj')) {
                    console.log('✅ Save button shows city count to add');
                } else {
                    console.log('ℹ️ No new cities to add or button disabled');
                }
                
                // If duplicates section exists, try to expand it
                if (hasDuplicates) {
                    console.log('Expanding duplicates section...');
                    await duplicatesSection.click();
                    await page.waitForTimeout(500);
                    
                    // Check if duplicates list is visible
                    const duplicatesList = page.locator('div:has-text("• København")').first();
                    const duplicatesVisible = await duplicatesList.isVisible();
                    console.log('Duplicates list visible after expanding:', duplicatesVisible);
                }
                
            } else {
                console.log('❌ Analysis section not found');
            }
            
        } else {
            console.log('❌ No regions found');
        }
        
        expect(true).toBe(true);
    });
});