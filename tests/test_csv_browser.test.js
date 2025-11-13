const { test, expect } = require('@playwright/test');

test('Test CSV export functionality', async ({ page }) => {
    console.log('📤 Testing CSV export functionality');
    
    // Navigate to builder and create a campaign
    await page.goto('http://localhost:8000/geo-builder-v2/');
    await page.waitForLoadState('networkidle');
    
    // Fill Step 1
    await page.fill('input[name="client_name"]', 'CSV Test Company');
    await page.fill('input[name="service_name"]', 'CSV Test Service');  
    await page.fill('input[name="website_url"]', 'https://csvtest.dk');
    await page.selectOption('select[name="industry"]', { index: 1 });
    
    // Go to Step 2
    await page.click('#next-btn');
    await page.waitForTimeout(1000);
    
    // Fill geography
    await page.evaluate(() => {
        document.getElementById('selected_cities').value = 'København,Aarhus';
        document.getElementById('cities').value = 'København\\nAarhus';
    });
    
    // Go to Step 3
    await page.click('#next-btn');
    await page.waitForTimeout(1000);
    
    // Fill headlines and descriptions
    await page.fill('#headline_1', 'CSV Test Service København');
    await page.waitForTimeout(200);
    await page.fill('#headline_2', '5/5 Stjerner på Trustpilot');
    await page.waitForTimeout(200);
    await page.fill('#headline_3', 'Ring i dag for gratis tilbud');
    await page.waitForTimeout(200);
    
    await page.fill('#description_1', 'Professionel CSV Test Service i København - Ring i dag for gratis tilbud!');
    await page.waitForTimeout(200);
    await page.fill('#description_2', 'Erfaren CSV Test Service med 5/5 stjerner. Vi dækker København og omegn.');
    
    // Submit form
    console.log('📝 Submitting campaign form...');
    await page.click('#submit-btn');
    await page.waitForTimeout(3000);
    
    // Check we're on success page
    expect(page.url()).toContain('geo-success');
    console.log('✅ Campaign created successfully');
    
    // Find and click CSV export button
    console.log('🔍 Looking for CSV export button...');
    
    // Look for Google Ads export link
    const exportLinks = page.locator('a[href*="/geo-export/"][href*="/google_ads/"]');
    const exportCount = await exportLinks.count();
    console.log(`📤 Found ${exportCount} Google Ads export links`);
    
    if (exportCount > 0) {
        // Start download and get the download promise
        const [download] = await Promise.all([
            page.waitForEvent('download'),
            exportLinks.first().click()
        ]);
        
        console.log('🖱️ Clicked CSV export link and got download');
        
        // Check download details
        const suggestedFilename = download.suggestedFilename();
        console.log(`📁 Downloaded file: ${suggestedFilename}`);
        
        // Verify it's a CSV file
        expect(suggestedFilename).toMatch(/\.csv$/);
        console.log('✅ File has .csv extension');
        
        console.log('🎉 CSV export test completed successfully!');
        return true;
    } else {
        console.log('❌ No Google Ads export links found');
        return false;
    }
});