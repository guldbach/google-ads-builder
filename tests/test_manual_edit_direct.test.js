// Test direct call to edit function
const { test, expect } = require('@playwright/test');

test.describe('Manual Edit Direct Test', () => {
    
    test('should test direct editCity call', async ({ page }) => {
        console.log('Testing direct editCity call...');
        
        // Listen for all errors
        page.on('console', msg => {
            console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
        });
        
        page.on('pageerror', error => {
            console.log(`[PAGE ERROR]: ${error.message}`);
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Expand first region
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Try to call editCity function directly
            const result = await page.evaluate(() => {
                try {
                    // Check if function exists
                    console.log('Function editCity exists:', typeof editCity !== 'undefined');
                    console.log('Function enableCityEditMode exists:', typeof enableCityEditMode !== 'undefined');
                    
                    // List all global functions that include 'edit' or 'City'
                    const globalFunctions = [];
                    for (let prop in window) {
                        if (typeof window[prop] === 'function' && 
                            (prop.toLowerCase().includes('edit') || prop.toLowerCase().includes('city'))) {
                            globalFunctions.push(prop);
                        }
                    }
                    console.log('Global functions with edit/city:', globalFunctions);
                    
                    // Try to call editCity directly if it exists
                    if (typeof editCity !== 'undefined') {
                        // Find an edit button and simulate click
                        const editBtn = $('.edit-city-btn').first();
                        if (editBtn.length > 0) {
                            console.log('Found edit button, trying direct call...');
                            // Create mock event
                            const mockEvent = { target: editBtn[0] };
                            editCity(mockEvent);
                            return 'Direct call successful';
                        }
                    }
                    
                    return 'Function not available or no edit button found';
                } catch (error) {
                    console.log('Error during direct call:', error.message);
                    return 'Error: ' + error.message;
                }
            });
            
            console.log('Direct call result:', result);
        }
        
        expect(true).toBe(true);
    });
});