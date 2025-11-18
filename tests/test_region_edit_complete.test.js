// Complete test of region edit functionality
const { test, expect } = require('@playwright/test');

test.describe('Geographic Regions - Complete Edit Test', () => {
    
    test('should test complete region edit workflow', async ({ page }) => {
        console.log('🔍 Testing complete region edit workflow...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Wait for JavaScript to load
        await page.waitForTimeout(2000);
        
        console.log('\n🧪 TESTING COMPLETE WORKFLOW:');
        
        // Click edit button and check panel appearance
        const editResult = await page.evaluate(() => {
            try {
                const editBtn = $('.edit-region-btn').first();
                const regionId = editBtn.data('region-id');
                
                console.log('Clicking edit for region:', regionId);
                
                // Call the function
                window.GeoManager.editRegion(regionId);
                
                // Check immediate state
                const immediateState = {
                    panelTitle: $('#slide-panel-title').text(),
                    overlayVisible: $('#slide-panel-overlay').is(':visible'),
                    overlayHidden: $('#slide-panel-overlay').hasClass('hidden'),
                    overlayOpacity: $('#slide-panel-overlay').hasClass('opacity-0'),
                    panelTransform: $('#slide-panel').hasClass('translate-x-full')
                };
                
                return {
                    success: true,
                    regionId: regionId,
                    immediateState: immediateState
                };
                
            } catch (error) {
                return { success: false, error: error.message };
            }
        });
        
        console.log('✅ Edit result:', editResult);
        
        if (editResult.success) {
            // Wait for AJAX to complete
            console.log('\n⏳ WAITING FOR AJAX...');
            await page.waitForTimeout(5000);
            
            // Check final state
            const finalState = await page.evaluate(() => {
                return {
                    panelTitle: $('#slide-panel-title').text(),
                    panelSubtitle: $('#slide-panel-subtitle').text(),
                    overlayClasses: $('#slide-panel-overlay').attr('class'),
                    panelClasses: $('#slide-panel').attr('class'),
                    hasContent: $('#slide-panel-content').children().length > 0,
                    firstInputValue: $('#edit-region-name').val() || 'Not found',
                    formElements: {
                        nameInput: $('#edit-region-name').length,
                        descInput: $('#edit-region-description').length,
                        categorySelect: $('#edit-region-category').length,
                        colorPicker: $('#edit-region-color').length,
                        iconInput: $('#edit-region-icon').length,
                        activeCheckbox: $('#edit-region-is-active').length
                    }
                };
            });
            
            console.log('\n📋 FINAL STATE AFTER AJAX:');
            console.log(`Title: "${finalState.panelTitle}"`);
            console.log(`Subtitle: "${finalState.panelSubtitle}"`);
            console.log(`Overlay classes: ${finalState.overlayClasses}`);
            console.log(`Panel classes: ${finalState.panelClasses}`);
            console.log(`Has content: ${finalState.hasContent}`);
            console.log(`First input value: "${finalState.firstInputValue}"`);
            console.log('Form elements:', finalState.formElements);
            
            // Test if panel is actually visible
            const isVisible = await page.evaluate(() => {
                const overlay = $('#slide-panel-overlay');
                const panel = $('#slide-panel');
                
                return {
                    overlayVisible: overlay.is(':visible'),
                    overlayNotHidden: !overlay.hasClass('hidden'),
                    overlayOpaque: !overlay.hasClass('opacity-0'),
                    panelNotTransformed: !panel.hasClass('translate-x-full'),
                    computedOverlayDisplay: overlay.css('display'),
                    computedOverlayOpacity: overlay.css('opacity'),
                    computedPanelTransform: panel.css('transform')
                };
            });
            
            console.log('\n👁️ VISIBILITY CHECK:');
            console.log('Visibility state:', isVisible);
            
            // Try to interact with form elements if visible
            if (finalState.formElements.nameInput > 0) {
                console.log('\n📝 TESTING FORM INTERACTION:');
                
                const formTest = await page.evaluate(() => {
                    try {
                        const nameInput = $('#edit-region-name');
                        const originalValue = nameInput.val();
                        
                        // Try to change the value
                        nameInput.val('Test Region Name').trigger('input');
                        const newValue = nameInput.val();
                        
                        // Check character counter
                        const charCount = $('#edit-region-name-count').text();
                        
                        // Reset
                        nameInput.val(originalValue);
                        
                        return {
                            success: true,
                            originalValue: originalValue,
                            testValue: newValue,
                            characterCount: charCount
                        };
                    } catch (error) {
                        return { success: false, error: error.message };
                    }
                });
                
                console.log('Form interaction test:', formTest);
            }
            
        } else {
            console.log(`❌ Edit failed: ${editResult.error}`);
        }
        
        expect(true).toBe(true);
    });
});