from django.db import models
from campaigns.models import Client, Campaign, AdGroup, Ad


class AIPromptTemplate(models.Model):
    PROMPT_TYPES = [
        ('usp_extraction', 'USP Extraction'),
        ('keyword_generation', 'Keyword Generation'),
        ('ad_copy_generation', 'Ad Copy Generation'),
        ('campaign_analysis', 'Campaign Analysis'),
        ('service_identification', 'Service Identification'),
    ]
    
    name = models.CharField(max_length=200)
    prompt_type = models.CharField(max_length=30, choices=PROMPT_TYPES)
    template = models.TextField()
    version = models.CharField(max_length=10, default='1.0')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} v{self.version}"


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
