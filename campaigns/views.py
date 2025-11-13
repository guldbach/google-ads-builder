from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Industry, Client, Campaign, AdGroup, Ad, Keyword, PerformanceDataImport, HistoricalCampaignPerformance, HistoricalKeywordPerformance
from usps.models import USPTemplate, ClientUSP
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
    
    context = {
        'industries': industries,
        'geo_templates': geo_templates,
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
        
        # Step 3: Headlines and descriptions
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
        
        # Generate geo keywords using enhanced template
        from .geo_export import GeoCampaignManager
        geo_keywords = GeoCampaignManager.create_geo_keywords(
            campaign=campaign,
            template=template,
            cities=cities,
            domain=domain
        )
        
        messages.success(request, f'Multi-step geo kampagne "{campaign_name}" oprettet med {len(geo_keywords)} keywords!')
        return redirect('geo_campaign_success', campaign_id=campaign.id)
        
    except Exception as e:
        messages.error(request, f'Fejl ved oprettelse af geo kampagne: {str(e)}')
        return redirect('geo_campaign_builder_v2')
