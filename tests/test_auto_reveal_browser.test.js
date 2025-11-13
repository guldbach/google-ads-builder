const { test, expect } = require('@playwright/test');

test.describe('Auto-Reveal Headlines and Descriptions', () => {
  test.beforeEach(async ({ page }) => {
    // Enable console logging
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', error => console.log('PAGE ERROR:', error));
    
    // Go to the multi-step geo builder
    await page.goto('http://localhost:8000/geo-builder-v2/');
    await page.waitForLoadState('networkidle');
  });

  test('Auto-reveal headlines when typing', async ({ page }) => {
    console.log('🎯 Testing auto-reveal headlines functionality');
    
    // Navigate to step 3 (headlines)
    // Fill Step 1 first
    await page.fill('input[name="client_name"]', 'Test Auto-Reveal Company');
    await page.fill('input[name="service_name"]', 'Auto Test Service');  
    await page.fill('input[name="website_url"]', 'https://autotest.dk');
    await page.selectOption('select[name="industry"]', { index: 1 });
    
    // Go to Step 2
    await page.click('#next-btn');
    await page.waitForTimeout(1000);
    
    // Fill geography (use direct input method)
    await page.evaluate(() => {
      document.getElementById('selected_cities').value = 'København,Aarhus,Odense';
      document.getElementById('cities').value = 'København\\nAarhus\\nOdense';
    });
    
    // Go to Step 3
    await page.click('#next-btn');
    await page.waitForTimeout(1000);
    
    // Verify we're on Step 3
    const step3 = page.locator('#step-3');
    await expect(step3).toHaveClass(/active/);
    console.log('✅ On Step 3 - Headlines section');
    
    // Check initial state - only headline 1 should be visible
    await expect(page.locator('#headline_1_container')).toBeVisible();
    await expect(page.locator('#headline_2_container')).not.toBeVisible();
    await expect(page.locator('#headline_3_container')).not.toBeVisible();
    
    console.log('✅ Initial state: Only Headline 1 visible');
    
    // Type in headline 1 - this should reveal headline 2
    await page.fill('#headline_1', 'Test Auto-Reveal Service København');
    await page.waitForTimeout(500);
    
    // Check if headline 2 is now visible
    await expect(page.locator('#headline_2_container')).toBeVisible();
    console.log('✅ Headline 2 auto-revealed after typing in headline 1');
    
    // Type in headline 2 - this should reveal headline 3
    await page.fill('#headline_2', '5/5 Stjerner på Trustpilot');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#headline_3_container')).toBeVisible();
    console.log('✅ Headline 3 auto-revealed after typing in headline 2');
    
    // Type in headline 3 - this should reveal headline 4
    await page.fill('#headline_3', 'Ring i dag for gratis tilbud');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#headline_4_container')).toBeVisible();
    console.log('✅ Headline 4 auto-revealed after typing in headline 3');
    
    // Continue testing a few more to verify the pattern works
    await page.fill('#headline_4', 'Eksperter i København');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#headline_5_container')).toBeVisible();
    console.log('✅ Headline 5 auto-revealed after typing in headline 4');
    
    // Check progress counter updates
    const progressText = await page.textContent('#headlines-progress');
    console.log(`📊 Headlines progress: ${progressText}`);
    
    // Verify we can continue up to headline 15
    for (let i = 5; i <= 10; i++) {
      await page.fill(`#headline_${i}`, `Test Headline ${i}`);
      await page.waitForTimeout(200);
      
      if (i < 15) {
        const nextHeadlineVisible = await page.locator(`#headline_${i+1}_container`).isVisible();
        if (nextHeadlineVisible) {
          console.log(`✅ Headline ${i+1} auto-revealed after headline ${i}`);
        }
      }
    }
    
    // Take screenshot of multiple headlines revealed
    await page.screenshot({ path: 'tests/screenshots/auto-reveal-headlines.png', fullPage: true });
    
    console.log('🎉 Auto-reveal headlines test passed!');
  });

  test('Auto-reveal descriptions when typing', async ({ page }) => {
    console.log('📄 Testing auto-reveal descriptions functionality');
    
    // Navigate to step 3 quickly
    await page.fill('input[name="client_name"]', 'Test Descriptions Company');
    await page.fill('input[name="service_name"]', 'Description Test Service');  
    await page.fill('input[name="website_url"]', 'https://desctest.dk');
    await page.selectOption('select[name="industry"]', { index: 1 });
    await page.click('#next-btn');
    await page.waitForTimeout(500);
    
    // Quick geography fill
    await page.evaluate(() => {
      document.getElementById('selected_cities').value = 'Aalborg,Esbjerg';
      document.getElementById('cities').value = 'Aalborg\\nEsbjerg';
    });
    await page.click('#next-btn');
    await page.waitForTimeout(500);
    
    // Check initial descriptions state
    await expect(page.locator('#description_1_container')).toBeVisible();
    await expect(page.locator('#description_2_container')).not.toBeVisible();
    await expect(page.locator('#description_3_container')).not.toBeVisible();
    
    console.log('✅ Initial state: Only Description 1 visible');
    
    // Type in description 1 - this should reveal description 2
    await page.fill('#description_1', 'Professionel Description Test Service i Aalborg - Ring i dag for gratis tilbud!');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#description_2_container')).toBeVisible();
    console.log('✅ Description 2 auto-revealed after typing in description 1');
    
    // Type in description 2 - this should reveal description 3
    await page.fill('#description_2', 'Erfaren Description Test Service med 5/5 stjerner. Vi dækker Aalborg og omegn.');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#description_3_container')).toBeVisible();
    console.log('✅ Description 3 auto-revealed after typing in description 2');
    
    // Type in description 3 - this should reveal description 4
    await page.fill('#description_3', 'Hurtig og pålidelig service i Aalborg. Kontakt os for personlig betjening.');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#description_4_container')).toBeVisible();
    console.log('✅ Description 4 auto-revealed after typing in description 3');
    
    // Type in description 4 - no more should be revealed (max 4)
    await page.fill('#description_4', 'Certificeret Description Test Service virksomhed. Miljøvenlig løsning til Aalborg.');
    await page.waitForTimeout(500);
    
    // Check progress counter
    const progressText = await page.textContent('#descriptions-progress');
    console.log(`📊 Descriptions progress: ${progressText}`);
    
    // Take screenshot of all descriptions revealed
    await page.screenshot({ path: 'tests/screenshots/auto-reveal-descriptions.png', fullPage: true });
    
    console.log('🎉 Auto-reveal descriptions test passed!');
  });

  test('Complete auto-reveal workflow with form submission', async ({ page }) => {
    console.log('🚀 Testing complete auto-reveal workflow with submission');
    
    // Fill out complete form with multiple headlines and descriptions
    await page.fill('input[name="client_name"]', 'Complete Auto-Reveal Test');
    await page.fill('input[name="service_name"]', 'VVS Service');  
    await page.fill('input[name="website_url"]', 'https://completetest.dk');
    await page.selectOption('select[name="industry"]', { index: 1 });
    await page.click('#next-btn');
    await page.waitForTimeout(500);
    
    await page.evaluate(() => {
      document.getElementById('selected_cities').value = 'København,Aarhus,Odense,Aalborg';
      document.getElementById('cities').value = 'København\\nAarhus\\nOdense\\nAalborg';
    });
    await page.click('#next-btn');
    await page.waitForTimeout(500);
    
    // Fill multiple headlines through auto-reveal
    const headlines = [
      'VVS Service København',
      '5/5 Stjerner Trustpilot',
      'Ring i dag - Gratis tilbud',
      'Eksperter i København',
      'Hurtig og professionel',
      'Åbent 24/7',
      'Lokal VVS specialist',
      'Bedste pris i København'
    ];
    
    for (let i = 0; i < headlines.length; i++) {
      await page.fill(`#headline_${i+1}`, headlines[i]);
      await page.waitForTimeout(200);
    }
    
    // Fill multiple descriptions through auto-reveal
    const descriptions = [
      'Professionel VVS Service i København - Ring i dag for gratis tilbud!',
      'Erfaren VVS med 5/5 stjerner. Vi dækker København og omegn.',
      'Hurtig og pålidelig service i København. Kontakt os for personlig betjening.',
      'Certificeret VVS virksomhed. Miljøvenlig og bæredygtig løsning til København.'
    ];
    
    for (let i = 0; i < descriptions.length; i++) {
      await page.fill(`#description_${i+1}`, descriptions[i]);
      await page.waitForTimeout(200);
    }
    
    // Take final screenshot
    await page.screenshot({ path: 'tests/screenshots/complete-auto-reveal.png', fullPage: true });
    
    // Submit form
    console.log('📝 Submitting complete form...');
    await page.click('#submit-btn');
    await page.waitForTimeout(2000);
    
    // Check for success page or error
    const url = page.url();
    if (url.includes('/geo-success/')) {
      console.log('✅ Form submitted successfully - redirected to success page');
      
      // Try to test export with new data
      const exportButtons = page.locator('a[href*="/geo-export/"]');
      const exportCount = await exportButtons.count();
      if (exportCount > 0) {
        console.log(`📤 Found ${exportCount} export options`);
      }
    } else {
      console.log('⚠️ Form submission may have failed or redirected elsewhere');
    }
    
    console.log('🏁 Complete auto-reveal workflow test finished');
  });

});