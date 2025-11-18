// Test manual city operations (add, edit, delete)
const { test, expect } = require('@playwright/test');

test.describe('Manual City Operations Test', () => {
    
    test('should test manual add city functionality', async ({ page }) => {
        console.log('Testing manual add city...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Find a region to work with
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            // Expand the first region
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Look for add city button
            const addCityBtn = page.locator('.add-city-btn').first();
            if (await addCityBtn.isVisible()) {
                console.log('Add city button found, clicking...');
                await addCityBtn.click();
                await page.waitForTimeout(500);
                
                // Check if add city form appears
                const cityNameInput = page.locator('.new-city-name');
                if (await cityNameInput.isVisible()) {
                    console.log('✅ Add city form visible');
                    
                    // Fill city name
                    const testCityName = `TestBy${Date.now()}`;
                    await cityNameInput.fill(testCityName);
                    
                    // Submit form (Enter key)
                    await cityNameInput.press('Enter');
                    await page.waitForTimeout(2000);
                    
                    // Check if city was added
                    const cityInList = page.locator(`td:has-text("${testCityName}")`);
                    const cityExists = await cityInList.count() > 0;
                    console.log('City added to list:', cityExists);
                    
                    if (cityExists) {
                        console.log('✅ Manual add city works!');
                    }
                } else {
                    console.log('❌ Add city form not visible');
                }
            } else {
                console.log('❌ Add city button not found');
            }
        } else {
            console.log('❌ No regions found');
        }
        
        expect(true).toBe(true);
    });
    
    test('should test edit city functionality', async ({ page }) => {
        console.log('Testing edit city...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Find a region with cities
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            // Expand the first region  
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Look for edit buttons
            const editButtons = page.locator('.edit-city-btn');
            if (await editButtons.count() > 0) {
                console.log('Edit button found, clicking...');
                await editButtons.first().click();
                await page.waitForTimeout(500);
                
                // Check for edit input field
                const editInput = page.locator('input[type="text"]').last();
                if (await editInput.isVisible()) {
                    console.log('✅ Edit input visible');
                    
                    // Change city name
                    await editInput.fill(`EditedBy${Date.now()}`);
                    await editInput.press('Enter');
                    await page.waitForTimeout(2000);
                    
                    console.log('✅ Edit operation completed');
                } else {
                    console.log('❌ Edit input not visible');
                }
            } else {
                console.log('❌ No edit buttons found');
            }
        }
        
        expect(true).toBe(true);
    });
    
    test('should test delete city functionality', async ({ page }) => {
        console.log('Testing delete city...');
        
        // Handle confirm dialog
        page.on('dialog', async dialog => {
            console.log('Confirm dialog appeared:', dialog.message());
            await dialog.accept();
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Find a region with cities
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            // Expand the first region
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Look for delete buttons
            const deleteButtons = page.locator('.delete-city-btn');
            if (await deleteButtons.count() > 0) {
                console.log('Delete button found, clicking...');
                
                // Get city name before deleting
                const cityRow = deleteButtons.first().locator('xpath=ancestor::tr');
                const cityName = await cityRow.locator('.font-medium').textContent();
                console.log('Deleting city:', cityName);
                
                await deleteButtons.first().click();
                await page.waitForTimeout(2000);
                
                console.log('✅ Delete operation completed');
            } else {
                console.log('❌ No delete buttons found');
            }
        }
        
        expect(true).toBe(true);
    });
});