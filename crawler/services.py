import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Set
import time
from django.utils import timezone
from .models import CrawlSession, WebPage, ExtractedUSP, ServiceArea
from usps.models import IndustryUSPPattern, USPTemplate


class WebsiteCrawler:
    def __init__(self, client, max_pages=20, delay=1):
        self.client = client
        self.max_pages = max_pages
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AdsBuilder/1.0)'
        })
        self.visited_urls = set()
        
    def crawl_website(self) -> CrawlSession:
        crawl_session = CrawlSession.objects.create(
            client=self.client,
            status='running'
        )
        
        try:
            base_url = self.client.website_url
            urls_to_crawl = [base_url]
            
            for url in urls_to_crawl:
                if len(self.visited_urls) >= self.max_pages:
                    break
                    
                if url in self.visited_urls:
                    continue
                    
                try:
                    page_data = self._crawl_page(url, crawl_session)
                    if page_data:
                        # Find additional URLs to crawl
                        new_urls = self._extract_internal_urls(page_data['content'], base_url)
                        urls_to_crawl.extend(new_urls)
                        
                    time.sleep(self.delay)
                    
                except Exception as e:
                    print(f"Error crawling {url}: {str(e)}")
                    continue
            
            crawl_session.status = 'completed'
            crawl_session.completed_at = timezone.now()
            crawl_session.pages_crawled = len(self.visited_urls)
            crawl_session.total_pages = len(self.visited_urls)
            crawl_session.save()
            
            # Extract USPs and services after crawling
            self._extract_usps_from_session(crawl_session)
            self._extract_services_from_session(crawl_session)
            
        except Exception as e:
            crawl_session.status = 'failed'
            crawl_session.error_message = str(e)
            crawl_session.save()
            
        return crawl_session
    
    def _crawl_page(self, url: str, crawl_session: CrawlSession) -> Dict:
        self.visited_urls.add(url)
        
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract page data
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ''
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc.get('content', '') if meta_desc else ''
        
        # Extract headings
        h1_tags = [h.get_text().strip() for h in soup.find_all('h1')]
        h2_tags = [h.get_text().strip() for h in soup.find_all('h2')]
        
        # Extract main content (remove scripts, styles, etc.)
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        content = soup.get_text()
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Determine page type
        url_lower = url.lower()
        is_service_page = any(keyword in url_lower for keyword in ['service', 'tjeneste', 'ydelse'])
        is_about_page = any(keyword in url_lower for keyword in ['about', 'om-os', 'om'])
        is_contact_page = any(keyword in url_lower for keyword in ['contact', 'kontakt'])
        
        # Create WebPage object
        web_page = WebPage.objects.create(
            crawl_session=crawl_session,
            url=url,
            title=title_text,
            content=content,
            meta_description=meta_description,
            h1_tags='|'.join(h1_tags),
            h2_tags='|'.join(h2_tags),
            word_count=len(content.split()),
            is_service_page=is_service_page,
            is_about_page=is_about_page,
            is_contact_page=is_contact_page
        )
        
        return {
            'url': url,
            'content': content,
            'title': title_text,
            'web_page': web_page
        }
    
    def _extract_internal_urls(self, content: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(content, 'html.parser')
        urls = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            # Only include same domain URLs
            if parsed_url.netloc == base_domain and parsed_url.scheme in ['http', 'https']:
                # Remove fragments and query params for cleaner URLs
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                if clean_url not in self.visited_urls and len(urls) < 50:
                    urls.append(clean_url)
                    
        return urls
    
    def _extract_usps_from_session(self, crawl_session: CrawlSession):
        """Extract USPs from all pages in the crawl session"""
        pages = WebPage.objects.filter(crawl_session=crawl_session)
        industry_patterns = IndustryUSPPattern.objects.filter(
            industry=self.client.industry
        )
        
        for page in pages:
            self._extract_usps_from_page(page, industry_patterns)
    
    def _extract_usps_from_page(self, page: WebPage, patterns):
        """Extract USPs from a single page using pattern matching"""
        content_sections = [
            page.title,
            page.meta_description,
            page.h1_tags,
            page.h2_tags,
            page.content[:2000]  # First 2000 characters of content
        ]
        
        for section in content_sections:
            if not section:
                continue
                
            # Pattern-based extraction
            for pattern in patterns:
                matches = re.finditer(pattern.pattern, section, re.IGNORECASE)
                for match in matches:
                    usp_text = match.group().strip()
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(section), match.end() + 100)
                    context = section[context_start:context_end]
                    
                    ExtractedUSP.objects.create(
                        web_page=page,
                        text=usp_text,
                        context=context,
                        confidence_score=pattern.weight,
                        extraction_method='pattern_matching',
                        position_on_page=self._determine_position(section, content_sections)
                    )
            
            # Common USP indicators
            usp_indicators = [
                r'(\d+\s*(år|hours?|timer|døgn|dage)[\s\w]*erfaring)',
                r'(døgnvagt|24/7|altid åben)',
                r'(hurtig|lynhurtig|samme dag|1-2 timer)',
                r'(gratis|ingen omkostninger)',
                r'(certificeret|autoriseret|godkendt)',
                r'(garanti|garanterer)',
                r'(lokal|i nærheden|tæt på)',
                r'(erfaren|specialist|ekspert)',
            ]
            
            for indicator_pattern in usp_indicators:
                matches = re.finditer(indicator_pattern, section, re.IGNORECASE)
                for match in matches:
                    usp_text = match.group().strip()
                    if len(usp_text) > 5:  # Skip too short matches
                        context_start = max(0, match.start() - 50)
                        context_end = min(len(section), match.end() + 50)
                        context = section[context_start:context_end]
                        
                        ExtractedUSP.objects.create(
                            web_page=page,
                            text=usp_text,
                            context=context,
                            confidence_score=0.7,
                            extraction_method='indicator_matching',
                            position_on_page=self._determine_position(section, content_sections)
                        )
    
    def _extract_services_from_session(self, crawl_session: CrawlSession):
        """Extract service areas from crawl session"""
        pages = WebPage.objects.filter(crawl_session=crawl_session)
        
        for page in pages:
            if page.is_service_page or any(keyword in page.title.lower() for keyword in ['service', 'tjeneste', 'ydelse']):
                self._extract_services_from_page(page)
    
    def _extract_services_from_page(self, page: WebPage):
        """Extract service areas from a single page"""
        # Common service patterns based on industry
        service_patterns = {
            'generic': [
                r'(reparation|installation|vedligeholdelse|service)',
                r'(rådgivning|konsulentydelser|support)',
                r'(design|udvikling|implementering)',
            ]
        }
        
        # Industry-specific patterns could be added here
        patterns = service_patterns.get('generic', [])
        
        content_to_analyze = f"{page.title} {page.h1_tags} {page.h2_tags} {page.content[:1000]}"
        
        for pattern in patterns:
            matches = re.finditer(pattern, content_to_analyze, re.IGNORECASE)
            for match in matches:
                service_text = match.group().strip()
                
                # Get surrounding context for better service description
                context_start = max(0, match.start() - 100)
                context_end = min(len(content_to_analyze), match.end() + 100)
                context = content_to_analyze[context_start:context_end]
                
                ServiceArea.objects.create(
                    web_page=page,
                    service_name=service_text,
                    service_description=context,
                    keywords_found=service_text,
                    priority_score=0.6
                )
    
    def _determine_position(self, section: str, all_sections: List[str]) -> str:
        """Determine where on the page the text was found"""
        if section == all_sections[0]:  # title
            return 'title'
        elif section == all_sections[1]:  # meta description
            return 'meta_description'
        elif section == all_sections[2]:  # h1
            return 'h1'
        elif section == all_sections[3]:  # h2
            return 'h2'
        else:
            return 'content'


class USPMatcher:
    """Match extracted USPs with predefined templates"""
    
    def __init__(self, client):
        self.client = client
    
    def match_extracted_usps(self):
        """Match extracted USPs with existing templates and create ClientUSPs"""
        from usps.models import ClientUSP
        
        crawl_sessions = CrawlSession.objects.filter(
            client=self.client, 
            status='completed'
        )
        
        for session in crawl_sessions:
            extracted_usps = ExtractedUSP.objects.filter(
                web_page__crawl_session=session
            )
            
            for extracted_usp in extracted_usps:
                # Try to match with existing USP templates
                templates = USPTemplate.objects.filter(
                    industry=self.client.industry,
                    is_active=True
                )
                
                best_match = None
                best_score = 0
                
                for template in templates:
                    score = self._calculate_similarity(
                        extracted_usp.text, 
                        template.text
                    )
                    if score > best_score and score > 0.3:
                        best_score = score
                        best_match = template
                
                # Create ClientUSP
                ClientUSP.objects.create(
                    client=self.client,
                    usp_template=best_match,
                    custom_text=extracted_usp.text,
                    is_discovered=True,
                    source_url=extracted_usp.web_page.url,
                    confidence_score=extracted_usp.confidence_score * best_score if best_match else extracted_usp.confidence_score
                )
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Simple similarity calculation based on common words"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0


class IntelligentWebsiteAnalyzer:
    """Udvidet website analyse med AI-drevet branche og service identifikation"""
    
    def __init__(self, client):
        self.client = client
        
    def analyze_website_comprehensive(self) -> Dict:
        """Komplet website analyse for kampagne generering"""
        
        # Get latest crawl session
        crawl_sessions = CrawlSession.objects.filter(
            client=self.client, 
            status='completed'
        ).order_by('-completed_at')
        
        if not crawl_sessions.exists():
            return {'error': 'Ingen crawl data tilgængelig'}
        
        latest_session = crawl_sessions.first()
        pages = WebPage.objects.filter(crawl_session=latest_session)
        
        if not pages.exists():
            return {'error': 'Ingen sider crawlet'}
        
        # Analyze different aspects
        analysis = {
            'industry_analysis': self._identify_industry_detailed(pages),
            'service_analysis': self._analyze_services_detailed(pages),
            'geographic_analysis': self._analyze_geographic_coverage(pages),
            'usp_analysis': self._analyze_usps(pages),
            'content_analysis': self._analyze_content_themes(pages),
            'business_model_analysis': self._analyze_business_model(pages)
        }
        
        return analysis
    
    def _identify_industry_detailed(self, pages) -> Dict:
        """Detaljeret branche identifikation"""
        
        # Combine all content
        all_content = ""
        title_content = ""
        heading_content = ""
        
        for page in pages[:5]:  # First 5 pages
            all_content += f" {page.content[:1000]}"
            title_content += f" {page.title}"
            heading_content += f" {page.h1_tags} {page.h2_tags}"
        
        # Industry detection patterns (udvidet)
        industry_indicators = {
            'VVS': {
                'keywords': ['vvs', 'blik', 'rør', 'badeværelse', 'toilet', 'varme', 'radiator', 'kedel', 'bruser', 'vandhane'],
                'services': ['installation', 'reparation', 'service', 'akut', 'lækage'],
                'weight': 0
            },
            'El/Elektriker': {
                'keywords': ['elektriker', 'el', 'elektro', 'installation', 'strøm', 'belysning', 'elinstallation', 'sikring'],
                'services': ['installation', 'reparation', 'fejlfinding', 'akut', 'elcheck'],
                'weight': 0
            },
            'Advokat': {
                'keywords': ['advokat', 'jurist', 'juridisk', 'ret', 'lov', 'retshjælp', 'advokatfirma'],
                'services': ['rådgivning', 'repræsentation', 'kontrakter', 'retssag'],
                'weight': 0
            },
            'Tandlæge': {
                'keywords': ['tandlæge', 'dental', 'tand', 'tandklinik', 'oral', 'mundhygiejne'],
                'services': ['undersøgelse', 'behandling', 'rens', 'fyldning', 'implantater'],
                'weight': 0
            },
            'Læge': {
                'keywords': ['læge', 'doktor', 'klinik', 'medicin', 'sundhed', 'behandling', 'konsultation'],
                'services': ['konsultation', 'undersøgelse', 'behandling', 'vaccination'],
                'weight': 0
            },
            'Bilmekaniker': {
                'keywords': ['bil', 'auto', 'mekaniker', 'værksted', 'bilreparation', 'motor', 'service'],
                'services': ['reparation', 'service', 'syn', 'værksted', 'diagnostik'],
                'weight': 0
            },
            'Rengøring': {
                'keywords': ['rengøring', 'clean', 'rengøringsservice', 'vinduespolering', 'erhvervsrengøring'],
                'services': ['rengøring', 'vinduespolering', 'gulvbehandling', 'specialrengøring'],
                'weight': 0
            },
            'Bygge/Håndværk': {
                'keywords': ['bygge', 'tømrer', 'murer', 'håndværk', 'renovering', 'ombygning', 'nybyg'],
                'services': ['byggeri', 'renovering', 'tilbygning', 'reparation'],
                'weight': 0
            },
            'Revisor': {
                'keywords': ['revisor', 'regnskab', 'bogholderi', 'skat', 'årsrapport', 'revision'],
                'services': ['revision', 'regnskab', 'rådgivning', 'selskabsstiftelse'],
                'weight': 0
            },
            'Ejendomsmægler': {
                'keywords': ['mægler', 'ejendom', 'bolig', 'hus', 'lejlighed', 'salg', 'køb', 'vurdering'],
                'services': ['salg', 'køb', 'vurdering', 'rådgivning'],
                'weight': 0
            }
        }
        
        content_lower = all_content.lower()
        
        # Calculate weights for each industry
        for industry, data in industry_indicators.items():
            # Count keyword occurrences
            keyword_score = sum(1 for keyword in data['keywords'] if keyword in content_lower)
            service_score = sum(1 for service in data['services'] if service in content_lower)
            
            # Bonus for title/heading content
            title_lower = title_content.lower()
            heading_lower = heading_content.lower()
            
            title_bonus = sum(2 for keyword in data['keywords'] if keyword in title_lower)
            heading_bonus = sum(1.5 for keyword in data['keywords'] if keyword in heading_lower)
            
            total_score = keyword_score + service_score + title_bonus + heading_bonus
            industry_indicators[industry]['weight'] = total_score
        
        # Find best match
        best_industry = max(industry_indicators.items(), key=lambda x: x[1]['weight'])
        
        if best_industry[1]['weight'] == 0:
            return {
                'industry': 'Andre',
                'confidence': 0.1,
                'detected_keywords': [],
                'alternative_industries': []
            }
        
        # Get alternatives
        sorted_industries = sorted(industry_indicators.items(), key=lambda x: x[1]['weight'], reverse=True)
        alternatives = [ind[0] for ind in sorted_industries[1:4] if ind[1]['weight'] > 0]
        
        # Calculate confidence based on score difference
        max_score = best_industry[1]['weight']
        second_score = sorted_industries[1][1]['weight'] if len(sorted_industries) > 1 else 0
        
        confidence = min(0.95, 0.4 + (max_score - second_score) / max(max_score, 1) * 0.5)
        
        return {
            'industry': best_industry[0],
            'confidence': confidence,
            'detected_keywords': [kw for kw in best_industry[1]['keywords'] if kw in content_lower],
            'alternative_industries': alternatives,
            'scores': {ind: data['weight'] for ind, data in industry_indicators.items()}
        }
    
    def _analyze_services_detailed(self, pages) -> Dict:
        """Detaljeret service analyse"""
        
        services_found = []
        service_pages = []
        
        for page in pages:
            page_services = self._extract_services_from_page_content(page)
            services_found.extend(page_services)
            
            if page.is_service_page or any(indicator in page.url.lower() for indicator in ['service', 'tjeneste', 'ydelse']):
                service_pages.append({
                    'url': page.url,
                    'title': page.title,
                    'services': page_services
                })
        
        # Deduplicate and categorize services
        unique_services = list(set(services_found))
        
        service_categories = self._categorize_services(unique_services)
        
        return {
            'total_services_found': len(unique_services),
            'service_categories': service_categories,
            'service_pages': service_pages,
            'all_services': unique_services
        }
    
    def _analyze_geographic_coverage(self, pages) -> Dict:
        """Analysér geografisk dækning"""
        
        all_content = " ".join([page.content for page in pages])
        
        # Danish cities and regions
        danish_locations = [
            'København', 'Aarhus', 'Odense', 'Aalborg', 'Esbjerg', 'Randers', 'Kolding', 'Horsens',
            'Vejle', 'Roskilde', 'Herning', 'Silkeborg', 'Næstved', 'Fredericia', 'Viborg',
            'Køge', 'Holstebro', 'Taastrup', 'Slagelse', 'Hillerød', 'Sønderborg', 'Frederikshavn',
            'Sjælland', 'Jylland', 'Fyn', 'Bornholm', 'Hovedstaden', 'Midtjylland', 'Nordjylland', 
            'Syddanmark', 'Sjælland'
        ]
        
        found_locations = []
        for location in danish_locations:
            if location.lower() in all_content.lower():
                found_locations.append(location)
        
        # Determine service area
        service_area = 'local'
        if len(found_locations) > 5:
            service_area = 'regional'
        if len(found_locations) > 10 or any(region in found_locations for region in ['Sjælland', 'Jylland', 'Fyn']):
            service_area = 'national'
        
        return {
            'locations_mentioned': found_locations,
            'service_area': service_area,
            'geographic_focus': found_locations[:3] if found_locations else ['Danmark']
        }
    
    def _analyze_usps(self, pages) -> Dict:
        """Analysér USPs fra crawlet content"""
        
        # Get existing extracted USPs
        extracted_usps = ExtractedUSP.objects.filter(
            web_page__in=pages
        ).order_by('-confidence_score')
        
        usps = []
        for usp in extracted_usps:
            usps.append({
                'text': usp.text,
                'confidence': usp.confidence_score,
                'source_page': usp.web_page.url,
                'position': usp.position_on_page
            })
        
        # Extract additional USPs with patterns
        additional_usps = self._extract_additional_usp_patterns(pages)
        usps.extend(additional_usps)
        
        # Sort by confidence and take top USPs
        usps.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'total_usps_found': len(usps),
            'high_confidence_usps': [usp for usp in usps if usp['confidence'] > 0.7],
            'all_usps': usps[:10],  # Top 10
            'usp_categories': self._categorize_usps(usps)
        }
    
    def _analyze_content_themes(self, pages) -> Dict:
        """Analysér content temaer for keyword inspiration"""
        
        all_content = ""
        for page in pages:
            all_content += f" {page.title} {page.h1_tags} {page.h2_tags} {page.content[:500]}"
        
        # Extract common themes/topics
        words = re.findall(r'\b\w{4,}\b', all_content.lower())
        word_freq = Counter(words)
        
        # Filter out common words
        common_words = {'denne', 'være', 'have', 'skal', 'kan', 'vil', 'også', 'meget', 'siden', 'hvordan', 'derfor'}
        filtered_words = {word: count for word, count in word_freq.most_common(50) if word not in common_words}
        
        return {
            'top_content_themes': list(filtered_words.keys())[:20],
            'word_frequency': filtered_words
        }
    
    def _analyze_business_model(self, pages) -> Dict:
        """Analysér forretningsmodel (B2B/B2C)"""
        
        all_content = " ".join([page.content for page in pages]).lower()
        
        b2b_indicators = ['virksomhed', 'erhverv', 'business', 'firma', 'selskab', 'kontrakt', 'aftale', 'samarbejde']
        b2c_indicators = ['privat', 'familie', 'hjem', 'personlig', 'individuel', 'kunde', 'borgere']
        
        b2b_score = sum(1 for indicator in b2b_indicators if indicator in all_content)
        b2c_score = sum(1 for indicator in b2c_indicators if indicator in all_content)
        
        if b2b_score > b2c_score * 1.5:
            business_type = 'B2B'
        elif b2c_score > b2b_score * 1.5:
            business_type = 'B2C'
        else:
            business_type = 'Both'
        
        return {
            'business_type': business_type,
            'b2b_score': b2b_score,
            'b2c_score': b2c_score
        }
    
    def _extract_services_from_page_content(self, page) -> List[str]:
        """Extract services from en enkelt side"""
        
        content = f"{page.title} {page.h1_tags} {page.h2_tags} {page.content[:1000]}".lower()
        
        # Service patterns
        service_patterns = [
            r'(installation af \w+)',
            r'(reparation af \w+)',
            r'(\w+ service)',
            r'(\w+ reparation)',
            r'(\w+ installation)',
            r'(akut \w+)',
            r'(\w+ hjælp)',
            r'(\w+ løsning)',
            r'(\w+ rådgivning)',
            r'(professionel \w+)'
        ]
        
        services = []
        for pattern in service_patterns:
            matches = re.findall(pattern, content)
            services.extend(matches)
        
        return [service.strip() for service in services if len(service.strip()) > 3]
    
    def _categorize_services(self, services: List[str]) -> Dict:
        """Kategoriser services"""
        
        categories = {
            'installation': [],
            'reparation': [],
            'rådgivning': [],
            'akut_service': [],
            'andre': []
        }
        
        for service in services:
            service_lower = service.lower()
            if 'installation' in service_lower:
                categories['installation'].append(service)
            elif 'reparation' in service_lower:
                categories['reparation'].append(service)
            elif 'rådgivning' in service_lower:
                categories['rådgivning'].append(service)
            elif 'akut' in service_lower or 'emergency' in service_lower:
                categories['akut_service'].append(service)
            else:
                categories['andre'].append(service)
        
        return categories
    
    def _extract_additional_usp_patterns(self, pages) -> List[Dict]:
        """Extract additional USP patterns"""
        
        additional_usps = []
        
        for page in pages:
            content = f"{page.title} {page.content[:2000]}"
            
            # USP patterns
            usp_patterns = [
                r'(\d+\s+års?\s+erfaring)',
                r'(24/7|døgnvagt|altid åben)',
                r'(gratis \w+)',
                r'(hurtig \w+)',
                r'(samme dag \w+)',
                r'(certificeret \w+)',
                r'(autoriseret \w+)',
                r'(garanti på \w+)',
                r'(lokal \w+)',
                r'(erfaren \w+)'
            ]
            
            for pattern in usp_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 5:
                        additional_usps.append({
                            'text': match.strip(),
                            'confidence': 0.6,
                            'source_page': page.url,
                            'position': 'content'
                        })
        
        return additional_usps
    
    def _categorize_usps(self, usps: List[Dict]) -> Dict:
        """Kategoriser USPs"""
        
        categories = {
            'erfaring': [],
            'hastighed': [],
            'pris': [],
            'kvalitet': [],
            'tilgængelighed': [],
            'andre': []
        }
        
        for usp in usps:
            text_lower = usp['text'].lower()
            if any(word in text_lower for word in ['år', 'erfaring', 'ekspert', 'specialist']):
                categories['erfaring'].append(usp)
            elif any(word in text_lower for word in ['hurtig', 'samme dag', 'akut', 'øjeblikkelig']):
                categories['hastighed'].append(usp)
            elif any(word in text_lower for word in ['gratis', 'billig', 'pris', 'tilbud']):
                categories['pris'].append(usp)
            elif any(word in text_lower for word in ['kvalitet', 'certificeret', 'autoriseret', 'garanti']):
                categories['kvalitet'].append(usp)
            elif any(word in text_lower for word in ['24/7', 'døgnvagt', 'åben', 'tilgængelig']):
                categories['tilgængelighed'].append(usp)
            else:
                categories['andre'].append(usp)
        
        return categories