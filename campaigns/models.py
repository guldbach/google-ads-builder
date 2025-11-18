from django.db import models
from django.contrib.auth.models import User


class Industry(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Client(models.Model):
    name = models.CharField(max_length=200)
    website_url = models.URLField()
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Campaign(models.Model):
    CAMPAIGN_TYPES = [
        ('search', 'Search'),
        ('display', 'Display'),
        ('shopping', 'Shopping'),
        ('video', 'Video'),
    ]
    
    BUDGET_TYPES = [
        ('daily', 'Daily'),
        ('total', 'Total Campaign'),
    ]
    
    AD_ROTATION_CHOICES = [
        ('optimize', 'Optimize'),
        ('rotate_evenly', 'Rotate evenly'),
        ('rotate_indefinitely', 'Rotate indefinitely'),
    ]
    
    BIDDING_STRATEGY_CHOICES = [
        ('manual_cpc', 'Manual CPC'),
        ('enhanced_cpc', 'Enhanced CPC'),
        ('target_cpa', 'Target CPA'),
        ('maximize_clicks', 'Maximize clicks'),
        ('target_roas', 'Target ROAS'),
    ]
    
    name = models.CharField(max_length=200)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES)
    budget_daily = models.DecimalField(max_digits=10, decimal_places=2)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPES, default='daily')
    target_location = models.CharField(max_length=200)
    target_language = models.CharField(max_length=50, default='da')
    status = models.CharField(max_length=20, default='draft')
    
    # New campaign settings
    ad_rotation = models.CharField(max_length=30, choices=AD_ROTATION_CHOICES, default='optimize')
    bidding_strategy = models.CharField(max_length=30, choices=BIDDING_STRATEGY_CHOICES, default='enhanced_cpc')
    default_bid = models.DecimalField(max_digits=8, decimal_places=2, default=15.00, help_text="Default CPC for ad groups")
    target_cpa = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Target CPA (if using Target CPA bidding)")
    target_roas = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Target ROAS (if using Target ROAS bidding)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.name} - {self.name}"


class AdGroup(models.Model):
    name = models.CharField(max_length=200)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    default_cpc = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_conversion_rate = models.FloatField(null=True, blank=True)
    priority_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.campaign.name} - {self.name}"


class Keyword(models.Model):
    MATCH_TYPES = [
        ('exact', 'Exact'),
        ('phrase', 'Phrase'),
        ('broad', 'Broad'),
    ]
    
    text = models.CharField(max_length=200)
    ad_group = models.ForeignKey(AdGroup, on_delete=models.CASCADE)
    match_type = models.CharField(max_length=10, choices=MATCH_TYPES)
    max_cpc = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_search_volume = models.IntegerField(null=True, blank=True)
    competition_level = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.text} ({self.match_type})"


class Ad(models.Model):
    ad_group = models.ForeignKey(AdGroup, on_delete=models.CASCADE)
    headline_1 = models.CharField(max_length=30)
    headline_2 = models.CharField(max_length=30)
    headline_3 = models.CharField(max_length=30, blank=True)
    description_1 = models.CharField(max_length=90)
    description_2 = models.CharField(max_length=90, blank=True)
    final_url = models.URLField()
    display_path_1 = models.CharField(max_length=15, blank=True)
    display_path_2 = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ad_group.name} - {self.headline_1}"


class CampaignPerformancePrediction(models.Model):
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE)
    estimated_ctr = models.FloatField(null=True, blank=True)
    estimated_conversion_rate = models.FloatField(null=True, blank=True)
    estimated_cpc = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_cost_per_conversion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# Performance Data Import Models
class PerformanceDataImport(models.Model):
    """Track imports af Google Ads performance data"""
    
    IMPORT_TYPES = [
        ('campaign', 'Campaign Performance'),
        ('keyword', 'Keyword Performance'),
        ('ad', 'Ad Performance'),
        ('account_structure', 'Full Account Structure'),
    ]
    
    import_type = models.CharField(max_length=20, choices=IMPORT_TYPES)
    file_name = models.CharField(max_length=200)
    imported_at = models.DateTimeField(auto_now_add=True)
    imported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    rows_imported = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='completed')
    error_details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.import_type} - {self.imported_at.strftime('%Y-%m-%d')}"


class HistoricalCampaignPerformance(models.Model):
    """Historiske performance data fra Google Ads"""
    
    campaign_name = models.CharField(max_length=200)
    client_name = models.CharField(max_length=200)
    industry_category = models.CharField(max_length=100, blank=True)
    
    # Performance metrics (jeres primære KPIs)
    conversions = models.IntegerField(default=0)
    cost_per_conversion = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    clicks = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    ctr = models.FloatField(default=0.0)
    avg_cpc = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    
    # Date range
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Metadata
    import_batch = models.ForeignKey(PerformanceDataImport, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # AI fields
    is_high_performer = models.BooleanField(default=False)
    performance_score = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.campaign_name} ({self.period_start} - {self.period_end})"

    class Meta:
        unique_together = ['campaign_name', 'client_name', 'period_start', 'period_end']


class HistoricalKeywordPerformance(models.Model):
    """Keyword performance data fra eksisterende kampagner"""
    
    keyword = models.CharField(max_length=200)
    match_type = models.CharField(max_length=10)
    campaign_name = models.CharField(max_length=200)
    ad_group_name = models.CharField(max_length=200)
    client_name = models.CharField(max_length=200)
    industry_category = models.CharField(max_length=100, blank=True)
    
    # Performance
    conversions = models.IntegerField(default=0)
    cost_per_conversion = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    clicks = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    ctr = models.FloatField(default=0.0)
    avg_cpc = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    
    # Date range
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Metadata
    import_batch = models.ForeignKey(PerformanceDataImport, on_delete=models.CASCADE)
    
    # AI analysis
    keyword_intent = models.CharField(max_length=50, blank=True)  # high/medium/low intent
    is_recommended = models.BooleanField(default=False)
    performance_score = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.keyword} ({self.match_type}) - {self.campaign_name}"


class IndustryPerformancePattern(models.Model):
    """AI-identificerede mønstre per branche"""
    
    industry_name = models.CharField(max_length=100)
    pattern_type = models.CharField(max_length=50)  # keyword_pattern, budget_pattern, negative_keywords
    
    # Pattern data (JSON)
    pattern_data = models.JSONField()
    
    # Performance metrics
    avg_cost_per_conversion = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    avg_conversion_rate = models.FloatField(null=True)
    avg_ctr = models.FloatField(null=True)
    
    # Metadata
    sample_size = models.IntegerField(default=0)  # Hvor mange kampagner/keywords mønsteret er baseret på
    confidence_score = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.industry_name} - {self.pattern_type}"

    class Meta:
        unique_together = ['industry_name', 'pattern_type']


# Structural Data Models from Google Ads Editor Export
class ImportedCampaignStructure(models.Model):
    """Campaign struktur fra Google Ads Editor export"""
    
    campaign_name = models.CharField(max_length=200)
    client_name = models.CharField(max_length=200, blank=True)
    industry_category = models.CharField(max_length=100, blank=True)
    
    # Campaign settings
    campaign_type = models.CharField(max_length=50, blank=True)
    budget_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_type = models.CharField(max_length=50, blank=True)
    bidding_strategy = models.CharField(max_length=100, blank=True)
    target_cpa = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Targeting
    locations = models.TextField(blank=True)
    languages = models.CharField(max_length=100, blank=True)
    
    # Metadata
    import_batch = models.ForeignKey(PerformanceDataImport, on_delete=models.CASCADE)
    ad_groups_count = models.IntegerField(default=0)
    keywords_count = models.IntegerField(default=0)
    ads_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.campaign_name} ({self.client_name})"


class ImportedAdGroupStructure(models.Model):
    """Ad Group struktur fra Google Ads Editor export"""
    
    campaign = models.ForeignKey(ImportedCampaignStructure, on_delete=models.CASCADE, related_name='imported_ad_groups')
    ad_group_name = models.CharField(max_length=200)
    
    # Ad Group settings
    default_bid = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Metadata
    keywords_count = models.IntegerField(default=0)
    ads_count = models.IntegerField(default=0)
    
    # Analysis fields
    keyword_theme = models.CharField(max_length=200, blank=True)  # AI detected theme
    service_category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.campaign.campaign_name} - {self.ad_group_name}"


class ImportedKeywordStructure(models.Model):
    """Keyword struktur fra Google Ads Editor export"""
    
    ad_group = models.ForeignKey(ImportedAdGroupStructure, on_delete=models.CASCADE, related_name='imported_keywords')
    keyword_text = models.CharField(max_length=200)
    match_type = models.CharField(max_length=20)
    max_cpc = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    final_url = models.URLField(blank=True)
    
    # Analysis fields
    keyword_intent = models.CharField(max_length=50, blank=True)  # high/medium/low
    keyword_category = models.CharField(max_length=100, blank=True)  # brand/service/location etc.

    def __str__(self):
        return f"{self.keyword_text} ({self.match_type})"


class ImportedAdStructure(models.Model):
    """Ad copy struktur fra Google Ads Editor export"""
    
    ad_group = models.ForeignKey(ImportedAdGroupStructure, on_delete=models.CASCADE, related_name='imported_ads')
    
    # Ad copy
    headline_1 = models.CharField(max_length=100, blank=True)
    headline_2 = models.CharField(max_length=100, blank=True) 
    headline_3 = models.CharField(max_length=100, blank=True)
    description_1 = models.CharField(max_length=200, blank=True)
    description_2 = models.CharField(max_length=200, blank=True)
    
    # URL structure
    final_url = models.URLField(blank=True)
    display_path_1 = models.CharField(max_length=50, blank=True)
    display_path_2 = models.CharField(max_length=50, blank=True)
    
    # Analysis fields
    ad_format_pattern = models.CharField(max_length=100, blank=True)  # AI detected pattern
    usp_elements = models.TextField(blank=True)  # Extracted USPs

    def __str__(self):
        return f"{self.headline_1} - {self.ad_group.ad_group_name}"


class ImportedNegativeKeyword(models.Model):
    """Negative keywords fra Google Ads Editor export"""
    
    LEVEL_CHOICES = [
        ('campaign', 'Campaign Level'),
        ('ad_group', 'Ad Group Level'),
    ]
    
    keyword_text = models.CharField(max_length=200)
    match_type = models.CharField(max_length=20)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    
    # References
    campaign = models.ForeignKey(ImportedCampaignStructure, on_delete=models.CASCADE, null=True, blank=True)
    ad_group = models.ForeignKey(ImportedAdGroupStructure, on_delete=models.CASCADE, null=True, blank=True)
    
    # Analysis
    negative_category = models.CharField(max_length=100, blank=True)  # job/diy/competitor etc.

    def __str__(self):
        return f"-{self.keyword_text} ({self.match_type})"


class CampaignArchitecturePattern(models.Model):
    """AI-identificerede campaign arkitektur mønstre"""
    
    industry_name = models.CharField(max_length=100)
    pattern_name = models.CharField(max_length=100)  # "VVS Standard Structure"
    
    # Pattern definition
    typical_campaign_structure = models.JSONField()  # Campaign types and their ad groups
    keyword_organization_patterns = models.JSONField()  # How keywords are grouped
    ad_copy_patterns = models.JSONField()  # Common ad formats and USPs
    negative_keyword_strategy = models.JSONField()  # Negative keyword patterns
    bidding_patterns = models.JSONField()  # Bidding strategies and CPCs
    
    # Metadata
    based_on_campaigns = models.IntegerField(default=0)  # How many campaigns this pattern is based on
    confidence_score = models.FloatField(default=0.0)
    success_indicators = models.JSONField(default=dict)  # What makes this pattern successful
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.industry_name} - {self.pattern_name}"

    class Meta:
        unique_together = ['industry_name', 'pattern_name']


# Geo Marketing Models
class GeoTemplate(models.Model):
    """Templates til geo marketing automation"""
    
    name = models.CharField(max_length=100, help_text="Template navn, f.eks. 'Murer Standard'")
    service_name = models.CharField(max_length=50, help_text="Service navn, f.eks. 'Murer', 'VVS'")
    
    # Meta templates med placeholders
    meta_title_template = models.CharField(
        max_length=200, 
        default="{SERVICE} {BYNAVN} - 5/5 Stjerner på Trustpilot - Ring idag",
        help_text="Brug {SERVICE}, {BYNAVN}, {URL_SLUG} placeholders"
    )
    meta_description_template = models.TextField(
        default="Skal du bruge en dygtig {SERVICE} i {BYNAVN}, vi har hjælpet mere end 500 kunder. Kontakt os idag, vi køre dagligt i {BYNAVN}",
        help_text="Brug {SERVICE}, {BYNAVN}, {URL_SLUG} placeholders"
    )
    
    # Google Ads RSA templates (3 headlines + 2 descriptions)
    headline_1_template = models.CharField(
        max_length=30, 
        default="{SERVICE} {BYNAVN}",
        help_text="Headline 1 - max 30 karakterer"
    )
    headline_2_template = models.CharField(
        max_length=30, 
        default="5/5 Stjerner Trustpilot",
        help_text="Headline 2 - max 30 karakterer"
    )
    headline_3_template = models.CharField(
        max_length=30, 
        default="Ring i dag - Gratis tilbud",
        help_text="Headline 3 - max 30 karakterer"
    )
    
    # Additional headlines 4-15 (auto-reveal system)
    headline_4_template = models.CharField(max_length=30, blank=True, help_text="Headline 4 - max 30 karakterer")
    headline_5_template = models.CharField(max_length=30, blank=True, help_text="Headline 5 - max 30 karakterer")
    headline_6_template = models.CharField(max_length=30, blank=True, help_text="Headline 6 - max 30 karakterer")
    headline_7_template = models.CharField(max_length=30, blank=True, help_text="Headline 7 - max 30 karakterer")
    headline_8_template = models.CharField(max_length=30, blank=True, help_text="Headline 8 - max 30 karakterer")
    headline_9_template = models.CharField(max_length=30, blank=True, help_text="Headline 9 - max 30 karakterer")
    headline_10_template = models.CharField(max_length=30, blank=True, help_text="Headline 10 - max 30 karakterer")
    headline_11_template = models.CharField(max_length=30, blank=True, help_text="Headline 11 - max 30 karakterer")
    headline_12_template = models.CharField(max_length=30, blank=True, help_text="Headline 12 - max 30 karakterer")
    headline_13_template = models.CharField(max_length=30, blank=True, help_text="Headline 13 - max 30 karakterer")
    headline_14_template = models.CharField(max_length=30, blank=True, help_text="Headline 14 - max 30 karakterer")
    headline_15_template = models.CharField(max_length=30, blank=True, help_text="Headline 15 - max 30 karakterer")
    
    description_1_template = models.CharField(
        max_length=90, 
        default="Professionel {SERVICE} i {BYNAVN} - Ring i dag for gratis tilbud!",
        help_text="Description 1 - max 90 karakterer"
    )
    description_2_template = models.CharField(
        max_length=90, 
        default="Erfaren {SERVICE} med 5/5 stjerner. Vi dækker {BYNAVN} og omegn.",
        help_text="Description 2 - max 90 karakterer"
    )
    
    # Additional descriptions 3-4 (auto-reveal system)
    description_3_template = models.CharField(max_length=90, blank=True, help_text="Description 3 - max 90 karakterer")
    description_4_template = models.CharField(max_length=90, blank=True, help_text="Description 4 - max 90 karakterer")
    
    # Default match type for keywords
    default_match_type = models.CharField(
        max_length=10, 
        choices=[('exact', 'Exact'), ('phrase', 'Phrase'), ('broad', 'Broad')],
        default='phrase',
        help_text="Standard match type for alle keywords"
    )
    
    # WordPress content template
    page_content_template = models.TextField(
        blank=True,
        help_text="WordPress side indhold template med placeholders"
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.service_name})"
    
    def validate_templates(self):
        """Validér at templates overholder Google Ads limits"""
        errors = []
        
        # Test placeholders med dummy data
        test_data = {'SERVICE': 'TestService', 'BYNAVN': 'TestBy'}
        
        # Validate all headline templates (1-15)
        for i in range(1, 16):
            field_name = f'headline_{i}_template'
            template = getattr(self, field_name, '')
            if template:  # Only validate if template is not empty
                processed = template.replace('{SERVICE}', test_data['SERVICE']).replace('{BYNAVN}', test_data['BYNAVN'])
                if len(processed) > 30:
                    errors.append(f'{field_name}: For lang ({len(processed)} karakterer, max 30)')
        
        # Validate all description templates (1-4)
        for i in range(1, 5):
            field_name = f'description_{i}_template'
            template = getattr(self, field_name, '')
            if template:  # Only validate if template is not empty
                processed = template.replace('{SERVICE}', test_data['SERVICE']).replace('{BYNAVN}', test_data['BYNAVN'])
                if len(processed) > 90:
                    errors.append(f'{field_name}: For lang ({len(processed)} karakterer, max 90)')
        
        return errors
    
    class Meta:
        verbose_name = "Geo Template"
        verbose_name_plural = "Geo Templates"


class GeoKeyword(models.Model):
    """Generated keywords fra geo kampagner"""
    
    MATCH_TYPES = [
        ('exact', 'Exact'),
        ('phrase', 'Phrase'),
        ('broad', 'Broad'),
    ]
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='geo_keywords')
    template = models.ForeignKey(GeoTemplate, on_delete=models.CASCADE)
    
    # Geographic data
    city_name = models.CharField(max_length=100)
    city_slug = models.CharField(max_length=100)  # URL-friendly version
    
    # Keyword data
    keyword_text = models.CharField(max_length=200)  # f.eks. "Murer Bagsværd"
    match_type = models.CharField(max_length=10, choices=MATCH_TYPES, default='phrase')
    max_cpc = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Landing page data
    final_url = models.URLField(help_text="Landing page URL, f.eks. /murer-bagsvaerd/")
    
    # Generated content
    meta_title = models.CharField(max_length=200)
    meta_description = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.keyword_text} → {self.final_url}"
    
    class Meta:
        unique_together = ['campaign', 'keyword_text']


class GeoExport(models.Model):
    """Track af geo marketing eksporter"""
    
    EXPORT_TYPES = [
        ('google_ads', 'Google Ads Import'),
        ('wordpress', 'WordPress WP All Import'),
        ('combined', 'Combined Export'),
    ]
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    template = models.ForeignKey(GeoTemplate, on_delete=models.CASCADE)
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPES)
    
    # Export data
    cities_exported = models.JSONField(help_text="Liste over eksporterede byer")
    keywords_count = models.IntegerField(default=0)
    
    # Files
    google_ads_file_path = models.CharField(max_length=500, blank=True)
    wordpress_file_path = models.CharField(max_length=500, blank=True)
    
    # Metadata
    exported_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    exported_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.campaign.name} - {self.export_type} ({self.exported_at.strftime('%Y-%m-%d')})"


# Negative Keywords System
class NegativeKeywordList(models.Model):
    """Globale negative keyword lister"""
    
    CATEGORY_CHOICES = [
        ('general', 'Generel Negativ Liste'),
        ('job', 'Job/Karriere Negative'),
        ('diy', 'Gør Det Selv Negative'),
        ('competitor', 'Konkurrent Negative'),
        ('location', 'Lokation Negative'),
        ('service_specific', 'Service Specifik'),
        ('quality', 'Kvalitet/Pris Negative'),
        ('other', 'Andet'),
    ]
    
    name = models.CharField(
        max_length=100, 
        help_text="Navn på listen, f.eks. 'VVS Generel Negativ Liste'"
    )
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='general'
    )
    description = models.TextField(
        blank=True, 
        help_text="Beskrivelse af hvad denne liste indeholder"
    )
    
    # Visual settings
    icon = models.CharField(
        max_length=10,
        default='📋',
        help_text="Emoji eller kort symbol for listen"
    )
    color = models.CharField(
        max_length=7,
        default='#8B5CF6',
        help_text="Hex farve kode for listen (f.eks. #8B5CF6)"
    )
    
    # Settings
    is_active = models.BooleanField(
        default=True, 
        help_text="Skal denne liste bruges automatisk i nye kampagner?"
    )
    # Industry relations
    industry = models.ForeignKey(
        Industry, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Primær branche denne liste er tilknyttet"
    )
    auto_apply_to_industries = models.JSONField(
        default=list,
        blank=True,
        help_text="Yderligere industrier som denne liste automatisk skal anvendes på"
    )
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_uploaded_file = models.CharField(max_length=255, blank=True)
    keywords_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.keywords_count} keywords)"
    
    def update_keywords_count(self):
        """Opdater antallet af keywords i listen"""
        self.keywords_count = self.negative_keywords.count()
        self.save(update_fields=['keywords_count'])
    
    class Meta:
        verbose_name = "Negative Keyword Liste"
        verbose_name_plural = "Negative Keyword Lister"
        ordering = ['-created_at']


class NegativeKeyword(models.Model):
    """Individuelle negative keywords"""
    
    MATCH_TYPES = [
        ('broad', 'Broad Match'),
        ('phrase', 'Phrase Match'),
        ('exact', 'Exact Match'),
    ]
    
    keyword_list = models.ForeignKey(
        NegativeKeywordList, 
        on_delete=models.CASCADE, 
        related_name='negative_keywords'
    )
    keyword_text = models.CharField(
        max_length=200, 
        help_text="Negative keyword (uden minus tegn)"
    )
    match_type = models.CharField(
        max_length=10, 
        choices=MATCH_TYPES, 
        default='broad'
    )
    
    # Metadata
    added_at = models.DateTimeField(auto_now_add=True)
    source_file_line = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Linje nummer fra upload fil"
    )
    notes = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Noter om dette keyword"
    )
    
    def __str__(self):
        symbols = {'broad': '', 'phrase': '"', 'exact': '['}
        symbol_end = {'broad': '', 'phrase': '"', 'exact': ']'}
        return f"-{symbols[self.match_type]}{self.keyword_text}{symbol_end[self.match_type]}"
    
    def clean(self):
        # Fjern minus tegn hvis bruger har tilføjet det
        if self.keyword_text.startswith('-'):
            self.keyword_text = self.keyword_text[1:].strip()
        
        # Fjern match type symbols hvis tilføjet
        self.keyword_text = self.keyword_text.strip('"[]')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Opdater count på parent list
        self.keyword_list.update_keywords_count()
    
    def delete(self, *args, **kwargs):
        keyword_list = self.keyword_list
        super().delete(*args, **kwargs)
        keyword_list.update_keywords_count()
    
    class Meta:
        unique_together = ['keyword_list', 'keyword_text', 'match_type']
        ordering = ['keyword_text']


class CampaignNegativeKeywordList(models.Model):
    """Tilknytning mellem kampagner og negative keyword lister"""
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='negative_lists')
    negative_list = models.ForeignKey(NegativeKeywordList, on_delete=models.CASCADE)
    
    # Settings
    applied_at = models.DateTimeField(auto_now_add=True)
    applied_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    # Export tracking
    included_in_last_export = models.BooleanField(default=False)
    last_exported_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.campaign.name} → {self.negative_list.name}"
    
    class Meta:
        unique_together = ['campaign', 'negative_list']


class NegativeKeywordUpload(models.Model):
    """Track uploads af negative keyword filer"""
    
    UPLOAD_STATUS_CHOICES = [
        ('processing', 'Behandler'),
        ('completed', 'Færdig'),
        ('failed', 'Fejlet'),
    ]
    
    keyword_list = models.ForeignKey(NegativeKeywordList, on_delete=models.CASCADE)
    original_filename = models.CharField(max_length=255)
    file_size_kb = models.IntegerField()
    
    # Processing results
    total_lines = models.IntegerField(default=0)
    keywords_added = models.IntegerField(default=0)
    keywords_skipped = models.IntegerField(default=0)
    keywords_errors = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=UPLOAD_STATUS_CHOICES, default='processing')
    error_details = models.TextField(blank=True)
    processing_notes = models.TextField(blank=True)
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.original_filename} → {self.keyword_list.name}"
    
    class Meta:
        ordering = ['-uploaded_at']


# Geographic Regions System (parallel to Negative Keywords System)
class GeographicRegion(models.Model):
    """Geografiske område lister til danske byer"""
    
    REGION_CATEGORIES = [
        ('nordsjælland', 'Nordsjælland'),
        ('money', 'Money Byer'),
        ('trekant', 'Trekantsområdet'),
        ('storkøbenhavn', 'Storkøbenhavn'),
        ('jylland', 'Jylland'),
        ('fyn', 'Fyn'),
        ('bornholm', 'Bornholm'),
        ('custom', 'Brugerdefineret'),
    ]
    
    name = models.CharField(
        max_length=100, 
        help_text="Navn på området, f.eks. 'Nordsjælland Standard'"
    )
    category = models.CharField(
        max_length=20, 
        choices=REGION_CATEGORIES, 
        default='custom'
    )
    description = models.TextField(
        blank=True, 
        help_text="Beskrivelse af hvilke byer denne region indeholder"
    )
    
    # Visual settings (identisk med NegativeKeywordList)
    icon = models.CharField(
        max_length=10,
        default='🗺️',
        help_text="Emoji eller kort symbol for regionen"
    )
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        help_text="Hex farve kode for regionen (f.eks. #3B82F6)"
    )
    
    # Settings
    is_active = models.BooleanField(
        default=True, 
        help_text="Skal denne region bruges til kampagner?"
    )
    # Industry relations
    industry = models.ForeignKey(
        Industry, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Primær branche denne region er tilknyttet"
    )
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cities_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.cities_count} byer)"
    
    def update_cities_count(self):
        """Opdater antallet af byer i regionen"""
        self.cities_count = self.cities.count()
        self.save(update_fields=['cities_count'])
    
    class Meta:
        verbose_name = "Geografisk Region"
        verbose_name_plural = "Geografiske Regioner"
        ordering = ['-created_at']


class DanishCity(models.Model):
    """Individuelle danske byer med metadata"""
    
    region = models.ForeignKey(
        GeographicRegion, 
        on_delete=models.CASCADE, 
        related_name='cities'
    )
    city_name = models.CharField(
        max_length=200, 
        help_text="Officielt bynavn"
    )
    city_synonym = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Synonym eller kendt som (f.eks. 'Nørrebro' for 'København N')"
    )
    postal_code = models.CharField(
        max_length=10, 
        help_text="Postnummer (f.eks. '2880')"
    )
    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text="Breddegrad (latitude) for Google Ads targeting"
    )
    longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text="Længdegrad (longitude) for Google Ads targeting"
    )
    
    # Metadata
    added_at = models.DateTimeField(auto_now_add=True)
    source_file_line = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Linje nummer fra upload fil"
    )
    notes = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Noter om denne by"
    )
    
    def __str__(self):
        if self.city_synonym:
            return f"{self.city_name} ({self.city_synonym}) - {self.postal_code}"
        return f"{self.city_name} - {self.postal_code}"
    
    def clean(self):
        # Trim whitespace and normalize case
        if self.city_name:
            self.city_name = self.city_name.strip().title()  # Normalize to Title Case
        if self.city_synonym:
            self.city_synonym = self.city_synonym.strip().title()
        if self.postal_code:
            self.postal_code = self.postal_code.strip()
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Opdater count på parent region
        self.region.update_cities_count()
    
    def delete(self, *args, **kwargs):
        region = self.region
        super().delete(*args, **kwargs)
        region.update_cities_count()
    
    class Meta:
        unique_together = ['region', 'city_name', 'postal_code']
        ordering = ['city_name']


class GeographicRegionUpload(models.Model):
    """Track uploads af geografiske region filer"""
    
    UPLOAD_STATUS_CHOICES = [
        ('processing', 'Behandler'),
        ('completed', 'Færdig'),
        ('failed', 'Fejlet'),
    ]
    
    region = models.ForeignKey(GeographicRegion, on_delete=models.CASCADE)
    original_filename = models.CharField(max_length=255)
    file_size_kb = models.IntegerField()
    
    # Processing results
    total_lines = models.IntegerField(default=0)
    cities_added = models.IntegerField(default=0)
    cities_skipped = models.IntegerField(default=0)
    cities_errors = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=UPLOAD_STATUS_CHOICES, default='processing')
    error_details = models.TextField(blank=True)
    processing_notes = models.TextField(blank=True)
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.original_filename} → {self.region.name}"
    
    class Meta:
        ordering = ['-uploaded_at']
