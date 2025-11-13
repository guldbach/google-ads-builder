#!/usr/bin/env python
"""
Debug kampagne 15 specifikt
"""
import os
import sys
import django
import requests

# Setup Django
sys.path.append('/Users/guldbach/google-ads-builder')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_builder.settings')
django.setup()

from campaigns.models import Campaign, GeoKeyword
from campaigns.geo_export import GeoCampaignExporter
import csv
import io

def debug_kampagne_15():
    """Debug den specifikke kampagne 15"""
    
    print("🔍 Debugging Kampagne 15...")
    print("=" * 60)
    
    try:
        # Find kampagne 15
        try:
            campaign = Campaign.objects.get(id=15)
            print(f"📋 Found campaign: {campaign.name}")
            print(f"📅 Created: {campaign.created_at if hasattr(campaign, 'created_at') else 'Unknown'}")
        except Campaign.DoesNotExist:
            print("❌ Campaign 15 not found!")
            return False
        
        # Check geo keywords
        geo_keywords = GeoKeyword.objects.filter(campaign=campaign)
        print(f"🔑 Geo Keywords: {geo_keywords.count()}")
        
        if geo_keywords.exists():
            # Use V2 exporter
            print("🚀 Using V2 GeoCampaignExporter...")
            exporter = GeoCampaignExporter(campaign)
            
            # Get campaign data structure
            campaign_data = exporter._create_campaign_data_from_model()
            
            print("🏢 Campaign Settings in Data:")
            camp_data = campaign_data.get('campaign', {})
            for key, value in camp_data.items():
                print(f"   {key}: {value}")
            
            print("\n📊 Testing actual CSV generation...")
            response = exporter.export_google_ads_csv()
            
            csv_content = response.content.decode('utf-8')
            lines = csv_content.split('\n')
            
            print(f"📄 CSV Lines: {len(lines)}")
            print(f"📄 First line (header): {lines[0]}")
            if len(lines) > 1:
                print(f"📄 Second line (campaign): {lines[1]}")
            
            # Parse and check specific values
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(csv_reader)
            
            # Find campaign row
            campaign_rows = [row for row in rows if row.get('Type') == 'Campaign']
            if campaign_rows:
                campaign_row = campaign_rows[0]
                print(f"\n🔍 Campaign Row Analysis:")
                
                checks = [
                    ('Campaign Type', 'Should be Search-only'),
                    ('Networks', 'Should be Search'),
                    ('Search Partners', 'Should be No'),
                    ('Display Network', 'Should be No'),
                    ('Political ads in EU', 'Should be No'),
                    ('Status', 'Should be Active'),
                ]
                
                for field, description in checks:
                    value = campaign_row.get(field, 'NOT_FOUND')
                    print(f"   {field}: '{value}' - {description}")
            
            # Check keyword rows
            keyword_rows = [row for row in rows if row.get('Type') == 'Keyword']
            if keyword_rows:
                print(f"\n🔑 Keywords Analysis ({len(keyword_rows)} keywords):")
                sample_kw = keyword_rows[0]
                print(f"   Sample Match Type: '{sample_kw.get('Match Type', 'NOT_FOUND')}'")
                print(f"   Sample Status: '{sample_kw.get('Status', 'NOT_FOUND')}'")
            
        else:
            print("⚠️ No geo keywords - might use legacy exporter")
            # Check if this uses legacy system
            from campaigns.geo_export import GeoCampaignManager
            try:
                response = GeoCampaignManager.export_geo_campaign(campaign, 'google_ads')
                print("📤 Used GeoCampaignManager export")
                
                csv_content = response.content.decode('utf-8')
                lines = csv_content.split('\n')
                print(f"📄 Legacy CSV Lines: {len(lines)}")
                print(f"📄 Legacy First line: {lines[0]}")
                if len(lines) > 1:
                    print(f"📄 Legacy Second line: {lines[1]}")
                
            except Exception as e:
                print(f"❌ Legacy export failed: {e}")
        
        # Test direct URL download
        print(f"\n🌐 Testing direct URL download...")
        url = "http://localhost:8000/geo-export/15/google_ads/"
        response = requests.get(url)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            lines = content.split('\n')
            print(f"📤 Direct download successful: {len(lines)} lines")
            print(f"📄 URL Header: {lines[0] if lines else 'EMPTY'}")
            if len(lines) > 1:
                print(f"📄 URL Data: {lines[1]}")
                
                # Quick check for problems
                second_line = lines[1]
                if 'Search-only' in second_line:
                    print("✅ Found Search-only in direct download")
                else:
                    print("❌ Search-only NOT found in direct download")
                    
                if ',No,' in second_line:
                    print("✅ Found No settings in direct download")
                else:
                    print("❌ No settings NOT found in direct download")
                    
                if ',Active,' in second_line:
                    print("✅ Found Active status in direct download")
                else:
                    print("❌ Active status NOT found in direct download")
            
        else:
            print(f"❌ Direct download failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    debug_kampagne_15()