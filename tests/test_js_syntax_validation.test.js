// Test to validate JavaScript syntax in the page
const { test, expect } = require('@playwright/test');

test.describe('JavaScript Syntax Validation', () => {
    
    test('should test if JavaScript has syntax errors', async ({ page }) => {
        console.log('Testing for JavaScript syntax errors...');
        
        // Capture JavaScript errors
        const jsErrors = [];
        page.on('pageerror', error => {
            jsErrors.push(error.message);
        });
        
        page.on('console', msg => {
            if (msg.type() === 'error') {
                jsErrors.push(`Console error: ${msg.text()}`);
            }
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Wait a bit for any delayed errors
        await page.waitForTimeout(3000);
        
        if (jsErrors.length > 0) {
            console.log('🔴 JavaScript Errors Found:');
            jsErrors.forEach((error, index) => {
                console.log(`${index + 1}. ${error}`);
            });
        } else {
            console.log('✅ No JavaScript errors found');
        }
        
        // Try to manually inject and test the toggle function
        const manualTest = await page.evaluate(() => {
            // Define the function manually
            window.testToggleRegionExpansion = function(regionId) {
                console.log('Manual toggle test for region:', regionId);
                
                const content = document.querySelector(`.cities-content[data-region-id="${regionId}"]`);
                const icon = document.querySelector(`.geographic-region-section[data-region-id="${regionId}"] .expansion-icon svg`);
                
                if (!content) {
                    return { error: 'Content element not found', selector: `.cities-content[data-region-id="${regionId}"]` };
                }
                
                const isVisible = content.style.display !== 'none';
                
                if (isVisible) {
                    content.style.display = 'none';
                    if (icon) icon.classList.remove('rotate-180');
                } else {
                    content.style.display = 'block';
                    if (icon) icon.classList.add('rotate-180');
                }
                
                return {
                    success: true,
                    toggled: !isVisible,
                    newState: content.style.display
                };
            };
            
            // Test with the first available region
            const firstRegion = document.querySelector('.geographic-region-section');
            if (firstRegion) {
                const regionId = firstRegion.getAttribute('data-region-id');
                return window.testToggleRegionExpansion(regionId);
            } else {
                return { error: 'No regions found' };
            }
        });
        
        console.log('Manual toggle test result:', manualTest);
        
        // Test if the issue is jQuery related
        const jqueryTest = await page.evaluate(() => {
            if (typeof $ === 'undefined') {
                return { error: 'jQuery not loaded' };
            }
            
            // Test jQuery selector for region content
            const firstRegion = document.querySelector('.geographic-region-section');
            if (firstRegion) {
                const regionId = firstRegion.getAttribute('data-region-id');
                const content = $(`.cities-content[data-region-id="${regionId}"]`);
                
                return {
                    regionId: regionId,
                    jquerySelector: `.cities-content[data-region-id="${regionId}"]`,
                    elementsFound: content.length,
                    isVisible: content.is(':visible'),
                    hasSlideDown: typeof content.slideDown === 'function'
                };
            } else {
                return { error: 'No regions found for jQuery test' };
            }
        });
        
        console.log('jQuery test result:', jqueryTest);
    });
});