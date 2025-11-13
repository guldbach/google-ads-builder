"""
Google Ads Editor eksport funktionalitet

Dette modul eksporterer kampagner til Google Ads Editor CSV format,
som kan importeres direkte i enhver Google Ads konto.
"""

import pandas as pd
import io
from typing import Dict, List, Any
from django.http import HttpResponse
from .models import Campaign, AdGroup, Ad, Keyword


class GoogleAdsEditorExporter:
    """Eksporter kampagner til Google Ads Editor format"""
    
    def __init__(self, campaign_id: int):
        self.campaign = Campaign.objects.get(id=campaign_id)
        self.ad_groups = AdGroup.objects.filter(campaign=self.campaign)
        self.ads = Ad.objects.filter(ad_group__campaign=self.campaign)
        self.keywords = Keyword.objects.filter(ad_group__campaign=self.campaign)
    
    def export_campaign_csv(self) -> HttpResponse:
        """Eksporter kampagne til CSV format der kan importeres i Google Ads Editor"""
        
        # Opret ExcelWriter objekt i memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Eksporter campaigns
            campaigns_df = self._create_campaigns_dataframe()
            campaigns_df.to_excel(writer, sheet_name='Campaigns', index=False)
            
            # Eksporter ad groups
            ad_groups_df = self._create_ad_groups_dataframe()
            ad_groups_df.to_excel(writer, sheet_name='Ad Groups', index=False)
            
            # Eksporter keywords
            keywords_df = self._create_keywords_dataframe()
            keywords_df.to_excel(writer, sheet_name='Keywords', index=False)
            
            # Eksporter ads
            ads_df = self._create_ads_dataframe()
            ads_df.to_excel(writer, sheet_name='Ads', index=False)
        
        # Præparer response
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        filename = f"{self.campaign.name.replace(' ', '_')}_google_ads_import.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def _create_campaigns_dataframe(self) -> pd.DataFrame:
        """Opret campaigns dataframe"""
        
        campaign_data = [{
            'Campaign': self.campaign.name,
            'Campaign Type': self.campaign.campaign_type.title(),
            'Budget': float(self.campaign.budget_daily),
            'Budget Type': 'Daily',
            'Delivery Method': 'Standard',
            'Start Date': '',  # Lad brugeren vælge
            'End Date': '',    # Lad brugeren vælge
            'Ad Rotation': 'Optimize',
            'Status': 'Paused',  # Start som paused så brugeren kan reviewe
            'Languages': self.campaign.target_language,
            'Location Target': self.campaign.target_location,
            'Location Bid Modifier': '1.00',
            'Bidding Strategy': 'Manual CPC',
            'Enhanced CPC': 'Yes',
        }]
        
        return pd.DataFrame(campaign_data)
    
    def _create_ad_groups_dataframe(self) -> pd.DataFrame:
        """Opret ad groups dataframe"""
        
        ad_group_data = []
        
        for ad_group in self.ad_groups:
            ad_group_data.append({
                'Campaign': self.campaign.name,
                'Ad Group': ad_group.name,
                'Default Bid': float(ad_group.default_cpc or 0),
                'Content Bid': '',
                'Status': 'Paused',  # Start som paused
                'Target CPA': '',
                'Target ROAS': '',
                'Tracking Template': '',
                'Custom Parameter': '',
            })
        
        return pd.DataFrame(ad_group_data)
    
    def _create_keywords_dataframe(self) -> pd.DataFrame:
        """Opret keywords dataframe"""
        
        keyword_data = []
        
        for keyword in self.keywords:
            match_type_mapping = {
                'exact': 'Exact',
                'phrase': 'Phrase', 
                'broad': 'Broad'
            }
            
            keyword_data.append({
                'Campaign': self.campaign.name,
                'Ad Group': keyword.ad_group.name,
                'Keyword': keyword.text,
                'Match Type': match_type_mapping.get(keyword.match_type, 'Phrase'),
                'Max CPC': float(keyword.max_cpc or 0),
                'Final URL': self.campaign.client.website_url,
                'Status': 'Paused',
                'Bid Strategy': '',
                'Custom Parameter': '',
                'Tracking Template': '',
            })
        
        return pd.DataFrame(keyword_data)
    
    def _create_ads_dataframe(self) -> pd.DataFrame:
        """Opret ads dataframe"""
        
        ads_data = []
        
        for ad in self.ads:
            ads_data.append({
                'Campaign': self.campaign.name,
                'Ad Group': ad.ad_group.name,
                'Ad Type': 'Expanded Text Ad',
                'Headline 1': ad.headline_1,
                'Headline 2': ad.headline_2,
                'Headline 3': ad.headline_3 or '',
                'Description Line 1': ad.description_1,
                'Description Line 2': ad.description_2 or '',
                'Final URL': ad.final_url,
                'Display Path 1': ad.display_path_1 or '',
                'Display Path 2': ad.display_path_2 or '',
                'Status': 'Paused',
                'Mobile Final URL': ad.final_url,
                'Tracking Template': '',
                'Custom Parameter': '',
            })
        
        return pd.DataFrame(ads_data)


def export_simple_csv_format(campaign_id: int) -> HttpResponse:
    """Simpel CSV eksport til Google Ads Editor"""
    
    campaign = Campaign.objects.get(id=campaign_id)
    ad_groups = AdGroup.objects.filter(campaign=campaign)
    keywords = Keyword.objects.filter(ad_group__campaign=campaign)
    ads = Ad.objects.filter(ad_group__campaign=campaign)
    
    # Opret CSV data
    csv_data = []
    
    # Header row
    csv_data.append([
        'Row Type', 'Campaign', 'Ad Group', 'Keyword', 'Match Type', 'Max CPC',
        'Headline 1', 'Headline 2', 'Description 1', 'Final URL', 'Status'
    ])
    
    # Campaign row
    csv_data.append([
        'Campaign', campaign.name, '', '', '', str(campaign.budget_daily),
        '', '', '', '', 'Paused'
    ])
    
    # Ad Groups
    for ad_group in ad_groups:
        csv_data.append([
            'Ad Group', campaign.name, ad_group.name, '', '', str(ad_group.default_cpc or ''),
            '', '', '', '', 'Paused'
        ])
    
    # Keywords
    for keyword in keywords:
        csv_data.append([
            'Keyword', campaign.name, keyword.ad_group.name, keyword.text, 
            keyword.match_type.title(), str(keyword.max_cpc or ''),
            '', '', '', campaign.client.website_url, 'Paused'
        ])
    
    # Ads
    for ad in ads:
        csv_data.append([
            'Ad', campaign.name, ad.ad_group.name, '', '', '',
            ad.headline_1, ad.headline_2, ad.description_1, ad.final_url, 'Paused'
        ])
    
    # Opret CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{campaign.name}_google_ads.csv"'
    
    import csv
    writer = csv.writer(response)
    for row in csv_data:
        writer.writerow(row)
    
    return response


def create_basic_campaign_template() -> Dict[str, Any]:
    """Opret basis kampagne template til hurtig oprettelse"""
    
    template = {
        'campaign_settings': {
            'name': 'Ny Search Kampagne',
            'type': 'search',
            'daily_budget': 500,  # 500 DKK
            'location': 'Danmark',
            'language': 'da',
            'bidding_strategy': 'manual_cpc',
            'enhanced_cpc': True
        },
        'ad_groups': [
            {
                'name': 'Primære Keywords',
                'default_cpc': 15.00,
                'keywords': [
                    {'text': '[branded keyword]', 'match_type': 'exact'},
                    {'text': '[service] [location]', 'match_type': 'phrase'},
                    {'text': '[industry] [location]', 'match_type': 'phrase'},
                ]
            },
            {
                'name': 'Brede Keywords',
                'default_cpc': 12.00,
                'keywords': [
                    {'text': '[service]', 'match_type': 'phrase'},
                    {'text': '[industry]', 'match_type': 'broad'},
                ]
            }
        ],
        'ads': [
            {
                'headline_1': '[Brand] - [Service]',
                'headline_2': '[USP 1]',
                'headline_3': '[Location]',
                'description_1': '[USP 2] - Ring i dag for gratis tilbud!',
                'description_2': 'Professionel service siden [år]',
                'final_url': '[website_url]'
            }
        ],
        'negative_keywords': [
            'job', 'arbejde', 'ledige stillinger', 'gratis', 'diy', 'selv'
        ]
    }
    
    return template