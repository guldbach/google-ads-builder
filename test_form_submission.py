#!/usr/bin/env python
"""
Test form submission til geo-builder-v2 for at sikre success redirect virker
"""
import os
import sys
import django
import requests

# Setup Django
sys.path.append('/Users/guldbach/google-ads-builder')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_builder.settings')
django.setup()

def test_form_submission():
    """Test form submission til at sikre redirect til success side"""
    
    # Test data
    form_data = {
        # Step 1: Campaign settings
        'client_name': 'Test Auto Submit Company',
        'industry': '1',  # Antag første industry ID
        'website_url': 'https://testsubmit.dk',
        'service_name': 'VVS Test',
        'domain': 'testsubmit.dk',
        'budget_daily': '500',
        'budget_type': 'daily',
        'ad_rotation': 'optimize',
        'bidding_strategy': 'enhanced_cpc',
        'default_bid': '15.00',
        'default_match_type': 'phrase',
        
        # Step 2: Geography  
        'selected_cities': 'København,Aarhus',
        
        # Step 3: Headlines - kun de første 3 (required)
        'headline_1_template': 'VVS Test København',
        'headline_2_template': '5/5 Stjerner Trustpilot',
        'headline_3_template': 'Ring i dag - Gratis tilbud',
        
        # Descriptions - kun de første 2 (required)
        'description_1_template': 'Professionel VVS Test i København - Ring i dag!',
        'description_2_template': 'Erfaren VVS Test med 5/5 stjerner. Vi dækker København og omegn.',
        
        # Meta templates
        'meta_title_template': 'VVS Test {BYNAVN} - 5/5 Stjerner på Trustpilot - Ring idag',
        'meta_description_template': 'Skal du bruge en dygtig VVS Test i {BYNAVN}, vi har hjælpet mere end 500 kunder.'
    }
    
    print("🧪 Testing form submission til geo-builder-v2...")
    print("=" * 60)
    
    try:
        # First get CSRF token
        session = requests.Session()
        response = session.get('http://localhost:8000/geo-builder-v2/')
        
        if response.status_code != 200:
            print(f"❌ Kunne ikke hente form side: {response.status_code}")
            return False
        
        # Extract CSRF token
        from django.middleware.csrf import get_token
        from django.test import RequestFactory
        
        # Get CSRF token properly
        rf = RequestFactory()
        request = rf.get('/')
        csrf_token = get_token(request)
        
        form_data['csrfmiddlewaretoken'] = csrf_token
        
        print("📝 Submitting form data...")
        
        # Submit form
        response = session.post(
            'http://localhost:8000/geo-builder-v2/',
            data=form_data,
            allow_redirects=False  # Don't follow redirects so we can check them
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 302:  # Redirect
            redirect_url = response.headers.get('Location', '')
            print(f"🔄 Redirect til: {redirect_url}")
            
            if 'geo-success' in redirect_url:
                print("✅ SUCCESS: Form redirecter korrekt til geo-success siden!")
                return True
            elif 'geo-builder-v2' in redirect_url:
                print("❌ FEJL: Form redirecter tilbage til builder (validation fejl)")
                return False
            else:
                print(f"⚠️ UVENTET: Form redirecter til ukendt side: {redirect_url}")
                return False
        else:
            print(f"❌ FEJL: Form returnerede status {response.status_code} i stedet for redirect")
            if response.content:
                print("Response indhold:")
                print(response.text[:500])
            return False
            
    except Exception as e:
        print(f"❌ Exception under test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_form_submission()
    if success:
        print("\n🎉 FORM SUBMISSION TEST BESTÅET!")
    else:
        print("\n💥 FORM SUBMISSION TEST FEJLEDE!")
    
    sys.exit(0 if success else 1)