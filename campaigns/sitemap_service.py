"""
Sitemap Crawling og City Page Matching Service
Bruges til at finde eksisterende bysider på kundens website.
"""

import re
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from .geo_utils import DanishSlugGenerator


class SitemapCrawler:
    """Crawler til kundens sitemap.xml"""

    def __init__(self, website_url: str, timeout: int = 10):
        self.website_url = website_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GoogleAdsBuilder/1.0; +https://example.com)'
        })

    def discover_sitemap(self) -> Optional[str]:
        """
        Find sitemap.xml - prøv standard placeringer.

        Returns:
            URL til sitemap hvis fundet, ellers None
        """
        # Standard sitemap lokationer at prøve
        sitemap_locations = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/wp-sitemap.xml',  # WordPress default
            '/sitemap/sitemap.xml',
            '/sitemaps/sitemap.xml',
        ]

        for location in sitemap_locations:
            sitemap_url = f"{self.website_url}{location}"
            try:
                response = self.session.head(sitemap_url, timeout=self.timeout, allow_redirects=True)
                if response.status_code == 200:
                    # Verificer at det er XML
                    content_type = response.headers.get('Content-Type', '')
                    if 'xml' in content_type or location.endswith('.xml'):
                        return sitemap_url
            except requests.RequestException:
                continue

        # Prøv robots.txt som fallback
        robots_sitemap = self._find_sitemap_in_robots()
        if robots_sitemap:
            return robots_sitemap

        return None

    def _find_sitemap_in_robots(self) -> Optional[str]:
        """Find sitemap URL fra robots.txt"""
        robots_url = f"{self.website_url}/robots.txt"
        try:
            response = self.session.get(robots_url, timeout=self.timeout)
            if response.status_code == 200:
                # Find "Sitemap:" linje
                for line in response.text.split('\n'):
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        return sitemap_url
        except requests.RequestException:
            pass
        return None

    def parse_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Parse sitemap XML og returner alle URLs.
        Håndterer både standard sitemap og sitemap index.

        Returns:
            Liste af alle URLs fundet i sitemap
        """
        all_urls = []

        try:
            response = self.session.get(sitemap_url, timeout=self.timeout)
            if response.status_code != 200:
                return []

            # Parse XML
            root = ET.fromstring(response.content)

            # Find namespace (kan variere)
            namespace = ''
            if root.tag.startswith('{'):
                namespace = root.tag.split('}')[0] + '}'

            # Check om det er sitemap index
            sitemaps = root.findall(f'.//{namespace}sitemap')
            if sitemaps:
                # Det er en sitemap index - parse hver sub-sitemap
                for sitemap in sitemaps:
                    loc = sitemap.find(f'{namespace}loc')
                    if loc is not None and loc.text:
                        sub_urls = self.parse_sitemap(loc.text)
                        all_urls.extend(sub_urls)
            else:
                # Standard sitemap - find alle URLs
                urls = root.findall(f'.//{namespace}url')
                for url in urls:
                    loc = url.find(f'{namespace}loc')
                    if loc is not None and loc.text:
                        all_urls.append(loc.text)

        except (requests.RequestException, ET.ParseError) as e:
            print(f"Sitemap parse error: {e}")

        return all_urls

    def crawl_all_urls(self) -> Tuple[bool, List[str], str]:
        """
        Hovedfunktion: Find og parse alle URLs fra sitemap.

        Returns:
            Tuple af (success, urls, message)
        """
        sitemap_url = self.discover_sitemap()

        if not sitemap_url:
            return False, [], "Kunne ikke finde sitemap.xml på websitet"

        urls = self.parse_sitemap(sitemap_url)

        if not urls:
            return False, [], f"Ingen URLs fundet i {sitemap_url}"

        return True, urls, f"Fandt {len(urls)} URLs i sitemap"


class CityPageMatcher:
    """Matcher URLs mod service+by kombinationer"""

    # Danske by-synonymer og varianter
    CITY_SYNONYMS = {
        'København': ['kobenhavn', 'koebenhavn', 'copenhagen', 'kbh', 'cph'],
        'Aarhus': ['aarhus', 'århus', 'aahus'],
        'Aalborg': ['aalborg', 'ålborg'],
        'Odense': ['odense'],
        'Randers': ['randers'],
        'Kolding': ['kolding'],
        'Horsens': ['horsens'],
        'Vejle': ['vejle'],
        'Roskilde': ['roskilde'],
        'Helsingør': ['helsingoer', 'helsingor', 'elsinore'],
        'Hillerød': ['hilleroed', 'hillerod'],
        'Næstved': ['naestved', 'nastved'],
        'Frederiksberg': ['frederiksberg', 'frb'],
        'Køge': ['koege', 'koge'],
        'Holbæk': ['holbaek', 'holbak'],
        'Slagelse': ['slagelse'],
        'Herning': ['herning'],
        'Silkeborg': ['silkeborg'],
        'Esbjerg': ['esbjerg'],
        'Fredericia': ['fredericia'],
        'Viborg': ['viborg'],
        'Sønderborg': ['soenderborg', 'sonderborg'],
        'Haderslev': ['haderslev'],
        'Rødovre': ['roedovre', 'rodovre'],
        'Hvidovre': ['hvidovre'],
        'Glostrup': ['glostrup'],
        'Albertslund': ['albertslund'],
        'Brøndby': ['broendby', 'brondby'],
        'Ishøj': ['ishoej', 'ishoj'],
        'Vallensbæk': ['vallensbaek', 'vallensbak'],
        'Greve': ['greve'],
        'Solrød': ['solroed', 'solrod'],
        'Taastrup': ['taastrup', 'høje-taastrup', 'hoeje-taastrup'],
        'Ballerup': ['ballerup'],
        'Gentofte': ['gentofte'],
        'Lyngby': ['lyngby', 'lyngby-taarbaek'],
        'Gladsaxe': ['gladsaxe'],
        'Herlev': ['herlev'],
        'Furesø': ['furesoe', 'fureso', 'farum', 'vaerloese'],
        'Egedal': ['egedal', 'olgod', 'smorum'],
        'Frederikssund': ['frederikssund'],
        'Allerød': ['alleroed', 'allerod'],
        'Hørsholm': ['hoersholm', 'horsholm'],
        'Rudersdal': ['rudersdal', 'birkeroed', 'holte'],
    }

    def __init__(self, service_name: str, cities: List[str]):
        self.service_name = service_name
        self.cities = cities
        self.service_slug = DanishSlugGenerator.slugify(service_name)

    def generate_url_variants(self, city: str) -> List[str]:
        """
        Generer alle mulige URL-varianter for en service+by kombination.

        Eksempel for "elektriker" + "København":
        - /elektriker-kobenhavn/
        - /elektriker-koebenhavn/
        - /elektrikerkobenhavn/
        - /elektriker_kobenhavn/
        - /elektriker-kbh/

        Returns:
            Liste af URL-varianter (uden domain)
        """
        variants = set()
        service_slug = self.service_slug

        # Hent by-varianter
        city_slugs = self._get_city_slug_variants(city)

        for city_slug in city_slugs:
            # Med bindestreg
            variants.add(f"/{service_slug}-{city_slug}/")
            variants.add(f"/{service_slug}-{city_slug}")

            # Uden bindestreg (sammenskrevet)
            variants.add(f"/{service_slug}{city_slug}/")
            variants.add(f"/{service_slug}{city_slug}")

            # Med underscore
            variants.add(f"/{service_slug}_{city_slug}/")
            variants.add(f"/{service_slug}_{city_slug}")

            # By først
            variants.add(f"/{city_slug}-{service_slug}/")
            variants.add(f"/{city_slug}-{service_slug}")

        return list(variants)

    def _get_city_slug_variants(self, city: str) -> List[str]:
        """Hent alle slug-varianter for en by"""
        variants = set()

        # Standard slug (æøå -> ae, oe, aa)
        standard_slug = DanishSlugGenerator.slugify(city)
        variants.add(standard_slug)

        # Uden bindestreger
        variants.add(standard_slug.replace('-', ''))

        # Find synonymer fra ordbog
        city_lower = city.lower()
        for canonical, synonyms in self.CITY_SYNONYMS.items():
            if city_lower == canonical.lower() or city_lower in [s.lower() for s in synonyms]:
                for synonym in synonyms:
                    variants.add(synonym.lower())
                    variants.add(synonym.lower().replace('-', ''))
                break

        return list(variants)

    def match_city_url(self, sitemap_urls: List[str], city: str) -> Optional[str]:
        """
        Find eksisterende URL for en by.

        Returns:
            URL hvis fundet, ellers None
        """
        variants = self.generate_url_variants(city)

        # Normaliser sitemap URLs til lowercase paths
        for sitemap_url in sitemap_urls:
            parsed = urlparse(sitemap_url)
            path = parsed.path.lower()

            for variant in variants:
                # Check om variant matcher path
                if path == variant.lower() or path == variant.lower().rstrip('/'):
                    return sitemap_url

                # Check også uden trailing slash
                if path.rstrip('/') == variant.lower().rstrip('/'):
                    return sitemap_url

        return None

    def match_all_cities(self, sitemap_urls: List[str]) -> List[Dict]:
        """
        Match alle byer mod sitemap URLs.

        Returns:
            Liste af dicts med {city, status, existing_url}
        """
        results = []
        existing_count = 0
        missing_count = 0

        for city in self.cities:
            existing_url = self.match_city_url(sitemap_urls, city)

            if existing_url:
                results.append({
                    'city': city,
                    'status': 'existing',
                    'existing_url': existing_url
                })
                existing_count += 1
            else:
                # Generer forventet URL for manglende side
                expected_url = DanishSlugGenerator.create_full_url(
                    self.service_name, city, leading_slash=True
                )
                results.append({
                    'city': city,
                    'status': 'missing',
                    'existing_url': None,
                    'expected_url': expected_url
                })
                missing_count += 1

        return results


def crawl_and_match(website_url: str, service_name: str, cities: List[str]) -> Dict:
    """
    Convenience funktion: Crawl sitemap og match alle byer.

    Returns:
        Dict med crawl og match resultater
    """
    # Crawl sitemap
    crawler = SitemapCrawler(website_url)
    success, urls, message = crawler.crawl_all_urls()

    if not success:
        return {
            'success': False,
            'error': message,
            'urls_found': 0,
            'results': []
        }

    # Match byer
    matcher = CityPageMatcher(service_name, cities)
    results = matcher.match_all_cities(urls)

    existing_count = sum(1 for r in results if r['status'] == 'existing')
    missing_count = sum(1 for r in results if r['status'] == 'missing')

    return {
        'success': True,
        'urls_found': len(urls),
        'message': message,
        'results': results,
        'existing_count': existing_count,
        'missing_count': missing_count
    }
