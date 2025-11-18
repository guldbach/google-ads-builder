// Geographic Regions Test Helpers
// Utility functions for Playwright tests

/**
 * Helper functions for Geographic Regions Manager testing
 */

class RegionTestHelpers {
    constructor(page) {
        this.page = page;
    }

    /**
     * Navigate to Geographic Regions Manager and wait for it to load
     */
    async navigateToRegionsManager() {
        await this.page.goto('http://localhost:8000/geographic-regions-manager/');
        await this.page.waitForSelector('#create-region-btn', { timeout: 10000 });
        
        // Ensure page is fully loaded by checking for statistics cards
        await this.page.waitForSelector('text=Total Lister', { timeout: 5000 });
    }

    /**
     * Open the create region slide panel
     */
    async openCreateRegionPanel() {
        await this.page.click('#create-region-btn');
        await this.page.waitForSelector('#slide-panel-overlay', { state: 'visible', timeout: 5000 });
        await this.page.waitForSelector('#create-list-name', { timeout: 3000 });
    }

    /**
     * Fill out the region creation form
     * @param {Object} regionData - The region data to fill
     */
    async fillRegionForm(regionData = {}) {
        const defaultData = {
            name: `Test Region ${Date.now()}`,
            description: 'Test region created by Playwright',
            category: 'custom',
            icon: '🧪',
            color: '#22C55E',
            ...regionData
        };

        await this.page.fill('#create-list-name', defaultData.name);
        await this.page.fill('#create-list-description', defaultData.description);
        await this.page.selectOption('#create-list-category', defaultData.category);
        await this.page.fill('#create-list-icon', defaultData.icon);
        await this.page.fill('#create-list-color', defaultData.color);

        return defaultData;
    }

    /**
     * Save the region form and wait for completion
     */
    async saveRegionForm() {
        await this.page.click('#slide-panel-save');
        await this.page.waitForSelector('#slide-panel-overlay', { state: 'hidden', timeout: 10000 });
        
        // Wait a bit for the page to update
        await this.page.waitForTimeout(1000);
    }

    /**
     * Close the slide panel using various methods
     * @param {string} method - 'close', 'cancel', or 'backdrop'
     */
    async closeSlidePanel(method = 'close') {
        switch (method) {
            case 'close':
                await this.page.click('#slide-panel-close');
                break;
            case 'cancel':
                await this.page.click('#slide-panel-cancel');
                break;
            case 'backdrop':
                await this.page.click('#slide-panel-overlay', { position: { x: 100, y: 100 } });
                break;
            default:
                throw new Error(`Unknown close method: ${method}`);
        }
        
        await this.page.waitForSelector('#slide-panel-overlay', { state: 'hidden', timeout: 5000 });
    }

    /**
     * Create a complete region for testing
     * @param {Object} regionData - Optional region data override
     * @returns {Object} - The created region data
     */
    async createTestRegion(regionData = {}) {
        await this.openCreateRegionPanel();
        const data = await this.fillRegionForm(regionData);
        await this.saveRegionForm();
        return data;
    }

    /**
     * Find a region card by name
     * @param {string} regionName - Name of the region to find
     * @returns {Object} - Playwright locator for the region card
     */
    findRegionCard(regionName) {
        return this.page.locator('.bg-white.rounded-2xl').filter({ hasText: regionName });
    }

    /**
     * Open region for editing
     * @param {string} regionName - Name of the region to edit
     */
    async openRegionForEdit(regionName) {
        const regionCard = this.findRegionCard(regionName);
        await regionCard.locator('button').filter({ hasText: 'Redigér' }).click();
        await this.page.waitForSelector('#slide-panel-overlay', { state: 'visible', timeout: 5000 });
        await this.page.waitForSelector('#edit-list-name', { timeout: 3000 });
    }

    /**
     * Delete a region
     * @param {string} regionName - Name of the region to delete
     */
    async deleteRegion(regionName) {
        const regionCard = this.findRegionCard(regionName);
        await regionCard.locator('button').filter({ hasText: 'Slet' }).click();
        
        // Handle confirmation dialog if it exists
        try {
            await this.page.waitForSelector('text=Er du sikker', { timeout: 2000 });
            await this.page.click('button:has-text("Slet")');
        } catch (e) {
            // No confirmation dialog, deletion was immediate
        }
        
        // Wait for the region to disappear
        await this.page.waitForFunction(
            (name) => !document.querySelector(`[data-testid="region-card"]:has-text("${name}")`) ||
                      document.querySelector(`[data-testid="region-card"]:has-text("${name}")`) === null,
            regionName,
            { timeout: 5000 }
        );
    }

    /**
     * Add a city to a region
     * @param {Object} cityData - City information
     */
    async addCityToCurrentRegion(cityData = {}) {
        const defaultCityData = {
            name: `Test City ${Date.now()}`,
            postalCode: '1234',
            synonym: '',
            notes: 'Test city for Playwright',
            ...cityData
        };

        // Look for add city button
        const addCityButton = this.page.locator('button').filter({ hasText: /tilføj.*by/i });
        
        if (await addCityButton.count() > 0) {
            await addCityButton.first().click();
            
            // Fill city form
            await this.page.fill('input[placeholder*="by"]', defaultCityData.name);
            await this.page.fill('input[placeholder*="postnummer"]', defaultCityData.postalCode);
            
            if (defaultCityData.synonym) {
                await this.page.fill('input[placeholder*="synonym"]', defaultCityData.synonym);
            }
            
            if (defaultCityData.notes) {
                await this.page.fill('textarea[placeholder*="note"]', defaultCityData.notes);
            }
            
            // Save city
            const saveCityButton = this.page.locator('button').filter({ hasText: /gem.*by/i });
            if (await saveCityButton.count() > 0) {
                await saveCityButton.click();
                await this.page.waitForTimeout(500); // Allow time for city to be added
            }
        }

        return defaultCityData;
    }

    /**
     * Verify region exists in the list
     * @param {string} regionName - Name of the region to verify
     */
    async verifyRegionExists(regionName) {
        await this.page.waitForSelector(`text=${regionName}`, { timeout: 10000 });
        return await this.page.locator(`text=${regionName}`).isVisible();
    }

    /**
     * Verify region does not exist in the list
     * @param {string} regionName - Name of the region to verify absence
     */
    async verifyRegionNotExists(regionName) {
        try {
            await this.page.waitForSelector(`text=${regionName}`, { timeout: 2000 });
            return false; // If found, verification failed
        } catch (e) {
            return true; // Not found, verification passed
        }
    }

    /**
     * Get region statistics from the dashboard
     * @returns {Object} - Statistics data
     */
    async getRegionStatistics() {
        const totalRegions = await this.page.locator('text=Total Lister').locator('..').locator('.text-3xl').textContent();
        const activeRegions = await this.page.locator('text=Aktive Lister').locator('..').locator('.text-3xl').textContent();
        
        return {
            total: parseInt(totalRegions) || 0,
            active: parseInt(activeRegions) || 0
        };
    }

    /**
     * Wait for loading states to complete
     */
    async waitForLoadingComplete() {
        // Wait for any loading spinners or disabled buttons to disappear
        try {
            await this.page.waitForSelector('.loading', { state: 'detached', timeout: 5000 });
        } catch (e) {
            // No loading state found, continue
        }
        
        try {
            await this.page.waitForSelector('button:disabled', { state: 'detached', timeout: 5000 });
        } catch (e) {
            // No disabled buttons found, continue
        }
    }

    /**
     * Take screenshot for debugging
     * @param {string} name - Screenshot name
     */
    async takeDebugScreenshot(name) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        await this.page.screenshot({ 
            path: `/tmp/playwright-debug-${name}-${timestamp}.png`,
            fullPage: true 
        });
    }

    /**
     * Check if slide panel is open
     */
    async isPanelOpen() {
        return await this.page.locator('#slide-panel-overlay').isVisible();
    }

    /**
     * Check if slide panel is closed
     */
    async isPanelClosed() {
        return await this.page.locator('#slide-panel-overlay').isHidden();
    }

    /**
     * Verify visual preview updates in real-time
     * @param {Object} testData - Data to test preview with
     */
    async verifyVisualPreview(testData = {}) {
        const defaultTest = {
            name: 'Preview Test',
            icon: '🎯',
            color: '#FF5722',
            ...testData
        };

        // Test name preview
        await this.page.fill('#create-list-name', defaultTest.name);
        await this.page.waitForFunction(
            (expectedName) => document.querySelector('#create-preview-name')?.textContent?.includes(expectedName),
            defaultTest.name,
            { timeout: 3000 }
        );

        // Test icon preview
        await this.page.fill('#create-list-icon', defaultTest.icon);
        await this.page.waitForFunction(
            (expectedIcon) => document.querySelector('#create-preview-icon')?.textContent?.includes(expectedIcon),
            defaultTest.icon,
            { timeout: 3000 }
        );

        // Test color preview
        await this.page.fill('#create-list-color', defaultTest.color);
        await this.page.waitForTimeout(500); // Allow color changes to apply

        return true;
    }
}

// Export the helper class
module.exports = { RegionTestHelpers };