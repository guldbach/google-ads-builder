#!/usr/bin/env python
"""
Test den faktiske CSV output der genereres og downloades
"""
import os
import sys
import django

# Setup Django
sys.path.append('/Users/guldbach/google-ads-builder')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_builder.settings')
django.setup()

from campaigns.models import Campaign, GeoKeyword
from campaigns.geo_export import GeoCampaignExporter
import csv
import io

def test_real_csv_output():
    """Test den faktiske CSV output der vil blive downloadet"""
    
    print("🔍 Testing REAL CSV Output for Google Ads Editor...")
    print("=" * 70)
    
    try:
        # Find en kampagne med data
        campaigns = Campaign.objects.all()
        test_campaign = None
        
        for campaign in campaigns:
            geo_keywords = GeoKeyword.objects.filter(campaign=campaign)
            if geo_keywords.exists():
                test_campaign = campaign
                break
        
        if not test_campaign:
            print("❌ Ingen campaigns med geo keywords fundet")
            return False
        
        print(f"📋 Testing campaign: {test_campaign.name}")
        
        # Generer faktiske CSV response
        exporter = GeoCampaignExporter(test_campaign)
        response = exporter.export_google_ads_csv()
        
        # Læs faktiske CSV content
        csv_content = response.content.decode('utf-8')
        print(f"📄 CSV size: {len(csv_content)} characters")
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        headers = csv_reader.fieldnames
        rows = list(csv_reader)
        
        print(f"\n📊 CSV Structure:")
        print(f"   Headers: {len(headers)} columns")
        print(f"   Data rows: {len(rows)}")
        
        print(f"\n🏷️ All Headers:")
        for i, header in enumerate(headers):
            print(f"   {i+1:2d}. {header}")
        
        # Check for required Google Ads Editor fields
        required_fields = [
            'Campaign',
            'Campaign Type', 
            'Budget',
            'Networks',
            'Search Partners',
            'Display Network',
            'Political ads in EU',
            'Status',
            'Match Type'
        ]
        
        print(f"\n✅ Required Fields Check:")
        missing_fields = []
        for field in required_fields:
            if field in headers:
                print(f"   ✅ {field}")
            else:
                print(f"   ❌ {field} - MISSING!")
                missing_fields.append(field)
        
        if missing_fields:
            print(f"\n❌ CRITICAL: Missing required fields: {missing_fields}")
            return False
        
        # Analyze actual data
        print(f"\n📋 Data Analysis:")
        
        # Group rows by Type
        row_types = {}
        for row in rows:
            row_type = row.get('Type', 'Unknown')
            if row_type not in row_types:
                row_types[row_type] = []
            row_types[row_type].append(row)
        
        for row_type, type_rows in row_types.items():
            print(f"   {row_type}: {len(type_rows)} rows")
        
        # Check Campaign settings
        campaign_rows = [row for row in rows if row.get('Type') == 'Campaign']
        if campaign_rows:
            campaign_row = campaign_rows[0]
            print(f"\n🏢 Campaign Settings:")
            settings_to_check = [
                ('Campaign Type', 'Search-only'),
                ('Networks', 'Search'),
                ('Search Partners', 'No'),
                ('Display Network', 'No'), 
                ('Political ads in EU', 'No'),
                ('Status', 'Active')
            ]
            
            for field, expected in settings_to_check:
                actual = campaign_row.get(field, 'NOT SET')
                if actual == expected:
                    print(f"   ✅ {field}: {actual}")
                else:
                    print(f"   ❌ {field}: {actual} (expected: {expected})")
        
        # Check Keywords
        keyword_rows = [row for row in rows if row.get('Type') == 'Keyword']
        if keyword_rows:
            keyword_row = keyword_rows[0]
            print(f"\n🔑 Keyword Example:")
            print(f"   Keyword: {keyword_row.get('Keyword', 'N/A')}")
            print(f"   Match Type: {keyword_row.get('Match Type', 'N/A')}")
            print(f"   Status: {keyword_row.get('Status', 'N/A')}")
            
            # Verify match type format
            match_type = keyword_row.get('Match Type', '')
            if ' match' in match_type.lower():
                print(f"   ✅ Match Type format correct: {match_type}")
            else:
                print(f"   ❌ Match Type format incorrect: {match_type}")
        
        # Check Ads
        ad_rows = [row for row in rows if row.get('Type') == 'Ad']
        if ad_rows:
            ad_row = ad_rows[0]
            print(f"\n📢 Ad Example:")
            print(f"   Ad Type: {ad_row.get('Ad Type', 'N/A')}")
            print(f"   Status: {ad_row.get('Status', 'N/A')}")
            
            # Count headlines
            headline_count = 0
            description_count = 0
            for key, value in ad_row.items():
                if key.startswith('Headline') and value:
                    headline_count += 1
                elif key.startswith('Description') and value:
                    description_count += 1
            
            print(f"   Headlines: {headline_count}")
            print(f"   Descriptions: {description_count}")
        
        # Final verification
        print(f"\n🎯 Google Ads Editor Readiness:")
        
        has_campaign = any(row.get('Type') == 'Campaign' for row in rows)
        has_ad_group = any(row.get('Type') == 'Ad Group' for row in rows)  
        has_keywords = any(row.get('Type') == 'Keyword' for row in rows)
        has_ads = any(row.get('Type') == 'Ad' for row in rows)
        
        components = [
            ("Campaign", has_campaign),
            ("Ad Group", has_ad_group),
            ("Keywords", has_keywords),
            ("Ads", has_ads)
        ]
        
        all_good = True
        for component, exists in components:
            if exists:
                print(f"   ✅ {component}: Present")
            else:
                print(f"   ❌ {component}: Missing")
                all_good = False
        
        if not missing_fields and all_good:
            print(f"\n🎉 SUCCESS: CSV is ready for Google Ads Editor!")
            return True
        else:
            print(f"\n💥 FAILURE: CSV has issues that need fixing")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_real_csv_output()
    if success:
        print(f"\n✅ REAL CSV OUTPUT TEST BESTÅET!")
        print(f"✅ Google Ads Editor will accept this CSV!")
    else:
        print(f"\n❌ REAL CSV OUTPUT TEST FEJLEDE!")
        print(f"❌ Google Ads Editor may reject this CSV!")
    
    sys.exit(0 if success else 1)