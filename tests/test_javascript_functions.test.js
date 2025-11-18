// Deep dive into JavaScript function availability and errors
const { test, expect } = require('@playwright/test');

test.describe('JavaScript Function Analysis', () => {
    
    test('should analyze JavaScript function availability and errors', async ({ page }) => {
        console.log('🔍 Deep analysis of JavaScript functions...');
        
        // Listen for console errors
        const consoleErrors = [];
        page.on('console', msg => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Wait for any potential JS errors to show up
        await page.waitForTimeout(2000);
        
        console.log('\n🔍 JAVASCRIPT CONSOLE ERRORS:');
        if (consoleErrors.length > 0) {
            consoleErrors.forEach((error, index) => {
                console.log(`❌ Error ${index + 1}: ${error}`);
            });
        } else {
            console.log('✅ No console errors found');
        }
        
        // Analyze specific functions in detail
        const functionAnalysis = await page.evaluate(() => {
            const results = {
                functions: {},
                globalVariables: {},
                eventHandlers: {},
                errors: []
            };
            
            try {
                // Test for specific functions
                results.functions = {
                    editCity: {
                        exists: typeof editCity !== 'undefined',
                        type: typeof editCity,
                        callable: typeof editCity === 'function'
                    },
                    deleteCity: {
                        exists: typeof deleteCity !== 'undefined',
                        type: typeof deleteCity,
                        callable: typeof deleteCity === 'function'
                    },
                    addNewCity: {
                        exists: typeof addNewCity !== 'undefined',
                        type: typeof addNewCity,
                        callable: typeof addNewCity === 'function'
                    },
                    addCity: {
                        exists: typeof addCity !== 'undefined',
                        type: typeof addCity,
                        callable: typeof addCity === 'function'
                    },
                    createRegion: {
                        exists: typeof createRegion !== 'undefined',
                        type: typeof createRegion,
                        callable: typeof createRegion === 'function'
                    },
                    openCreateRegionForm: {
                        exists: typeof openCreateRegionForm !== 'undefined',
                        type: typeof openCreateRegionForm,
                        callable: typeof openCreateRegionForm === 'function'
                    },
                    saveCityEdit: {
                        exists: typeof saveCityEdit !== 'undefined',
                        type: typeof saveCityEdit,
                        callable: typeof saveCityEdit === 'function'
                    },
                    enableCityEditMode: {
                        exists: typeof enableCityEditMode !== 'undefined',
                        type: typeof enableCityEditMode,
                        callable: typeof enableCityEditMode === 'function'
                    }
                };
                
                // Check jQuery and other globals
                results.globalVariables = {
                    jQuery: typeof $ !== 'undefined',
                    window$: typeof window.$ !== 'undefined',
                    jQueryVersion: typeof $ !== 'undefined' ? $.fn.jquery : 'not available'
                };
                
                // Check event handlers on buttons
                results.eventHandlers = {
                    editButtons: $('.edit-city-btn').map((i, el) => {
                        const $el = $(el);
                        return {
                            hasOnclick: !!$el.attr('onclick'),
                            hasDataHandler: !!$el.data('handler'),
                            hasEventListeners: !!$el.data('events'),
                            cityId: $el.data('city-id')
                        };
                    }).get(),
                    deleteButtons: $('.delete-city-btn').map((i, el) => {
                        const $el = $(el);
                        return {
                            hasOnclick: !!$el.attr('onclick'),
                            hasDataHandler: !!$el.data('handler'),
                            hasEventListeners: !!$el.data('events'),
                            cityId: $el.data('city-id')
                        };
                    }).get(),
                    addButtons: $('.add-city-btn, .btn:contains("Tilføj")').map((i, el) => {
                        const $el = $(el);
                        return {
                            hasOnclick: !!$el.attr('onclick'),
                            hasDataHandler: !!$el.data('handler'),
                            text: $el.text().trim()
                        };
                    }).get()
                };
                
            } catch (error) {
                results.errors.push(error.message);
            }
            
            return results;
        });
        
        console.log('\n⚡ JAVASCRIPT FUNCTION ANALYSIS:');
        Object.entries(functionAnalysis.functions).forEach(([name, info]) => {
            console.log(`📝 ${name}: ${info.callable ? '✅ Available' : '❌ Missing'} (${info.type})`);
        });
        
        console.log('\n🌐 GLOBAL VARIABLES:');
        console.log(`📚 jQuery: ${functionAnalysis.globalVariables.jQuery ? '✅' : '❌'} (${functionAnalysis.globalVariables.jQueryVersion})`);
        
        console.log('\n🔗 EVENT HANDLERS ANALYSIS:');
        console.log(`✏️ Edit buttons with handlers: ${functionAnalysis.eventHandlers.editButtons.filter(btn => btn.hasOnclick).length}/${functionAnalysis.eventHandlers.editButtons.length}`);
        console.log(`🗑️ Delete buttons with handlers: ${functionAnalysis.eventHandlers.deleteButtons.filter(btn => btn.hasOnclick).length}/${functionAnalysis.eventHandlers.deleteButtons.length}`);
        console.log(`➕ Add buttons found: ${functionAnalysis.eventHandlers.addButtons.length}`);
        
        // Test button click handlers
        if (functionAnalysis.eventHandlers.editButtons.length > 0) {
            console.log('\n🧪 TESTING EDIT BUTTON FUNCTIONALITY:');
            
            const editButtonTest = await page.evaluate(() => {
                try {
                    const editBtn = $('.edit-city-btn').first();
                    const onclickAttr = editBtn.attr('onclick');
                    
                    // Try to parse the onclick if it exists
                    if (onclickAttr) {
                        return {
                            success: true,
                            onclickContent: onclickAttr,
                            functionCalled: onclickAttr.includes('editCity') ? 'editCity' : 'unknown'
                        };
                    } else {
                        // Check for jQuery event handlers
                        const events = $._data(editBtn[0], 'events');
                        return {
                            success: true,
                            onclickContent: 'No onclick attribute',
                            jqueryEvents: events ? Object.keys(events) : []
                        };
                    }
                } catch (error) {
                    return { success: false, error: error.message };
                }
            });
            
            if (editButtonTest.success) {
                console.log(`🔍 Edit button onclick: ${editButtonTest.onclickContent}`);
                if (editButtonTest.functionCalled) {
                    console.log(`📞 Function called: ${editButtonTest.functionCalled}`);
                }
                if (editButtonTest.jqueryEvents) {
                    console.log(`🎭 jQuery events: ${editButtonTest.jqueryEvents.join(', ') || 'none'}`);
                }
            }
        }
        
        // Check for missing UI elements
        console.log('\n🎨 UI ELEMENTS ANALYSIS:');
        
        const uiAnalysis = await page.evaluate(() => {
            return {
                quickActionsSection: {
                    exists: $('.quick-actions').length > 0,
                    hasCreateButton: $('.quick-actions .btn:contains("Opret"), .btn-primary:contains("Opret")').length > 0,
                    hasImportButton: $('.quick-actions .btn:contains("Import"), .btn:contains("Importer")').length > 0
                },
                statsCards: {
                    count: $('.stat-card').length,
                    hasNumbers: $('.stat-card .text-3xl, .stat-card .text-2xl').length > 0
                },
                regionHeaders: {
                    count: $('.region-header').length,
                    hasToggleButtons: $('.region-header button, .region-header .toggle').length > 0
                },
                importSection: {
                    hasFileInput: $('input[type="file"]').length > 0,
                    hasUploadForm: $('form[enctype="multipart/form-data"]').length > 0,
                    hasTemplateDownload: $('.btn:contains("Template"), .btn:contains("Download")').length > 0
                }
            };
        });
        
        console.log(`🚀 Quick actions section: ${uiAnalysis.quickActionsSection.exists ? '✅' : '❌'}`);
        console.log(`📊 Stats cards with data: ${uiAnalysis.statsCards.hasNumbers ? '✅' : '❌'} (${uiAnalysis.statsCards.count} cards)`);
        console.log(`📋 Region toggle functionality: ${uiAnalysis.regionHeaders.hasToggleButtons ? '✅' : '❌'}`);
        console.log(`📁 File upload capability: ${uiAnalysis.importSection.hasFileInput ? '✅' : '❌'}`);
        console.log(`📋 Template download: ${uiAnalysis.importSection.hasTemplateDownload ? '✅' : '❌'}`);
        
        if (functionAnalysis.errors.length > 0) {
            console.log('\n❌ JAVASCRIPT ERRORS:');
            functionAnalysis.errors.forEach(error => console.log(`  ${error}`));
        }
        
        expect(true).toBe(true);
    });
});