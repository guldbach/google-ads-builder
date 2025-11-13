from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('builder/', views.campaign_builder, name='campaign_builder'),
    path('success/<int:campaign_id>/', views.campaign_success, name='campaign_success'),
    path('crawl-website/', views.crawl_website_ajax, name='crawl_website_ajax'),
    
    # Data import URLs
    path('data-import/', views.data_import_dashboard, name='data_import_dashboard'),
    path('import-performance/', views.import_performance_data, name='import_performance_data'),
    path('performance-overview/', views.performance_data_overview, name='performance_data_overview'),
    path('analyze-patterns/', views.analyze_patterns_ajax, name='analyze_patterns_ajax'),
    path('pattern-results/', views.pattern_results, name='pattern_results'),
    
    # Google Ads Export URLs
    path('export/<int:campaign_id>/', views.export_campaign_to_google_ads, name='export_campaign'),
    path('export-csv/<int:campaign_id>/', views.export_campaign_csv, name='export_campaign_csv'),
    path('quick-campaign/', views.quick_campaign_builder, name='quick_campaign'),
    
    # Geo Marketing URLs
    path('geo-builder/', views.geo_campaign_builder, name='geo_campaign_builder'),
    path('geo-builder-v2/', views.geo_campaign_builder_v2, name='geo_campaign_builder_v2'),
    path('geo-success/<int:campaign_id>/', views.geo_campaign_success, name='geo_campaign_success'),
    path('geo-export/<int:campaign_id>/<str:export_type>/', views.export_geo_campaign, name='export_geo_campaign'),
    path('geo-preview/', views.preview_geo_data, name='preview_geo_data'),
    path('geo-test/', views.test_geo_system, name='test_geo_system'),
]