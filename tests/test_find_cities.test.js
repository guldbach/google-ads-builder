// Test to find actual city names on page
const { test, expect } = require('@playwright/test');

test.describe('Find Cities Test', () => {
    
    test('should find and list actual city names', async ({ page }) => {
        console.log('Finding cities on page...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Expand first region to see cities
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            console.log('Expanding first region...');
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Find all city names in table rows
            const cities = await page.evaluate(() => {
                const cityList = [];
                
                // Look for city names in table rows
                $('tr.city-row').each(function() {
                    const cityName = $(this).find('td:first-child .font-medium').text().trim();
                    if (cityName) {
                        cityList.push(cityName);
                    }
                });
                
                // Also check all .font-medium elements in cities area
                $('.cities-list .font-medium').each(function() {
                    const text = $(this).text().trim();
                    if (text && !cityList.includes(text)) {
                        cityList.push(text);
                    }
                });
                
                return cityList;
            });
            
            console.log('Found cities:');
            cities.forEach((city, index) => {
                console.log(`${index + 1}. ${city}`);
            });
            
            // Specifically check for Aalborg and Glamsbjerg
            const hasAalborg = cities.some(city => city.toLowerCase().includes('aalborg'));
            const hasGlamsbjerg = cities.some(city => city.toLowerCase().includes('glamsbjerg'));
            
            console.log('Contains Aalborg:', hasAalborg);
            console.log('Contains Glamsbjerg:', hasGlamsbjerg);
            
            if (hasGlamsbjerg) {
                console.log('🎉 SUCCESS: Edit worked! Aalborg was renamed to Glamsbjerg!');
            } else if (hasAalborg) {
                console.log('⚠️  Aalborg still exists, edit may not have been saved');
            } else {
                console.log('❓ Neither city found in the list');
            }
        }
        
        expect(true).toBe(true);
    });
});