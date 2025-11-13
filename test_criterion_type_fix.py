#!/usr/bin/env python
"""
Test Criterion Type fix for Google Ads Editor
"""
import os
import sys
import django
import requests

# Setup Django
sys.path.append('/Users/guldbach/google-ads-builder')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_builder.settings')
django.setup()

def test_criterion_type_fix():
    """Test at Criterion Type er rettet"""
    
    print("🔧 Testing Criterion Type Fix for Google Ads Editor...")
    print("=" * 65)
    
    try:
        # Test kampagne 15 direkte
        url = "http://localhost:8000/geo-export/15/google_ads/"
        print(f"📥 Downloading from: {url}")
        
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Download failed: {response.status_code}")
            return False
            
        content = response.content.decode('utf-8')
        lines = content.split('\n')
        
        if len(lines) < 2:
            print("❌ CSV has too few lines")
            return False
            
        header = lines[0]
        print(f"📋 Header check:")
        
        # Check for problematic "Match Type"
        if "Match Type" in header:
            print(f"   ❌ Found problematic 'Match Type' column")
            return False
        else:
            print(f"   ✅ No 'Match Type' column found")
            
        # Check for correct "Criterion Type"
        if "Criterion Type" in header:
            print(f"   ✅ Found correct 'Criterion Type' column")
        else:
            print(f"   ❌ Missing 'Criterion Type' column")
            return False
            
        # Find keyword line to check match type values
        keyword_lines = [line for line in lines[1:] if ',Keyword,' in line]
        if keyword_lines:
            sample_keyword = keyword_lines[0]
            parts = sample_keyword.split(',')
            
            # Find criterion type column index
            header_parts = header.split(',')
            criterion_type_index = None
            for i, col in enumerate(header_parts):
                if col == 'Criterion Type':
                    criterion_type_index = i
                    break
                    
            if criterion_type_index is not None and criterion_type_index < len(parts):
                criterion_value = parts[criterion_type_index]
                print(f"   🔍 Sample Criterion Type: '{criterion_value}'")
                
                if ' match' in criterion_value.lower():
                    print(f"   ✅ Criterion Type format correct: {criterion_value}")
                else:
                    print(f"   ❌ Criterion Type format wrong: {criterion_value}")
                    return False
            else:
                print(f"   ⚠️ Could not find Criterion Type value in data")
        
        # Check other required columns
        required_columns = [
            'Campaign', 'Campaign Type', 'Budget', 'Networks', 
            'Search Partners', 'Display Network', 'Political ads in EU'
        ]
        
        print(f"\n📊 Required columns check:")
        for col in required_columns:
            if col in header:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col} - MISSING")
                return False
        
        print(f"\n🎯 Google Ads Editor Compatibility:")
        print(f"✅ Criterion Type column: Present") 
        print(f"✅ Match Type column: Removed")
        print(f"✅ All required fields: Present")
        print(f"✅ Match type format: Correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_criterion_type_fix()
    if success:
        print(f"\n🎉 CRITERION TYPE FIX SUCCESSFUL!")
        print(f"✅ Google Ads Editor match type errors should be resolved!")
    else:
        print(f"\n❌ CRITERION TYPE FIX FAILED!")
    
    sys.exit(0 if success else 1)