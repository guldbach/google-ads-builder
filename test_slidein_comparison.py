import asyncio
from playwright.async_api import async_playwright
import json

async def compare_slideins():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to USP manager
        await page.goto('http://localhost:8000/usps/manager/')
        
        print("🔍 Testing USP Manager Slide-ins Comparison\n")
        
        # Test 1: Open "Ny USP" slide-in
        print("📝 Opening 'Ny USP' slide-in...")
        await page.click('#add-usp-btn')
        await page.wait_for_selector('#slide-panel', state='visible')
        
        # Capture structure of create slide-in
        create_structure = await analyze_slidein_structure(page, "CREATE")
        
        # Close slide-in
        await page.click('#slide-panel-close')
        await page.wait_for_selector('#slide-panel', state='hidden')
        
        # Test 2: Open "Rediger USP" slide-in for first USP
        print("✏️  Opening 'Rediger USP' slide-in...")
        edit_button = await page.query_selector('.edit-usp-btn')
        if edit_button:
            await edit_button.click()
            await page.wait_for_selector('#slide-panel', state='visible')
            
            # Capture structure of edit slide-in  
            edit_structure = await analyze_slidein_structure(page, "EDIT")
            
            # Close slide-in
            await page.click('#slide-panel-close')
            await page.wait_for_selector('#slide-panel', state='hidden')
            
            # Compare structures
            await compare_structures(create_structure, edit_structure)
        else:
            print("❌ No edit button found - no USPs available")
        
        await browser.close()

async def analyze_slidein_structure(page, slide_type):
    """Analyze the structure and content of a slide-in panel"""
    print(f"   Analyzing {slide_type} slide-in structure...")
    
    structure = {
        'title': await page.inner_text('#slide-panel-title'),
        'subtitle': await page.inner_text('#slide-panel-subtitle'),
        'sections': [],
        'inputs': {},
        'buttons': [],
        'hidden_fields': []
    }
    
    # Analyze all sections
    sections = await page.query_selector_all('#slide-panel-content > div > div')
    for i, section in enumerate(sections):
        section_html = await section.inner_html()
        section_text = await section.inner_text()
        structure['sections'].append({
            'index': i,
            'classes': await section.get_attribute('class'),
            'text_preview': section_text[:100] + '...' if len(section_text) > 100 else section_text
        })
    
    # Analyze all input fields
    inputs = await page.query_selector_all('#slide-panel-content input, #slide-panel-content textarea, #slide-panel-content select')
    for input_elem in inputs:
        input_id = await input_elem.get_attribute('id')
        input_type = await input_elem.get_attribute('type') or await input_elem.evaluate('el => el.tagName.toLowerCase()')
        input_value = await input_elem.get_attribute('value') or await input_elem.input_value()
        input_placeholder = await input_elem.get_attribute('placeholder')
        
        if input_id:
            structure['inputs'][input_id] = {
                'type': input_type,
                'value': input_value,
                'placeholder': input_placeholder,
                'classes': await input_elem.get_attribute('class')
            }
    
    # Analyze all buttons
    buttons = await page.query_selector_all('#slide-panel-content button')
    for button in buttons:
        button_id = await button.get_attribute('id')
        button_text = await button.inner_text()
        button_classes = await button.get_attribute('class')
        
        structure['buttons'].append({
            'id': button_id,
            'text': button_text,
            'classes': button_classes
        })
    
    # Find hidden fields
    hidden_inputs = await page.query_selector_all('#slide-panel-content input[type="hidden"]')
    for hidden in hidden_inputs:
        hidden_id = await hidden.get_attribute('id')
        hidden_value = await hidden.get_attribute('value')
        structure['hidden_fields'].append({
            'id': hidden_id,
            'value': hidden_value
        })
    
    return structure

async def compare_structures(create_structure, edit_structure):
    """Compare the two slide-in structures and report differences"""
    print("\n🔍 COMPARISON RESULTS:")
    print("=" * 50)
    
    differences = []
    
    # Compare titles
    if create_structure['title'] != edit_structure['title']:
        differences.append(f"TITLE: Create='{create_structure['title']}' vs Edit='{edit_structure['title']}'")
    
    # Compare subtitles  
    if create_structure['subtitle'] != edit_structure['subtitle']:
        differences.append(f"SUBTITLE: Create='{create_structure['subtitle']}' vs Edit='{edit_structure['subtitle']}'")
    
    # Compare number of sections
    create_sections = len(create_structure['sections'])
    edit_sections = len(edit_structure['sections'])
    if create_sections != edit_sections:
        differences.append(f"SECTIONS COUNT: Create={create_sections} vs Edit={edit_sections}")
    
    # Compare input fields
    create_inputs = set(create_structure['inputs'].keys())
    edit_inputs = set(edit_structure['inputs'].keys())
    
    missing_in_create = edit_inputs - create_inputs
    missing_in_edit = create_inputs - edit_inputs
    
    if missing_in_create:
        differences.append(f"INPUTS MISSING IN CREATE: {list(missing_in_create)}")
    if missing_in_edit:
        differences.append(f"INPUTS MISSING IN EDIT: {list(missing_in_edit)}")
    
    # Compare common inputs for differences
    common_inputs = create_inputs & edit_inputs
    for input_id in common_inputs:
        create_input = create_structure['inputs'][input_id]
        edit_input = edit_structure['inputs'][input_id]
        
        # Check for type differences
        if create_input['type'] != edit_input['type']:
            differences.append(f"INPUT TYPE DIFF [{input_id}]: Create='{create_input['type']}' vs Edit='{edit_input['type']}'")
            
        # Check for placeholder differences
        if create_input['placeholder'] != edit_input['placeholder']:
            differences.append(f"PLACEHOLDER DIFF [{input_id}]: Create='{create_input['placeholder']}' vs Edit='{edit_input['placeholder']}'")
            
        # Check for class differences  
        if create_input['classes'] != edit_input['classes']:
            differences.append(f"CSS CLASSES DIFF [{input_id}]: Different styling classes")
    
    # Compare buttons
    create_button_count = len(create_structure['buttons'])
    edit_button_count = len(edit_structure['buttons'])
    if create_button_count != edit_button_count:
        differences.append(f"BUTTON COUNT: Create={create_button_count} vs Edit={edit_button_count}")
    
    # Compare hidden fields
    create_hidden = {hf['id']: hf['value'] for hf in create_structure['hidden_fields']}
    edit_hidden = {hf['id']: hf['value'] for hf in edit_structure['hidden_fields']}
    
    if set(create_hidden.keys()) != set(edit_hidden.keys()):
        differences.append(f"HIDDEN FIELDS DIFF: Create={list(create_hidden.keys())} vs Edit={list(edit_hidden.keys())}")
    
    # Print results
    if differences:
        print("❌ DIFFERENCES FOUND:")
        for i, diff in enumerate(differences, 1):
            print(f"   {i}. {diff}")
    else:
        print("✅ NO DIFFERENCES FOUND - Slide-ins are identical!")
    
    print("\n📊 DETAILED BREAKDOWN:")
    print(f"Create slide-in: {len(create_structure['inputs'])} inputs, {len(create_structure['buttons'])} buttons")
    print(f"Edit slide-in: {len(edit_structure['inputs'])} inputs, {len(edit_structure['buttons'])} buttons")
    
    # Show specific input field comparison
    print("\n🔍 INPUT FIELDS COMPARISON:")
    all_inputs = create_inputs | edit_inputs
    for input_id in sorted(all_inputs):
        create_exists = input_id in create_inputs
        edit_exists = input_id in edit_inputs
        
        status = "✅" if create_exists and edit_exists else "❌"
        create_marker = "✅" if create_exists else "❌"
        edit_marker = "✅" if edit_exists else "❌"
        
        print(f"   {status} {input_id:<25} Create:{create_marker} Edit:{edit_marker}")

if __name__ == "__main__":
    asyncio.run(compare_slideins())