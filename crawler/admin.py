from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import CrawlSession, WebPage, ExtractedUSP, ServiceArea
from .tasks import crawl_client_website

@admin.register(CrawlSession)
class CrawlSessionAdmin(admin.ModelAdmin):
    list_display = ['client', 'status', 'pages_crawled', 'total_pages', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at']
    search_fields = ['client__name']
    readonly_fields = ['started_at', 'completed_at', 'pages_crawled', 'total_pages']
    
    actions = ['start_new_crawl']
    
    def start_new_crawl(self, request, queryset):
        """Admin action to start new crawl for selected clients"""
        for session in queryset:
            crawl_client_website.delay(session.client.id)
        self.message_user(request, f"Started crawling for {queryset.count()} clients")
    start_new_crawl.short_description = "Start new crawl for selected clients"

@admin.register(WebPage)
class WebPageAdmin(admin.ModelAdmin):
    list_display = ['url', 'title', 'crawl_session', 'word_count', 'is_service_page', 'crawled_at']
    list_filter = ['is_service_page', 'is_about_page', 'is_contact_page', 'crawled_at']
    search_fields = ['url', 'title', 'content']
    readonly_fields = ['crawled_at', 'word_count']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('crawl_session', 'url', 'title', 'crawled_at')
        }),
        ('Content', {
            'fields': ('content', 'meta_description', 'h1_tags', 'h2_tags', 'word_count')
        }),
        ('Page Classification', {
            'fields': ('is_service_page', 'is_about_page', 'is_contact_page')
        })
    )

@admin.register(ExtractedUSP)
class ExtractedUSPAdmin(admin.ModelAdmin):
    list_display = ['text', 'web_page_url', 'confidence_score', 'extraction_method', 'position_on_page', 'created_at']
    list_filter = ['extraction_method', 'position_on_page', 'confidence_score', 'created_at']
    search_fields = ['text', 'context', 'web_page__url']
    readonly_fields = ['created_at']
    
    def web_page_url(self, obj):
        return obj.web_page.url
    web_page_url.short_description = 'Web Page URL'
    
    fieldsets = (
        ('USP Content', {
            'fields': ('web_page', 'text', 'context')
        }),
        ('Extraction Details', {
            'fields': ('confidence_score', 'extraction_method', 'position_on_page', 'created_at')
        })
    )

@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.ModelAdmin):
    list_display = ['service_name', 'web_page_url', 'priority_score', 'keywords_found']
    list_filter = ['priority_score']
    search_fields = ['service_name', 'service_description', 'keywords_found']
    
    def web_page_url(self, obj):
        return obj.web_page.url
    web_page_url.short_description = 'Web Page URL'
