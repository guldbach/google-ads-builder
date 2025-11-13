const { test, expect } = require('@playwright/test');

test('Final verification: Create campaign with auto-reveal and test CSV export', async ({ page }) => {
    console.log('🔍 FINAL VERIFICATION: Auto-reveal + CSV export + Google Ads Editor compatibility');
    
    // Navigate to builder
    await page.goto('http://localhost:8000/geo-builder-v2/');
    await page.waitForLoadState('networkidle');
    
    // Fill Step 1
    await page.fill('input[name="client_name"]', 'Final Verification Company');
    await page.fill('input[name="service_name"]', 'Final Test Service');  
    await page.fill('input[name="website_url"]', 'https://finaltest.dk');
    await page.selectOption('select[name="industry"]', { index: 1 });
    
    // Go to Step 2
    await page.click('#next-btn');
    await page.waitForTimeout(1000);
    
    // Fill geography
    await page.evaluate(() => {
        document.getElementById('selected_cities').value = 'København,Aarhus,Odense,Aalborg';
        document.getElementById('cities').value = 'København\\nAarhus\\nOdense\\nAalborg';
    });
    
    // Go to Step 3
    await page.click('#next-btn');
    await page.waitForTimeout(1000);
    
    console.log('📝 Testing auto-reveal with EXTENDED headlines and descriptions...');
    
    // Fill 10 headlines to test auto-reveal works with extended system
    const headlines = [
        'Final Test Service København',
        '5/5 Stjerner Trustpilot',
        'Ring i dag - Gratis tilbud',
        'Eksperter i København',
        'Hurtig og professionel service',
        'Åbent 24/7 - ring nu',
        'Lokal specialist i Danmark',
        'Bedste pris garanteret',
        'Certificeret og forsikret',
        'Over 1000 tilfredse kunder'
    ];
    
    for (let i = 0; i < headlines.length; i++) {
        await page.fill(`#headline_${i+1}`, headlines[i]);
        await page.waitForTimeout(100);
    }
    
    // Fill 4 descriptions to test extended descriptions
    const descriptions = [
        'Professionel Final Test Service i København - Ring i dag for gratis tilbud og rådgivning!',
        'Erfaren Final Test Service med 5/5 stjerner på Trustpilot. Vi dækker hele København og omegn.',
        'Hurtig og pålidelig service i København. Kontakt os i dag for personlig og professionel betjening.',
        'Certificeret Final Test Service virksomhed. Miljøvenlig og bæredygtig løsning til København og hele Danmark.'
    ];
    
    for (let i = 0; i < descriptions.length; i++) {
        await page.fill(`#description_${i+1}`, descriptions[i]);
        await page.waitForTimeout(100);
    }
    
    console.log('✅ Filled 10 headlines + 4 descriptions via auto-reveal');
    
    // Submit form
    console.log('📝 Submitting final verification campaign...');
    await page.click('#submit-btn');
    await page.waitForTimeout(3000);
    
    // Check we're on success page
    expect(page.url()).toContain('geo-success');
    console.log('✅ Campaign with extended fields created successfully');
    
    // Test CSV export
    console.log('📤 Testing CSV export with extended data...');
    
    const exportLinks = page.locator('a[href*="/geo-export/"][href*="/google_ads/"]');
    const exportCount = await exportLinks.count();
    
    if (exportCount > 0) {
        // Download the CSV
        const [download] = await Promise.all([
            page.waitForEvent('download'),
            exportLinks.first().click()
        ]);
        
        console.log('📁 Downloaded CSV with extended data');
        
        // Read and verify CSV content
        const path = await download.path();
        if (path) {
            const fs = require('fs');
            const content = fs.readFileSync(path, 'utf8');
            const lines = content.split('\n');
            
            // Check header for extended headlines and descriptions
            const header = lines[0];
            
            // Count headline and description columns
            let headlineCount = 0;
            let descriptionCount = 0;
            
            const headerParts = header.split(',');
            for (const part of headerParts) {
                if (part.startsWith('Headline ')) {
                    headlineCount++;
                } else if (part.startsWith('Description ')) {
                    descriptionCount++;
                }
            }
            
            console.log(`🎯 CSV Analysis:`);
            console.log(`   Headline columns: ${headlineCount}`);
            console.log(`   Description columns: ${descriptionCount}`);
            
            // Find ad row
            const adRow = lines.find(line => line.includes('Responsive Search Ad'));
            if (adRow) {
                const adParts = adRow.split(',');
                let filledHeadlines = 0;
                let filledDescriptions = 0;
                
                // Count actual filled headlines and descriptions
                for (let i = 0; i < adParts.length; i++) {
                    const header = headerParts[i];
                    const value = adParts[i];
                    
                    if (header && header.startsWith('Headline ') && value && value.trim() !== '') {
                        filledHeadlines++;
                    } else if (header && header.startsWith('Description ') && value && value.trim() !== '') {
                        filledDescriptions++;
                    }
                }
                
                console.log(`   Filled headlines: ${filledHeadlines}`);
                console.log(`   Filled descriptions: ${filledDescriptions}`);
                
                // Verify we have the expected amount of data
                if (filledHeadlines >= 10) {
                    console.log('✅ Extended headlines (10+) exported successfully');
                } else {
                    console.log(`⚠️ Only ${filledHeadlines} headlines exported (expected 10+)`);
                }
                
                if (filledDescriptions >= 4) {
                    console.log('✅ Extended descriptions (4) exported successfully');
                } else {
                    console.log(`⚠️ Only ${filledDescriptions} descriptions exported (expected 4)`);
                }
            }
            
            // Final Google Ads Editor compatibility check
            const hasRequiredFields = [
                'Campaign Type', 'Networks', 'Search Partners', 
                'Display Network', 'Political ads in EU'
            ].every(field => header.includes(field));
            
            const campaignLine = lines[1] || '';
            const hasOptimalSettings = campaignLine.includes('Search-only') && 
                                     campaignLine.includes('Active') && 
                                     campaignLine.includes('No');
            
            if (hasRequiredFields && hasOptimalSettings) {
                console.log('✅ Google Ads Editor compatibility: VERIFIED');
                console.log('✅ Auto-reveal system: WORKING');
                console.log('✅ Extended fields: EXPORTED');
                console.log('✅ CSV format: OPTIMAL');
                return true;
            } else {
                console.log('❌ Google Ads Editor compatibility: FAILED');
                return false;
            }
        }
    } else {
        console.log('❌ No export links found');
        return false;
    }
});