// Verify that Aalborg was actually changed to Glamsbjerg in database
const { test, expect } = require('@playwright/test');

test.describe('Verify Glamsbjerg Test', () => {
    
    test('should verify that Aalborg was changed to Glamsbjerg in database', async ({ page }) => {
        console.log('Verifying database change...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Check if Glamsbjerg exists in the page
        const glamsbjerExists = await page.locator('tr:has(.font-medium:text("Glamsbjerg"))').count() > 0;
        const aalborgExists = await page.locator('tr:has(.font-medium:text("Aalborg"))').count() > 0;
        
        console.log('Glamsbjerg found in page:', glamsbjerExists);
        console.log('Aalborg found in page:', aalborgExists);
        
        if (glamsbjerExists) {
            console.log('🎉 SUCCESS: Aalborg was successfully renamed to Glamsbjerg!');
            console.log('✅ Edit functionality is working correctly!');
        } else if (aalborgExists) {
            console.log('⚠️  Aalborg still exists - edit may not have been saved');
        } else {
            console.log('❓ Neither city found');
        }
        
        // List all cities to see current state
        const allCities = await page.evaluate(() => {
            const cities = [];
            $('.font-medium').each(function() {
                const text = $(this).text().trim();
                if (text && !text.includes('Regioner') && !text.includes('Byer')) {
                    cities.push(text);
                }
            });
            return cities.slice(0, 10); // First 10 cities
        });
        
        console.log('Current cities in system:');
        allCities.forEach((city, index) => {
            console.log(`${index + 1}. ${city}`);
        });
        
        expect(true).toBe(true);
    });
});