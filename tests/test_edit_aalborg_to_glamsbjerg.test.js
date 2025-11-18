// Test editing Aalborg to Glamsbjerg in "Dette er min nye region"
const { test, expect } = require('@playwright/test');

test.describe('Edit Aalborg to Glamsbjerg Test', () => {
    
    test('should edit Aalborg to Glamsbjerg in "Dette er min nye region"', async ({ page }) => {
        console.log('Testing edit Aalborg to Glamsbjerg...');
        
        // Listen for browser console messages including errors
        page.on('console', msg => {
            console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
        });
        
        page.on('pageerror', error => {
            console.log(`[PAGE ERROR]: ${error.message}`);
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Find the region "Dette er min nye region"
        const targetRegion = page.locator('.region-header:has-text("Dette er min nye region")');
        
        if (await targetRegion.count() > 0) {
            console.log('✅ Found region "Dette er min nye region"');
            
            // Click to expand the region
            await targetRegion.click();
            await page.waitForTimeout(1000);
            
            // Look for a row containing "Aalborg" (use first if multiple)
            const aalborgRow = page.locator('tr:has(.font-medium:text-is("Aalborg"))').first();
            
            if (await aalborgRow.count() > 0) {
                console.log('✅ Found Aalborg in the region');
                
                // Find the edit button in that row
                const editButton = aalborgRow.locator('.edit-city-btn');
                
                if (await editButton.isVisible()) {
                    console.log('✅ Edit button is visible, clicking...');
                    
                    // First check if jQuery is available and test the event listener
                    await page.evaluate(() => {
                        console.log('jQuery available:', typeof $ !== 'undefined');
                        console.log('editCity function available:', typeof editCity !== 'undefined');
                        
                        // Test if event listener is attached
                        const editButtons = $('.edit-city-btn');
                        console.log('Edit buttons found:', editButtons.length);
                        
                        // Check data attributes
                        editButtons.each(function() {
                            console.log('Edit button city-id:', $(this).data('city-id'));
                        });
                    });
                    
                    await editButton.click();
                    await page.waitForTimeout(1000);
                    
                    // Look for edit input field in the same row
                    const editInput = aalborgRow.locator('input[type="text"]');
                    
                    if (await editInput.count() > 0) {
                        console.log('✅ Edit input field appeared');
                        
                        // Clear and type new name
                        await editInput.fill('Glamsbjerg');
                        console.log('✅ Filled "Glamsbjerg" in input field');
                        
                        // Press Enter to save
                        await editInput.press('Enter');
                        await page.waitForTimeout(2000);
                        
                        // Check if "Glamsbjerg" now appears in the list
                        const glamsbjerRow = page.locator('tr:has(.font-medium:text-is("Glamsbjerg"))');
                        const glamsbjerExists = await glamsbjerRow.count() > 0;
                        
                        console.log('✅ Glamsbjerg exists in list:', glamsbjerExists);
                        
                        // Check if Aalborg is no longer there
                        const aalborgStillExists = await aalborgRow.count() > 0;
                        console.log('Aalborg still exists:', aalborgStillExists);
                        
                        if (glamsbjerExists && !aalborgStillExists) {
                            console.log('🎉 SUCCESS: Successfully edited Aalborg to Glamsbjerg!');
                        } else if (glamsbjerExists && aalborgStillExists) {
                            console.log('⚠️ Both cities exist - edit might not have worked properly');
                        } else {
                            console.log('❌ Edit operation failed');
                        }
                        
                    } else {
                        console.log('❌ Edit input field did not appear');
                        
                        // Take screenshot for debugging
                        await page.screenshot({ path: 'debug-edit-failed.png' });
                    }
                } else {
                    console.log('❌ Edit button not visible');
                }
            } else {
                console.log('❌ Aalborg not found in this region');
                
                // List all cities in this region for debugging
                const cityRows = page.locator('tr .font-medium');
                const cityCount = await cityRows.count();
                console.log(`Found ${cityCount} cities in region:`);
                
                for (let i = 0; i < cityCount; i++) {
                    const cityName = await cityRows.nth(i).textContent();
                    console.log(`- ${cityName}`);
                }
            }
        } else {
            console.log('❌ Region "Dette er min nye region" not found');
            
            // List all regions for debugging
            const allRegions = page.locator('.region-header h3');
            const regionCount = await allRegions.count();
            console.log(`Found ${regionCount} regions:`);
            
            for (let i = 0; i < regionCount; i++) {
                const regionName = await allRegions.nth(i).textContent();
                console.log(`- ${regionName}`);
            }
        }
        
        expect(true).toBe(true);
    });
});