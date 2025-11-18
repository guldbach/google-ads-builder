// Debug test for "Tilføj By" functionality
// This test will help identify why the add city button doesn't work

const { test, expect } = require('@playwright/test');

test.describe('Add City Debug Tests', () => {
    
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForSelector('#create-region-btn', { timeout: 10000 });
    });

    test('should debug add city functionality step by step', async ({ page }) => {
        console.log('Starting add city debug test...');
        
        // Step 1: Create a test region first
        await page.click('#create-region-btn');
        await page.waitForSelector('#slide-panel-overlay', { state: 'visible', timeout: 5000 });
        
        const regionName = `Debug Region ${Date.now()}`;
        await page.fill('#create-list-name', regionName);
        await page.fill('#create-list-description', 'Debug region for testing');
        await page.click('#slide-panel-save');
        await page.waitForSelector('#slide-panel-overlay', { state: 'hidden', timeout: 10000 });
        
        // Wait for region to appear
        await page.waitForTimeout(2000);
        console.log('Region created, looking for it...');
        
        // Step 2: Find and expand the region
        const regionHeader = page.locator('.region-header').filter({ hasText: regionName });
        await expect(regionHeader).toBeVisible({ timeout: 10000 });
        console.log('Region found, clicking to expand...');
        
        await regionHeader.click();
        await page.waitForTimeout(1000);
        
        // Step 3: Check if cities-content is now visible
        const citiesContent = page.locator('.cities-content').filter({ hasText: 'Tilføj Nye Byer' });
        const isVisible = await citiesContent.isVisible();
        console.log('Cities content visible:', isVisible);
        
        if (!isVisible) {
            console.log('ERROR: Cities content not visible after clicking header');
            await page.screenshot({ path: 'debug-cities-content-not-visible.png' });
            return;
        }
        
        // Step 4: Fill in city information
        console.log('Filling in city information...');
        
        // Find the form fields
        const cityNameInput = page.locator('.new-city-name');
        const synonymInput = page.locator('.new-city-synonym');
        const postalCodeInput = page.locator('.new-city-postal-code');
        const addButton = page.locator('.add-city-btn');
        
        // Check if form fields exist
        console.log('City name input count:', await cityNameInput.count());
        console.log('Synonym input count:', await synonymInput.count());
        console.log('Postal code input count:', await postalCodeInput.count());
        console.log('Add button count:', await addButton.count());
        
        // Take screenshot before filling
        await page.screenshot({ path: 'debug-before-filling-form.png' });
        
        // Fill the form
        await cityNameInput.fill('Test By');
        await synonymInput.fill('Test Synonym');
        await postalCodeInput.fill('1234');
        
        console.log('Form filled, taking screenshot...');
        await page.screenshot({ path: 'debug-after-filling-form.png' });
        
        // Step 5: Check if add button is clickable and has event listener
        const addButtonInfo = await addButton.evaluate((btn) => {
            return {
                disabled: btn.disabled,
                onclick: btn.onclick,
                hasClickListener: btn.addEventListener ? 'addEventListener available' : 'no addEventListener',
                dataAttributes: Array.from(btn.attributes).map(attr => `${attr.name}="${attr.value}"`),
                text: btn.textContent.trim()
            };
        });
        
        console.log('Add button info:', JSON.stringify(addButtonInfo, null, 2));
        
        // Step 6: Try to click the add button and observe what happens
        console.log('Clicking add button...');
        
        // Listen for network requests
        const networkRequests = [];
        page.on('request', request => {
            networkRequests.push({
                url: request.url(),
                method: request.method(),
                postData: request.postData()
            });
        });
        
        // Listen for console messages
        const consoleMessages = [];
        page.on('console', msg => {
            consoleMessages.push(`${msg.type()}: ${msg.text()}`);
        });
        
        // Click the button
        await addButton.click();
        
        // Wait a moment for any async actions
        await page.waitForTimeout(3000);
        
        // Take screenshot after click
        await page.screenshot({ path: 'debug-after-click-add.png' });
        
        // Check what happened
        console.log('Network requests after click:', networkRequests);
        console.log('Console messages after click:', consoleMessages);
        
        // Check if a new city appeared in the table
        const cityRows = page.locator('tr[data-city-id]');
        const cityCount = await cityRows.count();
        console.log('Number of cities after add:', cityCount);
        
        // Look for any error messages
        const errorMessages = page.locator('.error, .alert-error, [class*="error"]');
        const errorCount = await errorMessages.count();
        if (errorCount > 0) {
            console.log('Found error messages:');
            for (let i = 0; i < errorCount; i++) {
                const errorText = await errorMessages.nth(i).textContent();
                console.log(`Error ${i + 1}:`, errorText);
            }
        }
        
        // Check if the form was reset
        const cityNameValue = await cityNameInput.inputValue();
        const synonymValue = await synonymInput.inputValue();
        const postalCodeValue = await postalCodeInput.inputValue();
        
        console.log('Form values after click:');
        console.log('City name:', cityNameValue);
        console.log('Synonym:', synonymValue);
        console.log('Postal code:', postalCodeValue);
        
        console.log('Add city debug test completed');
    });

    test('should check for JavaScript event handlers', async ({ page }) => {
        console.log('Checking JavaScript event handlers...');
        
        // Create a region first
        await page.click('#create-region-btn');
        await page.waitForSelector('#slide-panel-overlay', { state: 'visible' });
        
        const regionName = `Handler Test ${Date.now()}`;
        await page.fill('#create-list-name', regionName);
        await page.click('#slide-panel-save');
        await page.waitForSelector('#slide-panel-overlay', { state: 'hidden' });
        await page.waitForTimeout(2000);
        
        // Expand region
        await page.locator('.region-header').filter({ hasText: regionName }).click();
        await page.waitForTimeout(1000);
        
        // Check for event handlers in the page
        const handlerInfo = await page.evaluate(() => {
            // Look for add city button
            const addButton = document.querySelector('.add-city-btn');
            
            if (!addButton) {
                return { error: 'Add city button not found' };
            }
            
            // Check for various event listeners
            const info = {
                hasOnClick: !!addButton.onclick,
                hasDataRegionId: addButton.getAttribute('data-region-id'),
                buttonText: addButton.textContent,
                classList: Array.from(addButton.classList),
                parentInfo: {
                    tagName: addButton.parentElement?.tagName,
                    classList: addButton.parentElement ? Array.from(addButton.parentElement.classList) : []
                }
            };
            
            // Check if jQuery event listeners exist
            if (window.$ && window.$.fn.jquery) {
                info.jqueryVersion = window.$.fn.jquery;
                
                // Try to get jQuery events data (this might not work due to jQuery internals)
                try {
                    const events = window.$._data ? window.$._data(addButton, 'events') : null;
                    info.jqueryEvents = events ? Object.keys(events) : 'No events or unable to access';
                } catch (e) {
                    info.jqueryEvents = 'Error accessing jQuery events: ' + e.message;
                }
            }
            
            // Look for click handlers in the document
            info.documentClickHandlers = [];
            
            // Check document ready functions
            info.documentReadyFunctions = window.documentReadyFunctions || 'Not available';
            
            return info;
        });
        
        console.log('JavaScript handler info:', JSON.stringify(handlerInfo, null, 2));
        
        // Also check if the add city function exists
        const functionCheck = await page.evaluate(() => {
            return {
                addNewCity: typeof window.addNewCity,
                addCityToTable: typeof window.addCityToTable,
                addKeywordToTable: typeof window.addKeywordToTable,
                globalFunctions: Object.getOwnPropertyNames(window).filter(name => 
                    name.toLowerCase().includes('add') || name.toLowerCase().includes('city')
                )
            };
        });
        
        console.log('Function availability:', JSON.stringify(functionCheck, null, 2));
    });

    test('should test if AJAX endpoint exists', async ({ page }) => {
        console.log('Testing AJAX endpoint...');
        
        // Try to manually call the add city AJAX endpoint
        const response = await page.evaluate(async () => {
            try {
                const testResponse = await fetch('/ajax/add-danish-city/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || 'no-csrf'
                    },
                    body: JSON.stringify({
                        region_id: 1,
                        city_name: 'Test City',
                        postal_code: '1234'
                    })
                });
                
                return {
                    status: response.status,
                    statusText: response.statusText,
                    ok: response.ok,
                    text: await response.text()
                };
            } catch (error) {
                return {
                    error: error.message
                };
            }
        });
        
        console.log('AJAX endpoint test result:', JSON.stringify(response, null, 2));
    });
});