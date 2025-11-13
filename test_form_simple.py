#!/usr/bin/env python
"""
Simple test af create_geo_campaign_v2 funktionalitet
"""
import os
import sys
import django

# Setup Django
sys.path.append('/Users/guldbach/google-ads-builder')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_builder.settings')
django.setup()

from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User
from django.http import HttpRequest
from campaigns.views import create_geo_campaign_v2
from campaigns.models import Industry

def test_form_processing():
    """Test form processing med Django test client"""
    
    print("🧪 Testing create_geo_campaign_v2 form processing...")
    print("=" * 60)
    
    try:
        # Ensure we have at least one industry
        industry, created = Industry.objects.get_or_create(
            name='Test Industry',
            defaults={'description': 'Test industry for validation'}
        )
        
        # Create a test request
        rf = RequestFactory()
        
        # Test data
        post_data = {
            # Step 1: Campaign settings
            'client_name': 'Test Form Company',
            'industry': str(industry.id),
            'website_url': 'https://testform.dk',
            'service_name': 'Test Service',
            'domain': 'testform.dk',
            'budget_daily': '500',
            'budget_type': 'daily',
            'ad_rotation': 'optimize', 
            'bidding_strategy': 'enhanced_cpc',
            'default_bid': '15.00',
            'default_match_type': 'phrase',
            
            # Step 2: Geography  
            'selected_cities': 'København,Aarhus',
            
            # Step 3: Headlines - kun de første 3 (required)
            'headline_1_template': '{SERVICE} {BYNAVN}',
            'headline_2_template': '5/5 Stjerner Trustpilot',
            'headline_3_template': 'Ring i dag - Gratis tilbud',
            
            # Descriptions - kun de første 2 (required)
            'description_1_template': 'Professionel {SERVICE} i {BYNAVN} - Ring i dag!',
            'description_2_template': 'Erfaren {SERVICE} med 5/5 stjerner. Vi dækker {BYNAVN} og omegn.',
            
            # Meta templates
            'meta_title_template': '{SERVICE} {BYNAVN} - 5/5 Stjerner på Trustpilot - Ring idag',
            'meta_description_template': 'Skal du bruge en dygtig {SERVICE} i {BYNAVN}, vi har hjælpet mere end 500 kunder.'
        }
        
        request = rf.post('/geo-builder-v2/', data=post_data)
        
        # Add a user to the request (required for campaign creation)
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        request.user = user
        
        print("📝 Calling create_geo_campaign_v2 view...")
        
        # Call the view function directly
        response = create_geo_campaign_v2(request)
        
        print(f"📊 Response status: {response.status_code}")
        
        if hasattr(response, 'url'):
            print(f"🔄 Redirect URL: {response.url}")
            
            if 'geo-success' in response.url:
                print("✅ SUCCESS: View redirecter korrekt til geo-success siden!")
                return True
            elif 'geo-builder-v2' in response.url:
                print("❌ FEJL: View redirecter tilbage til builder (validation fejl)")
                return False
            else:
                print(f"⚠️ UVENTET: View redirecter til: {response.url}")
                return False
        else:
            print("❌ FEJL: Ingen redirect response")
            if hasattr(response, 'content'):
                print("Response content preview:")
                print(str(response.content)[:300])
            return False
            
    except Exception as e:
        print(f"❌ Exception under test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_form_processing()
    if success:
        print("\n🎉 FORM PROCESSING TEST BESTÅET!")
    else:
        print("\n💥 FORM PROCESSING TEST FEJLEDE!")
    
    sys.exit(0 if success else 1)