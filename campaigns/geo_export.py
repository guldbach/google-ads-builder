"""
Geo Marketing Export System
Genererer Google Ads og WordPress filer fra geografiske kampagner
"""

import pandas as pd
import io
from typing import Dict, List, Any, Tuple
from django.http import HttpResponse
from django.utils import timezone
from .models import Campaign, GeoTemplate, GeoKeyword, GeoExport
from .geo_utils import GeoKeywordGenerator, GeoTemplateProcessor, DanishSlugGenerator


class GeoMarketingExporter:
    """Hovedklasse til geo marketing eksport"""
    
    def __init__(self, service_name: str, cities: List[str], template: GeoTemplate = None, domain: str = ""):
        self.service_name = service_name
        self.cities = cities
        self.template = template
        self.domain = domain
        self.generator = GeoKeywordGenerator(service_name, cities, domain)
    
    def export_google_ads(self) -> HttpResponse:
        """Eksporter Google Ads import fil (CSV - krævet af Google Ads Editor)"""
        
        # Generer kampagne data
        campaign_data = self._create_google_ads_data()
        
        # Kombiner alle data til én CSV fil
        all_data = []
        
        # Campaign data
        campaigns_df = pd.DataFrame([campaign_data['campaign']])
        campaigns_df['Type'] = 'Campaign'
        all_data.append(campaigns_df)
        
        # Ad Groups data
        ad_groups_df = pd.DataFrame([campaign_data['ad_group']])
        ad_groups_df['Type'] = 'Ad Group'
        all_data.append(ad_groups_df)
        
        # Keywords data
        keywords_df = pd.DataFrame(campaign_data['keywords'])
        keywords_df['Type'] = 'Keyword'
        all_data.append(keywords_df)
        
        # Ads data
        ads_df = pd.DataFrame([campaign_data['ad']])
        ads_df['Type'] = 'Ad'
        all_data.append(ads_df)
        
        # Kombiner alle DataFrames og fill missing values
        combined_df = pd.concat(all_data, ignore_index=True, sort=False).fillna('')
        
        # Opret CSV response
        response = HttpResponse(content_type='text/csv')
        filename = f"GEO_{self.service_name.replace(' ', '_')}_Google_Ads.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Skriv CSV data
        combined_df.to_csv(response, index=False, encoding='utf-8')
        
        return response
    
    def export_wordpress(self) -> HttpResponse:
        """Eksporter WordPress WP All Import fil (Excel)"""
        
        if not self.template:
            raise ValueError("GeoTemplate er påkrævet for WordPress eksport")
        
        # Generer WordPress data
        wordpress_data = self.generator.generate_wordpress_data(self.template)
        
        # Opret Excel response
        output = io.BytesIO()
        
        df = pd.DataFrame(wordpress_data)
        df.to_excel(output, index=False, engine='openpyxl')
        
        # Prep response
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        filename = f"WP_Import_{self.service_name.replace(' ', '_')}_Landing_Pages.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def export_combined_zip(self) -> HttpResponse:
        """Eksporter begge filer i en ZIP"""
        import zipfile
        from io import BytesIO
        
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Google Ads fil - nu som CSV
            google_ads_response = self.export_google_ads()
            google_ads_filename = f"Google_Ads_Import_{self.service_name}.csv"
            zip_file.writestr(google_ads_filename, google_ads_response.content)
            
            # WordPress fil
            if self.template:
                wp_response = self.export_wordpress()
                wp_filename = f"WordPress_Import_{self.service_name}.xlsx"
                zip_file.writestr(wp_filename, wp_response.content)
        
        zip_buffer.seek(0)
        
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        filename = f"GEO_{self.service_name.replace(' ', '_')}_Complete_Export.zip"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def _create_google_ads_data(self) -> Dict[str, Any]:
        """Opret Google Ads kampagne data struktur"""
        
        # Campaign
        campaign_data = {
            'Campaign': f"GEO: {self.service_name}",
            'Campaign Type': 'Search-only',
            'Budget': 500.00,  # Default budget
            'Budget Type': 'Daily',
            'Delivery Method': 'Standard',
            'Networks': 'Search',
            'Search Partners': 'No',
            'Display Network': 'No',
            'Political ads in EU': 'No',
            'Start Date': '',
            'End Date': '',
            'Ad Rotation': 'Optimize',
            'Status': 'Active',
            'Languages': 'da',
            'Location Target': 'Danmark',
            'Bidding Strategy': 'Manual CPC',
            'Enhanced CPC': 'Yes',
        }
        
        # Ad Group
        ad_group_data = {
            'Campaign': f"GEO: {self.service_name}",
            'Ad Group': f"GEO: {self.service_name}",
            'Default Bid': 15.00,
            'Status': 'Paused',
        }
        
        # Keywords
        keywords_data = []
        keywords_raw = self.generator.generate_keywords_data()
        
        for kw in keywords_raw:
            keyword_entry = {
                'Campaign': f"GEO: {self.service_name}",
                'Ad Group': f"GEO: {self.service_name}",
                'Keyword': kw['keyword_text'],
                'Criterion Type': 'Phrase',
                'Max CPC': 15.00,
                'Final URL': kw['final_url'],
                'Status': 'Active',
            }
            keywords_data.append(keyword_entry)
        
        # Responsive Search Ad
        ad_data = {
            'Campaign': f"GEO: {self.service_name}",
            'Ad Group': f"GEO: {self.service_name}",
            'Ad Type': 'Responsive Search Ad',
            'Headline 1': f'{{KeyWord:Prof. {self.service_name} På Sjælland}}',
            'Headline 2': f'{self.service_name} Med Øje For Detaljen',
            'Headline 3': f'Specialist i Alt {self.service_name}arbejde',
            'Description Line 1': f'{self.service_name} {{LOCATION(City):Sjælland}}. Kontakt os og få en pris direkte i telefonen',
            'Description Line 2': f'Gør som +5000 tilfredse kunder og kontakt os i dag. Vi hjælper med alt slags {self.service_name.lower()}arbejde',
            'Final URL': f'{self.domain}/' if self.domain else 'https://example.com/',
            'Status': 'Paused',
        }
        
        return {
            'campaign': campaign_data,
            'ad_group': ad_group_data,
            'keywords': keywords_data,
            'ad': ad_data
        }


class GeoCampaignExporter:
    """Modern exporter for V2 geo kampagner - bruger faktiske Campaign data"""
    
    def __init__(self, campaign):
        self.campaign = campaign
        self.geo_keywords = GeoKeyword.objects.filter(campaign=campaign)
        if self.geo_keywords.exists():
            self.template = self.geo_keywords.first().template
            self.cities = [gk.city_name for gk in self.geo_keywords]
        else:
            self.template = None
            self.cities = []
    
    def export_google_ads_csv(self) -> HttpResponse:
        """Eksporter til Google Ads Editor som CSV fil (krævet format - baseret på Jonas's struktur)"""
        
        # Generer Google Ads Editor kompatible data
        all_rows = self._create_google_ads_editor_data()
        
        # Opret DataFrame med alle kolonner
        df = pd.DataFrame(all_rows)
        
        # Opret response med korrekt encoding og separator
        response = HttpResponse(content_type='text/csv; charset=utf-16le')
        filename = f"Google_Ads_{self.campaign.name.replace(' ', '_')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Skriv til CSV med UTF-16 encoding og tab separator (som Google Ads Editor kræver)
        csv_content = df.to_csv(index=False, sep='\t', encoding='utf-16le', lineterminator='\r\n')
        response.write(csv_content)
        
        return response
    
    def export_google_ads_excel(self) -> HttpResponse:
        """Legacy metode - omdirigerer til CSV export"""
        return self.export_google_ads_csv()
    
    def _create_google_ads_editor_data(self) -> List[Dict[str, str]]:
        """Opret Google Ads Editor kompatible data baseret på Jonas's struktur"""
        
        # Definer alle 126 kolonner fra Google Ads Editor
        columns = [
            'Campaign', 'Labels', 'Campaign Type', 'Networks', 'Budget', 'Budget type', 
            'EU political ads', 'Standard conversion goals', 'Customer acquisition', 'Languages',
            'Bid Strategy Type', 'Bid Strategy Name', 'Enhanced CPC', 'Maximum CPC bid limit',
            'Start Date', 'End Date', 'Broad match keywords', 'Ad Schedule', 'Ad rotation',
            'Content exclusions', 'Targeting method', 'Exclusion method', 'Audience targeting',
            'Flexible Reach', 'AI Max', 'Text customization', 'Final URL expansion', 'Ad Group',
            'Max CPC', 'Max CPM', 'Target CPA', 'Max CPV', 'Target CPV', 'Percent CPC',
            'Target CPM', 'Target ROAS', 'Target CPC', 'Desktop Bid Modifier', 'Mobile Bid Modifier',
            'Tablet Bid Modifier', 'TV Screen Bid Modifier', 'Display Network Custom Bid Type',
            'Optimized targeting', 'Strict age and gender targeting', 'Search term matching',
            'Ad Group Type', 'Channels', 'Audience name', 'Age demographic', 'Gender demographic',
            'Income demographic', 'Parental status demographic', 'Remarketing audience segments',
            'Interest categories', 'Life events', 'Custom audience segments', 'Detailed demographics',
            'Remarketing audience exclusions', 'Tracking template', 'Final URL suffix',
            'Custom parameters', 'ID', 'Location', 'Reach', 'Location groups', 'Radius',
            'Unit', 'Bid Modifier', 'Keyword', 'Criterion Type', 'First page bid',
            'Top of page bid', 'First position bid', 'Quality score', 'Landing page experience',
            'Expected CTR', 'Ad relevance', 'Final URL', 'Final mobile URL', 'Ad type',
            'Headline 1', 'Headline 1 position', 'Headline 2', 'Headline 2 position',
            'Headline 3', 'Headline 3 position', 'Headline 4', 'Headline 4 position',
            'Headline 5', 'Headline 5 position', 'Headline 6', 'Headline 6 position',
            'Headline 7', 'Headline 7 position', 'Headline 8', 'Headline 8 position',
            'Headline 9', 'Headline 9 position', 'Headline 10', 'Headline 10 position',
            'Headline 11', 'Headline 11 position', 'Headline 12', 'Headline 12 position',
            'Headline 13', 'Headline 13 position', 'Headline 14', 'Headline 14 position',
            'Headline 15', 'Headline 15 position', 'Description 1', 'Description 1 position',
            'Description 2', 'Description 2 position', 'Description 3', 'Description 3 position',
            'Description 4', 'Description 4 position', 'Path 1', 'Path 2', 'Campaign Status',
            'Ad Group Status', 'Status', 'Approval Status', 'Ad strength', 'Comment'
        ]
        
        all_rows = []
        
        # 1. Campaign row
        campaign_row = {col: '' for col in columns}
        campaign_row.update({
            'Campaign': self.campaign.name,
            'Campaign Type': 'Search',
            'Networks': 'Google search',
            'Budget': f"{float(self.campaign.budget_daily):.2f}" if self.campaign.budget_daily else "100.00",
            'Budget type': 'Daily',
            'EU political ads': "Doesn't have EU political ads",
            'Standard conversion goals': 'Account-level',
            'Customer acquisition': 'Bid equally',
            'Languages': 'da',
            'Bid Strategy Type': self._get_bid_strategy_type(),
            'Enhanced CPC': 'Disabled' if self.campaign.bidding_strategy != 'enhanced_cpc' else 'Enabled',
            'Maximum CPC bid limit': f"{float(self.campaign.default_bid):.2f}" if self.campaign.default_bid else "45.00",
            'Start Date': '[]',
            'End Date': '[]',
            'Broad match keywords': 'Off',
            'Ad Schedule': '[]',
            'Ad rotation': self._get_ad_rotation(),
            'Content exclusions': '[]',
            'Targeting method': 'Location of presence or Area of interest',
            'Exclusion method': 'Location of presence',
            'Audience targeting': 'Audience segments',
            'Flexible Reach': 'Audience segments',
            'AI Max': 'Disabled',
            'Text customization': 'Disabled',
            'Final URL expansion': 'Disabled',
            'Campaign Status': 'Enabled'
        })
        all_rows.append(campaign_row)
        
        # 2. Ad Group row
        adgroup_row = {col: '' for col in columns}
        adgroup_row.update({
            'Campaign': self.campaign.name,
            'Languages': 'All',
            'Audience targeting': 'Audience segments',
            'Flexible Reach': 'Audience segments;Genders;Ages;Parental status;Household incomes',
            'Ad Group': f"{self.campaign.name} - Hovedgruppe",
            'Optimized targeting': 'Disabled',
            'Strict age and gender targeting': 'Disabled',
            'Search term matching': 'Enabled',
            'Ad Group Type': 'Standard',
            'Channels': '[]',
            'Campaign Status': 'Enabled',
            'Ad Group Status': 'Enabled'
        })
        all_rows.append(adgroup_row)
        
        # 3. Keyword rows
        for geo_keyword in self.geo_keywords:
            keyword_row = {col: '' for col in columns}
            keyword_row.update({
                'Campaign': self.campaign.name,
                'Ad Group': f"{self.campaign.name} - Hovedgruppe",
                'Max CPC': f"{float(geo_keyword.max_cpc):.2f}" if geo_keyword.max_cpc else f"{float(self.campaign.default_bid):.2f}" if self.campaign.default_bid else "45.00",
                'Keyword': geo_keyword.keyword_text,
                'Criterion Type': geo_keyword.match_type.title(),
                'First page bid': '0.00',
                'Top of page bid': '0.00', 
                'First position bid': '0.00',
                'Landing page experience': ' -',
                'Expected CTR': ' -',
                'Ad relevance': ' -',
                'Final URL': self._create_full_url(geo_keyword.final_url),
                'Campaign Status': 'Enabled',
                'Ad Group Status': 'Enabled',
                'Status': 'Enabled',
                'Approval Status': 'Pending review'
            })
            all_rows.append(keyword_row)
        
        # 4. Ad rows (hvis der er templates)
        if self.template and self.cities:
            sample_city = self.cities[0]
            ad_row = {col: '' for col in columns}
            ad_row.update({
                'Campaign': self.campaign.name,
                'Ad Group': f"{self.campaign.name} - Hovedgruppe",
                'Final URL': self._create_full_url(f"/{self._create_slug(sample_city)}/"),
                'Ad type': 'Responsive search ad',
                'Campaign Status': 'Enabled',
                'Ad Group Status': 'Enabled', 
                'Status': 'Enabled',
                'Approval Status': 'Pending review'
            })
            
            # Add headlines with positions
            for i in range(1, 16):
                headline_field = f'headline_{i}_template'
                if hasattr(self.template, headline_field):
                    headline_value = getattr(self.template, headline_field)
                    if headline_value and headline_value.strip():
                        processed_headline = self._process_template(headline_value, sample_city)
                        ad_row[f'Headline {i}'] = processed_headline
                        ad_row[f'Headline {i} position'] = ''
            
            # Add descriptions with positions  
            for i in range(1, 5):
                description_field = f'description_{i}_template'
                if hasattr(self.template, description_field):
                    description_value = getattr(self.template, description_field)
                    if description_value and description_value.strip():
                        processed_description = self._process_template(description_value, sample_city)
                        ad_row[f'Description {i}'] = processed_description
                        ad_row[f'Description {i} position'] = ''
            
            all_rows.append(ad_row)
        
        return all_rows
    
    def _get_bid_strategy_type(self) -> str:
        """Get bid strategy type for Google Ads Editor"""
        strategy_mapping = {
            'manual_cpc': 'Manual CPC',
            'enhanced_cpc': 'Enhanced CPC', 
            'target_cpa': 'Target CPA',
            'target_roas': 'Target ROAS',
            'maximize_clicks': 'Maximize clicks',
            'maximize_conversions': 'Maximize conversions'
        }
        return strategy_mapping.get(self.campaign.bidding_strategy, 'Maximize clicks')
    
    def _get_ad_rotation(self) -> str:
        """Get ad rotation for Google Ads Editor"""
        rotation_mapping = {
            'optimize': 'Optimize',
            'rotate_evenly': 'Rotate evenly',
            'rotate_indefinitely': 'Rotate indefinitely'
        }
        return rotation_mapping.get(self.campaign.ad_rotation, 'Rotate indefinitely')
    
    def _format_bidding_strategy(self) -> str:
        """Format bidding strategy til Google Ads format"""
        strategy_mapping = {
            'manual_cpc': 'Manual CPC',
            'enhanced_cpc': 'Manual CPC',
            'target_cpa': 'Target CPA',
            'target_roas': 'Target ROAS',
            'maximize_clicks': 'Maximize Clicks',
            'maximize_conversions': 'Maximize Conversions',
        }
        return strategy_mapping.get(self.campaign.bidding_strategy, 'Manual CPC')
    
    def _create_full_url(self, path: str) -> str:
        """Opret fuld URL med domain"""
        if path.startswith('http'):
            return path
        
        domain = getattr(self.campaign, 'website_url', '') or getattr(self.campaign.client, 'website_url', '') if hasattr(self.campaign, 'client') else ''
        if domain:
            if not domain.startswith('http'):
                domain = f"https://{domain}"
            return f"{domain.rstrip('/')}{path}"
        return f"https://example.com{path}"
    
    def _process_template(self, template: str, city: str) -> str:
        """Process template med city substitution"""
        if not template:
            return ""
        
        service_name = self.template.service_name if self.template else "Service"
        return template.replace('{SERVICE}', service_name).replace('{BYNAVN}', city)
    
    def _create_slug(self, city: str) -> str:
        """Opret URL slug fra by navn"""
        return DanishSlugGenerator.slugify(city)
    
    def _export_combined_v2(self, campaign: Campaign) -> HttpResponse:
        """Eksporter V2 kampagne som kombineret ZIP med Google Ads + WordPress"""
        import zipfile
        from io import BytesIO
        
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Google Ads fil (V2 exporter) - nu som CSV
            google_ads_response = self.export_google_ads_csv()
            google_ads_filename = f"Google_Ads_Import_{campaign.name.replace(' ', '_')}.csv"
            zip_file.writestr(google_ads_filename, google_ads_response.content)
            
            # WordPress fil (legacy exporter)
            if self.template:
                service_name = self.template.service_name
                legacy_exporter = GeoMarketingExporter(service_name, self.cities, self.template)
                wp_response = legacy_exporter.export_wordpress()
                wp_filename = f"WP_Import_{service_name.replace(' ', '_')}_Landing_Pages.xlsx"
                zip_file.writestr(wp_filename, wp_response.content)
        
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="Geo_Campaign_{campaign.name.replace(" ", "_")}_Complete.zip"'
        
        return response


class GeoCampaignManager:
    """Manager til at oprette og administrere geo kampagner"""
    
    @staticmethod
    def create_geo_campaign(
        campaign_name: str,
        service_name: str,
        cities: List[str],
        template: GeoTemplate,
        client,
        user
    ) -> Tuple[Campaign, List[GeoKeyword]]:
        """Opret en ny geo kampagne med keywords"""
        
        # Opret kampagne
        campaign = Campaign.objects.create(
            name=campaign_name,
            client=client,
            campaign_type='search',
            budget_daily=500.00,
            target_location=', '.join(cities[:5]),  # Første 5 byer som location
            status='draft'
        )
        
        # Generer geo keywords
        geo_keywords = []
        generator = GeoKeywordGenerator(service_name, cities)
        
        for city in cities:
            processor = GeoTemplateProcessor(service_name, city)
            processed = processor.process_geo_template(template)
            
            geo_keyword = GeoKeyword.objects.create(
                campaign=campaign,
                template=template,
                city_name=city,
                city_slug=processor.url_slug,
                keyword_text=processed['keyword_text'],
                match_type='phrase',
                max_cpc=15.00,
                final_url=processed['final_url'],
                meta_title=processed['meta_title'],
                meta_description=processed['meta_description'],
            )
            geo_keywords.append(geo_keyword)
        
        return campaign, geo_keywords
    
    @staticmethod 
    def create_geo_keywords(
        campaign: Campaign,
        template: GeoTemplate,
        cities: List[str],
        domain: str = ""
    ) -> List[GeoKeyword]:
        """Create geo keywords for an existing campaign"""
        
        geo_keywords = []
        generator = GeoKeywordGenerator(template.service_name, cities, domain)
        
        for city in cities:
            processor = GeoTemplateProcessor(template.service_name, city)
            processed = processor.process_geo_template(template)
            
            geo_keyword = GeoKeyword.objects.create(
                campaign=campaign,
                template=template,
                city_name=city,
                city_slug=processor.url_slug,
                keyword_text=processed['keyword_text'],
                match_type=template.default_match_type,
                max_cpc=campaign.default_bid,
                final_url=processed['final_url'],
                meta_title=processed['meta_title'],
                meta_description=processed['meta_description'],
            )
            geo_keywords.append(geo_keyword)
        
        return geo_keywords
    
    @staticmethod
    def export_geo_campaign(campaign: Campaign, export_type: str = 'combined') -> HttpResponse:
        """Eksporter eksisterende geo kampagne - auto-detekterer V2 vs legacy"""
        
        geo_keywords = GeoKeyword.objects.filter(campaign=campaign)
        if not geo_keywords.exists():
            raise ValueError("Ingen geo keywords fundet for kampagnen")
        
        # Tjek om det er en V2 kampagne (har nye felter)
        is_v2_campaign = (
            hasattr(campaign, 'ad_rotation') and campaign.ad_rotation or
            hasattr(campaign, 'bidding_strategy') and campaign.bidding_strategy or  
            hasattr(campaign, 'default_bid') and campaign.default_bid
        )
        
        if is_v2_campaign:
            # Brug moderne V2 exporter med faktiske Campaign data
            exporter = GeoCampaignExporter(campaign)
            
            if export_type == 'google_ads':
                return exporter.export_google_ads_csv()
            elif export_type == 'wordpress':
                # For WordPress export kan vi stadig bruge legacy system
                template = geo_keywords.first().template
                service_name = template.service_name
                cities = [gk.city_name for gk in geo_keywords]
                legacy_exporter = GeoMarketingExporter(service_name, cities, template)
                return legacy_exporter.export_wordpress()
            elif export_type == 'combined':
                # Opret combined ZIP med V2 Google Ads + legacy WordPress
                return exporter._export_combined_v2(campaign)
            else:
                raise ValueError(f"Ukendt eksport type: {export_type}")
        else:
            # Legacy kampagne - brug gamle system
            template = geo_keywords.first().template
            service_name = template.service_name
            cities = [gk.city_name for gk in geo_keywords]
            
            # Opret legacy exporter
            exporter = GeoMarketingExporter(service_name, cities, template)
            
            # Eksporter baseret på type
            if export_type == 'google_ads':
                return exporter.export_google_ads()
            elif export_type == 'wordpress':
                return exporter.export_wordpress()
            elif export_type == 'combined':
                return exporter.export_combined_zip()
            else:
                raise ValueError(f"Ukendt eksport type: {export_type}")


def create_demo_geo_template(service_name: str = "Murer") -> GeoTemplate:
    """Opret demo geo template"""
    
    template, created = GeoTemplate.objects.get_or_create(
        name=f"{service_name} Standard",
        service_name=service_name,
        defaults={
            'meta_title_template': f"{service_name} {{BYNAVN}} - 5/5 Stjerner på Trustpilot - Ring idag",
            'meta_description_template': f"Skal du bruge en dygtig {service_name.lower()} i {{BYNAVN}}, vi har hjælpet mere end 500 kunder. Kontakt os idag, vi køre dagligt i {{BYNAVN}}",
            'headline_1_template': f"{service_name} {{BYNAVN}}",
            'headline_2_template': "5/5 Stjerner Trustpilot",
            'description_1_template': f"Professionel {service_name.lower()} i {{BYNAVN}} - Ring i dag!",
            'page_content_template': f"<h1>{service_name} i {{BYNAVN}}</h1><p>Vi tilbyder professionel {service_name.lower()}service i {{BYNAVN}} og omegn. Kontakt os for et gratis tilbud.</p>",
        }
    )
    
    return template


# Test function
def test_geo_export():
    """Test geo eksport systemet"""
    
    # Test data
    service_name = "Fugemand"
    cities = ["Bagsværd", "Ølstykke", "Måløv"]
    
    # Opret template
    template = create_demo_geo_template(service_name)
    
    # Opret exporter
    exporter = GeoMarketingExporter(service_name, cities, template, "lundsfugeservice.dk")
    
    # Test data generation
    print("Testing Google Ads data generation...")
    google_ads_data = exporter._create_google_ads_data()
    print(f"Keywords generated: {len(google_ads_data['keywords'])}")
    
    print("Testing WordPress data generation...")
    wp_data = exporter.generator.generate_wordpress_data(template)
    print(f"WordPress pages generated: {len(wp_data)}")
    
    # Print sample data
    print("\nSample Google Ads keyword:")
    print(google_ads_data['keywords'][0])
    
    print("\nSample WordPress data:")
    print(wp_data[0])
    
    print("✅ Geo export test completed!")


if __name__ == "__main__":
    test_geo_export()