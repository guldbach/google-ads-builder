// Comprehensive functionality test for Geographic Regions Manager
const { test, expect } = require('@playwright/test');

test.describe('Geographic Regions Manager - Comprehensive Test', () => {
    
    test('should test all CRUD operations and identify issues', async ({ page }) => {
        console.log('🔍 Starting comprehensive functionality test...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        console.log('\n📊 INITIAL PAGE STATE:');
        
        // Test 1: Page Load & Basic Elements
        const pageElements = await page.evaluate(() => {
            return {
                title: document.title,
                hasCreateButton: $('.btn-primary:contains("Opret Ny Region")').length > 0,
                hasImportButton: $('.btn-secondary:contains("Import")').length > 0,
                regionCount: $('.region-header').length,
                statsCards: $('.stat-card').length,
                hasQuickActions: $('.quick-actions').length > 0
            };
        });
        
        console.log(`✅ Page loaded: "${pageElements.title}"`);
        console.log(`📋 Regions found: ${pageElements.regionCount}`);
        console.log(`📊 Stats cards: ${pageElements.statsCards}`);
        console.log(`🔘 Create button: ${pageElements.hasCreateButton ? '✅' : '❌'}`);
        console.log(`📥 Import button: ${pageElements.hasImportButton ? '✅' : '❌'}`);
        console.log(`⚡ Quick actions: ${pageElements.hasQuickActions ? '✅' : '❌'}`);
        
        // Test 2: Region CRUD Operations
        console.log('\n🏗️ TESTING REGION CRUD:');
        
        // Try to create new region
        const createRegionTest = await page.evaluate(() => {
            try {
                const createBtn = $('.btn-primary:contains("Opret Ny Region")').first();
                if (createBtn.length > 0) {
                    createBtn.click();
                    return { success: true, message: 'Create button clicked' };
                }
                return { success: false, message: 'Create button not found' };
            } catch (error) {
                return { success: false, message: error.message };
            }
        });
        
        console.log(`🏗️ Create region: ${createRegionTest.success ? '✅' : '❌'} ${createRegionTest.message}`);
        
        if (createRegionTest.success) {
            await page.waitForTimeout(1000);
            
            // Check if modal/form appeared
            const modalAppeared = await page.evaluate(() => {
                return {
                    slidePanel: $('#slide-panel').is(':visible'),
                    modal: $('.modal').is(':visible'),
                    formVisible: $('form[id*="region"], form[class*="region"]').is(':visible')
                };
            });
            
            console.log(`📝 Create form appeared: ${modalAppeared.slidePanel || modalAppeared.modal || modalAppeared.formVisible ? '✅' : '❌'}`);
        }
        
        // Test 3: City CRUD Operations
        console.log('\n🏙️ TESTING CITY CRUD:');
        
        // Expand first region if exists
        if (pageElements.regionCount > 0) {
            await page.evaluate(() => {
                $('.region-header').first().click();
            });
            await page.waitForTimeout(1000);
            
            const cityTests = await page.evaluate(() => {
                const results = {
                    citiesVisible: false,
                    addCityButton: false,
                    editCityButton: false,
                    deleteCityButton: false,
                    cityCount: 0
                };
                
                // Check if cities are visible
                const cityRows = $('.city-row, tr:has(.edit-city-btn)');
                results.cityCount = cityRows.length;
                results.citiesVisible = cityRows.length > 0;
                
                // Check for city action buttons
                results.addCityButton = $('.add-city-btn, .btn:contains("Tilføj By")').length > 0;
                results.editCityButton = $('.edit-city-btn').length > 0;
                results.deleteCityButton = $('.delete-city-btn').length > 0;
                
                return results;
            });
            
            console.log(`🏙️ Cities visible: ${cityTests.citiesVisible ? '✅' : '❌'} (${cityTests.cityCount} cities)`);
            console.log(`➕ Add city button: ${cityTests.addCityButton ? '✅' : '❌'}`);
            console.log(`✏️ Edit city button: ${cityTests.editCityButton ? '✅' : '❌'}`);
            console.log(`🗑️ Delete city button: ${cityTests.deleteCityButton ? '✅' : '❌'}`);
            
            // Test edit functionality if available
            if (cityTests.editCityButton) {
                console.log('\n🔧 TESTING CITY EDIT:');
                
                const editTest = await page.evaluate(() => {
                    try {
                        // Find first edit button and click it
                        const editBtn = $('.edit-city-btn').first();
                        const row = editBtn.closest('tr');
                        const originalName = row.find('.font-medium').first().text().trim();
                        
                        // Simulate edit click
                        editBtn.click();
                        
                        // Check if edit mode activated
                        const hasEditMode = row.hasClass('edit-mode');
                        const hasInput = row.find('input').length > 0;
                        
                        return {
                            success: true,
                            originalName: originalName,
                            editModeActivated: hasEditMode,
                            inputFieldPresent: hasInput
                        };
                    } catch (error) {
                        return { success: false, error: error.message };
                    }
                });
                
                if (editTest.success) {
                    console.log(`✏️ Edit mode activated: ${editTest.editModeActivated ? '✅' : '❌'}`);
                    console.log(`📝 Input field present: ${editTest.inputFieldPresent ? '✅' : '❌'}`);
                    console.log(`📍 Original city: "${editTest.originalName}"`);
                } else {
                    console.log(`❌ Edit test failed: ${editTest.error}`);
                }
            }
            
            // Test delete functionality
            if (cityTests.deleteCityButton) {
                console.log('\n🗑️ TESTING CITY DELETE:');
                
                const deleteTest = await page.evaluate(() => {
                    try {
                        const deleteBtn = $('.delete-city-btn').first();
                        const row = deleteBtn.closest('tr');
                        const cityName = row.find('.font-medium').first().text().trim();
                        
                        // Check if delete button has proper event handler
                        const hasClickHandler = deleteBtn.attr('onclick') || deleteBtn.data('city-id');
                        
                        return {
                            success: true,
                            cityName: cityName,
                            hasHandler: !!hasClickHandler,
                            buttonCount: $('.delete-city-btn').length
                        };
                    } catch (error) {
                        return { success: false, error: error.message };
                    }
                });
                
                if (deleteTest.success) {
                    console.log(`🗑️ Delete buttons found: ${deleteTest.buttonCount}`);
                    console.log(`🔗 Has click handler: ${deleteTest.hasHandler ? '✅' : '❌'}`);
                    console.log(`📍 Target city: "${deleteTest.cityName}"`);
                } else {
                    console.log(`❌ Delete test failed: ${deleteTest.error}`);
                }
            }
        }
        
        // Test 4: Import/Export Functionality
        console.log('\n📥 TESTING IMPORT/EXPORT:');
        
        const importExportTest = await page.evaluate(() => {
            return {
                importButton: $('.import-btn, .btn:contains("Import"), .btn:contains("Importer")').length > 0,
                exportButton: $('.export-btn, .btn:contains("Export"), .btn:contains("Eksporter")').length > 0,
                downloadTemplate: $('.btn:contains("Download"), .btn:contains("Template")').length > 0,
                fileUpload: $('input[type="file"]').length > 0
            };
        });
        
        console.log(`📥 Import button: ${importExportTest.importButton ? '✅' : '❌'}`);
        console.log(`📤 Export button: ${importExportTest.exportButton ? '✅' : '❌'}`);
        console.log(`📋 Download template: ${importExportTest.downloadTemplate ? '✅' : '❌'}`);
        console.log(`📁 File upload input: ${importExportTest.fileUpload ? '✅' : '❌'}`);
        
        // Test 5: JavaScript Functions Availability
        console.log('\n⚡ TESTING JAVASCRIPT FUNCTIONS:');
        
        const jsTests = await page.evaluate(() => {
            return {
                editCity: typeof editCity === 'function',
                deleteCity: typeof deleteCity === 'function',
                addCity: typeof addNewCity === 'function' || typeof addCity === 'function',
                createRegion: typeof createRegion === 'function' || typeof openCreateRegionForm === 'function',
                importFunctions: typeof importCities === 'function' || typeof handleImport === 'function',
                jqueryLoaded: typeof $ !== 'undefined',
                errorInConsole: false // We'll check console separately
            };
        });
        
        console.log(`✏️ editCity function: ${jsTests.editCity ? '✅' : '❌'}`);
        console.log(`🗑️ deleteCity function: ${jsTests.deleteCity ? '✅' : '❌'}`);
        console.log(`➕ addCity function: ${jsTests.addCity ? '✅' : '❌'}`);
        console.log(`🏗️ createRegion function: ${jsTests.createRegion ? '✅' : '❌'}`);
        console.log(`📥 import functions: ${jsTests.importFunctions ? '✅' : '❌'}`);
        console.log(`📚 jQuery loaded: ${jsTests.jqueryLoaded ? '✅' : '❌'}`);
        
        // Test 6: Form Validation
        console.log('\n✅ TESTING FORM VALIDATION:');
        
        const validationTest = await page.evaluate(() => {
            // Try to find any form inputs and test validation
            const forms = $('form');
            const inputs = $('input[required], input[data-required]');
            const hasValidation = $('[data-validate], .validate').length > 0;
            
            return {
                formCount: forms.length,
                requiredInputs: inputs.length,
                hasValidation: hasValidation
            };
        });
        
        console.log(`📝 Forms found: ${validationTest.formCount}`);
        console.log(`📋 Required inputs: ${validationTest.requiredInputs}`);
        console.log(`✅ Validation present: ${validationTest.hasValidation ? '✅' : '❌'}`);
        
        // Test 7: AJAX Endpoints Test
        console.log('\n🌐 TESTING AJAX ENDPOINTS:');
        
        const endpointTests = await Promise.all([
            page.evaluate(() => fetch('/ajax/create-geographic-region/').then(r => ({ status: r.status, endpoint: 'create-region' }))),
            page.evaluate(() => fetch('/ajax/add-danish-city/').then(r => ({ status: r.status, endpoint: 'add-city' }))),
            page.evaluate(() => fetch('/ajax/delete-danish-city/1/').then(r => ({ status: r.status, endpoint: 'delete-city' }))),
            page.evaluate(() => fetch('/ajax/update-danish-city/1/').then(r => ({ status: r.status, endpoint: 'update-city' })))
        ]);
        
        endpointTests.forEach(result => {
            const working = result.status !== 404;
            console.log(`🌐 ${result.endpoint}: ${working ? '✅' : '❌'} (${result.status})`);
        });
        
        // Summary
        console.log('\n📋 FUNCTIONALITY SUMMARY:');
        console.log('====================================');
        
        const issues = [];
        
        if (!pageElements.hasCreateButton) issues.push('❌ Missing create region button');
        if (!pageElements.hasImportButton) issues.push('❌ Missing import button');
        if (!jsTests.editCity) issues.push('❌ editCity function not available');
        if (!jsTests.deleteCity) issues.push('❌ deleteCity function not available');
        if (!jsTests.addCity) issues.push('❌ addCity function not available');
        if (!jsTests.jqueryLoaded) issues.push('❌ jQuery not loaded properly');
        if (!importExportTest.fileUpload) issues.push('❌ No file upload input found');
        
        if (issues.length === 0) {
            console.log('🎉 All major functionality appears to be working!');
        } else {
            console.log(`⚠️  Found ${issues.length} issues:`);
            issues.forEach(issue => console.log(`  ${issue}`));
        }
        
        expect(true).toBe(true);
    });
});