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
    
    # Negative Keywords URLs
    path('negative-keywords/', views.negative_keywords_dashboard, name='negative_keywords_dashboard'),
    path('negative-keywords-manager/', views.negative_keywords_manager, name='negative_keywords_manager'),
    path('negative-keywords/create/', views.create_negative_keyword_list, name='create_negative_keyword_list'),
    path('negative-keywords/<int:list_id>/', views.negative_keyword_list_detail, name='negative_keyword_list_detail'),
    path('negative-keywords/<int:list_id>/upload/', views.upload_negative_keywords, name='upload_negative_keywords'),
    
    # Modern Negative Keywords AJAX URLs
    path('ajax/create-negative-keyword-list/', views.create_negative_keyword_list_ajax, name='create_negative_keyword_list_ajax'),
    path('ajax/add-negative-keyword/', views.add_negative_keyword_ajax, name='add_negative_keyword_ajax'),
    path('ajax/delete-negative-keyword/<int:keyword_id>/', views.delete_negative_keyword_ajax, name='delete_negative_keyword_ajax'),
    path('ajax/update-negative-keyword/<int:keyword_id>/', views.update_negative_keyword_ajax, name='update_negative_keyword_ajax'),
    path('ajax/delete-negative-keyword-list/<int:list_id>/', views.delete_negative_keyword_list_ajax, name='delete_negative_keyword_list_ajax'),
    path('ajax/analyze-excel-import/<int:list_id>/', views.analyze_excel_import_for_list, name='analyze_excel_import_for_list'),
    path('ajax/cleanup-keywords/<int:list_id>/', views.cleanup_keywords, name='cleanup_keywords'),
    path('ajax/execute-excel-import/<int:list_id>/', views.execute_excel_import, name='execute_excel_import'),
    path('ajax/edit-negative-keyword-list/<int:list_id>/', views.edit_negative_keyword_list_ajax, name='edit_negative_keyword_list_ajax'),
    path('ajax/get-negative-keyword-list/<int:list_id>/', views.get_negative_keyword_list_ajax, name='get_negative_keyword_list_ajax'),
    path('download-negative-keywords-template/', views.download_negative_keywords_template, name='download_negative_keywords_template'),
    path('ajax/import-negative-keywords-excel/', views.import_negative_keywords_excel, name='import_negative_keywords_excel'),
    path('api/campaign/<int:campaign_id>/negative-keywords/', views.get_campaign_negative_keywords, name='get_campaign_negative_keywords'),
    path('campaign/<int:campaign_id>/apply-negative-keywords/', views.apply_negative_keywords_to_campaign, name='apply_negative_keywords_to_campaign'),
    path('geo-export/<int:campaign_id>/<str:export_type>/', views.export_geo_campaign, name='export_geo_campaign'),
    path('geo-preview/', views.preview_geo_data, name='preview_geo_data'),
    path('geo-test/', views.test_geo_system, name='test_geo_system'),
    
    # Geographic Regions Manager URLs
    path('geographic-regions-manager/', views.geographic_regions_manager, name='geographic_regions_manager'),
    path('ajax/create-geographic-region/', views.create_geographic_region_ajax, name='create_geographic_region_ajax'),
    path('ajax/add-danish-city/', views.add_danish_city_ajax, name='add_danish_city_ajax'),
    path('ajax/delete-danish-city/<int:city_id>/', views.delete_danish_city_ajax, name='delete_danish_city_ajax'),
    path('ajax/update-danish-city/<int:city_id>/', views.update_danish_city_ajax, name='update_danish_city_ajax'),
    path('ajax/delete-geographic-region/<int:region_id>/', views.delete_geographic_region_ajax, name='delete_geographic_region_ajax'),
    path('ajax/edit-geographic-region/<int:region_id>/', views.edit_geographic_region_ajax, name='edit_geographic_region_ajax'),
    path('download-danish-cities-template/', views.download_danish_cities_template, name='download_danish_cities_template'),
    path('ajax/import-danish-cities-excel/', views.import_danish_cities_excel, name='import_danish_cities_excel'),
    path('ajax/analyze-excel-import-cities/<int:region_id>/', views.analyze_excel_import_cities, name='analyze_excel_import_cities'),
    path('ajax/execute-excel-import-cities/<int:region_id>/', views.execute_excel_import_cities, name='execute_excel_import_cities'),
    
    # Industry Manager URLs  
    path('industry-manager/', views.industry_manager, name='industry_manager'),
    
    # Campaign Builder URLs
    path('campaign-builder/', views.campaign_builder_wizard, name='campaign_builder_wizard'),
    
    # Industry Manager AJAX URLs
    path('ajax/get-industry-services/<int:industry_id>/', views.get_industry_services_ajax, name='get_industry_services_ajax'),
    path('ajax/get-service-keywords/<int:service_id>/', views.get_service_keywords_ajax, name='get_service_keywords_ajax'),
    path('ajax/add-service-keyword/', views.add_service_keyword_ajax, name='add_service_keyword_ajax'),
    path('ajax/update-service-keyword/<int:keyword_id>/', views.update_service_keyword_ajax, name='update_service_keyword_ajax'),
    path('ajax/delete-service-keyword/<int:keyword_id>/', views.delete_service_keyword_ajax, name='delete_service_keyword_ajax'),
    path('ajax/create-industry/', views.create_industry_ajax, name='create_industry_ajax'),
    path('ajax/create-service/', views.create_service_ajax, name='create_service_ajax'),
    path('ajax/edit-industry/<int:industry_id>/', views.edit_industry_ajax, name='edit_industry_ajax'),
    path('ajax/edit-service/<int:service_id>/', views.edit_service_ajax, name='edit_service_ajax'),
    path('ajax/delete-service/<int:service_id>/', views.delete_service_ajax, name='delete_service_ajax'),
    path('ajax/delete-industry/<int:industry_id>/', views.delete_industry_ajax, name='delete_industry_ajax'),
]