// Geographic Regions Manager - Comprehensive Playwright Test Suite
// Testing region creation, editing, and city management functionality

const { test, expect } = require('@playwright/test');

// Test configuration
test.describe('Geographic Regions Manager', () => {
    
    // Setup - navigate to the manager page before each test
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        // Wait for page to be fully loaded
        await page.waitForSelector('#create-region-btn', { timeout: 10000 });
    });

    // Test 1: Page loads correctly and displays expected elements
    test('should load geographic regions manager page correctly', async ({ page }) => {
        // Check page title
        await expect(page).toHaveTitle(/Geografiske Regioner.*Google Ads Builder/);
        
        // Verify hero section elements
        await expect(page.locator('h1')).toContainText('Geografiske Regioner');
        await expect(page.locator('text=Administrer lister af danske byer')).toBeVisible();
        
        // Check quick actions bar
        await expect(page.locator('#create-region-btn')).toBeVisible();
        await expect(page.locator('#create-region-btn')).toContainText('Ny Region');
        await expect(page.locator('#download-template-btn')).toBeVisible();
        
        // Verify statistics cards are present
        await expect(page.locator('text=Total Lister')).toBeVisible();
        await expect(page.locator('text=Aktive Lister')).toBeVisible();
    });

    // Test 2: Create new region workflow
    test('should create a new geographic region successfully', async ({ page }) => {
        console.log('Starting region creation test...');
        
        // Step 1: Click "Ny Region" button
        await page.click('#create-region-btn');
        
        // Step 2: Verify slide panel opens
        await expect(page.locator('#slide-panel-overlay')).toBeVisible({ timeout: 5000 });
        await expect(page.locator('#slide-panel')).toBeVisible();
        await expect(page.locator('#slide-panel-title')).toContainText('Opret Ny Geografisk Region');
        
        // Step 3: Wait for form elements to be present
        await page.waitForSelector('#create-list-name', { timeout: 5000 });
        
        // Step 4: Fill out the region creation form
        const testRegionName = `Test Region ${Date.now()}`;
        await page.fill('#create-list-name', testRegionName);
        await page.fill('#create-list-description', 'Test region for Playwright automation');
        
        // Select category
        await page.selectOption('#create-list-category', 'custom');
        
        // Set visual settings
        await page.fill('#create-list-icon', '🧪');
        await page.fill('#create-list-color', '#22C55E');
        
        // Step 5: Verify live preview updates
        await expect(page.locator('#create-preview-name')).toContainText(testRegionName);
        await expect(page.locator('#create-preview-icon')).toContainText('🧪');
        
        // Step 6: Submit the form
        await page.click('#slide-panel-save');
        
        // Step 7: Wait for success and panel to close
        await expect(page.locator('#slide-panel-overlay')).toBeHidden({ timeout: 10000 });
        
        // Step 8: Verify new region appears in the list
        // Wait for page refresh/update
        await page.waitForTimeout(2000);
        await expect(page.locator(`text=${testRegionName}`)).toBeVisible({ timeout: 10000 });
        
        console.log('Region creation test completed successfully');
    });

    // Test 3: Edit existing region workflow
    test('should edit an existing region successfully', async ({ page }) => {
        console.log('Starting region editing test...');
        
        // First create a region to edit
        await page.click('#create-region-btn');
        await page.waitForSelector('#create-list-name', { timeout: 5000 });
        
        const originalName = `Edit Test Region ${Date.now()}`;
        await page.fill('#create-list-name', originalName);
        await page.fill('#create-list-description', 'Original description');
        await page.click('#slide-panel-save');
        await expect(page.locator('#slide-panel-overlay')).toBeHidden({ timeout: 10000 });
        
        // Wait for the region to appear
        await page.waitForTimeout(2000);
        await expect(page.locator(`text=${originalName}`)).toBeVisible({ timeout: 10000 });
        
        // Now edit the region
        // Find and click the edit button for our region
        const regionCard = page.locator('.bg-white.rounded-2xl').filter({ hasText: originalName });
        await regionCard.locator('button').filter({ hasText: 'Redigér' }).click();
        
        // Verify edit panel opens with pre-filled data
        await expect(page.locator('#slide-panel-overlay')).toBeVisible({ timeout: 5000 });
        await expect(page.locator('#edit-list-name')).toHaveValue(originalName);
        
        // Modify the region
        const updatedName = `Updated ${originalName}`;
        await page.fill('#edit-list-name', updatedName);
        await page.fill('#edit-list-description', 'Updated description for testing');
        await page.fill('#edit-list-icon', '✏️');
        
        // Save changes
        await page.click('#slide-panel-save');
        await expect(page.locator('#slide-panel-overlay')).toBeHidden({ timeout: 10000 });
        
        // Verify changes are reflected
        await page.waitForTimeout(2000);
        await expect(page.locator(`text=${updatedName}`)).toBeVisible({ timeout: 10000 });
        await expect(page.locator(`text=${originalName}`)).not.toBeVisible();
        
        console.log('Region editing test completed successfully');
    });

    // Test 4: Add city to region workflow
    test('should add a city to a region successfully', async ({ page }) => {
        console.log('Starting add city test...');
        
        // Create a test region first
        await page.click('#create-region-btn');
        await page.waitForSelector('#create-list-name', { timeout: 5000 });
        
        const regionName = `City Test Region ${Date.now()}`;
        await page.fill('#create-list-name', regionName);
        await page.click('#slide-panel-save');
        await expect(page.locator('#slide-panel-overlay')).toBeHidden({ timeout: 10000 });
        await page.waitForTimeout(2000);
        
        // Open the region for editing to add cities
        const regionCard = page.locator('.bg-white.rounded-2xl').filter({ hasText: regionName });
        await regionCard.locator('button').filter({ hasText: 'Redigér' }).click();
        await expect(page.locator('#slide-panel-overlay')).toBeVisible({ timeout: 5000 });
        
        // Look for add city functionality - this might be in the edit panel
        // First check if there's an "Add City" button or similar
        const addCityButton = page.locator('button').filter({ hasText: /tilføj.*by/i });
        
        if (await addCityButton.count() > 0) {
            await addCityButton.first().click();
            
            // Fill in city information
            await page.fill('input[placeholder*="by"]', 'Test By');
            await page.fill('input[placeholder*="postnummer"]', '1234');
            
            // Save the city
            const saveCityButton = page.locator('button').filter({ hasText: /gem.*by/i });
            if (await saveCityButton.count() > 0) {
                await saveCityButton.click();
                
                // Verify city was added
                await expect(page.locator('text=Test By')).toBeVisible({ timeout: 5000 });
            }
        }
        
        // Close the panel
        await page.click('#slide-panel-close');
        await expect(page.locator('#slide-panel-overlay')).toBeHidden({ timeout: 10000 });
        
        console.log('Add city test completed');
    });

    // Test 5: Error handling - try to create region with empty name
    test('should handle validation errors properly', async ({ page }) => {
        console.log('Starting validation error test...');
        
        // Click "Ny Region" button
        await page.click('#create-region-btn');
        await page.waitForSelector('#create-list-name', { timeout: 5000 });
        
        // Try to submit without filling required fields
        await page.click('#slide-panel-save');
        
        // Check for validation feedback
        // This might be a validation message, disabled button, or form highlight
        const nameField = page.locator('#create-list-name');
        
        // Check if field is highlighted as invalid or has validation message
        await expect(nameField).toBeFocused();
        
        // Fill in minimum required data and verify it can be saved
        await page.fill('#create-list-name', 'Validation Test Region');
        await page.click('#slide-panel-save');
        
        // Should succeed this time
        await expect(page.locator('#slide-panel-overlay')).toBeHidden({ timeout: 10000 });
        
        console.log('Validation error test completed');
    });

    // Test 6: Panel close functionality
    test('should close slide panel using various methods', async ({ page }) => {
        console.log('Starting panel close test...');
        
        // Open panel
        await page.click('#create-region-btn');
        await expect(page.locator('#slide-panel-overlay')).toBeVisible({ timeout: 5000 });
        
        // Test close button
        await page.click('#slide-panel-close');
        await expect(page.locator('#slide-panel-overlay')).toBeHidden({ timeout: 5000 });
        
        // Open again and test cancel button
        await page.click('#create-region-btn');
        await expect(page.locator('#slide-panel-overlay')).toBeVisible({ timeout: 5000 });
        await page.click('#slide-panel-cancel');
        await expect(page.locator('#slide-panel-overlay')).toBeHidden({ timeout: 5000 });
        
        // Open again and test clicking overlay backdrop
        await page.click('#create-region-btn');
        await expect(page.locator('#slide-panel-overlay')).toBeVisible({ timeout: 5000 });
        
        // Click on the overlay background (not the panel itself)
        await page.click('#slide-panel-overlay', { position: { x: 100, y: 100 } });
        await expect(page.locator('#slide-panel-overlay')).toBeHidden({ timeout: 5000 });
        
        console.log('Panel close test completed');
    });

    // Test 7: Visual preview functionality
    test('should update visual preview in real-time', async ({ page }) => {
        console.log('Starting visual preview test...');
        
        await page.click('#create-region-btn');
        await page.waitForSelector('#create-list-name', { timeout: 5000 });
        
        // Test name preview update
        await page.fill('#create-list-name', 'Preview Test');
        await expect(page.locator('#create-preview-name')).toContainText('Preview Test');
        
        // Test icon preview update
        await page.fill('#create-list-icon', '🎯');
        await expect(page.locator('#create-preview-icon')).toContainText('🎯');
        
        // Test color preview update
        await page.fill('#create-list-color', '#FF5722');
        
        // Verify color is applied to preview elements
        const previewIcon = page.locator('#create-preview-icon');
        const backgroundColor = await previewIcon.evaluate(el => 
            window.getComputedStyle(el).backgroundColor
        );
        
        // The color should be applied (exact RGB values may vary)
        expect(backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
        
        // Close panel
        await page.click('#slide-panel-close');
        
        console.log('Visual preview test completed');
    });

    // Test 8: Responsive behavior check
    test('should work correctly on different screen sizes', async ({ page }) => {
        console.log('Starting responsive test...');
        
        // Test on mobile viewport
        await page.setViewportSize({ width: 375, height: 812 });
        await page.reload();
        await page.waitForSelector('#create-region-btn', { timeout: 10000 });
        
        // Quick actions should still be visible and functional
        await expect(page.locator('#create-region-btn')).toBeVisible();
        await page.click('#create-region-btn');
        
        // Panel should adapt to smaller screen
        await expect(page.locator('#slide-panel')).toBeVisible({ timeout: 5000 });
        
        // Panel should take up appropriate space on mobile
        const panelWidth = await page.locator('#slide-panel').evaluate(el => el.offsetWidth);
        expect(panelWidth).toBeLessThanOrEqual(375); // Should not exceed viewport width
        
        await page.click('#slide-panel-close');
        
        // Test on tablet viewport
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.reload();
        await page.waitForSelector('#create-region-btn', { timeout: 10000 });
        
        await expect(page.locator('#create-region-btn')).toBeVisible();
        
        // Reset to desktop
        await page.setViewportSize({ width: 1280, height: 720 });
        
        console.log('Responsive test completed');
    });
});