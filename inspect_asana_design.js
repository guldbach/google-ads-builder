const { chromium } = require('playwright');

async function inspectAsanaDesign() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    console.log('Navigating to Asana...');
    await page.goto('https://asana.com', { waitUntil: 'domcontentloaded', timeout: 10000 });
    
    // Get computed styles for key elements
    const designAnalysis = await page.evaluate(() => {
      const results = {};
      
      // Get body styles
      const body = document.body;
      const bodyStyles = getComputedStyle(body);
      results.body = {
        fontFamily: bodyStyles.fontFamily,
        fontSize: bodyStyles.fontSize,
        lineHeight: bodyStyles.lineHeight,
        backgroundColor: bodyStyles.backgroundColor,
        color: bodyStyles.color
      };
      
      // Get header styles
      const h1 = document.querySelector('h1');
      if (h1) {
        const h1Styles = getComputedStyle(h1);
        results.h1 = {
          fontFamily: h1Styles.fontFamily,
          fontSize: h1Styles.fontSize,
          fontWeight: h1Styles.fontWeight,
          lineHeight: h1Styles.lineHeight,
          letterSpacing: h1Styles.letterSpacing,
          color: h1Styles.color
        };
      }
      
      // Get button styles
      const button = document.querySelector('button, .button, [role="button"]');
      if (button) {
        const buttonStyles = getComputedStyle(button);
        results.button = {
          fontFamily: buttonStyles.fontFamily,
          fontSize: buttonStyles.fontSize,
          fontWeight: buttonStyles.fontWeight,
          padding: buttonStyles.padding,
          backgroundColor: buttonStyles.backgroundColor,
          color: buttonStyles.color,
          borderRadius: buttonStyles.borderRadius,
          border: buttonStyles.border,
          boxShadow: buttonStyles.boxShadow
        };
      }
      
      // Get input styles
      const input = document.querySelector('input[type="text"], input[type="email"], textarea');
      if (input) {
        const inputStyles = getComputedStyle(input);
        results.input = {
          fontFamily: inputStyles.fontFamily,
          fontSize: inputStyles.fontSize,
          padding: inputStyles.padding,
          backgroundColor: inputStyles.backgroundColor,
          border: inputStyles.border,
          borderRadius: inputStyles.borderRadius,
          boxShadow: inputStyles.boxShadow
        };
      }
      
      // Get navigation styles
      const nav = document.querySelector('nav, header, .navbar');
      if (nav) {
        const navStyles = getComputedStyle(nav);
        results.nav = {
          backgroundColor: navStyles.backgroundColor,
          borderBottom: navStyles.borderBottom,
          boxShadow: navStyles.boxShadow,
          height: navStyles.height,
          padding: navStyles.padding
        };
      }
      
      // Get main content area styles
      const main = document.querySelector('main, .main-content, [role="main"]');
      if (main) {
        const mainStyles = getComputedStyle(main);
        results.main = {
          backgroundColor: mainStyles.backgroundColor,
          padding: mainStyles.padding,
          maxWidth: mainStyles.maxWidth
        };
      }
      
      // Get section styles - look for different background colors
      const sections = document.querySelectorAll('section, .section, .hero, .features');
      results.sections = [];
      sections.forEach((section, index) => {
        if (index < 5) { // Limit to first 5 sections
          const sectionStyles = getComputedStyle(section);
          results.sections.push({
            tagName: section.tagName,
            className: section.className,
            backgroundColor: sectionStyles.backgroundColor,
            padding: sectionStyles.padding,
            margin: sectionStyles.margin
          });
        }
      });
      
      return results;
    });
    
    console.log('=== ASANA DESIGN ANALYSIS ===');
    console.log('BODY:', JSON.stringify(designAnalysis.body, null, 2));
    console.log('H1:', JSON.stringify(designAnalysis.h1, null, 2));
    console.log('BUTTON:', JSON.stringify(designAnalysis.button, null, 2));
    console.log('INPUT:', JSON.stringify(designAnalysis.input, null, 2));
    console.log('NAV:', JSON.stringify(designAnalysis.nav, null, 2));
    console.log('MAIN:', JSON.stringify(designAnalysis.main, null, 2));
    console.log('SECTIONS:', JSON.stringify(designAnalysis.sections, null, 2));
    
    // Also take a screenshot for visual reference
    await page.screenshot({ 
      path: 'asana-design-reference.png', 
      fullPage: true 
    });
    console.log('Screenshot saved as asana-design-reference.png');
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
}

inspectAsanaDesign();