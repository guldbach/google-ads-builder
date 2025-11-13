from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from campaigns.models import Client, Industry
from crawler.services import WebsiteCrawler, USPMatcher


class Command(BaseCommand):
    help = 'Crawl a client website and extract USPs'

    def add_arguments(self, parser):
        parser.add_argument('--client-id', type=int, help='Client ID to crawl')
        parser.add_argument('--url', type=str, help='Website URL to crawl')
        parser.add_argument('--max-pages', type=int, default=10, help='Maximum pages to crawl')
        parser.add_argument('--create-test-client', action='store_true', help='Create a test client')

    def handle(self, *args, **options):
        if options['create_test_client']:
            self.create_test_client()
            return

        client_id = options.get('client_id')
        url = options.get('url')
        max_pages = options.get('max_pages', 10)

        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                self.stdout.write(f"Crawling website for client: {client.name}")
            except Client.DoesNotExist:
                raise CommandError(f'Client with id {client_id} does not exist')
        elif url:
            # Create temporary client for testing
            client = self.create_temp_client(url)
        else:
            raise CommandError('Either --client-id or --url must be provided')

        # Start crawling
        self.stdout.write(f"Starting crawl of {client.website_url} (max {max_pages} pages)...")
        
        crawler = WebsiteCrawler(client, max_pages=max_pages, delay=0.5)
        crawl_session = crawler.crawl_website()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Crawl completed! Session ID: {crawl_session.id}, '
                f'Status: {crawl_session.status}, '
                f'Pages crawled: {crawl_session.pages_crawled}'
            )
        )
        
        if crawl_session.status == 'completed':
            # Match USPs
            self.stdout.write("Matching extracted USPs with templates...")
            matcher = USPMatcher(client)
            matcher.match_extracted_usps()
            self.stdout.write(self.style.SUCCESS('USP matching completed!'))
            
            # Show results
            self.show_results(crawl_session)
        else:
            self.stdout.write(
                self.style.ERROR(f'Crawl failed: {crawl_session.error_message}')
            )

    def create_temp_client(self, url):
        """Create a temporary client for testing"""
        # Get or create default industry
        industry, _ = Industry.objects.get_or_create(
            name='Test Industry',
            defaults={'description': 'Test industry for crawler testing'}
        )
        
        # Get or create default user
        user, _ = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com'}
        )
        
        # Create client
        client = Client.objects.create(
            name=f'Test Client - {url}',
            website_url=url,
            industry=industry,
            description='Temporary client for testing crawler',
            created_by=user
        )
        
        self.stdout.write(f"Created temporary client: {client.name} (ID: {client.id})")
        return client

    def create_test_client(self):
        """Create a test client with sample data"""
        # Get or create industry
        industry, created = Industry.objects.get_or_create(
            name='Kloakservice',
            defaults={'description': 'Kloakservice og VVS reparationer'}
        )
        
        if created:
            self.stdout.write("Created industry: Kloakservice")
        
        # Get or create user
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write("Created admin user (password: admin123)")
        
        # Create test client
        client, created = Client.objects.get_or_create(
            name='Test Kloakservice A/S',
            defaults={
                'website_url': 'https://example.com',
                'industry': industry,
                'description': 'Test kloakservice virksomhed',
                'created_by': user
            }
        )
        
        if created:
            self.stdout.write(f"Created test client: {client.name} (ID: {client.id})")
        else:
            self.stdout.write(f"Test client already exists: {client.name} (ID: {client.id})")

    def show_results(self, crawl_session):
        """Show crawl results summary"""
        from crawler.models import WebPage, ExtractedUSP, ServiceArea
        from usps.models import ClientUSP
        
        pages = WebPage.objects.filter(crawl_session=crawl_session)
        usps = ExtractedUSP.objects.filter(web_page__crawl_session=crawl_session)
        services = ServiceArea.objects.filter(web_page__crawl_session=crawl_session)
        client_usps = ClientUSP.objects.filter(client=crawl_session.client)
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("CRAWL RESULTS SUMMARY")
        self.stdout.write("="*50)
        
        self.stdout.write(f"Pages crawled: {pages.count()}")
        self.stdout.write(f"Service pages: {pages.filter(is_service_page=True).count()}")
        self.stdout.write(f"About pages: {pages.filter(is_about_page=True).count()}")
        self.stdout.write(f"Contact pages: {pages.filter(is_contact_page=True).count()}")
        
        self.stdout.write(f"\nExtracted USPs: {usps.count()}")
        for usp in usps[:5]:  # Show first 5
            self.stdout.write(f"  - {usp.text[:60]}...")
        
        self.stdout.write(f"\nService areas: {services.count()}")
        for service in services[:5]:  # Show first 5
            self.stdout.write(f"  - {service.service_name}")
        
        self.stdout.write(f"\nClient USPs created: {client_usps.count()}")
        for client_usp in client_usps[:5]:  # Show first 5
            self.stdout.write(f"  - {client_usp.custom_text[:60]}...")
        
        self.stdout.write("\n" + "="*50)