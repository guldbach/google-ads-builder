// Compare localhost vs 127.0.0.1 endpoints
const { test, expect } = require('@playwright/test');

test.describe('URL Comparison Test', () => {
    
    test('should compare localhost vs 127.0.0.1 endpoints', async ({ page }) => {
        console.log('Testing localhost vs 127.0.0.1 differences...');
        
        // Test localhost first
        console.log('🔍 Testing http://localhost:8000/geographic-regions-manager/');
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        const localhostData = await page.evaluate(() => {
            return {
                title: document.title,
                regionCount: $('.region-header').length,
                regionTitles: $('.region-header h3').map((i, el) => $(el).text().trim()).get(),
                userInfo: $('.nav-user-info').text().trim() || 'Not authenticated',
                totalCities: $('.stat-card').first().find('.text-3xl').text().trim(),
                url: window.location.href
            };
        });
        
        console.log('📍 Localhost data:');
        console.log(`  - Regions: ${localhostData.regionCount}`);
        console.log(`  - User: ${localhostData.userInfo}`);
        console.log(`  - Total cities: ${localhostData.totalCities}`);
        console.log(`  - First 3 regions: ${localhostData.regionTitles.slice(0, 3).join(', ')}`);
        
        // Test 127.0.0.1
        console.log('\n🔍 Testing http://127.0.0.1:8000/geographic-regions-manager/');
        await page.goto('http://127.0.0.1:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        const ip127Data = await page.evaluate(() => {
            return {
                title: document.title,
                regionCount: $('.region-header').length,
                regionTitles: $('.region-header h3').map((i, el) => $(el).text().trim()).get(),
                userInfo: $('.nav-user-info').text().trim() || 'Not authenticated',
                totalCities: $('.stat-card').first().find('.text-3xl').text().trim(),
                url: window.location.href
            };
        });
        
        console.log('📍 127.0.0.1 data:');
        console.log(`  - Regions: ${ip127Data.regionCount}`);
        console.log(`  - User: ${ip127Data.userInfo}`);
        console.log(`  - Total cities: ${ip127Data.totalCities}`);
        console.log(`  - First 3 regions: ${ip127Data.regionTitles.slice(0, 3).join(', ')}`);
        
        // Compare
        console.log('\n🔄 COMPARISON:');
        if (localhostData.regionCount === ip127Data.regionCount) {
            console.log('✅ Same number of regions');
        } else {
            console.log(`❌ Different region counts: localhost=${localhostData.regionCount}, 127.0.0.1=${ip127Data.regionCount}`);
        }
        
        if (localhostData.userInfo === ip127Data.userInfo) {
            console.log('✅ Same authentication status');
        } else {
            console.log(`❌ Different auth: localhost="${localhostData.userInfo}", 127.0.0.1="${ip127Data.userInfo}"`);
        }
        
        if (localhostData.totalCities === ip127Data.totalCities) {
            console.log('✅ Same total cities count');
        } else {
            console.log(`❌ Different cities count: localhost="${localhostData.totalCities}", 127.0.0.1="${ip127Data.totalCities}"`);
        }
        
        // Compare region titles
        const sameRegions = JSON.stringify(localhostData.regionTitles) === JSON.stringify(ip127Data.regionTitles);
        if (sameRegions) {
            console.log('✅ Same regions in same order');
        } else {
            console.log('❌ Different regions or order');
            console.log('  Localhost regions:', localhostData.regionTitles);
            console.log('  127.0.0.1 regions:', ip127Data.regionTitles);
        }
        
        expect(true).toBe(true);
    });
});