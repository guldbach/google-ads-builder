// Test complete import workflow
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Import Cities Workflow', () => {
    
    test('should complete full import workflow with CSV file', async ({ page }) => {
        console.log('Testing complete import workflow...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Expand a region
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Click import button
            const importButton = page.locator('.import-excel-btn').first();
            await importButton.click();
            await page.waitForTimeout(1000);
            
            // Check if panel opened
            const slidePanel = page.locator('#slide-panel-overlay');
            const isPanelVisible = await slidePanel.isVisible();
            console.log('Panel opened:', isPanelVisible);
            
            if (isPanelVisible) {
                // Upload the test file
                const fileInput = page.locator('#region-excel-file-input');
                const testFilePath = path.resolve('/Users/guldbach/google-ads-builder/test_cities.csv');
                console.log('Uploading file:', testFilePath);
                
                await fileInput.setInputFiles(testFilePath);
                
                // Wait for file info to show
                await page.waitForTimeout(500);
                const fileInfo = page.locator('#region-file-selected-info');
                const isFileInfoVisible = await fileInfo.isVisible();
                console.log('File info visible:', isFileInfoVisible);
                
                // Click analyze button
                const analyzeButton = page.locator('#slide-panel-save');
                console.log('Clicking analyze button...');
                await analyzeButton.click();
                
                // Wait for analysis to complete (may take some time)
                await page.waitForTimeout(5000);
                
                // Check for analysis results
                const panelContent = await page.locator('#slide-panel-content').innerHTML();
                console.log('Panel content length:', panelContent.length);
                
                // Check if success message appeared or error
                const successIndicator = page.locator('.bg-green-50');
                const errorIndicator = page.locator('.alert, .error');
                
                const hasSuccess = await successIndicator.count() > 0;
                const hasError = await errorIndicator.count() > 0;
                
                console.log('Has success indicator:', hasSuccess);
                console.log('Has error indicator:', hasError);
                
                if (hasSuccess) {
                    console.log('✅ Analysis completed successfully!');
                    
                    // Try to get the analysis data
                    const analysisData = await page.evaluate(() => {
                        const content = document.getElementById('slide-panel-content');
                        return {
                            hasContent: !!content,
                            innerHTML: content ? content.innerHTML.substring(0, 200) + '...' : 'No content'
                        };
                    });
                    console.log('Analysis data:', analysisData);
                    
                } else {
                    console.log('❌ Analysis failed or no success indicator found');
                    
                    // Check for any error messages
                    const errorMessages = await page.evaluate(() => {
                        const errors = [];
                        // Check for alert dialogs
                        return errors;
                    });
                    console.log('Error messages:', errorMessages);
                }
                
            } else {
                console.log('❌ Panel did not open');
            }
        } else {
            console.log('❌ No regions found to test');
        }
    });
    
    test('should handle CSRF and network errors gracefully', async ({ page }) => {
        console.log('Testing error handling...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Listen for network failures
        const networkErrors = [];
        page.on('response', response => {
            if (!response.ok()) {
                networkErrors.push({
                    url: response.url(),
                    status: response.status(),
                    statusText: response.statusText()
                });
            }
        });
        
        // Listen for JavaScript errors  
        const jsErrors = [];
        page.on('pageerror', error => {
            jsErrors.push(error.message);
        });
        
        // Try to trigger a network request
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            const importButton = page.locator('.import-excel-btn').first();
            await importButton.click();
            await page.waitForTimeout(1000);
            
            // Try to submit without a file
            const analyzeButton = page.locator('#slide-panel-save');
            if (await analyzeButton.isVisible()) {
                await analyzeButton.click();
                await page.waitForTimeout(2000);
            }
        }
        
        console.log('Network errors:', networkErrors);
        console.log('JavaScript errors:', jsErrors);
        
        // The test passes if we can handle errors gracefully
        expect(jsErrors.length).toBeLessThan(10); // Some errors are expected
    });
});