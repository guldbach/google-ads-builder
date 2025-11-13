const { test, expect } = require('@playwright/test');

test.describe('Step 2 to Step 3 Navigation - Specific Debug', () => {
  test.beforeEach(async ({ page }) => {
    // Enable console logging
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', error => console.log('PAGE ERROR:', error));
    
    // Go to the multi-step geo builder
    await page.goto('/geo-builder-v2/');
    await page.waitForLoadState('networkidle');
  });

  test('Debug: Step 2 to Step 3 Navigation Issue', async ({ page }) => {
    console.log('🎯 Testing Step 2 → Step 3 navigation specifically');
    
    // Fill Step 1 first
    await page.fill('input[name="client_name"]', 'Test Company');
    await page.fill('input[name="service_name"]', 'Test Service');  
    await page.fill('input[name="website_url"]', 'https://test.com');
    await page.selectOption('select[name="industry"]', { index: 1 });
    
    // Go to Step 2
    await page.click('#next-btn');
    await page.waitForTimeout(1000);
    
    // Verify we're on Step 2
    const step2 = page.locator('#step-2');
    await expect(step2).toHaveClass(/active/);
    console.log('✅ Successfully on Step 2');
    
    // Take screenshot of Step 2
    await page.screenshot({ path: 'tests/screenshots/step-2-before-cities.png', fullPage: true });
    
    // Check if cities are already selected (from Google Maps)
    const selectedCitiesValue = await page.inputValue('#selected_cities');
    console.log('🏙️ Selected cities value:', selectedCitiesValue);
    
    if (!selectedCitiesValue || selectedCitiesValue.trim() === '') {
      console.log('⚠️ No cities selected, using manual input...');
      
      // Check if fallback is active
      const mapFallback = page.locator('#manual-cities-input');
      const fallbackVisible = await mapFallback.isVisible();
      
      if (fallbackVisible) {
        console.log('📝 Using manual cities input');
        await mapFallback.fill('København, Aarhus, Odense');
        await page.click('button[onclick="updateCitiesFromManualInput()"]');
        await page.waitForTimeout(500);
      } else {
        console.log('🗺️ Using direct input method');
        // Directly set cities value
        await page.evaluate(() => {
          document.getElementById('selected_cities').value = 'København,Aarhus,Odense';
          document.getElementById('cities').value = 'København\nAarhus\nOdense';
          // Update statistics
          document.getElementById('cities-count').textContent = '3';
          document.getElementById('estimated-keywords').textContent = '9';
          document.getElementById('estimated-pages').textContent = '3';
        });
      }
    }
    
    // Verify cities are now selected
    const updatedCitiesValue = await page.inputValue('#selected_cities');
    console.log('✅ Updated cities value:', updatedCitiesValue);
    
    // Take screenshot after cities selection
    await page.screenshot({ path: 'tests/screenshots/step-2-after-cities.png', fullPage: true });
    
    // Now try to go to Step 3
    console.log('🖱️ Clicking Next to go to Step 3...');
    const nextBtn = page.locator('#next-btn');
    
    // Check if next button is visible
    const nextBtnVisible = await nextBtn.isVisible();
    console.log('Next button visible:', nextBtnVisible);
    
    await nextBtn.click();
    await page.waitForTimeout(1000);
    
    // Take screenshot after clicking
    await page.screenshot({ path: 'tests/screenshots/step-2-after-next-click.png', fullPage: true });
    
    // Check if we moved to Step 3
    const step3 = page.locator('#step-3');
    const step3IsActive = await step3.evaluate(el => el.classList.contains('active'));
    
    console.log('📊 Step 3 active status:', step3IsActive);
    
    if (step3IsActive) {
      console.log('✅ SUCCESS: Moved to Step 3');
      await page.screenshot({ path: 'tests/screenshots/step-3-success.png', fullPage: true });
    } else {
      console.log('❌ FAILED: Could not move to Step 3');
      
      // Debug information
      const step2IsActive = await step2.evaluate(el => el.classList.contains('active'));
      console.log('Step 2 still active:', step2IsActive);
      
      // Check current step variable
      const currentStepValue = await page.evaluate(() => window.currentStep);
      console.log('Current step variable:', currentStepValue);
      
      // Check for validation errors
      const validationMessages = await page.locator('.border-red-500').count();
      console.log('Fields with validation errors:', validationMessages);
      
      // Check validation message visibility
      const validationMsgVisible = await page.locator('#cities-validation-message').isVisible();
      console.log('Cities validation message visible:', validationMsgVisible);
      
      // Check validation message text
      if (validationMsgVisible) {
        const validationText = await page.textContent('#cities-validation-message');
        console.log('Validation message text:', validationText);
      }
      
      // Try calling validation function directly
      const validationResult = await page.evaluate(() => {
        if (typeof validateCurrentStep === 'function') {
          return validateCurrentStep();
        }
        return 'Function not available';
      });
      console.log('Direct validation result:', validationResult);
      
      throw new Error(`Step 2 → Step 3 navigation failed. Step 2 active: ${step2IsActive}, Step 3 active: ${step3IsActive}`);
    }
  });

  test('Debug: Test Step 2 Validation Logic', async ({ page }) => {
    console.log('🔍 Testing Step 2 validation logic specifically');
    
    // Get to Step 2 first
    await page.fill('input[name="client_name"]', 'Test Company');
    await page.fill('input[name="service_name"]', 'Test Service');  
    await page.fill('input[name="website_url"]', 'https://test.com');
    await page.selectOption('select[name="industry"]', { index: 1 });
    await page.click('#next-btn');
    await page.waitForTimeout(1000);
    
    // Test validation with empty cities
    console.log('Testing with empty cities...');
    await page.evaluate(() => {
      document.getElementById('selected_cities').value = '';
      document.getElementById('cities').value = '';
    });
    
    await page.click('#next-btn');
    await page.waitForTimeout(500);
    
    const validationVisible = await page.locator('#cities-validation-message').isVisible();
    console.log('Validation message appears with empty cities:', validationVisible);
    
    // Test validation with cities
    console.log('Testing with cities filled...');
    await page.evaluate(() => {
      document.getElementById('selected_cities').value = 'København,Aarhus';
      document.getElementById('cities').value = 'København\nAarhus';
    });
    
    await page.click('#next-btn');
    await page.waitForTimeout(500);
    
    const step3Active = await page.evaluate(() => 
      document.getElementById('step-3').classList.contains('active')
    );
    console.log('Step 3 active after setting cities:', step3Active);
  });

});