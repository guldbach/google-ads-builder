#!/usr/bin/env python
"""
Test actual Excel download and verify content
"""
import requests
import pandas as pd
import io

def test_excel_download():
    """Download and inspect the actual Excel file"""
    
    print("🔗 Testing actual Excel download from browser...")
    
    try:
        # Find the campaign ID (should be 7 based on the logs)
        campaign_id = 7
        download_url = f"http://localhost:8000/geo-export/{campaign_id}/google_ads/"
        
        print(f"📥 Downloading: {download_url}")
        
        # Download the file
        response = requests.get(download_url)
        
        if response.status_code != 200:
            print(f"❌ Download failed: HTTP {response.status_code}")
            return False
        
        print(f"✅ Download successful: {len(response.content)} bytes")
        
        # Read Excel file
        excel_data = io.BytesIO(response.content)
        
        # Read all sheets
        excel_file = pd.ExcelFile(excel_data)
        sheet_names = excel_file.sheet_names
        
        print(f"📊 Excel sheets: {sheet_names}")
        
        # Read Campaigns sheet
        campaigns_df = pd.read_excel(excel_data, sheet_name='Campaigns')
        print(f"\n📋 Campaigns Sheet:")
        print(f"   Campaign Name: {campaigns_df['Campaign'].iloc[0]}")
        print(f"   Budget: {campaigns_df['Budget'].iloc[0]}")
        print(f"   Bidding Strategy: {campaigns_df['Bidding Strategy'].iloc[0]}")
        
        # Read Keywords sheet
        keywords_df = pd.read_excel(excel_data, sheet_name='Keywords')
        print(f"\n🔑 Keywords Sheet:")
        print(f"   Total keywords: {len(keywords_df)}")
        print(f"   Sample keyword: {keywords_df['Keyword'].iloc[0]}")
        print(f"   Match type: {keywords_df['Match Type'].iloc[0]}")
        print(f"   Max CPC: {keywords_df['Max CPC'].iloc[0]}")
        print(f"   Final URL: {keywords_df['Final URL'].iloc[0]}")
        
        # Read Ads sheet
        ads_df = pd.read_excel(excel_data, sheet_name='Ads')
        print(f"\n📢 Ads Sheet:")
        print(f"   Headlines: {ads_df['Headline 1'].iloc[0]}")
        print(f"   Description: {ads_df['Description 1'].iloc[0]}")
        
        # Verify it's not dummy data
        campaign_name = campaigns_df['Campaign'].iloc[0]
        budget = campaigns_df['Budget'].iloc[0]
        
        # Check for signs it's real data
        is_real_data = (
            "V2:" in campaign_name and  # V2 campaigns have this prefix
            budget != 500 and  # Not the hardcoded dummy budget
            "SEO" in campaign_name  # Contains the service from our test
        )
        
        if is_real_data:
            print("\n🎉 SUCCESS: Excel file contains REAL user data!")
            print("✅ Campaign name is specific (not generic dummy)")
            print("✅ Budget is user-chosen (not 500 default)")
            print("✅ Content matches user input")
        else:
            print("\n❌ PROBLEM: Excel file still contains dummy data")
            
        return is_real_data
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_excel_download()
    print(f"\n{'🏆 TEST PASSED' if success else '💥 TEST FAILED'}")