from django.contrib import admin
from .models import USPCategory, USPTemplate, ClientUSP, IndustryUSPPattern

@admin.register(USPCategory)
class USPCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(USPTemplate)
class USPTemplateAdmin(admin.ModelAdmin):
    list_display = ['text', 'category', 'industry', 'urgency_level', 'effectiveness_score', 'is_active']
    list_filter = ['category', 'industry', 'urgency_level', 'is_active']
    search_fields = ['text', 'keywords']

@admin.register(ClientUSP)
class ClientUSPAdmin(admin.ModelAdmin):
    list_display = ['client', 'custom_text', 'is_discovered', 'is_selected', 'confidence_score']
    list_filter = ['is_discovered', 'is_selected', 'client']
    search_fields = ['custom_text', 'client__name']

@admin.register(IndustryUSPPattern)
class IndustryUSPPatternAdmin(admin.ModelAdmin):
    list_display = ['industry', 'pattern', 'weight', 'created_at']
    list_filter = ['industry']
    search_fields = ['pattern', 'description']
