from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import (
    Industry, Client, Campaign, AdGroup, Ad, Keyword, PerformanceDataImport, 
    HistoricalCampaignPerformance, HistoricalKeywordPerformance,
    NegativeKeywordList, NegativeKeyword, CampaignNegativeKeywordList, NegativeKeywordUpload
)
from usps.models import USPTemplate, ClientUSP, USPMainCategory
from crawler.tasks import crawl_client_website
from crawler.models import ExtractedUSP
from .data_import import GoogleAdsDataImporter
from .google_ads_export import GoogleAdsEditorExporter, export_simple_csv_format, create_basic_campaign_template
from .geo_export import GeoMarketingExporter, GeoCampaignManager, create_demo_geo_template
from .geo_utils import DanishSlugGenerator, GeoKeywordGenerator, validate_geo_data
from .models import GeoTemplate, GeoKeyword, GeoExport
import json
import os
import tempfile


def campaign_builder(request):
    """Main campaign builder interface"""
    if request.method == 'POST':
        return create_campaign(request)
    
    # Get data for form
    industries = Industry.objects.all()
    usp_templates = USPTemplate.objects.filter(is_active=True)[:10]  # Limit for demo
    
    context = {
        'industries': industries,
        'usp_templates': usp_templates,
    }
    
    return render(request, 'campaigns/builder.html', context)


def create_campaign(request):
    """Process campaign creation form"""
    try:
        # Extract form data
        client_name = request.POST.get('client_name')
        industry_id = request.POST.get('industry')
        website_url = request.POST.get('website_url')
        description = request.POST.get('description', '')
        
        campaign_name = request.POST.get('campaign_name')
        campaign_type = request.POST.get('campaign_type')
        daily_budget = request.POST.get('daily_budget')
        target_location = request.POST.get('target_location')
        bidding_strategy = request.POST.get('bidding_strategy')
        target_cpa = request.POST.get('target_cpa')
        
        selected_usps = request.POST.getlist('selected_usps')
        custom_usps = [
            request.POST.get(f'custom_usp_{i}') 
            for i in range(1, 10) 
            if request.POST.get(f'custom_usp_{i}')
        ]
        
        # Validation
        if not all([client_name, industry_id, website_url, campaign_name, daily_budget]):
            messages.error(request, 'Alle påkrævede felter skal udfyldes')
            return redirect('campaign_builder')
        
        # Create or get industry
        industry = Industry.objects.get(id=industry_id)
        
        # Create or get client (for demo - in production you'd want proper user management)
        client, created = Client.objects.get_or_create(
            name=client_name,
            website_url=website_url,
            defaults={
                'industry': industry,
                'description': description,
                'created_by': request.user if request.user.is_authenticated else None
            }
        )
        
        # Create campaign
        campaign = Campaign.objects.create(
            name=campaign_name,
            client=client,
            campaign_type=campaign_type,
            budget_daily=daily_budget,
            target_location=target_location,
            status='draft'
        )
        
        # Add selected USPs
        for usp_id in selected_usps:
            usp_template = USPTemplate.objects.get(id=usp_id)
            ClientUSP.objects.create(
                client=client,
                usp_template=usp_template,
                custom_text=usp_template.text,
                is_selected=True
            )
        
        # Add custom USPs
        for custom_usp in custom_usps:
            if custom_usp.strip():
                ClientUSP.objects.create(
                    client=client,
                    custom_text=custom_usp.strip(),
                    is_selected=True
                )
        
        # Start website crawling in background
        if request.POST.get('generate_keywords'):
            crawl_client_website.delay(client.id, max_pages=10)
        
        # Generate basic ad group and keywords (simplified for demo)
        if request.POST.get('generate_ads'):
            create_basic_campaign_structure(campaign, client)
        
        messages.success(request, f'Kampagne "{campaign_name}" er oprettet! Website crawling er startet i baggrunden.')
        return redirect('campaign_success', campaign_id=campaign.id)
        
    except Exception as e:
        messages.error(request, f'Fejl ved oprettelse af kampagne: {str(e)}')
        return redirect('campaign_builder')


def create_basic_campaign_structure(campaign, client):
    """Create basic campaign structure with ad groups, keywords and ads"""
    
    # Get client USPs for ad creation
    client_usps = ClientUSP.objects.filter(client=client, is_selected=True)[:3]
    
    # Create main ad group
    ad_group = AdGroup.objects.create(
        name=f"{campaign.name} - Hovedgruppe",
        campaign=campaign,
        default_cpc=15.00,  # 15 DKK default CPC
        priority_score=100
    )
    
    # Create basic keywords based on industry and client name
    industry_keywords = [
        client.industry.name.lower(),
        f"{client.industry.name.lower()} {client.target_location}",
        f"{client.name.split()[0].lower()} {client.industry.name.lower()}",
    ]
    
    for keyword_text in industry_keywords:
        if keyword_text:
            Keyword.objects.create(
                text=keyword_text,
                ad_group=ad_group,
                match_type='phrase',
                max_cpc=15.00
            )
    
    # Create ads using USPs
    usp_texts = [usp.custom_text for usp in client_usps]
    
    # Create first ad
    headline_1 = f"{client.industry.name} i {campaign.target_location}"[:30]
    headline_2 = usp_texts[0][:30] if usp_texts else "Professionel service"
    headline_3 = usp_texts[1][:30] if len(usp_texts) > 1 else ""
    
    description_1 = f"Få hjælp fra {client.name}. " + (usp_texts[2] if len(usp_texts) > 2 else "Ring i dag!")
    description_1 = description_1[:90]
    
    Ad.objects.create(
        ad_group=ad_group,
        headline_1=headline_1,
        headline_2=headline_2,
        headline_3=headline_3,
        description_1=description_1,
        description_2="Ring i dag for gratis tilbud!"[:90],
        final_url=client.website_url,
        display_path_1=client.industry.name.lower()[:15],
        display_path_2=campaign.target_location.split(',')[0][:15]
    )


@csrf_exempt
def crawl_website_ajax(request):
    """AJAX endpoint for website crawling"""
    if request.method == 'POST':
        website_url = request.POST.get('website_url')
        
        if not website_url:
            return JsonResponse({'error': 'Ingen URL angivet'})
        
        try:
            # For demo purposes, we'll create a temporary client
            from django.contrib.auth.models import User
            from crawler.services import WebsiteCrawler
            
            # Get or create default industry and user
            industry, _ = Industry.objects.get_or_create(
                name='Test Industry',
                defaults={'description': 'Temporary industry for crawling'}
            )
            
            user = User.objects.first()
            if not user:
                user = User.objects.create_user('demo', 'demo@example.com', 'demo123')
            
            # Create temporary client
            temp_client = Client.objects.create(
                name=f'Temp - {website_url}',
                website_url=website_url,
                industry=industry,
                created_by=user
            )
            
            # Start crawling
            crawler = WebsiteCrawler(temp_client, max_pages=3, delay=0.5)
            crawl_session = crawler.crawl_website()
            
            # Get extracted USPs
            extracted_usps = ExtractedUSP.objects.filter(
                web_page__crawl_session=crawl_session
            )[:10]
            
            usp_data = []
            for usp in extracted_usps:
                usp_data.append({
                    'text': usp.text,
                    'confidence': usp.confidence_score,
                    'position': usp.position_on_page
                })
            
            return JsonResponse({
                'success': True,
                'usps_found': len(usp_data),
                'usps': usp_data,
                'pages_crawled': crawl_session.pages_crawled
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Fejl ved crawling: {str(e)}'})
    
    return JsonResponse({'error': 'Kun POST requests tilladt'})


def campaign_success(request, campaign_id):
    """Campaign creation success page"""
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        ad_groups = AdGroup.objects.filter(campaign=campaign)
        keywords = Keyword.objects.filter(ad_group__campaign=campaign)
        ads = Ad.objects.filter(ad_group__campaign=campaign)
        
        context = {
            'campaign': campaign,
            'ad_groups_count': ad_groups.count(),
            'keywords_count': keywords.count(),
            'ads_count': ads.count(),
            'ad_groups': ad_groups,
            'keywords': keywords[:10],  # Show first 10
            'ads': ads
        }
        
        return render(request, 'campaigns/success.html', context)
        
    except Campaign.DoesNotExist:
        messages.error(request, 'Kampagne ikke fundet')
        return redirect('campaign_builder')


def home(request):
    """Home page with campaign options"""
    return render(request, 'campaigns/home.html')


def data_import_dashboard(request):
    """Dashboard til at importere Google Ads performance data"""
    
    # Get recent imports
    recent_imports = PerformanceDataImport.objects.filter(
        imported_by=request.user if request.user.is_authenticated else None
    ).order_by('-imported_at')[:10]
    
    # Get statistics
    total_campaigns = HistoricalCampaignPerformance.objects.count()
    total_keywords = HistoricalKeywordPerformance.objects.count()
    
    context = {
        'recent_imports': recent_imports,
        'total_campaigns': total_campaigns,
        'total_keywords': total_keywords,
    }
    
    return render(request, 'campaigns/data_import.html', context)


@csrf_exempt
def import_performance_data(request):
    """AJAX endpoint til at importere performance data"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Kun POST requests tilladt'})
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'Ingen fil uploaded'})
    
    file = request.FILES['file']
    import_type = request.POST.get('import_type', 'campaign')
    
    # Validate file type
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    file_extension = os.path.splitext(file.name)[1].lower()
    
    if file_extension not in allowed_extensions:
        return JsonResponse({'error': 'Kun CSV og Excel filer er tilladt'})
    
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Create importer
        user = request.user if request.user.is_authenticated else None
        if not user:
            # Create a default user for demo
            from django.contrib.auth.models import User
            user, created = User.objects.get_or_create(
                username='demo',
                defaults={'email': 'demo@example.com'}
            )
        
        importer = GoogleAdsDataImporter(user)
        
        # Import based on type
        if import_type == 'campaign':
            result = importer.import_campaign_performance(temp_file_path, file.name)
        elif import_type == 'keyword':
            result = importer.import_keyword_performance(temp_file_path, file.name)
        elif import_type == 'account_structure':
            result = importer.import_account_structure(temp_file_path, file.name)
        else:
            result = {'success': False, 'error': 'Ukendt import type'}
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': f'Import fejl: {str(e)}'})


def performance_data_overview(request):
    """Oversigt over importeret performance data"""
    
    # Campaign performance summary
    campaigns = HistoricalCampaignPerformance.objects.select_related('import_batch').order_by('-created_at')[:50]
    
    # Keywords by industry
    keywords_by_industry = HistoricalKeywordPerformance.objects.values(
        'industry_category'
    ).distinct().order_by('industry_category')
    
    # Top performing campaigns (lowest cost per conversion)
    top_campaigns = HistoricalCampaignPerformance.objects.filter(
        cost_per_conversion__isnull=False,
        conversions__gte=5  # Minimum 5 conversions
    ).order_by('cost_per_conversion')[:20]
    
    context = {
        'campaigns': campaigns,
        'keywords_by_industry': keywords_by_industry,
        'top_campaigns': top_campaigns,
    }
    
    return render(request, 'campaigns/performance_overview.html', context)


@csrf_exempt
def analyze_patterns_ajax(request):
    """AJAX endpoint til at køre pattern analyse"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Kun POST requests tilladt'})
    
    try:
        from .pattern_analyzer import PerformancePatternAnalyzer
        
        analyzer = PerformancePatternAnalyzer()
        results = analyzer.analyze_all_patterns()
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def pattern_results(request):
    """Vis resultater af pattern analyse"""
    
    # Get all patterns
    from .models import IndustryPerformancePattern
    
    patterns = IndustryPerformancePattern.objects.all().order_by('industry_name', 'pattern_type')
    
    # Group by industry
    patterns_by_industry = {}
    for pattern in patterns:
        if pattern.industry_name not in patterns_by_industry:
            patterns_by_industry[pattern.industry_name] = {}
        patterns_by_industry[pattern.industry_name][pattern.pattern_type] = pattern
    
    context = {
        'patterns_by_industry': patterns_by_industry,
        'total_patterns': patterns.count(),
        'industries_count': len(patterns_by_industry)
    }
    
    return render(request, 'campaigns/pattern_results.html', context)


def export_campaign_to_google_ads(request, campaign_id):
    """Eksporter kampagne til Google Ads Editor Excel format"""
    try:
        exporter = GoogleAdsEditorExporter(campaign_id)
        return exporter.export_campaign_csv()
    except Campaign.DoesNotExist:
        messages.error(request, 'Kampagne ikke fundet')
        return redirect('campaign_builder')
    except Exception as e:
        messages.error(request, f'Fejl ved eksport: {str(e)}')
        return redirect('campaign_success', campaign_id=campaign_id)


def export_campaign_csv(request, campaign_id):
    """Eksporter kampagne til simpel CSV format"""
    try:
        return export_simple_csv_format(campaign_id)
    except Campaign.DoesNotExist:
        messages.error(request, 'Kampagne ikke fundet')
        return redirect('campaign_builder')
    except Exception as e:
        messages.error(request, f'Fejl ved CSV eksport: {str(e)}')
        return redirect('campaign_success', campaign_id=campaign_id)


def quick_campaign_builder(request):
    """Hurtig kampagne builder med forudindstillede templates"""
    
    if request.method == 'POST':
        return create_quick_campaign(request)
    
    # Hent industries og template data
    industries = Industry.objects.all()
    template = create_basic_campaign_template()
    
    context = {
        'industries': industries,
        'template': template,
        'quick_mode': True
    }
    
    return render(request, 'campaigns/quick_builder.html', context)


def create_quick_campaign(request):
    """Opret hurtig kampagne baseret på template"""
    try:
        # Basic campaign data
        client_name = request.POST.get('client_name')
        industry_id = request.POST.get('industry')
        website_url = request.POST.get('website_url')
        location = request.POST.get('location', 'Danmark')
        daily_budget = request.POST.get('daily_budget', 500)
        
        # Service keywords
        service_keywords = request.POST.get('service_keywords', '').split(',')
        service_keywords = [k.strip() for k in service_keywords if k.strip()]
        
        # Brand/company name for branded keywords
        brand_name = request.POST.get('brand_name', client_name)
        
        # USPs
        usp1 = request.POST.get('usp1', 'Professionel service')
        usp2 = request.POST.get('usp2', 'Hurtig levering')
        usp3 = request.POST.get('usp3', 'Konkurrencedygtige priser')
        
        # Validation
        if not all([client_name, industry_id, website_url]):
            messages.error(request, 'Udfyld venligst alle påkrævede felter')
            return redirect('quick_campaign')
        
        # Get or create industry
        industry = Industry.objects.get(id=industry_id)
        
        # Create client
        from django.contrib.auth.models import User
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        client, created = Client.objects.get_or_create(
            name=client_name,
            website_url=website_url,
            defaults={
                'industry': industry,
                'description': f'Hurtig kampagne for {industry.name}',
                'created_by': user
            }
        )
        
        # Create campaign
        campaign = Campaign.objects.create(
            name=f"{client_name} - Search Kampagne",
            client=client,
            campaign_type='search',
            budget_daily=daily_budget,
            target_location=location,
            status='draft'
        )
        
        # Create ad groups and content
        create_quick_campaign_structure(campaign, client, service_keywords, brand_name, usp1, usp2, usp3)
        
        messages.success(request, f'Hurtig kampagne "{campaign.name}" er oprettet!')
        return redirect('campaign_success', campaign_id=campaign.id)
        
    except Exception as e:
        messages.error(request, f'Fejl ved oprettelse: {str(e)}')
        return redirect('quick_campaign')


def create_quick_campaign_structure(campaign, client, service_keywords, brand_name, usp1, usp2, usp3):
    """Opret kampagne struktur baseret på hurtig template"""
    
    # Brand Ad Group
    brand_adgroup = AdGroup.objects.create(
        name="Brand Keywords",
        campaign=campaign,
        default_cpc=8.00,
        priority_score=100
    )
    
    # Brand keywords
    brand_keywords = [
        brand_name.lower(),
        f"{brand_name.lower()} {client.industry.name.lower()}",
        f"{brand_name.lower()} {campaign.target_location.lower()}"
    ]
    
    for keyword_text in brand_keywords:
        if keyword_text.strip():
            Keyword.objects.create(
                text=keyword_text,
                ad_group=brand_adgroup,
                match_type='exact',
                max_cpc=8.00
            )
    
    # Service Ad Groups
    if service_keywords:
        service_adgroup = AdGroup.objects.create(
            name="Service Keywords", 
            campaign=campaign,
            default_cpc=15.00,
            priority_score=90
        )
        
        for service in service_keywords[:5]:  # Max 5 services
            # Create exact and phrase match
            Keyword.objects.create(
                text=service,
                ad_group=service_adgroup,
                match_type='phrase',
                max_cpc=15.00
            )
            
            # Location based keyword
            location_keyword = f"{service} {campaign.target_location}"
            Keyword.objects.create(
                text=location_keyword,
                ad_group=service_adgroup,
                match_type='phrase', 
                max_cpc=18.00
            )
    
    # Generic industry keywords
    generic_adgroup = AdGroup.objects.create(
        name="Generiske Keywords",
        campaign=campaign,
        default_cpc=12.00,
        priority_score=70
    )
    
    generic_keywords = [
        f"{client.industry.name.lower()}",
        f"{client.industry.name.lower()} {campaign.target_location.lower()}",
        f"god {client.industry.name.lower()}"
    ]
    
    for keyword_text in generic_keywords:
        if keyword_text.strip():
            Keyword.objects.create(
                text=keyword_text,
                ad_group=generic_adgroup,
                match_type='phrase',
                max_cpc=12.00
            )
    
    # Create ads for each ad group
    ad_groups = [brand_adgroup, service_adgroup, generic_adgroup]
    
    for i, ad_group in enumerate(ad_groups):
        if ad_group.name == "Brand Keywords":
            headline1 = f"{brand_name}"[:30]
            headline2 = f"{usp1}"[:30]
            headline3 = f"{campaign.target_location}"[:30]
        else:
            headline1 = f"{client.industry.name} i {campaign.target_location}"[:30]
            headline2 = f"{usp1}"[:30]  
            headline3 = f"{usp2}"[:30]
        
        description1 = f"{usp3} - Ring i dag for gratis tilbud!"[:90]
        description2 = f"Professionel {client.industry.name.lower()} siden mange år"[:90]
        
        Ad.objects.create(
            ad_group=ad_group,
            headline_1=headline1,
            headline_2=headline2,
            headline_3=headline3,
            description_1=description1,
            description_2=description2,
            final_url=client.website_url,
            display_path_1=client.industry.name.lower().replace(' ', '')[:15],
            display_path_2=campaign.target_location.split(',')[0].lower()[:15]
        )


def geo_campaign_builder(request):
    """Geografisk kampagne builder med kort interface"""
    
    if request.method == 'POST':
        return create_geo_campaign(request)
    
    # Hent data til form
    industries = Industry.objects.all()
    geo_templates = GeoTemplate.objects.filter(is_active=True)
    
    context = {
        'industries': industries,
        'geo_templates': geo_templates,
        'google_maps_api_key': 'AIzaSyBDH6MTS0Hq0ISb0bNQjEAC14321pzM0jw',  # Fra dit kort eksempel
    }
    
    return render(request, 'campaigns/geo_builder.html', context)


def geo_campaign_builder_v2(request):
    """New multi-step geografisk kampagne builder"""
    
    if request.method == 'POST':
        return create_geo_campaign_v2(request)
    
    # Hent data til form
    industries = Industry.objects.all()
    geo_templates = GeoTemplate.objects.filter(is_active=True)
    
    # Get active negative keyword lists for selection
    negative_keyword_lists = NegativeKeywordList.objects.filter(
        is_active=True
    ).select_related('created_by').prefetch_related('negative_keywords')
    
    # Get USP categories and templates for selection
    usp_categories = USPMainCategory.objects.filter(
        is_active=True
    ).order_by('sort_order')
    
    usp_templates = USPTemplate.objects.filter(
        is_active=True,
        main_category__is_active=True
    ).select_related('main_category').prefetch_related('ideal_for_industries').order_by(
        'main_category__sort_order', 'priority_rank'
    )
    
    context = {
        'industries': industries,
        'geo_templates': geo_templates,
        'negative_keyword_lists': negative_keyword_lists,
        'usp_categories': usp_categories,
        'usp_templates': usp_templates,
        'google_maps_api_key': 'AIzaSyBDH6MTS0Hq0ISb0bNQjEAC14321pzM0jw',
    }
    
    return render(request, 'campaigns/geo_builder_v2.html', context)


def create_geo_campaign(request):
    """Opret geo kampagne baseret på kort udvalg"""
    try:
        # Basic data
        client_name = request.POST.get('client_name')
        industry_id = request.POST.get('industry')
        website_url = request.POST.get('website_url')
        service_name = request.POST.get('service_name')
        domain = request.POST.get('domain', '')
        
        # Geo data fra kort
        selected_cities = request.POST.get('selected_cities', '')
        cities = [city.strip() for city in selected_cities.split(',') if city.strip()]
        
        # Template data
        template_id = request.POST.get('template_id')
        meta_title_template = request.POST.get('meta_title_template')
        meta_description_template = request.POST.get('meta_description_template')
        
        # Validering
        is_valid, errors = validate_geo_data(service_name, cities)
        if not is_valid:
            for error in errors:
                messages.error(request, error)
            return redirect('geo_campaign_builder')
        
        if not all([client_name, industry_id, website_url, service_name]):
            messages.error(request, 'Alle påkrævede felter skal udfyldes')
            return redirect('geo_campaign_builder')
        
        # Opret eller hent template
        if template_id:
            template = GeoTemplate.objects.get(id=template_id)
        else:
            # Opret custom template
            template = GeoTemplate.objects.create(
                name=f"{service_name} Custom",
                service_name=service_name,
                meta_title_template=meta_title_template or f"{service_name} {{BYNAVN}} - 5/5 Stjerner på Trustpilot - Ring idag",
                meta_description_template=meta_description_template or f"Skal du bruge en dygtig {service_name.lower()} i {{BYNAVN}}, vi har hjælpet mere end 500 kunder. Kontakt os idag, vi køre dagligt i {{BYNAVN}}",
            )
        
        # Opret client og industry
        industry = Industry.objects.get(id=industry_id)
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        client, created = Client.objects.get_or_create(
            name=client_name,
            website_url=website_url,
            defaults={
                'industry': industry,
                'description': f'Geo kampagne for {service_name}',
                'created_by': user
            }
        )
        
        # Opret geo kampagne
        campaign_name = f"GEO: {service_name} - {len(cities)} byer"
        campaign, geo_keywords = GeoCampaignManager.create_geo_campaign(
            campaign_name=campaign_name,
            service_name=service_name,
            cities=cities,
            template=template,
            client=client,
            user=user
        )
        
        messages.success(request, f'Geo kampagne "{campaign_name}" oprettet med {len(geo_keywords)} keywords!')
        return redirect('geo_campaign_success', campaign_id=campaign.id)
        
    except Exception as e:
        messages.error(request, f'Fejl ved oprettelse af geo kampagne: {str(e)}')
        return redirect('geo_campaign_builder')


def geo_campaign_success(request, campaign_id):
    """Success side for geo kampagner"""
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        geo_keywords = GeoKeyword.objects.filter(campaign=campaign)
        
        if not geo_keywords.exists():
            messages.error(request, 'Ingen geo keywords fundet for kampagnen')
            return redirect('geo_campaign_builder')
        
        # Samlet statistik
        template = geo_keywords.first().template
        cities = [gk.city_name for gk in geo_keywords]
        
        context = {
            'campaign': campaign,
            'template': template,
            'geo_keywords_count': geo_keywords.count(),
            'cities': cities,
            'cities_count': len(cities),
            'service_name': template.service_name,
            'sample_keywords': geo_keywords[:5],
            'sample_urls': [gk.final_url for gk in geo_keywords[:3]],
        }
        
        return render(request, 'campaigns/geo_success.html', context)
        
    except Campaign.DoesNotExist:
        messages.error(request, 'Geo kampagne ikke fundet')
        return redirect('geo_campaign_builder')


@csrf_exempt
def export_geo_campaign(request, campaign_id, export_type):
    """Eksporter geo kampagne i forskellige formater"""
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        
        # Verificer at det er en geo kampagne
        geo_keywords = GeoKeyword.objects.filter(campaign=campaign)
        if not geo_keywords.exists():
            messages.error(request, 'Dette er ikke en geo kampagne')
            return redirect('campaign_success', campaign_id=campaign_id)
        
        # Eksporter
        response = GeoCampaignManager.export_geo_campaign(campaign, export_type)
        
        # Log eksport
        template = geo_keywords.first().template
        cities = [gk.city_name for gk in geo_keywords]
        
        GeoExport.objects.create(
            campaign=campaign,
            template=template,
            export_type=export_type,
            cities_exported=cities,
            keywords_count=geo_keywords.count(),
            exported_by=request.user if request.user.is_authenticated else None
        )
        
        return response
        
    except Campaign.DoesNotExist:
        messages.error(request, 'Kampagne ikke fundet')
        return redirect('geo_campaign_builder')
    except Exception as e:
        messages.error(request, f'Fejl ved eksport: {str(e)}')
        return redirect('geo_campaign_success', campaign_id=campaign_id)


@csrf_exempt 
def preview_geo_data(request):
    """AJAX endpoint til at preview geo data"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Kun POST requests tilladt'})
    
    try:
        service_name = request.POST.get('service_name')
        cities_string = request.POST.get('cities')
        domain = request.POST.get('domain', '')
        
        if not service_name or not cities_string:
            return JsonResponse({'error': 'Service navn og byer er påkrævet'})
        
        cities = [city.strip() for city in cities_string.split(',') if city.strip()]
        
        # Generer preview data
        generator = GeoKeywordGenerator(service_name, cities[:5], domain)  # Max 5 for preview
        keywords_data = generator.generate_keywords_data()
        
        # Sample WordPress data
        template = create_demo_geo_template(service_name)
        wp_data = generator.generate_wordpress_data(template)
        
        return JsonResponse({
            'success': True,
            'service_name': service_name,
            'cities_count': len(cities),
            'keywords_sample': keywords_data[:3],
            'wordpress_sample': wp_data[:3],
            'total_keywords': len(cities),
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Preview fejl: {str(e)}'})


def test_geo_system(request):
    """Test side til geo systemet"""
    
    # Test med Fugemand eksempel data
    service_name = "Fugemand"
    cities = ["Bagsværd", "Ølstykke", "Måløv", "Frederikssund", "Furesø"]
    domain = "lundsfugeservice.dk"
    
    # Opret template
    template = create_demo_geo_template(service_name)
    
    # Test generator
    generator = GeoKeywordGenerator(service_name, cities, domain)
    keywords_data = generator.generate_keywords_data()
    wordpress_data = generator.generate_wordpress_data(template)
    
    context = {
        'service_name': service_name,
        'cities': cities,
        'domain': domain,
        'template': template,
        'keywords_data': keywords_data,
        'wordpress_data': wordpress_data,
    }
    
    return render(request, 'campaigns/geo_test.html', context)


def create_geo_campaign_v2(request):
    """Create geo campaign from multi-step form"""
    try:
        # Step 1: Campaign settings
        client_name = request.POST.get('client_name')
        industry_id = request.POST.get('industry') 
        website_url = request.POST.get('website_url')
        service_name = request.POST.get('service_name')
        domain = request.POST.get('domain', '')
        budget_daily = request.POST.get('budget_daily', 500)
        budget_type = request.POST.get('budget_type', 'daily')
        ad_rotation = request.POST.get('ad_rotation', 'optimize')
        bidding_strategy = request.POST.get('bidding_strategy', 'enhanced_cpc')
        default_bid = request.POST.get('default_bid', 15.00)
        target_cpa = request.POST.get('target_cpa')
        target_roas = request.POST.get('target_roas')
        default_match_type = request.POST.get('default_match_type', 'phrase')
        
        # Step 2: Geography
        selected_cities = request.POST.get('selected_cities', '')
        cities = [city.strip() for city in selected_cities.split(',') if city.strip()]
        
        # Step 3: USP Workshop Data
        selected_usps_data = request.POST.get('selected_usps_data', '{}')
        try:
            usps_data = json.loads(selected_usps_data)
        except json.JSONDecodeError:
            usps_data = {}
        
        # Step 4: Headlines and descriptions
        # All headline templates (1-15)
        headline_templates = {}
        for i in range(1, 16):
            field_name = f'headline_{i}_template'
            default_value = ''
            if i == 1:
                default_value = '{SERVICE} {BYNAVN}'
            elif i == 2:
                default_value = '5/5 Stjerner Trustpilot'
            elif i == 3:
                default_value = 'Ring i dag - Gratis tilbud'
            
            headline_templates[field_name] = request.POST.get(field_name, default_value)
        
        # All description templates (1-4)
        description_templates = {}
        for i in range(1, 5):
            field_name = f'description_{i}_template'
            default_value = ''
            if i == 1:
                default_value = 'Professionel {SERVICE} i {BYNAVN} - Ring i dag for gratis tilbud!'
            elif i == 2:
                default_value = 'Erfaren {SERVICE} med 5/5 stjerner. Vi dækker {BYNAVN} og omegn.'
            
            description_templates[field_name] = request.POST.get(field_name, default_value)
        
        # Meta templates
        meta_title_template = request.POST.get('meta_title_template', '{SERVICE} {BYNAVN} - 5/5 Stjerner på Trustpilot - Ring idag')
        meta_description_template = request.POST.get('meta_description_template', 'Skal du bruge en dygtig {SERVICE} i {BYNAVN}, vi har hjælpet mere end 500 kunder. Kontakt os idag, vi køre dagligt i {BYNAVN}')
        
        # Validation
        is_valid, errors = validate_geo_data(service_name, cities)
        if not is_valid:
            for error in errors:
                messages.error(request, error)
            return redirect('geo_campaign_builder_v2')
            
        if not all([client_name, industry_id, website_url, service_name]):
            messages.error(request, 'Alle påkrævede felter skal udfyldes')
            return redirect('geo_campaign_builder_v2')
            
        # Validate headlines and descriptions character limits
        test_data = {'SERVICE': 'Test', 'BYNAVN': 'Test'}
        validation_errors = []
        
        # Validate first 3 headlines (required)
        for i in range(1, 4):
            field_name = f'headline_{i}_template'
            template = headline_templates.get(field_name, '')
            if template:
                try:
                    processed = template.replace('{SERVICE}', test_data['SERVICE']).replace('{BYNAVN}', test_data['BYNAVN'])
                    if len(processed) > 30:
                        validation_errors.append(f'Headline {i}: For lang ({len(processed)} karakterer, max 30)')
                except Exception:
                    validation_errors.append(f'Headline {i}: Ugyldig template')
        
        # Validate first 2 descriptions (required)
        for i in range(1, 3):
            field_name = f'description_{i}_template'
            template = description_templates.get(field_name, '')
            if template:
                try:
                    processed = template.replace('{SERVICE}', test_data['SERVICE']).replace('{BYNAVN}', test_data['BYNAVN'])
                    if len(processed) > 90:
                        validation_errors.append(f'Description {i}: For lang ({len(processed)} karakterer, max 90)')
                except Exception:
                    validation_errors.append(f'Description {i}: Ugyldig template')
        
        if validation_errors:
            for error in validation_errors:
                messages.error(request, error)
            return redirect('geo_campaign_builder_v2')
        
        # Create geo template with enhanced fields
        template = GeoTemplate.objects.create(
            name=f"{service_name} V2 Template",
            service_name=service_name,
            meta_title_template=meta_title_template,
            meta_description_template=meta_description_template,
            # Set all headline templates
            headline_1_template=headline_templates.get('headline_1_template', ''),
            headline_2_template=headline_templates.get('headline_2_template', ''),
            headline_3_template=headline_templates.get('headline_3_template', ''),
            headline_4_template=headline_templates.get('headline_4_template', ''),
            headline_5_template=headline_templates.get('headline_5_template', ''),
            headline_6_template=headline_templates.get('headline_6_template', ''),
            headline_7_template=headline_templates.get('headline_7_template', ''),
            headline_8_template=headline_templates.get('headline_8_template', ''),
            headline_9_template=headline_templates.get('headline_9_template', ''),
            headline_10_template=headline_templates.get('headline_10_template', ''),
            headline_11_template=headline_templates.get('headline_11_template', ''),
            headline_12_template=headline_templates.get('headline_12_template', ''),
            headline_13_template=headline_templates.get('headline_13_template', ''),
            headline_14_template=headline_templates.get('headline_14_template', ''),
            headline_15_template=headline_templates.get('headline_15_template', ''),
            
            # Set all description templates
            description_1_template=description_templates.get('description_1_template', ''),
            description_2_template=description_templates.get('description_2_template', ''),
            description_3_template=description_templates.get('description_3_template', ''),
            description_4_template=description_templates.get('description_4_template', ''),
            
            default_match_type=default_match_type,
        )
        
        # Create client and campaign with enhanced settings
        industry = Industry.objects.get(id=industry_id)
        from django.contrib.auth.models import User
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        client, created = Client.objects.get_or_create(
            name=client_name,
            website_url=website_url,
            defaults={
                'industry': industry,
                'description': f'Multi-step geo kampagne for {service_name}',
                'created_by': user
            }
        )
        
        # Create campaign with enhanced settings
        campaign_name = f"GEO V2: {service_name} - {len(cities)} byer"
        campaign = Campaign.objects.create(
            name=campaign_name,
            client=client,
            campaign_type='search',
            budget_daily=budget_daily,
            budget_type=budget_type,
            target_location='Multi-geo',
            ad_rotation=ad_rotation,
            bidding_strategy=bidding_strategy,
            default_bid=default_bid,
            target_cpa=float(target_cpa) if target_cpa else None,
            target_roas=float(target_roas) if target_roas else None,
            status='draft'
        )
        
        # Process and save USPs from USP Workshop
        usps_created = save_campaign_usps(campaign, client, usps_data)
        
        # Generate geo keywords using enhanced template
        from .geo_export import GeoCampaignManager
        geo_keywords = GeoCampaignManager.create_geo_keywords(
            campaign=campaign,
            template=template,
            cities=cities,
            domain=domain
        )
        
        messages.success(request, f'Multi-step geo kampagne "{campaign_name}" oprettet med {len(geo_keywords)} keywords og {usps_created} USPs!')
        return redirect('geo_campaign_success', campaign_id=campaign.id)
        
    except Exception as e:
        messages.error(request, f'Fejl ved oprettelse af geo kampagne: {str(e)}')
        return redirect('geo_campaign_builder_v2')


def save_campaign_usps(campaign, client, usps_data):
    """
    Process and save USPs from USP Workshop data
    
    Args:
        campaign: Campaign object
        client: Client object  
        usps_data: Dict with USP data from frontend
        
    Returns:
        int: Number of USPs created
    """
    from usps.models import ClientUSP, USPTemplate
    
    usps_created = 0
    
    for key, usp_info in usps_data.items():
        try:
            # Extract USP information
            template_id = usp_info.get('template_id')
            original_text = usp_info.get('original_text') 
            current_text = usp_info.get('current_text', '')
            is_modified = usp_info.get('is_modified', False)
            is_custom = usp_info.get('is_custom', False)
            
            # Skip empty USPs
            if not current_text or not current_text.strip():
                continue
                
            # Get template reference if not custom
            usp_template = None
            if not is_custom and template_id:
                try:
                    usp_template = USPTemplate.objects.get(id=template_id)
                except USPTemplate.DoesNotExist:
                    usp_template = None
            
            # Create ClientUSP
            client_usp = ClientUSP.objects.create(
                client=client,
                campaign=campaign,
                usp_template=usp_template,
                custom_text=current_text.strip(),
                original_text=original_text,
                is_modified=is_modified,
                is_custom=is_custom,
                is_selected=True
            )
            
            usps_created += 1
            
        except Exception as e:
            print(f"Error saving USP {key}: {e}")
            continue
    
    return usps_created


# =========================
# NEGATIVE KEYWORDS SYSTEM
# =========================

@login_required
def negative_keywords_dashboard(request):
    """Dashboard til negative keywords administration"""
    keyword_lists = NegativeKeywordList.objects.filter(
        created_by=request.user
    ).prefetch_related('negative_keywords')
    
    context = {
        'keyword_lists': keyword_lists,
        'total_keywords': sum(kl.keywords_count for kl in keyword_lists),
        'active_lists': keyword_lists.filter(is_active=True).count(),
    }
    
    return render(request, 'campaigns/negative_keywords_dashboard.html', context)


@login_required
def create_negative_keyword_list(request):
    """Opret ny negative keyword liste"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            category = request.POST.get('category', 'general')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active') == 'on'
            auto_apply_industries = request.POST.getlist('auto_apply_industries')
            
            keyword_list = NegativeKeywordList.objects.create(
                name=name,
                category=category,
                description=description,
                is_active=is_active,
                auto_apply_to_industries=auto_apply_industries,
                created_by=request.user
            )
            
            messages.success(request, f'Negative keyword liste "{name}" er oprettet!')
            return redirect('negative_keyword_list_detail', list_id=keyword_list.id)
            
        except Exception as e:
            messages.error(request, f'Fejl ved oprettelse: {str(e)}')
    
    # Get available industries for auto-apply
    industries = Industry.objects.all().values_list('name', flat=True)
    
    context = {
        'industries': industries,
        'category_choices': NegativeKeywordList.CATEGORY_CHOICES,
    }
    
    return render(request, 'campaigns/create_negative_keyword_list.html', context)


@login_required
def negative_keyword_list_detail(request, list_id):
    """Detaljer for en specifik negative keyword liste"""
    keyword_list = get_object_or_404(
        NegativeKeywordList, 
        id=list_id, 
        created_by=request.user
    )
    
    # Get keywords with pagination
    from django.core.paginator import Paginator
    keywords = keyword_list.negative_keywords.all()
    paginator = Paginator(keywords, 50)  # 50 keywords per side
    page = request.GET.get('page', 1)
    keywords_page = paginator.get_page(page)
    
    # Get upload history
    uploads = NegativeKeywordUpload.objects.filter(
        keyword_list=keyword_list
    ).order_by('-uploaded_at')[:10]
    
    context = {
        'keyword_list': keyword_list,
        'keywords': keywords_page,
        'uploads': uploads,
        'match_type_choices': NegativeKeyword.MATCH_TYPES,
    }
    
    return render(request, 'campaigns/negative_keyword_list_detail.html', context)


@login_required
def upload_negative_keywords(request, list_id):
    """Upload negative keywords fra fil"""
    keyword_list = get_object_or_404(
        NegativeKeywordList, 
        id=list_id, 
        created_by=request.user
    )
    
    if request.method == 'POST' and request.FILES.get('keyword_file'):
        try:
            uploaded_file = request.FILES['keyword_file']
            
            # Validér fil type
            if not uploaded_file.name.lower().endswith(('.txt', '.csv')):
                messages.error(request, 'Kun .txt og .csv filer er tilladt')
                return redirect('negative_keyword_list_detail', list_id=list_id)
            
            # Process file upload
            result = process_negative_keyword_file(
                uploaded_file, 
                keyword_list, 
                request.user
            )
            
            if result['success']:
                messages.success(
                    request, 
                    f'Upload færdig! {result["keywords_added"]} keywords tilføjet, {result["keywords_skipped"]} sprunget over'
                )
            else:
                messages.error(request, f'Upload fejl: {result["error"]}')
                
        except Exception as e:
            messages.error(request, f'Fejl ved upload: {str(e)}')
    
    return redirect('negative_keyword_list_detail', list_id=list_id)


def process_negative_keyword_file(uploaded_file, keyword_list, user):
    """Process uploaded negative keyword fil"""
    import csv
    import io
    from django.utils import timezone
    
    try:
        # Create upload record
        upload_record = NegativeKeywordUpload.objects.create(
            keyword_list=keyword_list,
            original_filename=uploaded_file.name,
            file_size_kb=uploaded_file.size // 1024,
            uploaded_by=user,
            status='processing'
        )
        
        # Read file content
        file_content = uploaded_file.read().decode('utf-8')
        lines = file_content.strip().split('\n')
        
        keywords_added = 0
        keywords_skipped = 0
        keywords_errors = 0
        error_details = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            try:
                # Parse keyword and match type
                keyword_text, match_type = parse_negative_keyword_line(line)
                
                # Check if keyword already exists
                if NegativeKeyword.objects.filter(
                    keyword_list=keyword_list,
                    keyword_text=keyword_text,
                    match_type=match_type
                ).exists():
                    keywords_skipped += 1
                    continue
                
                # Create negative keyword
                NegativeKeyword.objects.create(
                    keyword_list=keyword_list,
                    keyword_text=keyword_text,
                    match_type=match_type,
                    source_file_line=line_num
                )
                keywords_added += 1
                
            except Exception as e:
                keywords_errors += 1
                error_details.append(f'Linje {line_num}: {str(e)}')
        
        # Update upload record
        upload_record.status = 'completed'
        upload_record.completed_at = timezone.now()
        upload_record.total_lines = len(lines)
        upload_record.keywords_added = keywords_added
        upload_record.keywords_skipped = keywords_skipped
        upload_record.keywords_errors = keywords_errors
        upload_record.error_details = '\n'.join(error_details)
        upload_record.save()
        
        # Update keyword list count
        keyword_list.update_keywords_count()
        
        return {
            'success': True,
            'keywords_added': keywords_added,
            'keywords_skipped': keywords_skipped,
            'keywords_errors': keywords_errors
        }
        
    except Exception as e:
        # Update upload record with error
        upload_record.status = 'failed'
        upload_record.error_details = str(e)
        upload_record.completed_at = timezone.now()
        upload_record.save()
        
        return {
            'success': False,
            'error': str(e)
        }


def parse_negative_keyword_line(line):
    """Parse en linje fra negative keyword fil"""
    line = line.strip()
    
    # Remove leading minus if present
    if line.startswith('-'):
        line = line[1:].strip()
    
    # Determine match type based on symbols
    if line.startswith('[') and line.endswith(']'):
        match_type = 'exact'
        keyword_text = line[1:-1].strip()
    elif line.startswith('"') and line.endswith('"'):
        match_type = 'phrase'
        keyword_text = line[1:-1].strip()
    else:
        match_type = 'broad'
        keyword_text = line.strip()
    
    if not keyword_text:
        raise ValueError("Tomt keyword")
    
    return keyword_text, match_type


@login_required
def get_campaign_negative_keywords(request, campaign_id):
    """AJAX view til at hente negative keywords for kampagne"""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Get active negative keyword lists for this campaign
    negative_lists = NegativeKeywordList.objects.filter(
        campaignNegativekeywordlist__campaign=campaign,
        campaignNegativekeywordlist__is_active=True
    ).prefetch_related('negative_keywords')
    
    # Also get auto-applied lists based on industry
    auto_lists = NegativeKeywordList.objects.filter(
        is_active=True,
        auto_apply_to_industries__contains=[campaign.client.industry.name]
    ).prefetch_related('negative_keywords')
    
    # Combine all keywords
    all_keywords = []
    
    for neg_list in list(negative_lists) + list(auto_lists):
        for keyword in neg_list.negative_keywords.all():
            all_keywords.append({
                'text': keyword.keyword_text,
                'match_type': keyword.match_type,
                'list_name': neg_list.name,
                'formatted': str(keyword)
            })
    
    return JsonResponse({
        'keywords': all_keywords,
        'total_count': len(all_keywords)
    })


@login_required  
def apply_negative_keywords_to_campaign(request, campaign_id):
    """Anvend negative keyword lister til kampagne"""
    if request.method == 'POST':
        campaign = get_object_or_404(Campaign, id=campaign_id)
        selected_lists = request.POST.getlist('negative_lists')
        
        try:
            # Remove existing associations
            CampaignNegativeKeywordList.objects.filter(campaign=campaign).delete()
            
            # Add new associations
            for list_id in selected_lists:
                negative_list = NegativeKeywordList.objects.get(id=list_id)
                CampaignNegativeKeywordList.objects.create(
                    campaign=campaign,
                    negative_list=negative_list,
                    applied_by=request.user
                )
            
            messages.success(
                request, 
                f'{len(selected_lists)} negative keyword lister tilføjet til kampagne'
            )
            
        except Exception as e:
            messages.error(request, f'Fejl ved tilføjelse: {str(e)}')
    
    return redirect('campaign_detail', campaign_id=campaign_id)


# ====================================
# MODERN NEGATIVE KEYWORDS MANAGER - AJAX ENDPOINTS
# ====================================

@csrf_exempt
def negative_keywords_manager(request):
    """Modern negative keywords manager with enhanced UI"""
    if request.user.is_authenticated:
        keyword_lists = NegativeKeywordList.objects.filter(
            created_by=request.user
        ).prefetch_related('negative_keywords').select_related('industry').order_by('-created_at')
    else:
        # For demo purposes, show all lists when not authenticated
        keyword_lists = NegativeKeywordList.objects.all().prefetch_related('negative_keywords').select_related('industry').order_by('-created_at')
    
    # Get all industries for filter dropdown
    industries = Industry.objects.all().order_by('name')
    
    # Calculate statistics
    categories_used = set(kl.category for kl in keyword_lists)
    industries_used = set(kl.industry for kl in keyword_lists if kl.industry)
    
    context = {
        'keyword_lists': keyword_lists,
        'industries': industries,
        'total_keywords': sum(kl.keywords_count for kl in keyword_lists),
        'active_lists': keyword_lists.filter(is_active=True).count(),
        'categories_count': len(categories_used),
        'industries_count': len(industries_used),
    }
    
    return render(request, 'campaigns/negative_keywords_manager.html', context)


@csrf_exempt
def create_negative_keyword_list_ajax(request):
    """AJAX endpoint to create new negative keyword list"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', 'general')
            description = request.POST.get('description', '').strip()
            is_active = request.POST.get('is_active') == 'true'
            industry_id = request.POST.get('industry', '').strip()
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Liste navn er påkrævet'})
            
            # Check if name already exists for this user
            if NegativeKeywordList.objects.filter(
                name__iexact=name, 
                created_by=request.user
            ).exists():
                return JsonResponse({'success': False, 'error': 'En liste med dette navn eksisterer allerede'})
            
            # Get industry if provided
            industry = None
            if industry_id and industry_id != '':
                try:
                    industry = Industry.objects.get(id=industry_id)
                except Industry.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Ugyldig branche valgt'})
            
            keyword_list = NegativeKeywordList.objects.create(
                name=name,
                category=category,
                description=description,
                industry=industry,
                is_active=is_active,
                created_by=request.user,
                auto_apply_to_industries=[]
            )
            
            return JsonResponse({
                'success': True,
                'list': {
                    'id': keyword_list.id,
                    'name': keyword_list.name,
                    'category': keyword_list.category,
                    'description': keyword_list.description,
                    'is_active': keyword_list.is_active,
                    'keywords_count': 0
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt  
def add_negative_keyword_ajax(request):
    """AJAX endpoint to add new keyword to list"""
    if request.method == 'POST':
        try:
            list_id = request.POST.get('list_id')
            keyword_text = request.POST.get('keyword_text', '').strip()
            match_type = request.POST.get('match_type', 'broad')
            
            if not keyword_text:
                return JsonResponse({'success': False, 'error': 'Søgeord er påkrævet'})
            
            # Get the list (allow access for demo mode)
            if request.user.is_authenticated:
                keyword_list = get_object_or_404(
                    NegativeKeywordList, 
                    id=list_id, 
                    created_by=request.user
                )
            else:
                # Demo mode - allow access to any list
                keyword_list = get_object_or_404(NegativeKeywordList, id=list_id)
            
            # Intelligent hierarkisk analyse som ved Excel import
            from .services import NegativeKeywordConflictAnalyzer
            analyzer = NegativeKeywordConflictAnalyzer(keyword_list)
            
            # Normaliser keyword til analyzer format
            normalized_kw = {
                'text': keyword_text.lower().strip(),
                'original_text': keyword_text,
                'match_type': match_type
            }
            
            # Analyser relationerne
            relationships = analyzer._analyze_all_relationships(normalized_kw)
            removed_keywords = []
            
            if relationships['identical']:
                # Identisk keyword eksisterer allerede
                existing = relationships['identical'][0]
                return JsonResponse({
                    'success': False, 
                    'error': f'"{existing["original_text"]}" ({existing["match_type"]}) eksisterer allerede i listen'
                })
                
            elif relationships['blocked_by']:
                # Blokeret af højere hierarki
                blocking_kw = relationships['blocked_by'][0]
                return JsonResponse({
                    'success': False, 
                    'error': f'Blokeret af eksisterende "{blocking_kw["original_text"]}" ({blocking_kw["match_type"]}) - denne har højere hierarki og dækker allerede dette keyword'
                })
            
            else:
                # Safe to add - men check for cleanup opportunities
                if relationships['will_override']:
                    # Fjern redundante keywords først
                    for override_kw in relationships['will_override']:
                        existing_to_remove = NegativeKeyword.objects.filter(
                            id=override_kw['id'],
                            keyword_list=keyword_list
                        ).first()
                        
                        if existing_to_remove:
                            removed_keywords.append({
                                'text': existing_to_remove.keyword_text,
                                'match_type': existing_to_remove.match_type
                            })
                            existing_to_remove.delete()
                
                # Create the keyword
                keyword = NegativeKeyword.objects.create(
                    keyword_list=keyword_list,
                    keyword_text=keyword_text,
                    match_type=match_type
                )
                
                # Opdater keyword count
                keyword_list.update_keywords_count()
                
                response_data = {
                    'success': True,
                    'keyword': {
                        'id': keyword.id,
                        'text': keyword.keyword_text,
                        'match_type': keyword.match_type,
                        'match_type_display': keyword.get_match_type_display(),
                        'added_at': keyword.added_at.strftime('%d/%m %Y')
                    }
                }
                
                # Tilføj cleanup information hvis relevant
                if removed_keywords:
                    response_data['removed_keywords'] = removed_keywords
                    response_data['message'] = f'Tilføjet "{keyword_text}" ({match_type}) og fjernet {len(removed_keywords)} redundante keywords'
                
                return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt
def delete_negative_keyword_ajax(request, keyword_id):
    """AJAX endpoint to delete a negative keyword"""
    if request.method == 'POST':
        try:
            if request.user.is_authenticated:
                keyword = get_object_or_404(
                    NegativeKeyword, 
                    id=keyword_id,
                    keyword_list__created_by=request.user
                )
            else:
                # Demo mode - allow access to any keyword
                keyword = get_object_or_404(NegativeKeyword, id=keyword_id)
            
            keyword_text = keyword.keyword_text
            keyword.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Søgeordet "{keyword_text}" er slettet'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt
def update_negative_keyword_ajax(request, keyword_id):
    """AJAX endpoint to update a negative keyword"""
    if request.method == 'POST':
        try:
            if request.user.is_authenticated:
                keyword = get_object_or_404(
                    NegativeKeyword, 
                    id=keyword_id,
                    keyword_list__created_by=request.user
                )
            else:
                # Demo mode - allow access to any keyword
                keyword = get_object_or_404(NegativeKeyword, id=keyword_id)
            
            # Get new values
            new_keyword_text = request.POST.get('keyword_text', '').strip()
            new_match_type = request.POST.get('match_type', 'broad')
            
            # Validate inputs
            if not new_keyword_text:
                return JsonResponse({
                    'success': False, 
                    'error': 'Søgeord kan ikke være tomt'
                })
            
            if new_match_type not in ['broad', 'phrase', 'exact']:
                return JsonResponse({
                    'success': False, 
                    'error': 'Ugyldig match type'
                })
            
            # Check for duplicates in the same list (excluding current keyword)
            existing_keyword = NegativeKeyword.objects.filter(
                keyword_list=keyword.keyword_list,
                keyword_text__iexact=new_keyword_text,
                match_type=new_match_type
            ).exclude(id=keyword_id).first()
            
            if existing_keyword:
                return JsonResponse({
                    'success': False,
                    'error': f'Søgeordet "{new_keyword_text}" med {new_match_type} match findes allerede i listen'
                })
            
            # Update the keyword
            old_text = keyword.keyword_text
            old_match = keyword.match_type
            
            keyword.keyword_text = new_keyword_text
            keyword.match_type = new_match_type
            keyword.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Søgeord opdateret fra "{old_text}" ({old_match}) til "{new_keyword_text}" ({new_match_type})',
                'keyword': {
                    'id': keyword.id,
                    'text': keyword.keyword_text,
                    'match_type': keyword.match_type,
                    'match_type_display': keyword.get_match_type_display()
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt
def delete_negative_keyword_list_ajax(request, list_id):
    """AJAX endpoint to delete an entire negative keyword list"""
    if request.method == 'POST':
        try:
            keyword_list = get_object_or_404(
                NegativeKeywordList, 
                id=list_id,
                created_by=request.user
            )
            
            # Count keywords before deletion
            keywords_count = keyword_list.negative_keywords.count()
            list_name = keyword_list.name
            
            # Delete the list (keywords will be deleted automatically due to CASCADE)
            keyword_list.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Listen "{list_name}" og {keywords_count} søgeord er slettet'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt
def edit_negative_keyword_list_ajax(request, list_id):
    """AJAX endpoint to edit negative keyword list"""
    if request.method == 'POST':
        try:
            keyword_list = get_object_or_404(
                NegativeKeywordList, 
                id=list_id,
                created_by=request.user
            )
            
            # Update fields
            keyword_list.name = request.POST.get('name', keyword_list.name).strip()
            keyword_list.category = request.POST.get('category', keyword_list.category)
            keyword_list.description = request.POST.get('description', keyword_list.description).strip()
            keyword_list.is_active = request.POST.get('is_active') == 'true'
            
            # Update industry if provided
            industry_id = request.POST.get('industry')
            if industry_id:
                try:
                    from .models import Industry
                    industry = Industry.objects.get(id=industry_id)
                    keyword_list.industry = industry
                except Industry.DoesNotExist:
                    keyword_list.industry = None
            else:
                keyword_list.industry = None
            
            keyword_list.save()
            
            return JsonResponse({
                'success': True,
                'list': {
                    'id': keyword_list.id,
                    'name': keyword_list.name,
                    'category': keyword_list.category,
                    'description': keyword_list.description,
                    'is_active': keyword_list.is_active
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt 
def get_negative_keyword_list_ajax(request, list_id):
    """AJAX endpoint to get negative keyword list data"""
    if request.method == 'GET':
        try:
            keyword_list = get_object_or_404(
                NegativeKeywordList, 
                id=list_id,
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'list': {
                    'id': keyword_list.id,
                    'name': keyword_list.name,
                    'category': keyword_list.category,
                    'description': keyword_list.description,
                    'is_active': keyword_list.is_active,
                    'keywords_count': keyword_list.keywords_count
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt
def analyze_excel_import_for_list(request, list_id):
    """AJAX endpoint to analyze Excel import for specific list with conflict detection"""
    if request.method == 'POST':
        try:
            from .services import NegativeKeywordConflictAnalyzer
            import openpyxl
            import io
            
            # Get the list (allow access for demo mode)
            if request.user.is_authenticated:
                keyword_list = get_object_or_404(
                    NegativeKeywordList, 
                    id=list_id, 
                    created_by=request.user
                )
            else:
                # Demo mode - allow access to any list
                keyword_list = get_object_or_404(NegativeKeywordList, id=list_id)
            
            # Get uploaded file
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                return JsonResponse({'success': False, 'error': 'Ingen fil uploadet'})
            
            # Parse Excel file
            try:
                workbook = openpyxl.load_workbook(excel_file)
                worksheet = workbook.active
                
                # Read keywords from Excel
                import_keywords = []
                
                # Skip header row and read data
                for row_num in range(2, worksheet.max_row + 1):
                    keyword_text = worksheet.cell(row=row_num, column=1).value
                    match_type = worksheet.cell(row=row_num, column=2).value
                    
                    if keyword_text and match_type:
                        # Clean and validate data
                        keyword_text = str(keyword_text).strip()
                        match_type = str(match_type).lower().strip()
                        
                        # Normalize match type
                        if match_type in ['broad', 'broad match']:
                            match_type = 'broad'
                        elif match_type in ['phrase', 'phrase match']:
                            match_type = 'phrase'
                        elif match_type in ['exact', 'exact match']:
                            match_type = 'exact'
                        else:
                            continue  # Skip invalid match types
                        
                        if keyword_text:  # Only add non-empty keywords
                            import_keywords.append({
                                'text': keyword_text,
                                'match_type': match_type
                            })
                
                if not import_keywords:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Ingen gyldige keywords fundet i Excel filen. Tjek formatet.'
                    })
                
                # Initialize conflict analyzer
                analyzer = NegativeKeywordConflictAnalyzer(keyword_list)
                
                # Analyze conflicts
                analysis_result = analyzer.analyze_import(import_keywords)
                
                return JsonResponse({
                    'success': True,
                    'analysis': analysis_result,
                    'list_info': {
                        'id': keyword_list.id,
                        'name': keyword_list.name,
                        'existing_count': keyword_list.negative_keywords.count()
                    }
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'error': f'Fejl ved læsning af Excel fil: {str(e)}'
                })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt
def cleanup_keywords(request, list_id):
    """AJAX endpoint til at slette specifikke keywords fra listen"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            keyword_ids = data.get('keyword_ids', [])
            
            # Find keyword listen
            keyword_list = get_object_or_404(NegativeKeywordList, id=list_id)
            
            # Udfør cleanup
            from .services import NegativeKeywordConflictAnalyzer
            analyzer = NegativeKeywordConflictAnalyzer(keyword_list)
            result = analyzer.execute_cleanup(keyword_ids)
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'removed_count': result['removed_count'],
                    'removed_keywords': result['removed_keywords'],
                    'message': f"Successfuldt slettet {result['removed_count']} keywords"
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Ugyldig JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Fejl under sletning: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Kun POST requests tilladt'}, status=405)


@csrf_exempt
def execute_excel_import(request, list_id):
    """AJAX endpoint til at udføre den faktiske import efter konflikt-løsning"""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'excel_file' not in request.FILES:
                return JsonResponse({
                    'success': False,
                    'error': 'Ingen Excel fil uploadet'
                }, status=400)
            
            excel_file = request.FILES['excel_file']
            keywords_to_add = json.loads(request.POST.get('keywords_to_add', '[]'))
            
            # Find keyword listen
            keyword_list = get_object_or_404(NegativeKeywordList, id=list_id)
            
            # Parse Excel filen igen for at få rå data
            if excel_file.name.endswith('.xlsx'):
                import openpyxl
                workbook = openpyxl.load_workbook(excel_file, data_only=True)
                sheet = workbook.active
                excel_keywords = []
                
                for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
                    if row[0]:  # Hvis der er tekst i første kolonne
                        keyword_text = str(row[0]).strip()
                        match_type_raw = str(row[1]).strip().lower() if row[1] else 'broad'
                        
                        # Normalize match type from Excel format to our format
                        if match_type_raw in ['broad', 'broad match']:
                            match_type = 'broad'
                        elif match_type_raw in ['phrase', 'phrase match']:
                            match_type = 'phrase'
                        elif match_type_raw in ['exact', 'exact match']:
                            match_type = 'exact'
                        else:
                            match_type = 'broad'
                        
                        excel_keywords.append({
                            'text': keyword_text,
                            'match_type': match_type
                        })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Kun .xlsx filer understøttes'
                }, status=400)
            
            # Filtrer keywords baseret på brugerens valg (keywords_to_add)
            keywords_to_import = []
            print(f"[DEBUG] Filtering {len(excel_keywords)} excel keywords against {len(keywords_to_add)} selected")
            print(f"[DEBUG] Selected keywords: {keywords_to_add}")
            
            for kw in excel_keywords:
                # Check if this keyword should be added based on user selection
                # Normalize text to lowercase to match frontend analysis format
                keyword_key = f"{kw['text'].lower().strip()}_{kw['match_type']}"
                print(f"[DEBUG] Checking: {keyword_key}")
                if keyword_key in keywords_to_add:
                    keywords_to_import.append(kw)
                    print(f"[DEBUG] ✅ MATCHED: {keyword_key}")
                else:
                    print(f"[DEBUG] ❌ NOT SELECTED: {keyword_key}")
            
            keyword_list_debug = [f"{kw['text'].lower().strip()}_{kw['match_type']}" for kw in keywords_to_import]
            print(f"[DEBUG] Final keywords to import: {len(keywords_to_import)} - {keyword_list_debug}")
            
            # Intelligent hierarkisk import med auto-cleanup
            added_count = 0
            skipped_count = 0
            removed_count = 0
            errors = []
            removed_keywords = []
            
            # Brug conflict analyzer til hierarkisk analyse
            from .services import NegativeKeywordConflictAnalyzer
            analyzer = NegativeKeywordConflictAnalyzer(keyword_list)
            
            for kw in keywords_to_import:
                try:
                    # Normaliser keyword til format forventet af analyzer
                    normalized_kw = {
                        'text': kw['text'].lower().strip(),
                        'original_text': kw['text'],
                        'match_type': kw['match_type']
                    }
                    
                    # Analyser relationerne
                    relationships = analyzer._analyze_all_relationships(normalized_kw)
                    
                    if relationships['identical']:
                        # Identisk keyword eksisterer allerede - skip
                        skipped_count += 1
                        print(f"[DEBUG] SKIPPED - Identisk: {kw['text']} ({kw['match_type']})")
                        
                    elif relationships['blocked_by']:
                        # Blokeret af højere hierarki - skip
                        blocking_kw = relationships['blocked_by'][0]
                        skipped_count += 1
                        print(f"[DEBUG] BLOCKED - {kw['text']} ({kw['match_type']}) blokeret af {blocking_kw['original_text']} ({blocking_kw['match_type']})")
                        
                    else:
                        # Safe to add eller vil overskrive eksisterende
                        if relationships['will_override']:
                            # Fjern redundante keywords først
                            for override_kw in relationships['will_override']:
                                existing_to_remove = NegativeKeyword.objects.filter(
                                    id=override_kw['id'],
                                    keyword_list=keyword_list
                                ).first()
                                
                                if existing_to_remove:
                                    removed_keywords.append(f"{existing_to_remove.keyword_text} ({existing_to_remove.match_type})")
                                    existing_to_remove.delete()
                                    removed_count += 1
                                    print(f"[DEBUG] REMOVED - {existing_to_remove.keyword_text} ({existing_to_remove.match_type}) - overskrevet af {kw['text']} ({kw['match_type']})")
                        
                        # Tilføj det nye keyword
                        new_keyword = NegativeKeyword.objects.create(
                            keyword_list=keyword_list,
                            keyword_text=kw['text'],
                            match_type=kw['match_type']
                        )
                        added_count += 1
                        print(f"[DEBUG] ADDED - {kw['text']} ({kw['match_type']})")
                        
                        # Opdater analyzer's existing keywords efter tilføjelse
                        analyzer.existing_keywords = analyzer._get_existing_keywords()
                        
                except Exception as e:
                    errors.append(f"Fejl ved tilføjelse af '{kw['text']}': {str(e)}")
                    print(f"[DEBUG] ERROR - {kw['text']}: {str(e)}")
            
            # Opdater keywords count på listen
            keyword_list.update_keywords_count()
            
            print(f"[FINAL DEBUG] Import result: {added_count} added, {skipped_count} skipped, {len(errors)} errors")
            
            # Opret intelligent besked
            message_parts = [f"{added_count} tilføjet"]
            if removed_count > 0:
                message_parts.append(f"{removed_count} fjernet (redundante)")
            if skipped_count > 0:
                message_parts.append(f"{skipped_count} sprunget over")
            
            return JsonResponse({
                'success': True,
                'added_count': added_count,
                'skipped_count': skipped_count,
                'removed_count': removed_count,
                'removed_keywords': removed_keywords,
                'errors': errors,
                'total_keywords_in_list': keyword_list.keywords_count,
                'message': f"Import færdig: {', '.join(message_parts)}"
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Ugyldig JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Fejl under import: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Kun POST requests tilladt'}, status=405)


def download_negative_keywords_template(request):
    """Download Excel template for negative keywords import"""
    import openpyxl
    from django.http import HttpResponse
    from openpyxl.styles import Font, PatternFill
    import io
    
    # Create workbook and worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Negative Keywords Template"
    
    # Headers - kun 2 kolonner: Søgeord og Match Type
    headers = ['Søgeord', 'Match Type']
    for col, header in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")
    
    # Example data - kun søgeord og match type
    examples = [
        ['gratis', 'broad'],
        ['job', 'phrase'],
        ['diy', 'broad'],
        ['billigst', 'broad'],
        ['københavn', 'exact'],
    ]
    
    for row, example in enumerate(examples, 2):
        for col, value in enumerate(example, 1):
            worksheet.cell(row=row, column=col).value = value
    
    # Adjust column widths
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        worksheet.column_dimensions[column_letter].width = min(adjusted_width, 50)
    
    # Save to response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="negative_keywords_template.xlsx"'
    
    # Save workbook to response
    virtual_workbook = io.BytesIO()
    workbook.save(virtual_workbook)
    virtual_workbook.seek(0)
    response.write(virtual_workbook.read())
    
    return response


@csrf_exempt
def import_negative_keywords_excel(request):
    """AJAX endpoint to import negative keywords from Excel file"""
    if request.method == 'POST':
        try:
            if 'excel_file' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'Ingen fil uploaded'})
            
            excel_file = request.FILES['excel_file']
            
            # Validate file type
            if not excel_file.name.lower().endswith(('.xlsx', '.xls')):
                return JsonResponse({'success': False, 'error': 'Kun Excel filer (.xlsx, .xls) er understøttet'})
            
            # Process the Excel file
            result = process_negative_keywords_excel(excel_file, request.user)
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Fejl ved import: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


def process_negative_keywords_excel(excel_file, user):
    """Process uploaded Excel file with negative keywords"""
    import openpyxl
    import io
    from collections import defaultdict
    
    try:
        # Read Excel file
        workbook = openpyxl.load_workbook(excel_file)
        worksheet = workbook.active
        
        # Expected headers
        expected_headers = ['Liste Navn', 'Kategori', 'Søgeord', 'Match Type']
        
        # Get headers from first row
        headers = []
        for col in range(1, 6):  # Check first 5 columns
            cell_value = worksheet.cell(row=1, column=col).value
            if cell_value:
                headers.append(str(cell_value).strip())
        
        # Check if we have minimum required headers
        missing_headers = []
        for expected in expected_headers:
            if expected not in headers:
                missing_headers.append(expected)
        
        if missing_headers:
            return {
                'success': False, 
                'error': f'Manglende kolonner: {", ".join(missing_headers)}'
            }
        
        # Map header positions
        header_map = {}
        for i, header in enumerate(headers):
            header_map[header] = i + 1
        
        # Process data rows
        lists_data = defaultdict(lambda: {
            'category': 'general',
            'keywords': []
        })
        
        processed_rows = 0
        skipped_rows = 0
        errors = []
        
        for row_num in range(2, worksheet.max_row + 1):
            try:
                # Get cell values
                list_name = worksheet.cell(row=row_num, column=header_map['Liste Navn']).value
                category = worksheet.cell(row=row_num, column=header_map.get('Kategori', 1)).value
                keyword = worksheet.cell(row=row_num, column=header_map['Søgeord']).value
                match_type = worksheet.cell(row=row_num, column=header_map['Match Type']).value
                
                # Skip empty rows
                if not list_name or not keyword:
                    skipped_rows += 1
                    continue
                
                # Clean and validate data
                list_name = str(list_name).strip()
                category = str(category).strip().lower() if category else 'general'
                keyword = str(keyword).strip()
                match_type = str(match_type).strip().lower() if match_type else 'broad'
                
                # Validate match type
                valid_match_types = ['broad', 'phrase', 'exact']
                if match_type not in valid_match_types:
                    match_type = 'broad'
                
                # Validate category
                valid_categories = [
                    'general', 'job', 'diy', 'competitor', 'location', 
                    'service_specific', 'quality', 'other'
                ]
                if category not in valid_categories:
                    category = 'general'
                
                # Add to lists_data
                if list_name not in lists_data:
                    lists_data[list_name]['category'] = category
                
                lists_data[list_name]['keywords'].append({
                    'text': keyword,
                    'match_type': match_type
                })
                
                processed_rows += 1
                
            except Exception as e:
                errors.append(f'Række {row_num}: {str(e)}')
                skipped_rows += 1
                continue
        
        # Create lists and keywords in database
        created_lists = 0
        created_keywords = 0
        
        for list_name, list_data in lists_data.items():
            try:
                # Get or create the list
                keyword_list, created = NegativeKeywordList.objects.get_or_create(
                    name=list_name,
                    created_by=user,
                    defaults={
                        'category': list_data['category'],
                        'description': f'Importeret fra Excel - {len(list_data["keywords"])} søgeord',
                        'is_active': True,
                        'auto_apply_to_industries': []
                    }
                )
                
                if created:
                    created_lists += 1
                
                # Add keywords to the list
                for keyword_data in list_data['keywords']:
                    # Check if keyword already exists
                    if not NegativeKeyword.objects.filter(
                        keyword_list=keyword_list,
                        keyword_text__iexact=keyword_data['text'],
                        match_type=keyword_data['match_type']
                    ).exists():
                        NegativeKeyword.objects.create(
                            keyword_list=keyword_list,
                            keyword_text=keyword_data['text'],
                            match_type=keyword_data['match_type']
                        )
                        created_keywords += 1
                
            except Exception as e:
                errors.append(f'Liste "{list_name}": {str(e)}')
                continue
        
        # Return results
        return {
            'success': True,
            'summary': {
                'created_lists': created_lists,
                'created_keywords': created_keywords,
                'processed_rows': processed_rows,
                'skipped_rows': skipped_rows,
                'errors': errors[:10]  # Limit to first 10 errors
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Fejl ved læsning af Excel fil: {str(e)}'
        }
