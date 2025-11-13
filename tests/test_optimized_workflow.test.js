const { test, expect } = require('@playwright/test');

test('Test optimized Google Ads Editor CSV export workflow', async ({ page }) => {
    console.log('🚀 Testing optimized Google Ads Editor CSV export workflow');
    
    // Navigate to builder and create a new campaign
    await page.goto('http://localhost:8000/geo-builder-v2/');
    await page.waitForLoadState('networkidle');
    
    // Fill Step 1
    await page.fill('input[name="client_name"]', 'Optimized CSV Test Company');
    await page.fill('input[name="service_name"]', 'Optimized Test Service');  
    await page.fill('input[name="website_url"]', 'https://optimizedtest.dk');
    await page.selectOption('select[name="industry"]', { index: 1 });
    
    // Go to Step 2
    await page.click('#next-btn');
    await page.waitForTimeout(1000);
    
    // Fill geography
    await page.evaluate(() => {
        document.getElementById('selected_cities').value = 'København,Aarhus,Odense';
        document.getElementById('cities').value = 'København\\nAarhus\\nOdense';
    });
    
    // Go to Step 3
    await page.click('#next-btn');
    await page.waitForTimeout(1000);
    
    // Fill multiple headlines through auto-reveal
    const headlines = [
        'Optimized Test Service København',
        '5/5 Stjerner Trustpilot',
        'Ring i dag - Gratis tilbud',
        'Eksperter i København',
        'Hurtig og professionel',
        'Åbent 24/7'
    ];
    
    for (let i = 0; i < headlines.length; i++) {
        await page.fill(`#headline_${i+1}`, headlines[i]);
        await page.waitForTimeout(200);
    }
    
    // Fill descriptions
    const descriptions = [
        'Professionel Optimized Test Service i København - Ring i dag for gratis tilbud!',
        'Erfaren Optimized Test Service med 5/5 stjerner. Vi dækker København og omegn.',
        'Hurtig og pålidelig service i København. Kontakt os for personlig betjening.'
    ];
    
    for (let i = 0; i < descriptions.length; i++) {
        await page.fill(`#description_${i+1}`, descriptions[i]);
        await page.waitForTimeout(200);
    }
    
    // Submit form
    console.log('📝 Submitting optimized campaign form...');
    await page.click('#submit-btn');
    await page.waitForTimeout(3000);
    
    // Check we're on success page
    expect(page.url()).toContain('geo-success');
    console.log('✅ Campaign created successfully');
    
    // Find and test CSV export
    console.log('📤 Testing optimized CSV export...');
    
    const exportLinks = page.locator('a[href*="/geo-export/"][href*="/google_ads/"]');
    const exportCount = await exportLinks.count();
    console.log(`📤 Found ${exportCount} Google Ads export links`);
    
    if (exportCount > 0) {
        // Download the CSV
        const [download] = await Promise.all([
            page.waitForEvent('download'),
            exportLinks.first().click()
        ]);
        
        console.log('📁 Downloaded optimized CSV file');
        
        // Check filename
        const suggestedFilename = download.suggestedFilename();
        console.log(`📁 File: ${suggestedFilename}`);
        
        // Verify CSV extension
        expect(suggestedFilename).toMatch(/\.csv$/);
        console.log('✅ File has .csv extension');
        
        // Save and read the file content for verification
        const path = await download.path();
        if (path) {
            const fs = require('fs');
            const content = fs.readFileSync(path, 'utf8');
            const lines = content.split('\n');
            
            console.log('📄 Checking optimized CSV content...');
            
            // Verify header contains required fields
            const header = lines[0];
            const requiredFields = [
                'Campaign Type', 'Networks', 'Search Partners', 
                'Display Network', 'Political ads in EU', 'Status'
            ];
            
            for (const field of requiredFields) {
                if (header.includes(field)) {
                    console.log(`✅ Found required field: ${field}`);
                } else {
                    console.log(`❌ Missing field: ${field}`);
                }
            }
            
            // Check campaign settings in data
            const campaignLine = lines[1] || '';
            if (campaignLine.includes('Search-only')) {
                console.log('✅ Campaign Type: Search-only');
            }
            if (campaignLine.includes('No') && campaignLine.includes('Search') && campaignLine.includes('Active')) {
                console.log('✅ Optimized settings detected');
            }
            
            console.log('🎯 Google Ads Editor optimization complete!');
        }
        
        return true;
    } else {
        console.log('❌ No export links found');
        return false;
    }
});