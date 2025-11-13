import pandas as pd
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from django.utils.dateparse import parse_date
from django.db import transaction
from .models import (
    PerformanceDataImport, 
    HistoricalCampaignPerformance, 
    HistoricalKeywordPerformance,
    Industry,
    ImportedCampaignStructure,
    ImportedAdGroupStructure,
    ImportedKeywordStructure,
    ImportedAdStructure,
    ImportedNegativeKeyword
)


class GoogleAdsDataImporter:
    """Import og processér Google Ads performance data fra CSV/Excel filer"""
    
    def __init__(self, user):
        self.user = user
        self.errors = []
        
    def import_campaign_performance(self, file_path: str, file_name: str) -> Dict:
        """Import campaign performance data"""
        
        try:
            # Read file (støtter både CSV og Excel)
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            else:
                # Try different encodings for CSV files
                df = self._read_csv_with_encoding(file_path)
            
            # Clean column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Create import record
            import_record = PerformanceDataImport.objects.create(
                import_type='campaign',
                file_name=file_name,
                imported_by=self.user,
                status='processing'
            )
            
            success_count = 0
            error_count = 0
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    campaign_data = self._process_campaign_row(row, import_record)
                    if campaign_data:
                        success_count += 1
                except Exception as e:
                    error_count += 1
                    self.errors.append(f"Row {index + 1}: {str(e)}")
            
            # Update import record
            import_record.rows_imported = success_count
            import_record.errors_count = error_count
            import_record.status = 'completed' if error_count == 0 else 'completed_with_errors'
            import_record.error_details = '\n'.join(self.errors[:50])  # Limit error details
            import_record.save()
            
            return {
                'success': True,
                'rows_imported': success_count,
                'errors': error_count,
                'import_id': import_record.id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def import_keyword_performance(self, file_path: str, file_name: str) -> Dict:
        """Import keyword performance data"""
        
        try:
            # Read file
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            else:
                # Try different encodings for CSV files
                df = self._read_csv_with_encoding(file_path)
            
            # Clean column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Create import record
            import_record = PerformanceDataImport.objects.create(
                import_type='keyword',
                file_name=file_name,
                imported_by=self.user,
                status='processing'
            )
            
            success_count = 0
            error_count = 0
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    keyword_data = self._process_keyword_row(row, import_record)
                    if keyword_data:
                        success_count += 1
                except Exception as e:
                    error_count += 1
                    self.errors.append(f"Row {index + 1}: {str(e)}")
            
            # Update import record
            import_record.rows_imported = success_count
            import_record.errors_count = error_count
            import_record.status = 'completed' if error_count == 0 else 'completed_with_errors'
            import_record.error_details = '\n'.join(self.errors[:50])
            import_record.save()
            
            return {
                'success': True,
                'rows_imported': success_count,
                'errors': error_count,
                'import_id': import_record.id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def import_account_structure(self, file_path: str, file_name: str) -> Dict:
        """Import full account structure from Google Ads Editor export"""
        
        try:
            # Read file
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            else:
                df = self._read_csv_with_encoding(file_path)
            
            # Clean column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Create import record
            import_record = PerformanceDataImport.objects.create(
                import_type='account_structure',
                file_name=file_name,
                imported_by=self.user,
                status='processing'
            )
            
            # Parse the structural data
            result = self._parse_account_structure(df, import_record)
            
            # Update import record
            import_record.rows_imported = result.get('total_rows', 0)
            import_record.errors_count = result.get('errors', 0)
            import_record.status = 'completed' if result.get('errors', 0) == 0 else 'completed_with_errors'
            import_record.error_details = '\n'.join(self.errors[:50])
            import_record.save()
            
            return {
                'success': True,
                'campaigns_imported': result.get('campaigns', 0),
                'ad_groups_imported': result.get('ad_groups', 0),
                'keywords_imported': result.get('keywords', 0),
                'ads_imported': result.get('ads', 0),
                'import_id': import_record.id,
                'message': 'Account structure imported successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_campaign_row(self, row, import_record) -> Optional[HistoricalCampaignPerformance]:
        """Process en enkelt campaign performance row"""
        
        # Mapping af mulige column navne (Google Ads kan have forskellige navne)
        campaign_name = self._get_column_value(row, ['campaign', 'campaign name', 'kampagne', 'kampagnenavn'])
        client_name = self._get_column_value(row, ['client', 'client name', 'kunde', 'kundenavn', 'account'])
        
        # Performance metrics
        conversions = self._get_numeric_value(row, ['conversions', 'konverteringer'])
        cost_per_conversion = self._get_numeric_value(row, ['cost/conv.', 'cost per conversion', 'omkostning pr. konvertering'])
        total_cost = self._get_numeric_value(row, ['cost', 'omkostning', 'total cost'])
        clicks = self._get_numeric_value(row, ['clicks', 'klik'])
        impressions = self._get_numeric_value(row, ['impressions', 'visninger'])
        ctr = self._get_numeric_value(row, ['ctr', 'click-through rate'])
        avg_cpc = self._get_numeric_value(row, ['avg. cpc', 'average cpc', 'gennemsnitlig cpc'])
        
        # Date range
        period_start = self._get_date_value(row, ['start date', 'fra dato', 'period start'])
        period_end = self._get_date_value(row, ['end date', 'til dato', 'period end'])
        
        # Validation
        if not campaign_name or not client_name:
            raise ValueError("Campaign name og client name er påkrævet")
        
        if conversions is None or conversions < 1:
            return None  # Skip campaigns with no conversions
        
        # Default dates hvis ikke angivet
        if not period_start:
            period_start = datetime.now().date() - timedelta(days=30)
        if not period_end:
            period_end = datetime.now().date()
        
        # Auto-detect industry fra campaign name
        industry_category = self._detect_industry_from_campaign_name(campaign_name, client_name)
        
        # Create or update record
        campaign_perf, created = HistoricalCampaignPerformance.objects.get_or_create(
            campaign_name=campaign_name,
            client_name=client_name,
            period_start=period_start,
            period_end=period_end,
            defaults={
                'industry_category': industry_category,
                'conversions': conversions or 0,
                'cost_per_conversion': cost_per_conversion,
                'total_cost': total_cost or 0,
                'clicks': clicks or 0,
                'impressions': impressions or 0,
                'ctr': ctr or 0.0,
                'avg_cpc': avg_cpc,
                'import_batch': import_record
            }
        )
        
        return campaign_perf
    
    def _process_keyword_row(self, row, import_record) -> Optional[HistoricalKeywordPerformance]:
        """Process en enkelt keyword performance row"""
        
        # Mapping af column navne
        keyword = self._get_column_value(row, ['keyword', 'søgeord', 'search term'])
        match_type = self._get_column_value(row, ['match type', 'match', 'matchtype'])
        campaign_name = self._get_column_value(row, ['campaign', 'campaign name', 'kampagne'])
        ad_group_name = self._get_column_value(row, ['ad group', 'adgroup', 'annoncegruppe'])
        client_name = self._get_column_value(row, ['client', 'client name', 'kunde', 'account'])
        
        # Performance metrics
        conversions = self._get_numeric_value(row, ['conversions', 'konverteringer'])
        cost_per_conversion = self._get_numeric_value(row, ['cost/conv.', 'cost per conversion'])
        total_cost = self._get_numeric_value(row, ['cost', 'omkostning'])
        clicks = self._get_numeric_value(row, ['clicks', 'klik'])
        impressions = self._get_numeric_value(row, ['impressions', 'visninger'])
        ctr = self._get_numeric_value(row, ['ctr'])
        avg_cpc = self._get_numeric_value(row, ['avg. cpc', 'average cpc'])
        
        # Date range
        period_start = self._get_date_value(row, ['start date', 'fra dato'])
        period_end = self._get_date_value(row, ['end date', 'til dato'])
        
        # Validation
        if not keyword or not campaign_name:
            raise ValueError("Keyword og campaign name er påkrævet")
        
        if conversions is None or conversions < 1:
            return None  # Skip keywords without conversions
        
        # Clean match type
        if match_type:
            match_type = match_type.lower().strip()
            if 'exact' in match_type:
                match_type = 'exact'
            elif 'phrase' in match_type:
                match_type = 'phrase'
            elif 'broad' in match_type:
                match_type = 'broad'
        else:
            match_type = 'broad'  # Default
        
        # Default dates
        if not period_start:
            period_start = datetime.now().date() - timedelta(days=30)
        if not period_end:
            period_end = datetime.now().date()
        
        # Auto-detect industry
        industry_category = self._detect_industry_from_campaign_name(campaign_name, client_name or '')
        
        # Create record
        keyword_perf, created = HistoricalKeywordPerformance.objects.get_or_create(
            keyword=keyword,
            match_type=match_type,
            campaign_name=campaign_name,
            ad_group_name=ad_group_name or '',
            client_name=client_name or '',
            period_start=period_start,
            period_end=period_end,
            defaults={
                'industry_category': industry_category,
                'conversions': conversions or 0,
                'cost_per_conversion': cost_per_conversion,
                'total_cost': total_cost or 0,
                'clicks': clicks or 0,
                'impressions': impressions or 0,
                'ctr': ctr or 0.0,
                'avg_cpc': avg_cpc,
                'import_batch': import_record
            }
        )
        
        return keyword_perf
    
    def _get_column_value(self, row, possible_names: List[str]) -> Optional[str]:
        """Find værdi fra row baseret på mulige column navne"""
        for name in possible_names:
            if name in row and pd.notna(row[name]):
                return str(row[name]).strip()
        return None
    
    def _get_numeric_value(self, row, possible_names: List[str]) -> Optional[float]:
        """Find numerisk værdi fra row"""
        for name in possible_names:
            if name in row and pd.notna(row[name]):
                value = row[name]
                if isinstance(value, str):
                    # Clean string (fjern valuta tegn, kommaer etc.)
                    value = re.sub(r'[^\d.,]', '', value)
                    value = value.replace(',', '.')
                try:
                    return float(value)
                except ValueError:
                    continue
                except:
                    continue
        return None
    
    def _get_date_value(self, row, possible_names: List[str]) -> Optional[object]:
        """Find date værdi fra row"""
        for name in possible_names:
            if name in row and pd.notna(row[name]):
                value = row[name]
                if isinstance(value, str):
                    parsed_date = parse_date(value)
                    if parsed_date:
                        return parsed_date
                elif hasattr(value, 'date'):
                    return value.date()
        return None
    
    def _detect_industry_from_campaign_name(self, campaign_name: str, client_name: str) -> str:
        """Simple industry detection baseret på campaign/client navne"""
        
        text = f"{campaign_name} {client_name}".lower()
        
        # Industry patterns
        industry_patterns = {
            'VVS': ['vvs', 'blik', 'rør', 'badeværelse', 'toilet', 'fj vvs', 'varme'],
            'El': ['el', 'elektriker', 'elektro', 'belysning', 'strøm'],
            'Advokat': ['advokat', 'jurist', 'jura', 'advokatfirma', 'ret'],
            'Tandlæge': ['tandlæge', 'dental', 'tand', 'klinik'],
            'Læge': ['læge', 'doktor', 'medicin', 'sundhed'],
            'Bilmekaniker': ['bil', 'auto', 'mekaniker', 'værksted', 'reparation'],
            'Rengøring': ['rengøring', 'clean', 'rens'],
            'Byg': ['byg', 'tømrer', 'murer', 'håndværk', 'renovation'],
            'Revisorer': ['revisor', 'regnskab', 'bogholderi', 'skat'],
            'Ejendomsmægler': ['mægler', 'ejendom', 'bolig', 'hus', 'lejlighed']
        }
        
        for industry, patterns in industry_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return industry
        
        return 'Andre'  # Default category
    
    def _read_csv_with_encoding(self, file_path: str):
        """Read CSV file with automatic encoding detection"""
        
        # List of encodings to try (most common first)
        encodings = [
            'utf-8',
            'utf-16',
            'utf-16-le', 
            'utf-16-be',
            'iso-8859-1',
            'cp1252',
            'latin-1'
        ]
        
        for encoding in encodings:
            try:
                # Try reading with current encoding
                df = pd.read_csv(file_path, encoding=encoding)
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                # If it's not an encoding error, try the next encoding
                continue
        
        # If all encodings fail, try with error handling
        try:
            # Use error_bad_lines parameter for older pandas versions
            try:
                df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
            except TypeError:
                # Fallback for older pandas versions
                df = pd.read_csv(file_path, encoding='utf-8', error_bad_lines=False)
            return df
        except Exception as e:
            raise Exception(f"Kunne ikke læse filen med nogen encoding. Fejl: {str(e)}")
    
    def _parse_account_structure(self, df: pd.DataFrame, import_record) -> Dict:
        """Parse Google Ads Editor full account export"""
        
        result = {
            'campaigns': 0,
            'ad_groups': 0, 
            'keywords': 0,
            'ads': 0,
            'errors': 0,
            'total_rows': len(df)
        }
        
        # Group data by campaign, ad group etc.
        campaigns_data = {}
        
        for index, row in df.iterrows():
            try:
                # Extract basic info
                campaign_name = self._get_column_value(row, [
                    'campaign', 'campaign name', 'kampagne', 'kampagnenavn'
                ])
                
                ad_group_name = self._get_column_value(row, [
                    'ad group', 'adgroup', 'ad group name', 'annoncegruppe'
                ])
                
                if not campaign_name:
                    continue  # Skip rows without campaign name
                
                # Auto-detect data type based on available columns
                row_type = self._detect_row_type(row)
                
                # Initialize campaign data structure
                if campaign_name not in campaigns_data:
                    campaigns_data[campaign_name] = {
                        'campaign_info': {},
                        'ad_groups': {},
                        'campaign_negatives': []
                    }
                
                # Process based on row type
                if row_type == 'campaign':
                    campaigns_data[campaign_name]['campaign_info'] = self._extract_campaign_info(row)
                    
                elif row_type == 'ad_group' and ad_group_name:
                    if ad_group_name not in campaigns_data[campaign_name]['ad_groups']:
                        campaigns_data[campaign_name]['ad_groups'][ad_group_name] = {
                            'ad_group_info': {},
                            'keywords': [],
                            'ads': [],
                            'negatives': []
                        }
                    campaigns_data[campaign_name]['ad_groups'][ad_group_name]['ad_group_info'] = self._extract_ad_group_info(row)
                    
                elif row_type == 'keyword' and ad_group_name:
                    keyword_data = self._extract_keyword_info(row)
                    if keyword_data:
                        campaigns_data[campaign_name]['ad_groups'][ad_group_name]['keywords'].append(keyword_data)
                        
                elif row_type == 'ad' and ad_group_name:
                    ad_data = self._extract_ad_info(row)
                    if ad_data:
                        campaigns_data[campaign_name]['ad_groups'][ad_group_name]['ads'].append(ad_data)
                        
                elif row_type == 'negative_keyword':
                    negative_data = self._extract_negative_keyword_info(row)
                    if negative_data:
                        if ad_group_name:
                            campaigns_data[campaign_name]['ad_groups'][ad_group_name]['negatives'].append(negative_data)
                        else:
                            campaigns_data[campaign_name]['campaign_negatives'].append(negative_data)
                
            except Exception as e:
                result['errors'] += 1
                self.errors.append(f"Row {index + 1}: {str(e)}")
                continue
        
        # Save structured data to database
        self._save_structured_data(campaigns_data, import_record, result)
        
        return result
    
    def _detect_row_type(self, row) -> str:
        """Detect what type of row this is based on available columns"""
        
        # Check for specific column patterns
        if self._get_column_value(row, ['keyword', 'søgeord', 'search term']):
            if self._get_column_value(row, ['negative', 'negativ']):
                return 'negative_keyword'
            return 'keyword'
            
        elif self._get_column_value(row, ['headline', 'overskrift', 'headline 1']):
            return 'ad'
            
        elif self._get_column_value(row, ['ad group', 'adgroup', 'annoncegruppe']):
            return 'ad_group'
            
        elif self._get_column_value(row, ['campaign', 'kampagne']):
            return 'campaign'
            
        return 'unknown'
    
    def _extract_campaign_info(self, row) -> Dict:
        """Extract campaign information from row"""
        
        return {
            'campaign_type': self._get_column_value(row, ['campaign type', 'type', 'kampagnetype']),
            'budget_amount': self._get_numeric_value(row, ['budget', 'daily budget', 'dagligt budget']),
            'budget_type': self._get_column_value(row, ['budget type', 'budgettype']),
            'bidding_strategy': self._get_column_value(row, ['bidding strategy', 'budstrategi']),
            'target_cpa': self._get_numeric_value(row, ['target cpa', 'target cost per acquisition']),
            'locations': self._get_column_value(row, ['locations', 'lokationer', 'geographic targeting']),
            'languages': self._get_column_value(row, ['languages', 'sprog'])
        }
    
    def _extract_ad_group_info(self, row) -> Dict:
        """Extract ad group information from row"""
        
        return {
            'default_bid': self._get_numeric_value(row, ['default bid', 'max cpc', 'standard bud'])
        }
    
    def _extract_keyword_info(self, row) -> Optional[Dict]:
        """Extract keyword information from row"""
        
        keyword_text = self._get_column_value(row, ['keyword', 'søgeord', 'search term'])
        if not keyword_text:
            return None
            
        return {
            'keyword_text': keyword_text,
            'match_type': self._get_column_value(row, ['match type', 'matchtype', 'match']),
            'max_cpc': self._get_numeric_value(row, ['max cpc', 'maksimum cpc', 'bid']),
            'final_url': self._get_column_value(row, ['final url', 'destination url', 'landing page'])
        }
    
    def _extract_ad_info(self, row) -> Optional[Dict]:
        """Extract ad copy information from row"""
        
        headline_1 = self._get_column_value(row, ['headline 1', 'headline', 'overskrift 1'])
        if not headline_1:
            return None
            
        return {
            'headline_1': headline_1,
            'headline_2': self._get_column_value(row, ['headline 2', 'overskrift 2']),
            'headline_3': self._get_column_value(row, ['headline 3', 'overskrift 3']),
            'description_1': self._get_column_value(row, ['description 1', 'beskrivelse 1', 'description']),
            'description_2': self._get_column_value(row, ['description 2', 'beskrivelse 2']),
            'final_url': self._get_column_value(row, ['final url', 'destination url']),
            'display_path_1': self._get_column_value(row, ['path 1', 'display path 1']),
            'display_path_2': self._get_column_value(row, ['path 2', 'display path 2'])
        }
    
    def _extract_negative_keyword_info(self, row) -> Optional[Dict]:
        """Extract negative keyword information from row"""
        
        keyword_text = self._get_column_value(row, ['negative keyword', 'negativ søgeord', 'keyword'])
        if not keyword_text:
            return None
            
        return {
            'keyword_text': keyword_text,
            'match_type': self._get_column_value(row, ['match type', 'matchtype']),
            'level': 'campaign'  # Default, will be updated based on context
        }
    
    def _save_structured_data(self, campaigns_data: Dict, import_record, result: Dict):
        """Save parsed structural data to database"""
        
        for campaign_name, campaign_data in campaigns_data.items():
            try:
                # Create campaign
                campaign_info = campaign_data['campaign_info']
                industry_category = self._detect_industry_from_campaign_name(campaign_name, "")
                
                imported_campaign = ImportedCampaignStructure.objects.create(
                    campaign_name=campaign_name,
                    client_name=campaign_name.split(' - ')[0] if ' - ' in campaign_name else '',
                    industry_category=industry_category,
                    campaign_type=campaign_info.get('campaign_type', ''),
                    budget_amount=campaign_info.get('budget_amount'),
                    budget_type=campaign_info.get('budget_type', ''),
                    bidding_strategy=campaign_info.get('bidding_strategy', ''),
                    target_cpa=campaign_info.get('target_cpa'),
                    locations=campaign_info.get('locations', ''),
                    languages=campaign_info.get('languages', ''),
                    import_batch=import_record
                )
                result['campaigns'] += 1
                
                # Create ad groups
                for ad_group_name, ad_group_data in campaign_data['ad_groups'].items():
                    ad_group_info = ad_group_data['ad_group_info']
                    
                    imported_ad_group = ImportedAdGroupStructure.objects.create(
                        campaign=imported_campaign,
                        ad_group_name=ad_group_name,
                        default_bid=ad_group_info.get('default_bid'),
                        keywords_count=len(ad_group_data['keywords']),
                        ads_count=len(ad_group_data['ads'])
                    )
                    result['ad_groups'] += 1
                    
                    # Create keywords
                    for keyword_data in ad_group_data['keywords']:
                        ImportedKeywordStructure.objects.create(
                            ad_group=imported_ad_group,
                            keyword_text=keyword_data['keyword_text'],
                            match_type=keyword_data.get('match_type', 'broad'),
                            max_cpc=keyword_data.get('max_cpc'),
                            final_url=keyword_data.get('final_url', '')
                        )
                        result['keywords'] += 1
                    
                    # Create ads
                    for ad_data in ad_group_data['ads']:
                        ImportedAdStructure.objects.create(
                            ad_group=imported_ad_group,
                            headline_1=ad_data['headline_1'],
                            headline_2=ad_data.get('headline_2', ''),
                            headline_3=ad_data.get('headline_3', ''),
                            description_1=ad_data.get('description_1', ''),
                            description_2=ad_data.get('description_2', ''),
                            final_url=ad_data.get('final_url', ''),
                            display_path_1=ad_data.get('display_path_1', ''),
                            display_path_2=ad_data.get('display_path_2', '')
                        )
                        result['ads'] += 1
                    
                    # Create ad group level negative keywords
                    for negative_data in ad_group_data['negatives']:
                        ImportedNegativeKeyword.objects.create(
                            keyword_text=negative_data['keyword_text'],
                            match_type=negative_data.get('match_type', 'broad'),
                            level='ad_group',
                            campaign=imported_campaign,
                            ad_group=imported_ad_group
                        )
                
                # Create campaign level negative keywords
                for negative_data in campaign_data['campaign_negatives']:
                    ImportedNegativeKeyword.objects.create(
                        keyword_text=negative_data['keyword_text'],
                        match_type=negative_data.get('match_type', 'broad'),
                        level='campaign',
                        campaign=imported_campaign
                    )
                
                # Update counts
                imported_campaign.ad_groups_count = len(campaign_data['ad_groups'])
                imported_campaign.keywords_count = sum(len(ag['keywords']) for ag in campaign_data['ad_groups'].values())
                imported_campaign.ads_count = sum(len(ag['ads']) for ag in campaign_data['ad_groups'].values())
                imported_campaign.save()
                
            except Exception as e:
                result['errors'] += 1
                self.errors.append(f"Campaign {campaign_name}: {str(e)}")
                continue