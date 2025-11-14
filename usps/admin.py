from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    USPMainCategory, USPCategoryTemplate, USPTemplate, USPSet,
    ClientUSP, USPCategory, IndustryUSPPattern
)


@admin.register(USPMainCategory)
class USPMainCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'icon_display', 'name', 'sort_order', 'is_recommended_per_campaign', 
        'max_selections', 'usp_count', 'is_active'
    ]
    list_filter = ['is_active', 'is_recommended_per_campaign']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']
    list_editable = ['sort_order', 'is_active', 'max_selections']
    
    fieldsets = (
        ('Grundlæggende Information', {
            'fields': ('name', 'description', 'sort_order')
        }),
        ('Visuel Design', {
            'fields': ('icon', 'color')
        }),
        ('Kampagne Indstillinger', {
            'fields': ('is_recommended_per_campaign', 'max_selections')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def icon_display(self, obj):
        return format_html(
            '<span style="font-size: 1.5rem; color: {};">{}</span>',
            obj.color, obj.icon
        )
    icon_display.short_description = "Ikon"
    
    def usp_count(self, obj):
        count = obj.usptemplate_set.count()
        url = reverse('admin:usps_usptemplate_changelist') + f'?main_category__id={obj.id}'
        return format_html('<a href="{}">{} USPs</a>', url, count)
    usp_count.short_description = "Antal USPs"


@admin.register(USPCategoryTemplate)
class USPCategoryTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_industries_display', 'auto_populate_usps', 'is_active']
    list_filter = ['auto_populate_usps', 'is_active', 'target_industries']
    search_fields = ['name', 'description']
    filter_horizontal = ['target_industries']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'target_industries')
        }),
        ('Category Data', {
            'fields': ('category_data',),
            'description': 'JSON array med kategori objekter'
        }),
        ('Settings', {
            'fields': ('auto_populate_usps', 'is_active')
        }),
    )
    
    def target_industries_display(self, obj):
        industries = obj.target_industries.all()[:3]
        display = ", ".join([ind.name for ind in industries])
        if obj.target_industries.count() > 3:
            display += f" +{obj.target_industries.count() - 3} flere"
        return display or "Alle brancher"
    target_industries_display.short_description = "Målgrupper"


class USPTemplateInline(admin.TabularInline):
    model = USPTemplate
    extra = 0
    fields = ['priority_rank', 'text', 'effectiveness_score', 'is_active']
    ordering = ['priority_rank']


@admin.register(USPTemplate)
class USPTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'priority_display', 'text_preview', 'category_display', 'industries_display', 
        'effectiveness_score', 'is_active'
    ]
    list_filter = ['main_category', 'is_active', 'ideal_for_industries', 'urgency_level']
    search_fields = ['text', 'explanation', 'keywords']
    filter_horizontal = ['ideal_for_industries']
    list_editable = ['is_active']
    ordering = ['main_category__sort_order', 'priority_rank']
    
    fieldsets = (
        ('USP Information', {
            'fields': ('main_category', 'text', 'priority_rank')
        }),
        ('Targeting', {
            'fields': ('ideal_for_industries',)
        }),
        ('Documentation', {
            'fields': ('explanation', 'example_headlines', 'placeholders_used')
        }),
        ('Performance & Settings', {
            'fields': ('effectiveness_score', 'urgency_level', 'keywords', 'is_active')
        }),
        ('Legacy (Kompatibilitet)', {
            'fields': ('category',),
            'classes': ('collapse',)
        }),
    )
    
    def priority_display(self, obj):
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;">#{}</span>',
            obj.main_category.color if obj.main_category else '#gray', 
            obj.priority_rank
        )
    priority_display.short_description = "Prioritet"
    
    def text_preview(self, obj):
        return obj.text[:60] + "..." if len(obj.text) > 60 else obj.text
    text_preview.short_description = "USP Tekst"
    
    def category_display(self, obj):
        if obj.main_category:
            return format_html('{} {}', obj.main_category.icon, obj.main_category.name)
        return "Ingen kategori"
    category_display.short_description = "Kategori"
    
    def industries_display(self, obj):
        industries = obj.ideal_for_industries.all()[:2]
        display = ", ".join([ind.name for ind in industries])
        if obj.ideal_for_industries.count() > 2:
            display += f" +{obj.ideal_for_industries.count() - 2}"
        return display or "Alle brancher"
    industries_display.short_description = "Brancher"


@admin.register(USPSet)
class USPSetAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'industry', 'service_name', 'completion_status', 
        'usp_count', 'effectiveness_score', 'is_template'
    ]
    list_filter = ['is_template', 'industry', 'created_by']
    search_fields = ['name', 'service_name']
    filter_horizontal = ['selected_usps']
    readonly_fields = ['effectiveness_score', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'campaign', 'industry', 'service_name')
        }),
        ('USP Selection', {
            'fields': ('selected_usps',)
        }),
        ('Targeting', {
            'fields': ('target_areas',)
        }),
        ('Settings', {
            'fields': ('created_by', 'is_template')
        }),
        ('Performance', {
            'fields': ('effectiveness_score', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def completion_status(self, obj):
        completed, total = obj.get_category_completion()
        color = 'green' if obj.is_complete() else 'orange'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/{} kategorier</span>',
            color, completed, total
        )
    completion_status.short_description = "Fuldførsel"
    
    def usp_count(self, obj):
        return obj.selected_usps.count()
    usp_count.short_description = "Antal USPs"


# Legacy admin interfaces
@admin.register(USPCategory)
class USPCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']
    
    class Meta:
        verbose_name = "Legacy USP Category"


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
    readonly_fields = ['created_at']
    
    class Meta:
        verbose_name = "Legacy USP Pattern"
