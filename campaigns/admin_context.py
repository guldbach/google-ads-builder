from django.contrib.admin import AdminSite
from django.shortcuts import render
from .models import Campaign, NegativeKeywordList, NegativeKeyword, GeoTemplate, Industry


class CustomAdminSite(AdminSite):
    site_title = "Google Ads Builder"
    site_header = "Google Ads Builder Admin"
    index_title = "Administrationspanel"
    
    def index(self, request, extra_context=None):
        """Custom admin index with statistics"""
        
        # Gather statistics
        stats = {
            'total_campaigns': Campaign.objects.count(),
            'total_negative_keywords': NegativeKeyword.objects.count(),
            'active_templates': GeoTemplate.objects.filter(is_active=True).count(),
            'total_industries': Industry.objects.count(),
        }
        
        extra_context = extra_context or {}
        extra_context.update(stats)
        
        return super().index(request, extra_context)


# Create custom admin site instance
admin_site = CustomAdminSite(name='custom_admin')