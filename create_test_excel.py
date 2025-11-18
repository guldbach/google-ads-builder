#!/usr/bin/env python
"""
Create a real Excel file for testing Execute Import functionality
"""
import openpyxl

def create_test_excel():
    """Create a real Excel file with test keywords"""
    
    # Create workbook and worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Test Keywords"
    
    # Headers
    worksheet['A1'] = 'Søgeord'
    worksheet['B1'] = 'Match Type'
    
    # Test data
    test_data = [
        ['vvs test keyword 1', 'Broad Match'],
        ['vvs test keyword 2', 'Exact Match'], 
        ['vvs test keyword 3', 'Phrase Match'],
        ['vvs test keyword 4', 'Broad Match'],
        ['vvs test keyword 5', 'Exact Match']
    ]
    
    # Add test data
    for row_num, (keyword, match_type) in enumerate(test_data, 2):
        worksheet[f'A{row_num}'] = keyword
        worksheet[f'B{row_num}'] = match_type
    
    # Save file
    file_path = '/tmp/test_keywords_real.xlsx'
    workbook.save(file_path)
    print(f"✅ Created real Excel file: {file_path}")
    
    return file_path

if __name__ == "__main__":
    create_test_excel()