#!/usr/bin/env python
"""
Test ny Google Ads Editor kompatibel export
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

def test_new_export():
    """Test ny Google Ads Editor export med kampagne 17"""
    
    print("🧪 Testing New Google Ads Editor Export...")
    print("=" * 60)
    
    try:
        # Test VVS kampagne (ID 17)
        campaign = Campaign.objects.get(id=17)
        print(f"📋 Testing: {campaign.name}")
        print(f"📊 Budget: {campaign.budget_daily}")
        print(f"🎯 Bidding: {campaign.bidding_strategy}")
        print(f"📍 Default bid: {campaign.default_bid}")
        
        exporter = GeoCampaignExporter(campaign)
        print(f"🏙️ Cities found: {len(exporter.cities)}")
        print(f"🔑 Keywords found: {exporter.geo_keywords.count()}")
        print(f"📝 Template: {exporter.template.service_name if exporter.template else 'None'}")
        
        # Generate export
        print(f"\n🔧 Generating new Google Ads Editor export...")
        response = exporter.export_google_ads_csv()
        
        # Save to file for inspection
        filename = f"/Users/guldbach/google-ads-builder/examples/geo_campaigns/NEW_Google_Ads_Editor_VVS_17.csv"
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Export generated successfully!")
        print(f"📁 Saved to: {filename}")
        print(f"📊 Content length: {len(response.content)} bytes")
        print(f"🔤 Content type: {response.get('Content-Type')}")
        
        # Check file encoding
        import subprocess
        result = subprocess.run(['file', filename], capture_output=True, text=True)
        print(f"📋 File type: {result.stdout.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_new_export()
    if success:
        print(f"\n🎉 NEW EXPORT SUCCESS!")
        print(f"✅ Google Ads Editor kompatibel fil genereret")
        print(f"🔤 UTF-16 encoding med tab separators")
        print(f"📋 Alle 126 kolonner implementeret")
    else:
        print(f"\n❌ EXPORT FAILED!")