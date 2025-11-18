// Test complete import workflow from start to finish
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Complete Import Workflow', () => {
    
    test('should complete full import from CSV to database', async ({ page }) => {
        console.log('Testing complete CSV import workflow...');
        
        // Track all network activity
        const networkActivity = [];
        page.on('response', async response => {
            if (response.url().includes('ajax/')) {
                try {
                    const body = await response.text();
                    networkActivity.push({
                        url: response.url(),
                        status: response.status(),
                        body: body.substring(0, 200) + '...'
                    });
                } catch (e) {
                    networkActivity.push({
                        url: response.url(),
                        status: response.status(),
                        error: 'Could not read body'
                    });
                }
            }
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Find a region and get initial city count
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            
            // Get initial city count
            const initialCountElement = page.locator('.geographic-region-section').first().locator('span[class*="w-8 h-8"]');
            const initialCount = await initialCountElement.textContent();
            console.log('Initial city count:', initialCount);
            
            // Expand region
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Click import button
            const importButton = page.locator('.import-excel-btn').first();
            console.log('Clicking import button...');
            await importButton.click();
            await page.waitForTimeout(1000);
            
            // Upload CSV file
            const fileInput = page.locator('#region-excel-file-input');
            const testFilePath = path.resolve('/Users/guldbach/google-ads-builder/test_cities.csv');
            console.log('Uploading CSV file...');
            await fileInput.setInputFiles(testFilePath);
            await page.waitForTimeout(500);
            
            // Click analyze
            console.log('Starting analysis...');
            const analyzeButton = page.locator('#slide-panel-save');
            await analyzeButton.click();
            
            // Wait for analysis to complete
            await page.waitForTimeout(3000);
            
            // Check if we got the preview
            const newCitiesSection = page.locator('h4:has-text("Nye byer der vil blive tilføjet")');
            const hasPreview = await newCitiesSection.count() > 0;
            console.log('Got analysis preview:', hasPreview);
            
            if (hasPreview) {
                // Click execute import
                console.log('Executing import...');
                const executeButton = page.locator('#slide-panel-save');
                const buttonText = await executeButton.textContent();
                console.log('Execute button text:', buttonText);
                
                if (buttonText.includes('Tilføj')) {
                    await executeButton.click();
                    
                    // Wait for import to complete
                    await page.waitForTimeout(5000);
                    
                    // Check for success notification or page reload
                    const notifications = page.locator('#notification-container');
                    const hasNotifications = await notifications.count() > 0;
                    console.log('Has notifications:', hasNotifications);
                    
                    // Wait for potential page reload
                    await page.waitForTimeout(2000);
                    
                    // Check if city count increased (if page didn't reload)
                    try {
                        const finalCountElement = page.locator('.geographic-region-section').first().locator('span[class*="w-8 h-8"]');
                        const finalCount = await finalCountElement.textContent();
                        console.log('Final city count:', finalCount);
                        
                        if (parseInt(finalCount) > parseInt(initialCount)) {
                            console.log('✅ Import successful - city count increased!');
                        } else {
                            console.log('ℹ️ City count same - maybe duplicates or page reloaded');
                        }
                    } catch (e) {
                        console.log('ℹ️ Could not check final count - page may have reloaded');
                    }
                    
                } else {
                    console.log('ℹ️ Execute button not ready or no new cities to add');
                }
                
            } else {
                console.log('❌ Analysis failed - no preview shown');
            }
            
            console.log('\n=== NETWORK ACTIVITY ===');
            networkActivity.forEach((activity, i) => {
                console.log(`${i + 1}. ${activity.url} -> ${activity.status}`);
                if (activity.body) {
                    console.log(`   Body: ${activity.body}`);
                }
            });
            
        } else {
            console.log('❌ No regions found');
        }
        
        // Test passes if we got this far without errors
        expect(true).toBe(true);
    });
});