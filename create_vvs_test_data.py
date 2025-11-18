#!/usr/bin/env python3
"""
Create VVS test data for negative keywords manager
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_builder.settings')
django.setup()

from django.contrib.auth.models import User
from campaigns.models import Industry, NegativeKeywordList, NegativeKeyword

def create_vvs_test_data():
    print("🔧 Creating VVS Test Data for Negative Keywords")
    print("=" * 60)
    
    # Get or create VVS industry
    vvs_industry, created = Industry.objects.get_or_create(
        name="VVS",
        defaults={
            'description': "Varme, Ventilation og Sanitet"
        }
    )
    
    if created:
        print(f"✅ Created VVS Industry: {vvs_industry.name}")
    else:
        print(f"✅ Found existing VVS Industry: {vvs_industry.name}")
    
    # Get or create admin user (for created_by field)
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_user(
                username='admin',
                password='admin123',
                is_superuser=True,
                is_staff=True
            )
            print("✅ Created admin user")
    except:
        admin_user = User.objects.first()  # Fallback to any user
    
    # Create VVS negative keyword list
    vvs_list, created = NegativeKeywordList.objects.get_or_create(
        name="VVS Konkurrenter & DIY",
        defaults={
            'category': 'competitor',
            'industry': vvs_industry,
            'description': 'Negative søgeord for VVS branchen - konkurrenter og gør-det-selv relaterede søgninger',
            'is_active': True,
            'created_by': admin_user,
            'auto_apply_to_industries': []
        }
    )
    
    if created:
        print(f"✅ Created VVS Negative Keywords List: {vvs_list.name}")
    else:
        print(f"✅ Found existing VVS List: {vvs_list.name}")
    
    # VVS-specific negative keywords
    vvs_keywords = [
        {
            'keyword_text': 'gør det selv',
            'match_type': 'broad',
            'reason': 'DIY søgninger - ikke professionel VVS service'
        },
        {
            'keyword_text': 'diy',
            'match_type': 'phrase',
            'reason': 'DIY forkortelse - samme årsag som gør det selv'
        },
        {
            'keyword_text': 'billig vvs',
            'match_type': 'phrase',
            'reason': 'Prisbevidste søgere der ikke værdisætter kvalitet'
        },
        {
            'keyword_text': 'gratis',
            'match_type': 'broad',
            'reason': 'Søgere der ikke forventer at betale for professionel service'
        }
    ]
    
    # Add keywords to the list
    keywords_added = 0
    keywords_existed = 0
    
    for keyword_data in vvs_keywords:
        keyword, created = NegativeKeyword.objects.get_or_create(
            keyword_list=vvs_list,
            keyword_text=keyword_data['keyword_text'],
            defaults={
                'match_type': keyword_data['match_type']
            }
        )
        
        if created:
            print(f"   ➕ Added keyword: '{keyword_data['keyword_text']}' ({keyword_data['match_type']})")
            print(f"      Reason: {keyword_data['reason']}")
            keywords_added += 1
        else:
            keywords_existed += 1
    
    # Update keywords count
    vvs_list.update_keywords_count()
    
    print(f"\n📊 SUMMARY:")
    print(f"   Industry: {vvs_industry.name}")
    print(f"   List: {vvs_list.name}")
    print(f"   Keywords added: {keywords_added}")
    print(f"   Keywords already existed: {keywords_existed}")
    print(f"   Total keywords in list: {vvs_list.keywords_count}")
    
    print(f"\n🎯 TEST INSTRUCTIONS:")
    print(f"   1. Visit: http://localhost:8000/negative-keywords-manager/")
    print(f"   2. Use 'Filter branche' dropdown and select 'VVS'")
    print(f"   3. You should see the 'VVS Konkurrenter & DIY' list")
    print(f"   4. Click on the list to expand and see the 4 negative keywords")
    print(f"   5. Try creating a new list and select 'VVS' as the industry")
    
    print(f"\n✅ VVS Test Data Created Successfully! 🎉")

if __name__ == "__main__":
    create_vvs_test_data()