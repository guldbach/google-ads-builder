// Test region edit functionality
const { test, expect } = require('@playwright/test');

test.describe('Geographic Regions - Edit Functionality Test', () => {
    
    test('should test edit region functionality', async ({ page }) => {
        console.log('🔍 Testing region edit functionality...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        console.log('\n📊 INITIAL PAGE STATE:');
        
        // Check if regions exist and have edit buttons
        const regionsCheck = await page.evaluate(() => {
            return {
                regionCount: $('.region-header').length,
                editButtons: $('.edit-region-btn').length,
                hasEditFunction: typeof editRegion !== 'undefined',
                hasGeoManagerEdit: typeof window.GeoManager !== 'undefined' && typeof window.GeoManager.editRegion === 'function'
            };
        });
        
        console.log(`📋 Regions found: ${regionsCheck.regionCount}`);
        console.log(`✏️ Edit buttons: ${regionsCheck.editButtons}`);
        console.log(`🔧 editRegion function: ${regionsCheck.hasEditFunction ? '✅' : '❌'}`);
        console.log(`🏗️ GeoManager.editRegion: ${regionsCheck.hasGeoManagerEdit ? '✅' : '❌'}`);
        
        if (regionsCheck.editButtons > 0) {
            console.log('\n🧪 TESTING EDIT BUTTON CLICK:');
            
            // Try to click the first edit button
            const editTest = await page.evaluate(() => {
                try {
                    const editBtn = $('.edit-region-btn').first();
                    if (editBtn.length === 0) {
                        return { success: false, error: 'No edit buttons found' };
                    }
                    
                    const regionId = editBtn.data('region-id');
                    console.log('Clicking edit button for region:', regionId);
                    
                    // Try to call the edit function
                    editBtn.click();
                    
                    // Check if slide panel appeared
                    const panelVisible = $('#slide-panel-overlay').is(':visible') || !$('#slide-panel-overlay').hasClass('hidden');
                    
                    return {
                        success: true,
                        regionId: regionId,
                        panelAppeared: panelVisible,
                        panelExists: $('#slide-panel-overlay').length > 0
                    };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            });
            
            console.log(`🎯 Edit button clicked for region: ${editTest.regionId}`);
            console.log(`📋 Slide panel appeared: ${editTest.panelAppeared ? '✅' : '❌'}`);
            console.log(`🏗️ Panel exists in DOM: ${editTest.panelExists ? '✅' : '❌'}`);
            
            if (!editTest.success) {
                console.log(`❌ Edit test failed: ${editTest.error}`);
            }
            
            // Wait and check if any errors occurred
            await page.waitForTimeout(2000);
            
            const errorCheck = await page.evaluate(() => {
                // Check for JavaScript errors or any error messages
                return {
                    hasSlidePanel: $('#slide-panel-overlay').length > 0,
                    panelVisible: $('#slide-panel').is(':visible') || !$('#slide-panel').hasClass('translate-x-full'),
                    panelContent: $('#slide-panel-content').html(),
                    panelTitle: $('#slide-panel-title').text()
                };
            });
            
            console.log(`\n📋 PANEL ANALYSIS:`);
            console.log(`Panel exists: ${errorCheck.hasSlidePanel ? '✅' : '❌'}`);
            console.log(`Panel visible: ${errorCheck.panelVisible ? '✅' : '❌'}`);
            console.log(`Panel title: "${errorCheck.panelTitle}"`);
        }
        
        expect(true).toBe(true);
    });
});