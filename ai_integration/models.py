from django.db import models
from campaigns.models import Client, Campaign, AdGroup, Ad


class AIPromptTemplate(models.Model):
    PROMPT_TYPES = [
        ('usp_extraction', 'USP Extraction'),
        ('keyword_generation', 'Keyword Generation'),
        ('ad_copy_generation', 'Ad Copy Generation'),
        ('campaign_analysis', 'Campaign Analysis'),
        ('service_identification', 'Service Identification'),
        # Generation prompts (used in services.py)
        ('generate_descriptions', 'Google Ads Beskrivelser'),
        ('generate_meta_tags', 'Meta Tags (Programmatic)'),
        ('generate_seo_meta_tags', 'SEO Meta Tags'),
        ('generate_company_description', 'Virksomhedsbeskrivelse'),
        ('perplexity_research', 'Online Research (Perplexity)'),
        # SEO page content generation
        ('generate_page_content', 'Sideindhold (ny side)'),
        ('rewrite_page_content', 'Omskriv sideindhold'),
    ]

    name = models.CharField(max_length=200)
    prompt_type = models.CharField(max_length=50, choices=PROMPT_TYPES, unique=True)
    template = models.TextField(help_text="Legacy field - use prompt_text instead")
    prompt_text = models.TextField(blank=True, help_text="The actual prompt template with placeholders")
    placeholders = models.JSONField(
        default=list,
        blank=True,
        help_text="List of placeholder definitions: [{'name': '{service_name}', 'description': 'Servicens navn'}]"
    )
    model_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="AI model settings: {'model': 'gpt-4.1', 'temperature': 0.7, 'max_tokens': 500}"
    )
    version = models.CharField(max_length=10, default='1.0')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} v{self.version}"

    def get_prompt_text(self):
        """Return prompt_text if available, otherwise fall back to template."""
        return self.prompt_text if self.prompt_text else self.template


class AIAnalysisSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    analysis_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    input_data = models.JSONField()
    results = models.JSONField(null=True, blank=True)
    tokens_used = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"AI Analysis {self.client.name} - {self.analysis_type}"


class GeneratedAdCopy(models.Model):
    ai_session = models.ForeignKey(AIAnalysisSession, on_delete=models.CASCADE)
    ad_group = models.ForeignKey(AdGroup, on_delete=models.CASCADE, null=True, blank=True)
    headline_1 = models.CharField(max_length=30)
    headline_2 = models.CharField(max_length=30)
    headline_3 = models.CharField(max_length=30, blank=True)
    description_1 = models.CharField(max_length=90)
    description_2 = models.CharField(max_length=90, blank=True)
    quality_score = models.FloatField(default=0.5)
    relevance_score = models.FloatField(default=0.5)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.headline_1} - {self.headline_2}"


class KeywordSuggestion(models.Model):
    ai_session = models.ForeignKey(AIAnalysisSession, on_delete=models.CASCADE)
    keyword_text = models.CharField(max_length=200)
    suggested_match_type = models.CharField(max_length=10)
    search_volume_estimate = models.IntegerField(null=True, blank=True)
    competition_estimate = models.CharField(max_length=20, blank=True)
    relevance_score = models.FloatField()
    suggested_cpc = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.keyword_text


class CampaignOptimizationSuggestion(models.Model):
    OPTIMIZATION_TYPES = [
        ('budget_allocation', 'Budget Allocation'),
        ('keyword_expansion', 'Keyword Expansion'),
        ('ad_group_split', 'Ad Group Split'),
        ('negative_keywords', 'Negative Keywords'),
        ('bid_adjustment', 'Bid Adjustment'),
    ]
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    ai_session = models.ForeignKey(AIAnalysisSession, on_delete=models.CASCADE)
    optimization_type = models.CharField(max_length=30, choices=OPTIMIZATION_TYPES)
    suggestion = models.TextField()
    expected_impact = models.TextField()
    confidence_score = models.FloatField()
    is_implemented = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.campaign.name} - {self.optimization_type}"


class LoadingWidget(models.Model):
    """
    Configurable loading widgets (Roberto animations) for AI operations.
    Supports different SVG animations and text configurations.
    """
    OPERATION_TYPES = [
        ('random', 'Tilfældig rotation'),
        ('service_detection', 'Service/Branche detektion'),
        ('usp_analysis', 'USP Analyse'),
        ('company_description', 'Virksomhedsbeskrivelse'),
        ('company_research', 'Virksomheds Research'),
        ('meta_tags', 'Meta Tags Generering'),
        ('seo_content', 'SEO Indhold'),
        ('content_generation', 'Indhold Generering'),
        ('crawling', 'Website Crawling'),
    ]

    name = models.CharField(max_length=100, help_text="Widget navn, fx 'Roberto Typing'")
    operation_type = models.CharField(
        max_length=50,
        choices=OPERATION_TYPES,
        default='random',
        help_text="Hvilken operation denne widget vises ved, eller 'random' for tilfældig rotation"
    )

    # SVG content - the robot animation
    svg_content = models.TextField(
        help_text="SVG kode for robot animation (inkl. <svg> tags)"
    )

    # Text configuration stored as JSON for flexibility
    text_config = models.JSONField(
        default=dict,
        help_text="""Tekst konfiguration:
        {
            "line1": "> Analyserer...",
            "line2": "> Finder data",
            "line3": "  og services",
            "loadingText": "Tænker",
            "subtitle": "Roberto arbejder hårdt"
        }"""
    )

    # Optional CSS class for styling variants
    css_class = models.CharField(max_length=100, blank=True)

    # Lifecycle and priority
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(
        default=0,
        help_text="Højere prioritet = vises oftere i tilfældig rotation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'name']
        verbose_name = 'Loading Widget'
        verbose_name_plural = 'Loading Widgets'

    def __str__(self):
        return f"{self.name} ({self.get_operation_type_display()})"

    def get_text_config(self):
        """Return text config with defaults for missing keys."""
        defaults = {
            'line1': '> Loading...',
            'line2': '> Arbejder',
            'line3': '  på det',
            'loadingText': 'Vent',
            'subtitle': 'Roberto arbejder'
        }
        config = self.text_config or {}
        return {**defaults, **config}
