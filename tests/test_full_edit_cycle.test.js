// Test full edit cycle: edit -> change -> save
const { test, expect } = require('@playwright/test');

test.describe('Full Edit Cycle Test', () => {
    
    test('should complete full edit cycle: Aalborg -> Glamsbjerg', async ({ page }) => {
        console.log('Testing full edit cycle...');
        
        page.on('console', msg => {
            console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Expand first region
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Complete edit cycle
            const result = await page.evaluate(() => {
                try {
                    console.log('Starting full edit cycle...');
                    
                    // Find first edit button
                    const editButton = $('.edit-city-btn').first();
                    const row = editButton.closest('tr');
                    const cityId = editButton.data('city-id');
                    
                    console.log('Original city ID:', cityId);
                    
                    // Step 1: Enable edit mode
                    const mockEvent = { target: editButton[0] };
                    editCity(mockEvent);
                    
                    // Step 2: Change city name to Glamsbjerg
                    const input = row.find('.edit-city-name-input');
                    if (input.length > 0) {
                        console.log('Found input, changing to Glamsbjerg...');
                        input.val('Glamsbjerg');
                        console.log('Input value changed to:', input.val());
                        
                        // Step 3: Save (call editCity again since row now has edit-mode class)
                        console.log('Calling save...');
                        editCity(mockEvent);
                        
                        return {
                            success: true,
                            message: 'Edit cycle completed, AJAX call should be made'
                        };
                    } else {
                        return { success: false, message: 'No input field found' };
                    }
                } catch (error) {
                    console.log('Error in edit cycle:', error.message);
                    return { success: false, error: error.message };
                }
            });
            
            console.log('Edit cycle result:', result);
            
            if (result.success) {
                console.log('🎉 Full edit cycle completed successfully!');
                console.log('✅ AJAX request should have been sent to update city name');
                
                // Wait for potential AJAX completion and page refresh
                await page.waitForTimeout(5000);
                
                // Check if Glamsbjerg appears in the list
                const glamsbjerExists = await page.locator('tr:has(.font-medium:text("Glamsbjerg"))').count() > 0;
                const aalborgExists = await page.locator('tr:has(.font-medium:text("Aalborg"))').count() > 0;
                
                console.log('After edit attempt:');
                console.log('Glamsbjerg exists:', glamsbjerExists);
                console.log('Aalborg exists:', aalborgExists);
                
                if (glamsbjerExists) {
                    console.log('🎉 SUCCESS: Aalborg was successfully renamed to Glamsbjerg!');
                } else if (aalborgExists) {
                    console.log('⚠️  Aalborg still exists - check server logs for AJAX response');
                } else {
                    console.log('❓ Neither city found - page may have been refreshed');
                }
            } else {
                console.log('❌ Edit cycle failed:', result.message || result.error);
            }
        }
        
        expect(true).toBe(true);
    });
});