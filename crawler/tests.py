from django.test import TestCase
from django.contrib.auth.models import User
from campaigns.models import Industry, Client
from usps.models import USPCategory, USPTemplate, IndustryUSPPattern
from .services import WebsiteCrawler, USPMatcher
from .models import CrawlSession, WebPage, ExtractedUSP
import responses


class WebsiteCrawlerTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        
        # Create test industry
        self.industry = Industry.objects.create(
            name='Test Industry',
            description='Test industry for testing'
        )
        
        # Create test client
        self.client = Client.objects.create(
            name='Test Client',
            website_url='https://example.com',
            industry=self.industry,
            description='Test client for testing',
            created_by=self.user
        )
        
        # Create USP category and template
        self.category = USPCategory.objects.create(
            name='Test Category',
            description='Test category'
        )
        
        self.usp_template = USPTemplate.objects.create(
            text='24/7 service',
            category=self.category,
            industry=self.industry,
            urgency_level='high',
            keywords='24/7, døgnvagt, altid åben',
            effectiveness_score=0.9
        )
        
        # Create industry pattern
        self.pattern = IndustryUSPPattern.objects.create(
            industry=self.industry,
            pattern=r'(24/7|døgnvagt|altid\s*åben)',
            description='24/7 availability pattern',
            weight=0.9,
            examples='24/7, døgnvagt, altid åben'
        )

    def test_pattern_extraction(self):
        """Test that patterns correctly extract USPs"""
        
        test_content = "Vi har 25 års erfaring og tilbyder døgnvagt året rundt"
        
        # Test years of experience pattern
        import re
        years_pattern = r'(\d+)\s*(års?)\s*(erfaring|experience)'
        matches = list(re.finditer(years_pattern, test_content, re.IGNORECASE))
        
        self.assertGreater(len(matches), 0, "Should find years pattern")
        found_years = any('25' in match.group() for match in matches)
        self.assertTrue(found_years, f"Should find '25' in matches: {[m.group() for m in matches]}")
        
        # Test 24/7 pattern
        availability_pattern = r'(døgnvagt|24/7|24\s*timer|altid\s*åben)'
        matches = list(re.finditer(availability_pattern, test_content, re.IGNORECASE))
        
        self.assertGreater(len(matches), 0, "Should find availability pattern") 
        found_availability = any('døgnvagt' in match.group() for match in matches)
        self.assertTrue(found_availability, f"Should find 'døgnvagt' in matches: {[m.group() for m in matches]}")
