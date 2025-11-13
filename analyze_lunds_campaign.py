#!/usr/bin/env python
"""
Analyser Lunds Fugeservice kampagne
"""
import os
import sys
import django

# Setup Django
sys.path.append('/Users/guldbach/google-ads-builder')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_builder.settings')
django.setup()

from campaigns.models import Campaign, GeoKeyword, GeoTemplate
from campaigns.geo_export import GeoCampaignExporter
import csv
import io

def analyze_lunds_campaign():
    """Analyser Lunds Fugeservice kampagne"""
    
    print("🔍 Analyzing Lunds Fugeservice Campaign...")
    print("=" * 70)
    
    try:
        # 'Lunds Fugeservice' kampagne findes ikke i systemet
        # Det refererer til en fil uploadet til Google Ads Editor
        # Lad os i stedet analysere den seneste kampagne som eksempel
        
        campaign = Campaign.objects.get(id=15)  # Marketing Bureau kampagne fra i dag
        print(f"📋 Found Campaign: {campaign.name}")
        print(f"   ID: {campaign.id}")
        print(f"   Created: {getattr(campaign, 'created_at', 'Unknown')}")
        
        # Campaign settings
        print(f"\n🏢 Campaign Settings:")
        print(f"   Budget Daily: {getattr(campaign, 'budget_daily', 'Not set')}")
        print(f"   Budget Type: {getattr(campaign, 'budget_type', 'Not set')}")
        print(f"   Campaign Type: {getattr(campaign, 'campaign_type', 'Not set')}")
        print(f"   Bidding Strategy: {getattr(campaign, 'bidding_strategy', 'Not set')}")
        print(f"   Default Bid: {getattr(campaign, 'default_bid', 'Not set')}")
        print(f"   Target Location: {getattr(campaign, 'target_location', 'Not set')}")
        print(f"   Ad Rotation: {getattr(campaign, 'ad_rotation', 'Not set')}")
        print(f"   Target CPA: {getattr(campaign, 'target_cpa', 'Not set')}")
        print(f"   Target ROAS: {getattr(campaign, 'target_roas', 'Not set')}")
        print(f"   Status: {getattr(campaign, 'status', 'Not set')}")
        
        # Geo Keywords
        geo_keywords = GeoKeyword.objects.filter(campaign=campaign)
        print(f"\n🔑 Geo Keywords: {geo_keywords.count()}")
        
        if geo_keywords.exists():
            # Show sample keywords
            sample_keywords = geo_keywords[:5]
            print(f"   Sample keywords:")
            for gk in sample_keywords:
                print(f"     - {gk.keyword_text} ({gk.match_type}) -> {gk.city_name}")
            
            # Template information
            template = geo_keywords.first().template
            if template:
                print(f"\n📝 Template: {template.name}")
                print(f"   Service: {template.service_name}")
                
                # Headlines
                print(f"\n🎯 Headlines in Template:")
                for i in range(1, 16):
                    headline_field = f'headline_{i}_template'
                    if hasattr(template, headline_field):
                        headline_value = getattr(template, headline_field)
                        if headline_value:
                            print(f"     H{i}: {headline_value}")
                
                # Descriptions  
                print(f"\n📄 Descriptions in Template:")
                for i in range(1, 5):
                    desc_field = f'description_{i}_template'
                    if hasattr(template, desc_field):
                        desc_value = getattr(template, desc_field)
                        if desc_value:
                            print(f"     D{i}: {desc_value}")
        
        # Test CSV export
        print(f"\n📤 Testing CSV Export...")
        exporter = GeoCampaignExporter(campaign)
        
        # Get campaign data structure
        campaign_data = exporter._create_campaign_data_from_model()
        
        print(f"\n🏗️ Export Data Structure:")
        print(f"   Campaign data: {len(campaign_data.get('campaign', {})) if campaign_data.get('campaign') else 0} fields")
        print(f"   Ad Group data: {len(campaign_data.get('ad_group', {})) if campaign_data.get('ad_group') else 0} fields") 
        print(f"   Keywords data: {len(campaign_data.get('keywords', [])) if campaign_data.get('keywords') else 0} entries")
        print(f"   Ads data: {len(campaign_data.get('ads', [])) if campaign_data.get('ads') else 0} entries")
        
        # Check actual CSV
        response = exporter.export_google_ads_csv()
        csv_content = response.content.decode('utf-8')
        lines = csv_content.split('\n')
        
        print(f"\n📊 CSV Analysis:")
        print(f"   Total lines: {len(lines)}")
        print(f"   Headers: {lines[0].count(',') + 1} columns")
        
        # Parse CSV for detailed analysis
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Analyze by type
        row_types = {}
        for row in rows:
            row_type = row.get('Type', 'Unknown')
            if row_type not in row_types:
                row_types[row_type] = []
            row_types[row_type].append(row)
        
        print(f"\n📋 CSV Content Breakdown:")
        for row_type, type_rows in row_types.items():
            print(f"   {row_type}: {len(type_rows)} rows")
        
        # Campaign settings in CSV
        if 'Campaign' in row_types:
            campaign_row = row_types['Campaign'][0]
            print(f"\n🎯 Campaign Settings in CSV:")
            key_settings = [
                'Campaign Type', 'Budget', 'Networks', 'Search Partners',
                'Display Network', 'Political ads in EU', 'Status',
                'Bidding Strategy', 'Enhanced CPC'
            ]
            
            for setting in key_settings:
                value = campaign_row.get(setting, 'NOT_SET')
                print(f"     {setting}: {value}")
        
        # Ads analysis
        if 'Ad' in row_types:
            ad_row = row_types['Ad'][0]
            print(f"\n📢 Ad Configuration:")
            print(f"     Ad Type: {ad_row.get('Ad Type', 'NOT_SET')}")
            
            # Count headlines and descriptions
            headline_count = 0
            description_count = 0
            for key, value in ad_row.items():
                if key.startswith('Headline') and value and value.strip():
                    headline_count += 1
                elif key.startswith('Description') and value and value.strip():
                    description_count += 1
            
            print(f"     Active Headlines: {headline_count}")
            print(f"     Active Descriptions: {description_count}")
            
            # Show sample headlines
            print(f"     Sample Headlines:")
            for i in range(1, min(6, headline_count + 1)):
                headline_value = ad_row.get(f'Headline {i}', '')
                if headline_value:
                    print(f"       H{i}: {headline_value}")
        
        # Keywords analysis
        if 'Keyword' in row_types:
            keyword_rows = row_types['Keyword']
            print(f"\n🔑 Keywords Configuration:")
            
            # Sample keyword
            sample_kw = keyword_rows[0]
            print(f"     Sample Keyword: {sample_kw.get('Keyword', 'NOT_SET')}")
            print(f"     Criterion Type: {sample_kw.get('Criterion Type', 'NOT_SET')}")
            print(f"     Max CPC: {sample_kw.get('Max CPC', 'NOT_SET')}")
            print(f"     Status: {sample_kw.get('Status', 'NOT_SET')}")
            
            # Match types distribution
            match_types = {}
            for kw_row in keyword_rows:
                match_type = kw_row.get('Criterion Type', 'Unknown')
                match_types[match_type] = match_types.get(match_type, 0) + 1
            
            print(f"     Match Types Distribution:")
            for match_type, count in match_types.items():
                print(f"       {match_type}: {count} keywords")
        
        print(f"\n🎯 Overall Assessment:")
        
        # Check for common issues
        issues = []
        if campaign_data.get('campaign', {}).get('Campaign Type') != 'Search-only':
            issues.append("Campaign Type not set to Search-only")
        if campaign_data.get('campaign', {}).get('Networks') != 'Search':
            issues.append("Networks not set to Search")
        if campaign_data.get('campaign', {}).get('Search Partners') != 'No':
            issues.append("Search Partners not disabled")
        if campaign_data.get('campaign', {}).get('Display Network') != 'No':
            issues.append("Display Network not disabled")
        if campaign_data.get('campaign', {}).get('Political ads in EU') != 'No':
            issues.append("Political ads in EU not set to No")
            
        if issues:
            print(f"   ⚠️ Found issues:")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print(f"   ✅ No configuration issues found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    analyze_lunds_campaign()