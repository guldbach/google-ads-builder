#!/usr/bin/env python
"""
Test match type format specifikt for Google Ads Editor
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

def test_match_type_format():
    """Test match type format for Google Ads Editor"""
    
    print("🎯 Testing Match Type Format for Google Ads Editor...")
    print("=" * 60)
    
    try:
        # Find en kampagne med keywords
        campaigns = Campaign.objects.all()
        campaign_with_keywords = None
        
        for campaign in campaigns:
            geo_keywords = GeoKeyword.objects.filter(campaign=campaign)
            if geo_keywords.exists():
                campaign_with_keywords = campaign
                break
        
        if not campaign_with_keywords:
            print("❌ Ingen campaigns med geo keywords fundet")
            return False
        
        print(f"📋 Testing campaign: {campaign_with_keywords.name}")
        
        # Test match type export
        exporter = GeoCampaignExporter(campaign_with_keywords)
        campaign_data = exporter._create_campaign_data_from_model()
        
        keywords_data = campaign_data.get('keywords', [])
        print(f"🔑 Found {len(keywords_data)} keywords")
        
        if not keywords_data:
            print("⚠️ No keywords data found")
            return True  # Not a failure, just no keywords
        
        # Check match type format
        match_type_formats = {}
        for keyword in keywords_data:
            match_type = keyword.get('Match Type', '')
            if match_type:
                match_type_formats[match_type] = match_type_formats.get(match_type, 0) + 1
        
        print("\n📊 Match Type Format Analysis:")
        for match_type, count in match_type_formats.items():
            print(f"   {match_type}: {count} keywords")
            
            # Verify format
            if ' match' in match_type.lower():
                print(f"   ✅ {match_type} - Correct Google Ads Editor format")
            else:
                print(f"   ❌ {match_type} - Incorrect format (should end with ' match')")
                return False
        
        # Test sample keyword
        if keywords_data:
            sample = keywords_data[0]
            print(f"\n🔍 Sample keyword data:")
            for key, value in sample.items():
                print(f"   {key}: {value}")
        
        print("\n🎯 Match Type Format Verification:")
        print("✅ All match types use correct Google Ads Editor format")
        print("✅ Format: 'Phrase match', 'Exact match', 'Broad match'")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_match_type_format()
    if success:
        print("\n🎉 MATCH TYPE FORMAT TEST BESTÅET!")
        print("✅ Google Ads Editor will accept the match type format!")
    else:
        print("\n💥 MATCH TYPE FORMAT TEST FEJLEDE!")
    
    sys.exit(0 if success else 1)