// Test for "Importer Byer" button functionality
const { test, expect } = require('@playwright/test');

test.describe('Import Button Debug', () => {
    
    test('should test import button functionality step by step', async ({ page }) => {
        console.log('Testing "Importer Byer" button...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Listen for JavaScript errors
        const consoleMessages = [];
        page.on('console', msg => {
            consoleMessages.push(`${msg.type()}: ${msg.text()}`);
        });
        
        // First expand a region to access the import button
        console.log('Step 1: Expanding region to access import button...');
        const regionHeaders = page.locator('.region-header');
        const regionCount = await regionHeaders.count();
        console.log('Found regions:', regionCount);
        
        if (regionCount > 0) {
            // Click first region to expand it
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Look for the import button
            const importButton = page.locator('.import-excel-btn');
            const importButtonCount = await importButton.count();
            console.log('Import buttons found:', importButtonCount);
            
            if (importButtonCount > 0) {
                console.log('Step 2: Testing import button attributes...');
                
                // Check button attributes
                const buttonInfo = await importButton.first().evaluate(btn => ({
                    dataRegionId: btn.getAttribute('data-region-id'),
                    title: btn.getAttribute('title'),
                    classList: Array.from(btn.classList),
                    textContent: btn.textContent.trim()
                }));
                console.log('Button info:', buttonInfo);
                
                console.log('Step 3: Testing click event...');
                
                // Listen for network requests
                const networkRequests = [];
                page.on('request', request => {
                    networkRequests.push({
                        url: request.url(),
                        method: request.method()
                    });
                });
                
                // Click the import button
                await importButton.first().click();
                await page.waitForTimeout(2000);
                
                // Check if slide panel appeared
                const slidePanel = page.locator('#slide-panel-overlay');
                const isPanelVisible = await slidePanel.isVisible();
                console.log('Slide panel visible after click:', isPanelVisible);
                
                // Check for specific panel content
                if (isPanelVisible) {
                    const panelTitle = await page.locator('#slide-panel-title').textContent();
                    console.log('Panel title:', panelTitle);
                    
                    const panelContent = await page.locator('#slide-panel-content').innerHTML();
                    console.log('Panel has content:', panelContent.length > 0);
                    
                    // Look for file input
                    const fileInput = page.locator('#region-excel-file-input');
                    const hasFileInput = await fileInput.count() > 0;
                    console.log('File input found:', hasFileInput);
                    
                    console.log('✅ Import button opens slide panel correctly!');
                } else {
                    console.log('❌ Import button did not open slide panel');
                    
                    // Check if there are JavaScript errors
                    console.log('Console messages:', consoleMessages);
                    
                    // Check if the click handler exists
                    const handlerCheck = await page.evaluate(() => {
                        const btn = document.querySelector('.import-excel-btn');
                        return {
                            hasOnclick: !!btn?.onclick,
                            hasEventListeners: btn ? 'Event listeners not directly accessible' : 'Button not found'
                        };
                    });
                    console.log('Event handler check:', handlerCheck);
                    
                    // Try to check if openImportExcelForRegion function exists
                    const functionCheck = await page.evaluate(() => {
                        return {
                            openImportExcelForRegion: typeof window.openImportExcelForRegion,
                            openImportExcelForList: typeof window.openImportExcelForList,
                            openSlidePanel: typeof window.openSlidePanel
                        };
                    });
                    console.log('Function availability:', functionCheck);
                }
                
                // Check network requests
                console.log('Network requests made:', networkRequests.length);
                if (networkRequests.length > 0) {
                    console.log('Recent requests:', networkRequests.slice(-3));
                }
                
            } else {
                console.log('❌ No import buttons found after expanding region');
            }
        } else {
            console.log('❌ No regions found to test');
        }
        
        console.log('All console messages:', consoleMessages);
    });
    
    test('should test JavaScript function definitions', async ({ page }) => {
        console.log('Testing JavaScript function definitions...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(3000); // Wait for all scripts to load
        
        const functionStatus = await page.evaluate(() => {
            const functions = {};
            
            // Check all relevant functions
            const functionNames = [
                'openImportExcelForRegion',
                'openImportExcelForList', 
                'openSlidePanel',
                'generateImportExcelForRegionContent',
                'analyzeExcelForRegion',
                'executeRegionImport',
                'toggleRegionExpansion'
            ];
            
            functionNames.forEach(name => {
                functions[name] = typeof window[name];
            });
            
            // Also check if jQuery event handlers are set up
            functions.jqueryLoaded = typeof $ !== 'undefined';
            if (typeof $ !== 'undefined') {
                functions.documentReady = 'jQuery loaded';
            }
            
            return functions;
        });
        
        console.log('Function status:', functionStatus);
        
        // Test if we can manually call the import function
        const manualTest = await page.evaluate(() => {
            try {
                if (typeof window.openImportExcelForRegion === 'function') {
                    // Create a fake event object
                    const fakeEvent = {
                        target: {
                            closest: function(selector) {
                                if (selector === '.import-excel-btn') {
                                    return {
                                        'data': function(attr) {
                                            if (attr === 'region-id') return '5';
                                            return null;
                                        },
                                        getAttribute: function(attr) {
                                            if (attr === 'data-region-id') return '5';
                                            return null;
                                        }
                                    };
                                } else if (selector === '.geographic-region-section') {
                                    return {
                                        find: function() {
                                            return {
                                                text: function() {
                                                    return {
                                                        trim: function() { return 'Test Region'; }
                                                    };
                                                }
                                            };
                                        }
                                    };
                                }
                                return null;
                            }
                        }
                    };
                    
                    window.openImportExcelForRegion(fakeEvent);
                    return { success: true, message: 'Function called successfully' };
                } else {
                    return { success: false, message: 'Function not defined' };
                }
            } catch (error) {
                return { success: false, message: 'Error: ' + error.message };
            }
        });
        
        console.log('Manual function test:', manualTest);
    });
});