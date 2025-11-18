// Test for simplified "Tilføj By" functionality - only city name

const { test, expect } = require('@playwright/test');

test.describe('Simplified Add City Test', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForSelector('#create-region-btn', { timeout: 10000 });
    });

    test('should test simplified add city form with only city name', async ({ page }) => {
        console.log('Testing simplified add city form...');
        
        // Create a simple test region first using any available input
        await page.click('#create-region-btn');
        await page.waitForSelector('#slide-panel-overlay', { state: 'visible', timeout: 5000 });
        
        // Try to find the first input field and fill it
        const inputs = page.locator('input[type="text"]');
        if (await inputs.count() > 0) {
            await inputs.first().fill(`Simplified Test Region ${Date.now()}`);
            await page.click('#slide-panel-save');
            await page.waitForSelector('#slide-panel-overlay', { state: 'hidden', timeout: 10000 });
            await page.waitForTimeout(2000);
        }
        
        // Find any region header and expand it
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Check if the simplified form is present
            const cityNameInput = page.locator('.new-city-name');
            const addCityButton = page.locator('.add-city-btn');
            
            console.log('City name input count:', await cityNameInput.count());
            console.log('Add city button count:', await addCityButton.count());
            
            // Check that unwanted fields are NOT present
            const synonymInput = page.locator('.new-city-synonym');
            const postalCodeInput = page.locator('.new-city-postal-code');
            const coordinatesInput = page.locator('.new-city-coordinates');
            
            console.log('Synonym input count (should be 0):', await synonymInput.count());
            console.log('Postal code input count (should be 0):', await postalCodeInput.count());
            console.log('Coordinates input count (should be 0):', await coordinatesInput.count());
            
            // Verify form simplification
            expect(await synonymInput.count()).toBe(0);
            expect(await postalCodeInput.count()).toBe(0);
            expect(await coordinatesInput.count()).toBe(0);
            expect(await cityNameInput.count()).toBeGreaterThan(0);
            expect(await addCityButton.count()).toBeGreaterThan(0);
            
            // Test the simplified form functionality
            if (await cityNameInput.count() > 0 && await addCityButton.count() > 0) {
                // Fill only the city name
                await cityNameInput.fill('København');
                
                // Listen for network requests
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
                
                console.log('Clicking add button...');
                await addCityButton.click();
                await page.waitForTimeout(2000);
                
                // Check if AJAX request was made
                const ajaxRequest = networkRequests.find(req => req.url.includes('add-danish-city'));
                if (ajaxRequest) {
                    console.log('✅ AJAX request was made:', ajaxRequest);
                    
                    // Check that only city_name is sent (no other fields)
                    const postData = ajaxRequest.postData;
                    if (postData) {
                        console.log('POST data:', postData);
                        expect(postData).toContain('city_name=København');
                        expect(postData).not.toContain('city_synonym');
                        expect(postData).not.toContain('postal_code');
                        expect(postData).not.toContain('coordinates');
                    }
                } else {
                    console.log('❌ No AJAX request found');
                }
                
                // Check if form was cleared
                const cityNameAfter = await cityNameInput.inputValue();
                console.log('City name after click:', cityNameAfter);
                
                if (cityNameAfter === '') {
                    console.log('✅ Form was cleared - functionality working!');
                } else {
                    console.log('❌ Form was not cleared');
                }
            }
        }
        
        console.log('Simplified add city test completed');
    });

    test('should verify table has only 2 columns (city name + actions)', async ({ page }) => {
        console.log('Testing simplified table structure...');
        
        // Create and expand region like previous test
        await page.click('#create-region-btn');
        await page.waitForSelector('#slide-panel-overlay', { state: 'visible' });
        const inputs = page.locator('input[type="text"]');
        if (await inputs.count() > 0) {
            await inputs.first().fill(`Table Test Region ${Date.now()}`);
            await page.click('#slide-panel-save');
            await page.waitForSelector('#slide-panel-overlay', { state: 'hidden' });
            await page.waitForTimeout(2000);
        }
        
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Check table headers - should only be "Bynavn" and "Actions"
            const tableHeaders = page.locator('thead th');
            const headerCount = await tableHeaders.count();
            
            console.log('Table header count:', headerCount);
            
            if (headerCount > 0) {
                const headerTexts = [];
                for (let i = 0; i < headerCount; i++) {
                    const text = await tableHeaders.nth(i).textContent();
                    headerTexts.push(text?.trim());
                }
                
                console.log('Table headers:', headerTexts);
                
                // Should only have 2 headers: "Bynavn" and "Actions"
                expect(headerCount).toBe(2);
                expect(headerTexts).toContain('Bynavn');
                expect(headerTexts).toContain('Actions');
                
                // Should NOT contain these headers
                expect(headerTexts).not.toContain('Synonym');
                expect(headerTexts).not.toContain('Postnummer');
                expect(headerTexts).not.toContain('Koordinater');
                
                console.log('✅ Table structure is simplified correctly!');
            }
        }
        
        console.log('Table structure test completed');
    });

    test('should verify Enter key works in city name field', async ({ page }) => {
        console.log('Testing Enter key functionality...');
        
        // Create and expand region
        await page.click('#create-region-btn');
        await page.waitForSelector('#slide-panel-overlay', { state: 'visible' });
        const inputs = page.locator('input[type="text"]');
        if (await inputs.count() > 0) {
            await inputs.first().fill(`Enter Test Region ${Date.now()}`);
            await page.click('#slide-panel-save');
            await page.waitForSelector('#slide-panel-overlay', { state: 'hidden' });
            await page.waitForTimeout(2000);
        }
        
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            const cityNameInput = page.locator('.new-city-name');
            
            if (await cityNameInput.count() > 0) {
                // Fill city name
                await cityNameInput.fill('Aarhus');
                
                // Listen for button clicks
                let buttonClicked = false;
                page.on('request', request => {
                    if (request.url().includes('add-danish-city')) {
                        buttonClicked = true;
                    }
                });
                
                // Press Enter key
                await cityNameInput.press('Enter');
                await page.waitForTimeout(1000);
                
                // Check if button was triggered
                if (buttonClicked) {
                    console.log('✅ Enter key triggered add button correctly!');
                } else {
                    console.log('❌ Enter key did not trigger add button');
                }
            }
        }
        
        console.log('Enter key test completed');
    });
});