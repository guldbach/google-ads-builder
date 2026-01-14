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
    path('ajax/get-negative-keywords/<int:list_id>/', views.get_negative_keywords_for_list_ajax, name='get_negative_keywords_for_list_ajax'),
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
    path('ajax/suggest-postal-code/', views.suggest_postal_code_ajax, name='suggest_postal_code_ajax'),
    path('ajax/delete-danish-city/<int:city_id>/', views.delete_danish_city_ajax, name='delete_danish_city_ajax'),
    path('ajax/update-danish-city/<int:city_id>/', views.update_danish_city_ajax, name='update_danish_city_ajax'),
    path('ajax/delete-geographic-region/<int:region_id>/', views.delete_geographic_region_ajax, name='delete_geographic_region_ajax'),
    path('ajax/edit-geographic-region/<int:region_id>/', views.edit_geographic_region_ajax, name='edit_geographic_region_ajax'),
    path('download-danish-cities-template/', views.download_danish_cities_template, name='download_danish_cities_template'),
    path('ajax/import-danish-cities-excel/', views.import_danish_cities_excel, name='import_danish_cities_excel'),
    path('ajax/analyze-excel-import-cities/<int:region_id>/', views.analyze_excel_import_cities, name='analyze_excel_import_cities'),
    path('ajax/execute-excel-import-cities/<int:region_id>/', views.execute_excel_import_cities, name='execute_excel_import_cities'),
    path('ajax/generate-negative-city-list/', views.generate_negative_city_list, name='generate_negative_city_list'),
    path('ajax/get-negative-city-count/', views.get_negative_city_count, name='get_negative_city_count'),

    # Industry Manager URLs  
    path('industry-manager/', views.industry_manager, name='industry_manager'),
    
    # Campaign Builder URLs
    path('campaign-builder/', views.campaign_builder_wizard, name='campaign_builder_wizard'),
    
    # Industry Manager AJAX URLs
    path('ajax/get-industry-services/<int:industry_id>/', views.get_industry_services_ajax, name='get_industry_services_ajax'),
    path('ajax/get-service-keywords/<int:service_id>/', views.get_service_keywords_ajax, name='get_service_keywords_ajax'),
    path('ajax/get-negative-keyword-lists/', views.get_negative_keyword_lists_ajax, name='get_negative_keyword_lists_ajax'),
    path('ajax/add-service-keyword/', views.add_service_keyword_ajax, name='add_service_keyword_ajax'),
    path('ajax/update-service-keyword/<int:keyword_id>/', views.update_service_keyword_ajax, name='update_service_keyword_ajax'),
    path('ajax/delete-service-keyword/<int:keyword_id>/', views.delete_service_keyword_ajax, name='delete_service_keyword_ajax'),
    
    # SEO Keywords AJAX URLs
    path('ajax/get-service-seo-keywords/<int:service_id>/', views.get_service_seo_keywords_ajax, name='get_service_seo_keywords_ajax'),
    path('ajax/add-service-seo-keyword/<int:service_id>/', views.add_service_seo_keyword_ajax, name='add_service_seo_keyword_ajax'),
    path('ajax/update-service-seo-keyword/<int:keyword_id>/', views.update_service_seo_keyword_ajax, name='update_service_seo_keyword_ajax'),
    path('ajax/delete-service-seo-keyword/<int:keyword_id>/', views.delete_service_seo_keyword_ajax, name='delete_service_seo_keyword_ajax'),

    # Meta Tag Examples AJAX URLs (Few-Shot AI Learning)
    path('ajax/get-service-meta-examples/<int:service_id>/', views.get_service_meta_examples_ajax, name='get_service_meta_examples_ajax'),
    path('ajax/add-service-meta-example/<int:service_id>/', views.add_service_meta_example_ajax, name='add_service_meta_example_ajax'),
    path('ajax/update-service-meta-example/<int:example_id>/', views.update_service_meta_example_ajax, name='update_service_meta_example_ajax'),
    path('ajax/delete-service-meta-example/<int:example_id>/', views.delete_service_meta_example_ajax, name='delete_service_meta_example_ajax'),

    # Negative Keywords Integration AJAX URLs
    path('ajax/search-negative-keyword-lists/', views.search_negative_keyword_lists_ajax, name='search_negative_keyword_lists_ajax'),
    path('ajax/get-service-negative-lists/<int:service_id>/', views.get_service_negative_lists_ajax, name='get_service_negative_lists_ajax'),
    path('ajax/connect-negative-list/<int:service_id>/', views.connect_negative_list_to_service_ajax, name='connect_negative_list_to_service_ajax'),
    path('ajax/disconnect-negative-list/<int:connection_id>/', views.disconnect_negative_list_from_service_ajax, name='disconnect_negative_list_from_service_ajax'),
    
    path('ajax/create-industry/', views.create_industry_ajax, name='create_industry_ajax'),
    path('ajax/create-service/', views.create_service_ajax, name='create_service_ajax'),
    path('ajax/edit-industry/<int:industry_id>/', views.edit_industry_ajax, name='edit_industry_ajax'),
    path('ajax/edit-service/<int:service_id>/', views.edit_service_ajax, name='edit_service_ajax'),
    path('ajax/delete-service/<int:service_id>/', views.delete_service_ajax, name='delete_service_ajax'),
    path('ajax/delete-industry/<int:industry_id>/', views.delete_industry_ajax, name='delete_industry_ajax'),
    
    # Industry Keywords AJAX URLs  
    path('ajax/get-industry-keywords/<int:industry_id>/', views.get_industry_keywords_ajax, name='get_industry_keywords_ajax'),
    path('ajax/add-industry-keyword/<int:industry_id>/', views.add_industry_keyword_ajax, name='add_industry_keyword_ajax'),
    path('ajax/update-industry-keyword/<int:keyword_id>/', views.update_industry_keyword_ajax, name='update_industry_keyword_ajax'),
    path('ajax/delete-industry-keyword/<int:keyword_id>/', views.delete_industry_keyword_ajax, name='delete_industry_keyword_ajax'),
    
    # Industry SEO Keywords AJAX URLs
    path('ajax/get-industry-seo-keywords/<int:industry_id>/', views.get_industry_seo_keywords_ajax, name='get_industry_seo_keywords_ajax'),
    path('ajax/add-industry-seo-keyword/<int:industry_id>/', views.add_industry_seo_keyword_ajax, name='add_industry_seo_keyword_ajax'),
    path('ajax/update-industry-seo-keyword/<int:keyword_id>/', views.update_industry_seo_keyword_ajax, name='update_industry_seo_keyword_ajax'),
    path('ajax/delete-industry-seo-keyword/<int:keyword_id>/', views.delete_industry_seo_keyword_ajax, name='delete_industry_seo_keyword_ajax'),

    # AI Description Generation
    path('ajax/generate-descriptions/', views.generate_descriptions_ajax, name='generate_descriptions_ajax'),
    path('ajax/generate-company-description/', views.generate_company_description_ajax, name='generate_company_description_ajax'),
    path('ajax/analyze-website-usps/', views.analyze_website_for_usps_ajax, name='analyze_website_for_usps_ajax'),
    path('ajax/scrape-detect-services/', views.scrape_and_detect_services_ajax, name='scrape_and_detect_services_ajax'),
    path('ajax/generate-seo-content/', views.generate_seo_content_ajax, name='generate_seo_content_ajax'),

    # Programmatic Byside AJAX URLs
    path('ajax/crawl-sitemap/', views.crawl_sitemap_ajax, name='crawl_sitemap_ajax'),
    path('ajax/match-city-pages/', views.match_city_pages_ajax, name='match_city_pages_ajax'),
    path('ajax/generate-programmatic-descriptions/', views.generate_programmatic_descriptions_ajax, name='generate_programmatic_descriptions_ajax'),
    path('ajax/generate-seo-meta/', views.generate_seo_meta_ajax, name='generate_seo_meta_ajax'),

    # Postal Code Manager URLs
    path('postal-manager/', views.postal_manager, name='postal_manager'),
    path('ajax/update-postal-code/', views.update_postal_code_ajax, name='update_postal_code_ajax'),
    path('api/postal-codes/', views.get_postal_codes_api, name='get_postal_codes_api'),

    # Campaign Builder Export
    path('export-campaign-builder-csv/', views.export_campaign_builder_csv, name='export_campaign_builder_csv'),

    # SEO Content Export (WordPress WP All Import compatible)
    path('ajax/export-seo-content-csv/', views.export_seo_content_csv, name='export_seo_content_csv'),
]