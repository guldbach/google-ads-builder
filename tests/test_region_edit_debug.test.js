// Debug test for region edit functionality
const { test, expect } = require('@playwright/test');

test.describe('Geographic Regions - Edit Debug Test', () => {
    
    test('should debug edit region functionality step by step', async ({ page }) => {
        console.log('🔍 Debug testing region edit functionality...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Wait for any JavaScript to load
        await page.waitForTimeout(2000);
        
        console.log('\n📊 DETAILED ANALYSIS:');
        
        // First, let's see what region containers look like
        const regionAnalysis = await page.evaluate(() => {
            const regionElements = $('.region-container, .geographic-region-section, [data-region-id]');
            const editButtons = $('.edit-region-btn');
            
            console.log('Region containers found:', regionElements.length);
            console.log('Edit buttons found:', editButtons.length);
            
            // Let's examine the first region structure
            const firstRegion = regionElements.first();
            const firstEditBtn = editButtons.first();
            
            return {
                regionContainers: regionElements.length,
                editButtons: editButtons.length,
                firstRegionHtml: firstRegion.length > 0 ? firstRegion.prop('outerHTML').substring(0, 500) : 'Not found',
                firstEditBtnData: firstEditBtn.length > 0 ? {
                    regionId: firstEditBtn.data('region-id'),
                    onclick: firstEditBtn.attr('onclick'),
                    classes: firstEditBtn.attr('class')
                } : 'Not found'
            };
        });
        
        console.log(`📋 Region containers: ${regionAnalysis.regionContainers}`);
        console.log(`✏️ Edit buttons: ${regionAnalysis.editButtons}`);
        console.log(`🏗️ First region HTML: ${regionAnalysis.firstRegionHtml}`);
        console.log(`🎯 First edit button data:`, regionAnalysis.firstEditBtnData);
        
        // Now let's test clicking with detailed error handling
        console.log('\n🧪 TESTING EDIT CLICK WITH ERROR HANDLING:');
        
        const editClickResult = await page.evaluate(() => {
            try {
                const editBtn = $('.edit-region-btn').first();
                if (editBtn.length === 0) {
                    return { success: false, error: 'No edit buttons found' };
                }
                
                const regionId = editBtn.data('region-id');
                console.log('Found edit button with region ID:', regionId);
                
                // Let's see if the region container exists
                const regionContainer = $(`.region-container[data-region-id="${regionId}"]`);
                console.log('Region container found:', regionContainer.length);
                
                // Also check for geographic-region-section
                const altRegionContainer = $(`.geographic-region-section[data-region-id="${regionId}"]`);
                console.log('Alt region container found:', altRegionContainer.length);
                
                // Check if the functions exist
                const hasEditRegion = typeof window.editRegion === 'function';
                const hasGeoManagerEdit = typeof window.GeoManager !== 'undefined' && typeof window.GeoManager.editRegion === 'function';
                
                console.log('editRegion function exists:', hasEditRegion);
                console.log('GeoManager.editRegion exists:', hasGeoManagerEdit);
                
                if (hasGeoManagerEdit) {
                    console.log('Calling GeoManager.editRegion...');
                    window.GeoManager.editRegion(regionId);
                    
                    // Check panel state after call
                    const panelState = {
                        overlayExists: $('#slide-panel-overlay').length > 0,
                        overlayVisible: $('#slide-panel-overlay').is(':visible') || !$('#slide-panel-overlay').hasClass('hidden'),
                        panelExists: $('#slide-panel').length > 0,
                        panelVisible: $('#slide-panel').is(':visible') || !$('#slide-panel').hasClass('translate-x-full'),
                        panelTitle: $('#slide-panel-title').text()
                    };
                    
                    return {
                        success: true,
                        regionId: regionId,
                        regionContainerFound: regionContainer.length > 0,
                        altContainerFound: altRegionContainer.length > 0,
                        panelState: panelState
                    };
                } else {
                    return { success: false, error: 'GeoManager.editRegion not available' };
                }
                
            } catch (error) {
                return { success: false, error: error.message, stack: error.stack };
            }
        });
        
        console.log(`✅ Edit click result:`, editClickResult);
        
        if (editClickResult.success) {
            console.log(`🎯 Region ID: ${editClickResult.regionId}`);
            console.log(`🏗️ Region container found: ${editClickResult.regionContainerFound}`);
            console.log(`🏗️ Alt container found: ${editClickResult.altContainerFound}`);
            console.log(`📋 Panel state:`, editClickResult.panelState);
            
            // Wait a bit for any AJAX to complete
            await page.waitForTimeout(3000);
            
            // Check final state
            const finalState = await page.evaluate(() => {
                return {
                    panelTitle: $('#slide-panel-title').text(),
                    panelContent: $('#slide-panel-content').html()?.substring(0, 200) || 'Empty',
                    overlayClasses: $('#slide-panel-overlay').attr('class'),
                    panelClasses: $('#slide-panel').attr('class')
                };
            });
            
            console.log('\n📋 FINAL PANEL STATE:');
            console.log(`Title: "${finalState.panelTitle}"`);
            console.log(`Content preview: ${finalState.panelContent}`);
            console.log(`Overlay classes: ${finalState.overlayClasses}`);
            console.log(`Panel classes: ${finalState.panelClasses}`);
        } else {
            console.log(`❌ Edit click failed: ${editClickResult.error}`);
            if (editClickResult.stack) {
                console.log(`Stack: ${editClickResult.stack}`);
            }
        }
        
        expect(true).toBe(true);
    });
});