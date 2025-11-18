// Test direct call to edit function to debug
const { test, expect } = require('@playwright/test');

test.describe('Direct Edit Call Test', () => {
    
    test('should test direct call to edit function', async ({ page }) => {
        console.log('Testing direct edit function call...');
        
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
            
            // Try direct function call
            const result = await page.evaluate(() => {
                try {
                    console.log('Testing direct function call...');
                    console.log('editCity available:', typeof editCity);
                    console.log('enableCityEditMode available:', typeof enableCityEditMode);
                    
                    // Find first edit button
                    const editButton = $('.edit-city-btn').first();
                    if (editButton.length > 0) {
                        console.log('Found edit button:', editButton.data('city-id'));
                        
                        // Create mock event and call function directly
                        const mockEvent = {
                            target: editButton[0]
                        };
                        
                        console.log('Calling editCity function directly...');
                        editCity(mockEvent);
                        
                        // Check if edit mode was activated
                        const row = editButton.closest('tr');
                        const hasEditMode = row.hasClass('edit-mode');
                        const hasInput = row.find('.edit-city-name-input').length > 0;
                        
                        console.log('Row has edit-mode class:', hasEditMode);
                        console.log('Row has edit input:', hasInput);
                        console.log('Row HTML:', row.html());
                        
                        return {
                            success: true,
                            hasEditMode,
                            hasInput,
                            cityId: editButton.data('city-id')
                        };
                    }
                    
                    return { success: false, message: 'No edit button found' };
                } catch (error) {
                    console.log('Error in direct call:', error.message);
                    return { success: false, error: error.message };
                }
            });
            
            console.log('Direct call result:', result);
            
            if (result.success) {
                if (result.hasEditMode && result.hasInput) {
                    console.log('🎉 SUCCESS: Edit mode activated!');
                } else {
                    console.log('❌ Edit mode not fully activated');
                    console.log('Has edit mode class:', result.hasEditMode);
                    console.log('Has input field:', result.hasInput);
                }
            } else {
                console.log('❌ Direct call failed:', result.message || result.error);
            }
        }
        
        expect(true).toBe(true);
    });
});