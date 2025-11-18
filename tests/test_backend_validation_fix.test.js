// Test to verify that the backend validation fix works
// This test will directly test the add city AJAX endpoint

const { test, expect } = require('@playwright/test');

test.describe('Backend Validation Fix Test', () => {
    
    test('should test that city creation works with only city name', async ({ page }) => {
        console.log('Testing backend validation fix...');
        
        await page.goto('http://localhost:8000/geographic-regions-manager/');
        await page.waitForLoadState('networkidle');
        
        // First, let's check if we have any existing regions
        const regionHeaders = page.locator('.region-header');
        const regionCount = await regionHeaders.count();
        
        console.log('Found regions:', regionCount);
        
        if (regionCount === 0) {
            console.log('No existing regions found. Creating one first...');
            
            // Create a region using AJAX directly
            const createRegionResponse = await page.evaluate(async () => {
                const formData = new FormData();
                formData.append('name', 'Test Region for Backend Validation');
                formData.append('description', 'Test region');
                formData.append('category', 'custom');
                formData.append('icon', '🗺️');
                formData.append('color', '#3B82F6');
                formData.append('is_active', 'true');
                
                try {
                    const response = await fetch('/ajax/create-geographic-region/', {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || 'no-csrf'
                        }
                    });
                    
                    return {
                        status: response.status,
                        data: await response.json()
                    };
                } catch (error) {
                    return { error: error.message };
                }
            });
            
            console.log('Create region response:', createRegionResponse);
            
            if (createRegionResponse.data?.success) {
                console.log('✅ Region created successfully');
                await page.reload();
                await page.waitForLoadState('networkidle');
            } else {
                console.log('❌ Failed to create region');
                return;
            }
        }
        
        // Get the first region ID
        const regionId = await page.evaluate(() => {
            const firstRegion = document.querySelector('[data-region-id]');
            return firstRegion ? firstRegion.getAttribute('data-region-id') : null;
        });
        
        console.log('Testing with region ID:', regionId);
        
        if (!regionId) {
            console.log('❌ No region ID found');
            return;
        }
        
        // Test adding a city with only city name (the simplified form)
        const addCityResponse = await page.evaluate(async (testRegionId) => {
            const formData = new FormData();
            formData.append('region_id', testRegionId);
            formData.append('city_name', 'København Test');
            // Note: NOT adding postal_code, city_synonym, or coordinates
            
            try {
                const response = await fetch('/ajax/add-danish-city/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || 'no-csrf'
                    }
                });
                
                const data = await response.json();
                return {
                    status: response.status,
                    data: data
                };
            } catch (error) {
                return { error: error.message };
            }
        }, regionId);
        
        console.log('Add city response:', addCityResponse);
        
        // Verify that the request was successful
        expect(addCityResponse.status).toBe(200);
        expect(addCityResponse.data.success).toBe(true);
        
        // Check that the response contains the expected city data
        expect(addCityResponse.data.city).toBeDefined();
        expect(addCityResponse.data.city.city_name).toBe('København Test');
        expect(addCityResponse.data.message).toContain('København Test');
        
        console.log('✅ Backend validation fix confirmed working!');
        console.log('✅ City can be created with only city_name');
        console.log('✅ No postal_code, synonym, or coordinates required');
        
        // Test that we get proper error for missing city name
        const errorResponse = await page.evaluate(async (testRegionId) => {
            const formData = new FormData();
            formData.append('region_id', testRegionId);
            // Note: NOT adding city_name - should fail
            
            try {
                const response = await fetch('/ajax/add-danish-city/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || 'no-csrf'
                    }
                });
                
                return {
                    status: response.status,
                    data: await response.json()
                };
            } catch (error) {
                return { error: error.message };
            }
        }, regionId);
        
        console.log('Error test response:', errorResponse);
        
        // Verify that missing city name gives proper error
        expect(errorResponse.data.success).toBe(false);
        expect(errorResponse.data.error).toBe('Region og bynavn er påkrævet');
        
        console.log('✅ Error handling also works correctly');
        console.log('✅ Backend validation fix is complete and working!');
    });
});