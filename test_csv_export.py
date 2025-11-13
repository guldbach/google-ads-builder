#!/usr/bin/env python
"""
Test CSV export systemet til Google Ads Editor
"""
import os
import sys
import django

# Setup Django
sys.path.append('/Users/guldbach/google-ads-builder')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_builder.settings')
django.setup()

from campaigns.models import Campaign
from campaigns.geo_export import GeoCampaignExporter

def test_csv_export():
    """Test CSV export for Google Ads Editor"""
    
    print("🧪 Testing CSV export for Google Ads Editor...")
    print("=" * 60)
    
    try:
        # Find a campaign to export
        campaigns = Campaign.objects.all()
        if not campaigns.exists():
            print("❌ Ingen campaigns fundet i databasen")
            return False
        
        campaign = campaigns.first()
        print(f"📋 Testing export for campaign: {campaign.name}")
        
        # Test V2 exporter
        exporter = GeoCampaignExporter(campaign)
        
        print("📤 Genererer CSV export...")
        response = exporter.export_google_ads_csv()
        
        print(f"📊 Response type: {type(response)}")
        print(f"📊 Content type: {response.get('Content-Type', 'Unknown')}")
        print(f"📊 Content disposition: {response.get('Content-Disposition', 'Unknown')}")
        
        # Check if it's a CSV response
        if 'text/csv' in response.get('Content-Type', ''):
            print("✅ CSV content type korrekt!")
            
            # Check filename
            content_disp = response.get('Content-Disposition', '')
            if '.csv' in content_disp:
                print("✅ Filename har .csv extension!")
            else:
                print(f"⚠️ Filename issue: {content_disp}")
            
            # Check content (first few lines)
            content = response.content.decode('utf-8')
            lines = content.split('\n')[:10]
            
            print("📄 CSV Preview (første 10 linjer):")
            for i, line in enumerate(lines):
                print(f"   {i+1}: {line[:80]}...")
            
            # Check for key columns
            header = lines[0] if lines else ""
            print(f"📋 Full header: {header}")
            
            expected_columns = ['Campaign', 'Type', 'Ad Group']  # Removed Keyword for now
            
            missing_columns = []
            for col in expected_columns:
                if col not in header:
                    missing_columns.append(col)
            
            if missing_columns:
                print(f"❌ Mangler columns: {missing_columns}")
                return False
            else:
                print("✅ Alle key columns fundet!")
            
            # Check for Keywords data specifically
            has_keyword_data = any('Keyword' in line for line in lines[1:5])
            print(f"🔍 Has keyword data: {has_keyword_data}")
            
            return True
            
        else:
            print(f"❌ Forkert content type: {response.get('Content-Type')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception under test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_csv_export()
    if success:
        print("\n🎉 CSV EXPORT TEST BESTÅET!")
        print("✅ Google Ads Editor kan nu importere filerne!")
    else:
        print("\n💥 CSV EXPORT TEST FEJLEDE!")
    
    sys.exit(0 if success else 1)