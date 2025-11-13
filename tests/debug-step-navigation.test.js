const { test, expect } = require('@playwright/test');

test.describe('Multi-Step Geo Campaign Builder - Debug Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Enable console logging
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', error => console.log('PAGE ERROR:', error));
    
    // Go to the multi-step geo builder
    await page.goto('/geo-builder-v2/');
    await page.waitForLoadState('networkidle');
  });

  test('Debug: Step 1 to Step 2 Navigation', async ({ page }) => {
    console.log('🎯 Starting Step 1 to Step 2 navigation test');
    
    // Take initial screenshot
    await page.screenshot({ path: 'tests/screenshots/step-1-initial.png', fullPage: true });
    
    // Check that we're on Step 1
    const step1 = page.locator('#step-1');
    await expect(step1).toHaveClass(/active/);
    console.log('✅ Step 1 is active');
    
    // Fill out Step 1 form fields
    console.log('📝 Filling out Step 1 form fields...');
    
    await page.fill('input[name="client_name"]', 'Test Company');
    await page.fill('input[name="service_name"]', 'Test Service');  
    await page.fill('input[name="website_url"]', 'https://test.com');
    await page.selectOption('select[name="industry"]', { index: 1 }); // Select first available option
    
    // Take screenshot after filling
    await page.screenshot({ path: 'tests/screenshots/step-1-filled.png', fullPage: true });
    
    // Check if Next button is visible and enabled
    const nextBtn = page.locator('#next-btn');
    await expect(nextBtn).toBeVisible();
    console.log('✅ Next button is visible');
    
    // Click Next button
    console.log('🖱️ Clicking Next button...');
    await nextBtn.click();
    
    // Wait a moment for any transitions
    await page.waitForTimeout(1000);
    
    // Take screenshot after clicking
    await page.screenshot({ path: 'tests/screenshots/after-next-click.png', fullPage: true });
    
    // Check if we moved to Step 2
    const step2 = page.locator('#step-2');
    const step2IsActive = await step2.evaluate(el => el.classList.contains('active'));
    
    console.log('📊 Step 2 active status:', step2IsActive);
    
    if (step2IsActive) {
      console.log('✅ SUCCESS: Moved to Step 2');
      await expect(step2).toHaveClass(/active/);
    } else {
      console.log('❌ PROBLEM: Still on Step 1');
      
      // Debug information
      const step1IsActive = await step1.evaluate(el => el.classList.contains('active'));
      console.log('Step 1 still active:', step1IsActive);
      
      // Check current step variable
      const currentStepValue = await page.evaluate(() => window.currentStep);
      console.log('Current step variable:', currentStepValue);
      
      // Check for validation errors
      const validationMessages = await page.locator('.border-red-500').count();
      console.log('Fields with validation errors:', validationMessages);
      
      // Check console for JavaScript errors
      const hasErrors = await page.evaluate(() => {
        return window.console.error.toString();
      });
      
      throw new Error(`Step navigation failed. Step 1 active: ${step1IsActive}, Step 2 active: ${step2IsActive}`);
    }
  });

  test('Debug: Check Form Validation', async ({ page }) => {
    console.log('🔍 Testing form validation behavior');
    
    // Try clicking Next without filling any fields
    const nextBtn = page.locator('#next-btn');
    await nextBtn.click();
    
    await page.waitForTimeout(500);
    
    // Check if validation prevents progression
    const step1 = page.locator('#step-1');
    const step1IsActive = await step1.evaluate(el => el.classList.contains('active'));
    
    console.log('Step 1 still active after empty form click:', step1IsActive);
    
    // Count validation errors
    const errorFields = await page.locator('.border-red-500').count();
    console.log('Fields with validation errors:', errorFields);
    
    await page.screenshot({ path: 'tests/screenshots/validation-errors.png', fullPage: true });
  });

  test('Debug: JavaScript Function Availability', async ({ page }) => {
    console.log('🔧 Testing JavaScript function availability');
    
    // Test if functions are defined
    const functionsTest = await page.evaluate(() => {
      return {
        nextStep: typeof nextStep !== 'undefined',
        showStep: typeof showStep !== 'undefined', 
        validateCurrentStep: typeof validateCurrentStep !== 'undefined',
        currentStep: window.currentStep || 'undefined'
      };
    });
    
    console.log('JavaScript functions status:', functionsTest);
    
    // Test calling nextStep directly
    try {
      await page.evaluate(() => nextStep());
      console.log('✅ nextStep() called successfully');
    } catch (error) {
      console.log('❌ Error calling nextStep():', error.message);
    }
  });

  test('Debug: Check Step Elements Exist', async ({ page }) => {
    console.log('🔍 Checking if step elements exist in DOM');
    
    const stepElements = await page.evaluate(() => {
      return {
        step1: !!document.getElementById('step-1'),
        step2: !!document.getElementById('step-2'), 
        step3: !!document.getElementById('step-3'),
        nextBtn: !!document.getElementById('next-btn'),
        prevBtn: !!document.getElementById('prev-btn'),
        submitBtn: !!document.getElementById('submit-btn')
      };
    });
    
    console.log('Step elements exist:', stepElements);
    
    // Check classes on step elements
    const stepClasses = await page.evaluate(() => {
      const step1 = document.getElementById('step-1');
      const step2 = document.getElementById('step-2');
      return {
        step1Classes: step1 ? Array.from(step1.classList) : 'not found',
        step2Classes: step2 ? Array.from(step2.classList) : 'not found'
      };
    });
    
    console.log('Step element classes:', stepClasses);
  });

});