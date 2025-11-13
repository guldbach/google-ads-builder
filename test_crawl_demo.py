#!/usr/bin/env python
"""
Demo script til at teste web crawling funktionaliteten
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ads_builder.settings')
django.setup()

from django.contrib.auth.models import User
from campaigns.models import Industry, Client
from crawler.services import WebsiteCrawler, USPMatcher
from crawler.models import CrawlSession, WebPage, ExtractedUSP
from usps.models import ClientUSP
import requests_mock

def demo_crawling():
    print("🚀 Google Ads Builder - Web Crawling Demo")
    print("=" * 50)
    
    # Get or create test data
    industry = Industry.objects.get(name='Kloakservice')
    user = User.objects.get(username='admin')
    
    # Create a demo client
    client, created = Client.objects.get_or_create(
        name='Demo Kloakservice ApS',
        defaults={
            'website_url': 'https://demo-kloakservice.dk',
            'industry': industry,
            'description': 'Demo kloakservice til test af crawler',
            'created_by': user
        }
    )
    
    print(f"📋 Client: {client.name}")
    print(f"🌐 Website: {client.website_url}")
    print(f"🏢 Industry: {client.industry.name}")
    
    # Mock en realistisk kloakservice website
    mock_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Demo Kloakservice - Døgnvagt og hurtig service</title>
        <meta name="description" content="Professionel kloakservice med døgnvagt året rundt. 25 års erfaring. Akut service inden for 1-2 timer.">
    </head>
    <body>
        <header>
            <h1>Demo Kloakservice ApS</h1>
            <nav>
                <a href="/services">Services</a>
                <a href="/om-os">Om os</a>
                <a href="/kontakt">Kontakt</a>
            </nav>
        </header>
        
        <main>
            <section class="hero">
                <h1>Akut kloakservice - døgnvagt året rundt</h1>
                <p>Vi tilbyder hurtig og professionel kloakservice med døgnvagt året rundt. 
                Ring til os når som helst - vi er der inden for 1-2 timer!</p>
            </section>
            
            <section class="services">
                <h2>Vores services</h2>
                <ul>
                    <li>Akut kloakreparationer</li>
                    <li>Kloakspuling og rensning</li>
                    <li>TV-inspektion af kloak</li>
                    <li>Gratis besigtigelse og tilbud</li>
                </ul>
            </section>
            
            <section class="about">
                <h2>Over 25 års erfaring</h2>
                <p>Med over 25 års erfaring inden for kloakservice er vi specialister i alle typer 
                kloakproblemer. Vi er certificeret og tilbyder 2 års garanti på alt arbejde.</p>
                <p>Som lokal kloakmester i dit område er vi altid tæt på når du har brug for hjælp.</p>
            </section>
            
            <section class="guarantees">
                <h2>Vores garantier</h2>
                <ul>
                    <li>Døgnvagt 24/7 året rundt</li>
                    <li>Akut service inden for 1-2 timer</li>
                    <li>2 års garanti på alt arbejde</li>
                    <li>Fast pris - ingen overraskelser</li>
                    <li>Gratis besigtigelse</li>
                    <li>Weekend og helligdage service</li>
                </ul>
            </section>
        </main>
    </body>
    </html>
    '''
    
    # Simuler crawling med mock data
    with requests_mock.Mocker() as m:
        m.get('https://demo-kloakservice.dk', text=mock_html)
        
        print(f"\n🕷️  Starting crawl...")
        crawler = WebsiteCrawler(client, max_pages=1, delay=0)
        crawl_session = crawler.crawl_website()
        
        print(f"✅ Crawl completed!")
        print(f"   Status: {crawl_session.status}")
        print(f"   Pages crawled: {crawl_session.pages_crawled}")
        
        # Show results
        show_crawl_results(crawl_session)

def show_crawl_results(crawl_session):
    print(f"\n📊 CRAWL RESULTS")
    print("=" * 30)
    
    # Pages
    pages = WebPage.objects.filter(crawl_session=crawl_session)
    print(f"📄 Pages crawled: {pages.count()}")
    
    for page in pages:
        print(f"   📍 {page.url}")
        print(f"   📰 Title: {page.title}")
        print(f"   📝 Word count: {page.word_count}")
        print(f"   🏷️  Service page: {page.is_service_page}")
        print(f"   🏷️  About page: {page.is_about_page}")
    
    # Extracted USPs
    usps = ExtractedUSP.objects.filter(web_page__crawl_session=crawl_session)
    print(f"\n🎯 Extracted USPs: {usps.count()}")
    
    for usp in usps:
        print(f"   💡 '{usp.text}'")
        print(f"      Confidence: {usp.confidence_score:.2f}")
        print(f"      Method: {usp.extraction_method}")
        print(f"      Position: {usp.position_on_page}")
    
    # Client USPs (matched)
    client_usps = ClientUSP.objects.filter(client=crawl_session.client)
    print(f"\n🎪 Client USPs created: {client_usps.count()}")
    
    for client_usp in client_usps:
        print(f"   ✨ '{client_usp.custom_text}'")
        print(f"      Discovered: {client_usp.is_discovered}")
        print(f"      Selected: {client_usp.is_selected}")
        print(f"      Confidence: {client_usp.confidence_score:.2f}")
        if client_usp.usp_template:
            print(f"      Template: {client_usp.usp_template.text}")

def show_admin_info():
    print(f"\n🔐 ADMIN ACCESS")
    print("=" * 20)
    print(f"URL: http://localhost:8000/admin/")
    print(f"Username: admin")
    print(f"Password: admin123")
    print(f"\nYou can view all crawl data in the admin interface!")

if __name__ == "__main__":
    demo_crawling()
    show_admin_info()