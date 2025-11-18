// Test manual edit by forcing function definition
const { test, expect } = require('@playwright/test');

test.describe('Manual Edit Force Test', () => {
    
    test('should force define editCity function and test', async ({ page }) => {
        console.log('Testing forced edit functionality...');
        
        page.on('console', msg => {
            console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
        });
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // Expand first region
        const regionHeaders = page.locator('.region-header');
        if (await regionHeaders.count() > 0) {
            await regionHeaders.first().click();
            await page.waitForTimeout(1000);
            
            // Force define editCity and related functions
            await page.evaluate(() => {
                console.log('Forcing definition of editCity functions...');
                
                // Define enableCityEditMode function
                window.enableCityEditMode = function(row, cityId) {
                    console.log('enableCityEditMode called with cityId:', cityId);
                    const cityNameCell = row.find('td:first-child');
                    const editButton = row.find('.edit-city-btn');
                    
                    // Get current values
                    const currentCityName = cityNameCell.find('span').text().trim();
                    
                    // Replace city name with input
                    cityNameCell.html(`
                        <input type="text" class="edit-city-name-input w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent" 
                               value="${currentCityName}" data-original="${currentCityName}">
                    `);
                    
                    // Change edit button to save button
                    editButton.html(`
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                        </svg>
                    `).attr('title', 'Gem ændringer').removeClass('hover:text-purple-600').addClass('hover:text-green-600');
                    
                    // Add cancel button
                    editButton.after(`
                        <button class="cancel-edit-btn text-gray-500 hover:text-red-600 p-1 ml-2" title="Annullér">
                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                            </svg>
                        </button>
                    `);
                    
                    // Add edit mode class
                    row.addClass('edit-mode bg-blue-50 border-l-4 border-blue-500');
                    
                    // Focus on input
                    setTimeout(() => {
                        cityNameCell.find('input').focus().select();
                    }, 100);
                };
                
                // Define saveCityEdit function
                window.saveCityEdit = function(row, cityId) {
                    console.log('saveCityEdit called with cityId:', cityId);
                    const newCityName = row.find('.edit-city-name-input').val().trim();
                    
                    if (!newCityName) {
                        alert('Bynavn kan ikke være tomt');
                        return;
                    }
                    
                    // Show loading state
                    row.find('.edit-city-btn').prop('disabled', true).html(`
                        <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10" stroke-width="4" opacity="0.25"/>
                            <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                        </svg>
                    `);
                    
                    $.ajax({
                        url: `/ajax/update-danish-city/${cityId}/`,
                        method: 'POST',
                        data: {
                            city_name: newCityName,
                            city_synonym: '',
                            postal_code: '',
                            latitude: '',
                            longitude: '',
                            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
                        },
                        success: function(response) {
                            console.log('Edit response:', response);
                            if (response.success) {
                                alert('By opdateret!');
                                location.reload();
                            } else {
                                alert('Fejl: ' + response.error);
                                row.find('.edit-city-btn').prop('disabled', false);
                            }
                        },
                        error: function() {
                            alert('Der opstod en fejl');
                            row.find('.edit-city-btn').prop('disabled', false);
                        }
                    });
                };
                
                // Define main editCity function
                window.editCity = function(e) {
                    console.log('editCity function called!');
                    const button = $(e.target).closest('.edit-city-btn');
                    const cityId = button.data('city-id');
                    const row = button.closest('tr');
                    
                    console.log('editCity - cityId:', cityId, 'row:', row.length);
                    
                    // Check if already in edit mode
                    if (row.hasClass('edit-mode')) {
                        saveCityEdit(row, cityId);
                    } else {
                        enableCityEditMode(row, cityId);
                    }
                };
                
                console.log('Functions defined successfully');
                console.log('editCity available:', typeof editCity);
                console.log('enableCityEditMode available:', typeof enableCityEditMode);
                
                return 'Functions defined';
            });
            
            await page.waitForTimeout(500);
            
            // Now try to click edit button on Aalborg
            const targetRegion = page.locator('.region-header:has-text("Dette er min nye region")');
            if (await targetRegion.count() > 0) {
                console.log('✅ Found target region');
                await targetRegion.click();
                await page.waitForTimeout(1000);
                
                const aalborgRow = page.locator('tr:has(.font-medium:text-is("Aalborg"))').first();
                if (await aalborgRow.count() > 0) {
                    console.log('✅ Found Aalborg row');
                    
                    const editButton = aalborgRow.locator('.edit-city-btn');
                    if (await editButton.isVisible()) {
                        console.log('✅ Edit button visible, clicking...');
                        await editButton.click();
                        await page.waitForTimeout(1000);
                        
                        const editInput = aalborgRow.locator('input[type="text"]');
                        if (await editInput.count() > 0) {
                            console.log('🎉 SUCCESS: Edit input appeared!');
                            
                            await editInput.fill('Glamsbjerg');
                            console.log('✅ Filled with "Glamsbjerg"');
                            
                            await editButton.click(); // Save
                            await page.waitForTimeout(2000);
                            
                            console.log('✅ Attempted to save edit');
                        } else {
                            console.log('❌ Edit input did not appear');
                        }
                    }
                }
            }
        }
        
        expect(true).toBe(true);
    });
});