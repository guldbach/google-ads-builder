// Quick test for the fixed "Tilføj By" functionality

const { test, expect } = require('@playwright/test');

test.describe('Add City Quick Test', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForSelector('#create-region-btn', { timeout: 10000 });
    });

    test('should test add city button click response', async ({ page }) => {
        console.log('Testing add city button after fix...');
        
        // Create a test region first
        await page.click('#create-region-btn');
        await page.waitForSelector('#slide-panel-overlay', { state: 'visible', timeout: 5000 });
        
        // Try to find any input field in the panel to fill basic info
        const nameInput = page.locator('input[type="text"]').first();
        await nameInput.fill(`Test Region ${Date.now()}`);
        
        await page.click('#slide-panel-save');
        await page.waitForSelector('#slide-panel-overlay', { state: 'hidden', timeout: 10000 });
        
        // Wait and look for any region to expand
        await page.waitForTimeout(2000);
        
        // Find any region header and click it to expand
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Look for the add city form
            const addCityButton = page.locator('.add-city-btn');
            console.log('Add city button count:', await addCityButton.count());
            
            if (await addCityButton.count() > 0) {
                // Try to fill the form
                const cityNameInput = page.locator('.new-city-name');
                const postalCodeInput = page.locator('.new-city-postal-code');
                
                if (await cityNameInput.count() > 0 && await postalCodeInput.count() > 0) {
                    await cityNameInput.fill('Test By');
                    await postalCodeInput.fill('1234');
                    
                    console.log('Form filled, clicking add button...');
                    
                    // Listen for console logs and network activity
                    const consoleMessages = [];
                    page.on('console', msg => {
                        consoleMessages.push(`${msg.type()}: ${msg.text()}`);
                    });
                    
                    const networkRequests = [];
                    page.on('request', request => {
                        if (request.url().includes('/ajax/')) {
                            networkRequests.push({
                                url: request.url(),
                                method: request.method(),
                                postData: request.postData()
                            });
                        }
                    });
                    
                    // Click the add button
                    await addCityButton.click();
                    await page.waitForTimeout(3000);
                    
                    console.log('Console messages after click:', consoleMessages);
                    console.log('Network requests after click:', networkRequests);
                    
                    // Check if any AJAX request was made
                    const ajaxRequest = networkRequests.find(req => req.url.includes('add-danish-city'));
                    if (ajaxRequest) {
                        console.log('✅ AJAX request was made:', ajaxRequest);
                    } else {
                        console.log('❌ No AJAX request found');
                    }
                    
                    // Check if form was cleared (indicates success)
                    const cityNameAfter = await cityNameInput.inputValue();
                    const postalCodeAfter = await postalCodeInput.inputValue();
                    
                    console.log('City name after click:', cityNameAfter);
                    console.log('Postal code after click:', postalCodeAfter);
                    
                    if (cityNameAfter === '' && postalCodeAfter === '') {
                        console.log('✅ Form was cleared - likely success!');
                    } else {
                        console.log('❌ Form was not cleared');
                    }
                    
                } else {
                    console.log('❌ Form inputs not found');
                }
            } else {
                console.log('❌ Add city button not found');
            }
        } else {
            console.log('❌ No region headers found');
        }
        
        console.log('Test completed');
    });

    test('should check for JavaScript function availability', async ({ page }) => {
        const functionCheck = await page.evaluate(() => {
            return {
                addNewCity: typeof window.addNewCity,
                addCityToTable: typeof window.addCityToTable,
                updateCityCount: typeof window.updateCityCount,
                showSuccessNotification: typeof window.showSuccessNotification,
                showErrorNotification: typeof window.showErrorNotification
            };
        });
        
        console.log('Function availability check:', functionCheck);
        
        // All functions should be available
        expect(functionCheck.addNewCity).toBe('function');
        expect(functionCheck.addCityToTable).toBe('function');
        expect(functionCheck.updateCityCount).toBe('function');
        expect(functionCheck.showSuccessNotification).toBe('function');
        expect(functionCheck.showErrorNotification).toBe('function');
    });
});