from django.contrib import admin
from .models import (
    Industry, Client, Campaign, AdGroup, Keyword, Ad, 
    CampaignPerformancePrediction
)

@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'website_url', 'industry', 'created_by', 'created_at']
    list_filter = ['industry', 'created_at']
    search_fields = ['name', 'website_url']

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'campaign_type', 'budget_daily', 'status', 'created_at']
    list_filter = ['campaign_type', 'status', 'created_at']
    search_fields = ['name', 'client__name']

@admin.register(AdGroup)
class AdGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign', 'default_cpc', 'priority_score', 'created_at']
    list_filter = ['campaign__campaign_type', 'created_at']
    search_fields = ['name', 'campaign__name']

@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ['text', 'ad_group', 'match_type', 'max_cpc', 'competition_level']
    list_filter = ['match_type', 'competition_level']
    search_fields = ['text', 'ad_group__name']

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ['headline_1', 'headline_2', 'ad_group', 'created_at']
    search_fields = ['headline_1', 'headline_2', 'ad_group__name']

@admin.register(CampaignPerformancePrediction)
class CampaignPerformancePredictionAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'estimated_ctr', 'estimated_conversion_rate', 'confidence_score']
    search_fields = ['campaign__name']
