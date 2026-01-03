"""
Utility funktioner til geo marketing automation
"""

import re
import unicodedata
from typing import Dict, List, Tuple
from django.template import Context, Template


class DanishSlugGenerator:
    """Generator til danske URL slugs"""
    
    DANISH_CHAR_MAP = {
        'æ': 'ae',
        'ø': 'oe', 
        'å': 'aa',
        'Æ': 'AE',
        'Ø': 'OE',
        'Å': 'AA',
    }
    
    @classmethod
    def slugify(cls, text: str) -> str:
        """
        Konverter dansk tekst til URL-friendly slug
        
        Eksempler:
        "Måløv" -> "maaloev"
        "Frederikssund" -> "frederikssund" 
        "Bagsværd" -> "bagsvaerd"
        "Ølstykke" -> "oelstykke"
        """
        if not text:
            return ""
        
        # Konverter til lowercase
        text = text.lower().strip()
        
        # Erstat danske karakterer
        for danish_char, replacement in cls.DANISH_CHAR_MAP.items():
            text = text.replace(danish_char.lower(), replacement)
        
        # Fjern specielle karakterer og erstat med bindestreg
        text = re.sub(r'[^a-z0-9\-]', '-', text)
        
        # Fjern multiple bindestreger
        text = re.sub(r'-+', '-', text)
        
        # Fjern bindestreger fra start/slut
        text = text.strip('-')
        
        return text
    
    @classmethod
    def create_service_slug(cls, service: str, city: str) -> str:
        """
        Opret service+by slug
        
        Eksempel: ("Fugemand", "Bagsværd") -> "fugemand-bagsvaerd"
        """
        service_slug = cls.slugify(service)
        city_slug = cls.slugify(city)
        
        return f"{service_slug}-{city_slug}"
    
    @classmethod
    def create_full_url(cls, service: str, city: str, domain: str = "", leading_slash: bool = True) -> str:
        """
        Opret fuld landing page URL

        Eksempel: ("Fugemand", "Bagsværd", "lundsfugeservice.dk")
        -> "https://lundsfugeservice.dk/fugemand-bagsvaerd/"
        """
        slug = cls.create_service_slug(service, city)

        if domain:
            if not domain.startswith('http'):
                domain = f"https://{domain}"
            url = f"{domain}/{slug}/"
        else:
            url = f"/{slug}/" if leading_slash else f"{slug}/"

        return url

    @classmethod
    def generate_slug_variants(cls, text: str) -> List[str]:
        """
        Generer alle varianter af en slug til URL matching.

        Eksempel: "København" -> ['kobenhavn', 'koebenhavn', 'copenhagen', 'kbh']

        Returns:
            Liste af alle slug-varianter
        """
        if not text:
            return []

        variants = set()
        text_lower = text.lower().strip()

        # Standard slug med æøå -> ae, oe, aa
        standard_slug = cls.slugify(text)
        variants.add(standard_slug)

        # Uden bindestreger
        variants.add(standard_slug.replace('-', ''))

        # Med original æøå (til matching)
        simple_slug = re.sub(r'[^a-zæøå0-9\-]', '-', text_lower)
        simple_slug = re.sub(r'-+', '-', simple_slug).strip('-')
        if simple_slug:
            variants.add(simple_slug)
            variants.add(simple_slug.replace('-', ''))

        # Alternativ konvertering (ø -> o, æ -> a, å -> a)
        alt_map = {'æ': 'a', 'ø': 'o', 'å': 'a'}
        alt_text = text_lower
        for char, replacement in alt_map.items():
            alt_text = alt_text.replace(char, replacement)
        alt_slug = re.sub(r'[^a-z0-9\-]', '-', alt_text)
        alt_slug = re.sub(r'-+', '-', alt_slug).strip('-')
        if alt_slug and alt_slug != standard_slug:
            variants.add(alt_slug)
            variants.add(alt_slug.replace('-', ''))

        return list(variants)

    @classmethod
    def normalize_url_path(cls, url_path: str) -> str:
        """
        Normaliser en URL path til sammenligning.
        Fjerner slashes, lowercase, og standardiserer æøå.

        Eksempel: "/Elektriker-København/" -> "elektriker-koebenhavn"
        """
        if not url_path:
            return ""

        # Fjern slashes og lowercase
        path = url_path.strip('/').lower()

        # Erstat danske karakterer
        for danish_char, replacement in cls.DANISH_CHAR_MAP.items():
            path = path.replace(danish_char.lower(), replacement)

        # Fjern ugyldige karakterer
        path = re.sub(r'[^a-z0-9\-]', '', path)

        return path

    @classmethod
    def urls_match(cls, url1: str, url2: str) -> bool:
        """
        Check om to URLs matcher (ignorerer æøå varianter og slashes).

        Eksempel:
        "/elektriker-kobenhavn/" og "/elektriker-koebenhavn" -> True
        """
        return cls.normalize_url_path(url1) == cls.normalize_url_path(url2)


class GeoTemplateProcessor:
    """Processor til geo marketing templates med placeholders"""
    
    def __init__(self, service_name: str, city_name: str, domain: str = ""):
        self.service_name = service_name
        self.city_name = city_name
        self.domain = domain
        self.url_slug = DanishSlugGenerator.create_service_slug(service_name, city_name)
        self.full_url = DanishSlugGenerator.create_full_url(service_name, city_name, domain)
        
        # Context for template rendering
        self.context = {
            'SERVICE': service_name,
            'BYNAVN': city_name,
            'URL_SLUG': self.url_slug,
            'FULL_URL': self.full_url,
        }
    
    def process_template(self, template_text: str) -> str:
        """
        Process template med placeholders
        
        Eksempel:
        "{SERVICE} {BYNAVN} - 5/5 Stjerner" -> "Murer Bagsværd - 5/5 Stjerner"
        """
        if not template_text:
            return ""
        
        # Simple placeholder replacement
        result = template_text
        for placeholder, value in self.context.items():
            result = result.replace(f"{{{placeholder}}}", value)
        
        return result
    
    def process_geo_template(self, geo_template) -> Dict[str, str]:
        """
        Process en komplet GeoTemplate og returner alle felter
        
        Returns:
            Dict med processede template felter
        """
        return {
            'meta_title': self.process_template(geo_template.meta_title_template),
            'meta_description': self.process_template(geo_template.meta_description_template),
            'headline_1': self.process_template(geo_template.headline_1_template),
            'headline_2': self.process_template(geo_template.headline_2_template),
            'description_1': self.process_template(geo_template.description_1_template),
            'page_content': self.process_template(geo_template.page_content_template),
            'keyword_text': f"{geo_template.service_name} {self.city_name}",
            'final_url': self.full_url,
            'url_slug': self.url_slug,
        }


class GeoKeywordGenerator:
    """Generator til geo keywords og URLs"""
    
    def __init__(self, service_name: str, cities: List[str], domain: str = ""):
        self.service_name = service_name
        self.cities = cities
        self.domain = domain
    
    def generate_keywords_data(self) -> List[Dict[str, str]]:
        """
        Generer keywords data for alle byer
        
        Returns:
            Liste med keyword data dicts
        """
        keywords_data = []
        
        for city in self.cities:
            processor = GeoTemplateProcessor(self.service_name, city, self.domain)
            
            keyword_data = {
                'city_name': city,
                'city_slug': processor.url_slug.split('-')[-1],  # Sidste del efter bindestreg
                'keyword_text': f"{self.service_name} {city}",
                'final_url': processor.full_url,
                'url_slug': processor.url_slug,
            }
            
            keywords_data.append(keyword_data)
        
        return keywords_data
    
    def generate_wordpress_data(self, geo_template) -> List[Dict[str, str]]:
        """
        Generer WordPress WP All Import data
        
        Returns:
            Liste med WordPress import data
        """
        wordpress_data = []
        
        for city in self.cities:
            processor = GeoTemplateProcessor(self.service_name, city, self.domain)
            processed = processor.process_geo_template(geo_template)
            
            wp_data = {
                'branche_by': f"{self.service_name} {city}",
                'url_slug': f"/{processed['url_slug']}/",
                'bynavn': city,
                'meta_title': processed['meta_title'],
                'meta_description': processed['meta_description'],
                'page_content': processed['page_content'],
            }
            
            wordpress_data.append(wp_data)
        
        return wordpress_data


def validate_geo_data(service_name: str, cities: List[str]) -> Tuple[bool, List[str]]:
    """
    Validér geo marketing data
    
    Returns:
        Tuple af (is_valid, error_messages)
    """
    errors = []
    
    if not service_name or not service_name.strip():
        errors.append("Service navn er påkrævet")
    
    if not cities or len(cities) == 0:
        errors.append("Mindst én by skal vælges")
    
    # Check for empty city names
    empty_cities = [city for city in cities if not city or not city.strip()]
    if empty_cities:
        errors.append("Alle byer skal have navne")
    
    # Check for duplicate cities
    unique_cities = set(cities)
    if len(unique_cities) != len(cities):
        errors.append("Duplikerede byer fundet")
    
    return len(errors) == 0, errors


# Test functions for development
def test_slug_generator():
    """Test slug generator med danske eksempler"""
    test_cases = [
        ("Fugemand", "Bagsværd", "fugemand-bagsvaerd"),
        ("Murer", "Ølstykke", "murer-oelstykke"),
        ("VVS", "Måløv", "vvs-maaloev"),
        ("Elektriker", "Furesø", "elektriker-furesoe"),
    ]
    
    for service, city, expected in test_cases:
        result = DanishSlugGenerator.create_service_slug(service, city)
        print(f"{service} + {city} -> {result} (expected: {expected})")
        assert result == expected, f"Fejl: {result} != {expected}"
    
    print("✅ Alle slug tests passed!")


def test_template_processor():
    """Test template processor"""
    processor = GeoTemplateProcessor("Murer", "Bagsværd", "murefirma.dk")
    
    template = "{SERVICE} {BYNAVN} - 5/5 Stjerner på Trustpilot - Ring idag"
    result = processor.process_template(template)
    expected = "Murer Bagsværd - 5/5 Stjerner på Trustpilot - Ring idag"
    
    print(f"Template: {template}")
    print(f"Result: {result}")
    print(f"Expected: {expected}")
    
    assert result == expected, f"Template processing fejl: {result} != {expected}"
    print("✅ Template processor test passed!")


if __name__ == "__main__":
    test_slug_generator()
    test_template_processor()