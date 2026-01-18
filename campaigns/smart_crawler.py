"""
Smart Sitemap Crawler Service
Handles intelligent crawling with modification detection and page categorization.
"""
import hashlib
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from email.utils import parsedate_to_datetime

from django.utils import timezone

from .sitemap_service import SitemapCrawler
from .geo_utils import DanishSlugGenerator


class SmartCrawler:
    """
    Smart crawler that tracks page modifications and categorizes pages.
    """

    def __init__(self, client, timeout: int = 10):
        self.client = client
        # Ensure website URL has protocol
        website_url = client.website_url.rstrip('/') if client.website_url else ''
        if website_url and not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        self.website_url = website_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GoogleAdsBuilder/1.0)'
        })

    def sync_sitemap(self) -> Dict:
        """
        Sync TrackedPages with website sitemap.

        1. Crawl sitemap.xml
        2. For each URL: create/update TrackedPage
        3. Mark found_in_sitemap = True for found pages
        4. Auto-detect page types
        5. Return stats

        Returns:
            Dict with {success, new_pages, updated_pages, total_pages, message}
        """
        from .models import TrackedPage

        if not self.website_url:
            return {
                'success': False,
                'message': 'Ingen website URL konfigureret',
                'new_pages': 0,
                'updated_pages': 0,
                'total_pages': 0
            }

        # Crawl sitemap
        crawler = SitemapCrawler(self.website_url, self.timeout)
        success, urls, message = crawler.crawl_all_urls()

        if not success:
            return {
                'success': False,
                'message': message,
                'new_pages': 0,
                'updated_pages': 0,
                'total_pages': 0
            }

        # Get city slugs for byside detection
        city_slugs = self._get_city_slugs()

        # Reset found_in_sitemap for all pages
        TrackedPage.objects.filter(client=self.client).update(found_in_sitemap=False)

        new_pages = 0
        updated_pages = 0

        for url in urls:
            # Extract path from URL
            parsed = urlparse(url)
            url_path = parsed.path or '/'

            # Ensure path ends with /
            if not url_path.endswith('/'):
                url_path += '/'

            # Detect page type
            page_type = self._detect_page_type(url_path, city_slugs)

            # Create or update TrackedPage
            tracked_page, created = TrackedPage.objects.get_or_create(
                client=self.client,
                url_path=url_path,
                defaults={
                    'full_url': url,
                    'page_type': page_type,
                    'found_in_sitemap': True,
                }
            )

            if created:
                new_pages += 1
            else:
                # Update existing page
                tracked_page.found_in_sitemap = True
                tracked_page.full_url = url
                if tracked_page.page_type == 'service':
                    # Only update type if it was default
                    tracked_page.page_type = page_type
                tracked_page.save()
                updated_pages += 1

        total_pages = TrackedPage.objects.filter(client=self.client).count()

        return {
            'success': True,
            'message': f'Fandt {len(urls)} sider i sitemap',
            'new_pages': new_pages,
            'updated_pages': updated_pages,
            'total_pages': total_pages
        }

    def check_page_headers(self, url: str) -> Dict:
        """
        Send HEAD request to check Last-Modified and ETag headers.

        Returns:
            Dict with {last_modified, etag, content_length, status_code}
        """
        result = {
            'last_modified': None,
            'etag': None,
            'content_length': None,
            'status_code': None,
            'error': None
        }

        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            result['status_code'] = response.status_code

            if response.status_code == 200:
                # Parse Last-Modified header
                last_modified = response.headers.get('Last-Modified')
                if last_modified:
                    try:
                        result['last_modified'] = parsedate_to_datetime(last_modified)
                    except (ValueError, TypeError):
                        pass

                # Get ETag
                result['etag'] = response.headers.get('ETag', '')

                # Get Content-Length
                content_length = response.headers.get('Content-Length')
                if content_length:
                    try:
                        result['content_length'] = int(content_length)
                    except ValueError:
                        pass

        except requests.RequestException as e:
            result['error'] = str(e)

        return result

    def check_modifications(self) -> Dict:
        """
        Check all tracked pages for modifications.

        Returns:
            Dict with {checked, modified, unchanged, errors}
        """
        from .models import TrackedPage

        pages = TrackedPage.objects.filter(
            client=self.client,
            found_in_sitemap=True
        )

        stats = {
            'checked': 0,
            'modified': 0,
            'unchanged': 0,
            'errors': 0
        }

        for page in pages:
            if not page.full_url:
                continue

            headers = self.check_page_headers(page.full_url)
            stats['checked'] += 1

            if headers['error']:
                stats['errors'] += 1
                continue

            # Check if modified
            is_modified = False

            if headers['last_modified']:
                if page.last_modified_header is None:
                    is_modified = True
                elif headers['last_modified'] > page.last_modified_header:
                    is_modified = True

            if headers['etag'] and headers['etag'] != page.etag:
                is_modified = True

            # Update page
            page.last_checked_at = timezone.now()
            if headers['last_modified']:
                page.last_modified_header = headers['last_modified']
            if headers['etag']:
                page.etag = headers['etag']
            page.save()

            if is_modified:
                stats['modified'] += 1
            else:
                stats['unchanged'] += 1

        return stats

    def _detect_page_type(self, url_path: str, city_slugs: List[str]) -> str:
        """
        Auto-detect page type based on URL path.

        Returns:
            'byside', 'service', 'blog', or 'other'
        """
        path = url_path.lower()

        # Check for city pages (byside)
        for slug in city_slugs:
            if slug in path:
                return 'byside'

        # Check for blog
        if '/blog/' in path or '/nyheder/' in path or '/artikel/' in path or '/news/' in path:
            return 'blog'

        # Check for other known types
        other_patterns = [
            '/kontakt', '/contact',
            '/om-os', '/om-', '/about',
            '/betingelser', '/vilkaar', '/terms',
            '/referencer', '/cases', '/portfolio',
            '/priser', '/prices', '/pricing',
            '/job', '/karriere', '/career',
            '/privatlivspolitik', '/privacy',
            '/cookie', '/gdpr'
        ]

        # Root page is 'other'
        if path == '/' or path == '':
            return 'other'

        if any(p in path for p in other_patterns):
            return 'other'

        # Default to service page
        return 'service'

    def _get_city_slugs(self) -> List[str]:
        """
        Get all city slugs from selected geographic regions.
        """
        from .models import GeographicRegion

        city_slugs = []

        campaign_config = self.client.campaign_config or {}
        selected_region_ids = campaign_config.get('geographic_region_ids', [])

        if not selected_region_ids:
            return city_slugs

        regions = GeographicRegion.objects.filter(id__in=selected_region_ids).prefetch_related('cities')

        for region in regions:
            for city in region.cities.all():
                slug = DanishSlugGenerator.slugify(city.city_name)
                city_slugs.append(slug)
                # Also add variant without hyphens
                city_slugs.append(slug.replace('-', ''))

        return city_slugs

    def get_page_stats(self) -> Dict:
        """
        Get statistics about tracked pages.

        Returns:
            Dict with counts by status and type
        """
        from .models import TrackedPage
        from django.db.models import Count

        pages = TrackedPage.objects.filter(client=self.client)

        # Count by type
        type_counts = dict(pages.values('page_type').annotate(count=Count('id')).values_list('page_type', 'count'))

        # Count by status
        total = pages.count()
        live_count = pages.filter(created_by_us=True, found_in_sitemap=True).count()
        pending_count = pages.filter(created_by_us=True, found_in_sitemap=False).count()
        existing_count = pages.filter(created_by_us=False).count()

        return {
            'total': total,
            'by_status': {
                'live': live_count,
                'pending': pending_count,
                'existing': existing_count,
            },
            'by_type': {
                'byside': type_counts.get('byside', 0),
                'service': type_counts.get('service', 0),
                'blog': type_counts.get('blog', 0),
                'other': type_counts.get('other', 0),
            }
        }


def sync_client_sitemap(client_id: int) -> Dict:
    """
    Convenience function to sync sitemap for a client.
    """
    from .models import Client

    try:
        client = Client.objects.get(id=client_id)
        crawler = SmartCrawler(client)
        return crawler.sync_sitemap()
    except Client.DoesNotExist:
        return {
            'success': False,
            'message': f'Client {client_id} not found'
        }
