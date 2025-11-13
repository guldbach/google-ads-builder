from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Industry, Client, Campaign, AdGroup, Keyword, Ad, 
    CampaignPerformancePrediction, NegativeKeywordList, 
    NegativeKeyword, CampaignNegativeKeywordList, NegativeKeywordUpload, GeoTemplate
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


# Negative Keywords Admin
class NegativeKeywordInline(admin.TabularInline):
    model = NegativeKeyword
    extra = 0
    fields = ['keyword_text', 'match_type', 'notes']
    ordering = ['keyword_text']


@admin.register(NegativeKeywordList)
class NegativeKeywordListAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'keywords_count', 'is_active', 
        'auto_apply_industries', 'created_by', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['keywords_count', 'created_at', 'updated_at']
    inlines = [NegativeKeywordInline]
    
    fieldsets = (
        ('Grundlæggende Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Indstillinger', {
            'fields': ('is_active', 'auto_apply_to_industries')
        }),
        ('Metadata', {
            'fields': ('keywords_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def auto_apply_industries(self, obj):
        """Vis industrier som liste"""
        if obj.auto_apply_to_industries:
            return ", ".join(obj.auto_apply_to_industries)
        return "-"
    auto_apply_industries.short_description = "Auto Apply Industries"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Ny liste
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(NegativeKeyword)
class NegativeKeywordAdmin(admin.ModelAdmin):
    list_display = ['keyword_text', 'match_type', 'keyword_list', 'added_at']
    list_filter = ['match_type', 'keyword_list', 'added_at']
    search_fields = ['keyword_text', 'keyword_list__name']
    readonly_fields = ['added_at']
    
    fieldsets = (
        ('Keyword Information', {
            'fields': ('keyword_list', 'keyword_text', 'match_type')
        }),
        ('Metadata', {
            'fields': ('notes', 'source_file_line', 'added_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CampaignNegativeKeywordList)
class CampaignNegativeKeywordListAdmin(admin.ModelAdmin):
    list_display = [
        'campaign', 'negative_list', 'is_active', 
        'applied_by', 'applied_at', 'last_exported_at'
    ]
    list_filter = ['is_active', 'applied_at', 'negative_list__category']
    search_fields = ['campaign__name', 'negative_list__name']
    readonly_fields = ['applied_at', 'last_exported_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'campaign', 'negative_list', 'applied_by'
        )


@admin.register(NegativeKeywordUpload)
class NegativeKeywordUploadAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'keyword_list', 'status', 
        'keywords_added', 'keywords_errors', 'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['status', 'uploaded_at', 'keyword_list__category']
    search_fields = ['original_filename', 'keyword_list__name']
    readonly_fields = [
        'uploaded_at', 'completed_at', 'total_lines', 
        'keywords_added', 'keywords_skipped', 'keywords_errors'
    ]
    
    fieldsets = (
        ('Upload Information', {
            'fields': ('keyword_list', 'original_filename', 'file_size_kb')
        }),
        ('Processing Results', {
            'fields': (
                'status', 'total_lines', 'keywords_added', 
                'keywords_skipped', 'keywords_errors'
            )
        }),
        ('Details', {
            'fields': ('processing_notes', 'error_details'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Uploads sker via custom view, ikke admin
        return False


@admin.register(GeoTemplate)
class GeoTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'service_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Grundlæggende Information', {
            'fields': ('name', 'service_name', 'is_active', 'default_match_type')
        }),
        ('SEO Meta Templates', {
            'fields': ('meta_title_template', 'meta_description_template')
        }),
        ('Google Ads Headlines', {
            'fields': (
                'headline_1_template', 'headline_2_template', 'headline_3_template',
                'headline_4_template', 'headline_5_template', 'headline_6_template'
            ),
            'classes': ('collapse',)
        }),
        ('Google Ads Descriptions', {
            'fields': (
                'description_1_template', 'description_2_template', 
                'description_3_template', 'description_4_template'
            ),
            'classes': ('collapse',)
        }),
        ('WordPress Content', {
            'fields': ('page_content_template',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
