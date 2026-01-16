"""
AI Service Layer for Google Ads Builder.

Provides AI-powered content generation using OpenAI GPT-4/5 and Perplexity.
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from django.conf import settings


def get_token_param_name(model: str) -> str:
    """
    Get the correct token parameter name for the given model.
    GPT-5+ models use 'max_completion_tokens', older models use 'max_tokens'.
    """
    if model and model.startswith('gpt-5'):
        return 'max_completion_tokens'
    return 'max_tokens'


def build_completion_kwargs(model: str, messages: list, temperature: float, max_tokens: int) -> dict:
    """
    Build the kwargs dict for chat.completions.create() with correct token param.
    """
    token_param = get_token_param_name(model)
    return {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        token_param: max_tokens
    }


class WebsiteScraper:
    """Scrape and extract text content from websites."""

    def __init__(self, max_content_length=6000):
        self.max_content_length = max_content_length
        # Initialize OpenAI client for AI-based review classification
        api_key = settings.OPENAI_API_KEY
        self.openai_client = OpenAI(api_key=api_key) if api_key else None
        # Multiple User-Agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        ]
        # Browser-like headers to avoid being blocked
        # Note: Don't set Accept-Encoding manually - let requests handle it automatically
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        # Keep backwards compatible headers property
        self.headers = {**self.base_headers, 'User-Agent': self.user_agents[0]}
        # HIGH priority: Awards, reviews, concrete achievements (should come first)
        self.high_priority_keywords = [
            'finalist', 'vinder', 'nomineret', 'kåret', 'årets',
            'trustpilot', 'stjerner', 'anmeldelser',
            'års erfaring', '+ anmeld', '+100', '+1000',
        ]
        # MEDIUM priority: Credentials and key facts
        self.medium_priority_keywords = [
            'certificer', 'autoriseret', 'godkendt',
            '24 timer', 'døgnvagt',
            'etableret', 'grundlagt',
        ]

    def _get_prompt_from_db(self, prompt_type):
        """
        Get prompt template and settings from database.

        Returns tuple of (prompt_text, model_settings) or (None, None) if not found.
        """
        try:
            from ai_integration.models import AIPromptTemplate
            prompt = AIPromptTemplate.objects.filter(
                prompt_type=prompt_type,
                is_active=True
            ).first()
            if prompt and prompt.prompt_text:
                return prompt.get_prompt_text(), prompt.model_settings or {}
        except Exception as e:
            print(f"Warning: Could not load prompt from DB: {e}")
        return None, None

    def _get_priority_level(self, text):
        """
        Get priority level of text: 2=high, 1=medium, 0=regular.
        High priority: awards, reviews, concrete achievements
        Medium priority: credentials, 24/7 service
        """
        text_lower = text.lower()
        if any(kw in text_lower for kw in self.high_priority_keywords):
            return 2
        if any(kw in text_lower for kw in self.medium_priority_keywords):
            return 1
        return 0

    def _is_priority_content(self, text):
        """Check if text contains priority keywords (for backwards compat)."""
        return self._get_priority_level(text) > 0

    def scrape_website(self, url, timeout=10):
        """
        Fetch and extract text content from a website.

        Args:
            url: Website URL to scrape
            timeout: Request timeout in seconds

        Returns:
            str: Extracted text content (max max_content_length chars)
        """
        if not url:
            return ""

        # Ensure URL has protocol
        if not url.startswith('http'):
            url = 'https://' + url

        # Try multiple user agents if first attempt fails
        response = None
        last_error = None

        for i, user_agent in enumerate(self.user_agents):
            try:
                headers = {**self.base_headers, 'User-Agent': user_agent}
                response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                response.raise_for_status()

                # Check if we actually got HTML content
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type or len(response.content) > 100:
                    break  # Success, exit retry loop

            except requests.RequestException as e:
                last_error = e
                print(f"Scrape attempt {i+1} failed for {url} with {user_agent[:50]}...: {e}")
                continue

        if response is None or response.status_code != 200:
            print(f"All scrape attempts failed for {url}: {last_error}")
            return ""

        try:
            # Ensure proper encoding - use response.text which handles encoding detection
            # or explicitly set encoding to UTF-8 if not detected
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header',
                                'aside', 'form', 'noscript', 'iframe']):
                element.decompose()

            # Separate content by priority level: high, medium, regular
            high_priority = []
            medium_priority = []
            regular_text = []

            # Get main content areas - prefer elements with actual content
            def has_content(element):
                """Check if element has meaningful text content."""
                if not element:
                    return False
                return len(element.find_all(['p', 'h1', 'h2', 'h3', 'li'])) > 0

            main_content = None
            for candidate in [soup.find('main'), soup.find('article'), soup.find('body')]:
                if has_content(candidate):
                    main_content = candidate
                    break

            # Fallback to body if nothing found
            if not main_content:
                main_content = soup.find('body')

            if main_content:
                # Extract headings
                for heading in main_content.find_all(['h1', 'h2', 'h3']):
                    text = heading.get_text(strip=True)
                    if text and len(text) > 3:
                        formatted = f"## {text}"
                        level = self._get_priority_level(text)
                        if level == 2:
                            high_priority.append(formatted)
                        elif level == 1:
                            medium_priority.append(formatted)
                        else:
                            regular_text.append(formatted)

                # Extract paragraphs
                for p in main_content.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        level = self._get_priority_level(text)
                        if level == 2:
                            high_priority.append(text)
                        elif level == 1:
                            medium_priority.append(text)
                        else:
                            regular_text.append(text)

                # Extract list items (often contain USPs)
                for li in main_content.find_all('li'):
                    text = li.get_text(strip=True)
                    level = self._get_priority_level(text)
                    # Allow longer list items if they contain priority keywords
                    max_li_len = 400 if level > 0 else 200
                    if text and len(text) > 10 and len(text) < max_li_len:
                        formatted = f"• {text}"
                        if level == 2:
                            high_priority.append(formatted)
                        elif level == 1:
                            medium_priority.append(formatted)
                        else:
                            regular_text.append(formatted)

                # Look for specific USP-like elements (always high priority)
                seen = set(high_priority + medium_priority + regular_text)
                for el in main_content.find_all(['span', 'div', 'strong', 'b']):
                    text = el.get_text(strip=True)
                    if text and len(text) < 100 and (
                        '+' in text or
                        'års' in text.lower() or
                        'erfaring' in text.lower() or
                        'anmeld' in text.lower() or
                        'trustpilot' in text.lower() or
                        'finalist' in text.lower() or
                        'vinder' in text.lower() or
                        'certificer' in text.lower() or
                        'stjerner' in text.lower() or
                        '%' in text
                    ):
                        formatted = f"[USP] {text}"
                        if formatted not in seen:
                            high_priority.append(formatted)
                            seen.add(formatted)

            # Combine: high priority first, then medium, then regular
            all_text = high_priority + medium_priority + regular_text

            # Join and clean
            full_text = '\n'.join(all_text)
            full_text = re.sub(r'\n{3,}', '\n\n', full_text)
            full_text = re.sub(r' {2,}', ' ', full_text)

            # Truncate if too long
            if len(full_text) > self.max_content_length:
                full_text = full_text[:self.max_content_length] + "..."

            return full_text.strip()

        except Exception as e:
            print(f"Website parsing error for {url}: {e}")
            return ""

    async def scrape_with_playwright(self, url, wait_for_selectors=None):
        """
        Scrape website using Playwright for JavaScript-rendered content.
        Use this when you need to capture dynamic widgets like Trustpilot reviews.

        Args:
            url: URL to scrape
            wait_for_selectors: List of CSS selectors to wait for (e.g., ['.trustpilot-widget'])

        Returns:
            str: Rendered HTML content
        """
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Set a realistic user agent
                await page.set_extra_http_headers({
                    'Accept-Language': 'da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7'
                })

                await page.goto(url, wait_until='networkidle', timeout=30000)

                # Wait for specific selectors if provided (e.g., Trustpilot widget)
                if wait_for_selectors:
                    for selector in wait_for_selectors:
                        try:
                            await page.wait_for_selector(selector, timeout=5000)
                        except Exception:
                            pass  # Continue if selector not found

                # Extra wait for dynamic content to fully render
                await page.wait_for_timeout(2000)

                # Get rendered HTML
                html = await page.content()
                return html

            except Exception as e:
                print(f"Playwright scraping error for {url}: {e}")
                return ""
            finally:
                await browser.close()

    def scrape_website_with_playwright(self, url, timeout=30):
        """
        Synchronous wrapper for Playwright scraping.
        Use this to capture JavaScript-rendered content like Trustpilot widgets.

        Args:
            url: Website URL to scrape
            timeout: Request timeout in seconds

        Returns:
            tuple: (text_content, reviews_list) - Extracted text and detected reviews
        """
        import asyncio

        if not url:
            return "", []

        # Ensure URL has protocol
        if not url.startswith('http'):
            url = 'https://' + url

        # Run async Playwright scraping
        try:
            # Check if we're in an existing event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, need to handle differently
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_playwright_sync, url)
                    html = future.result(timeout=timeout)
            except RuntimeError:
                # No running loop, create new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    html = loop.run_until_complete(
                        self.scrape_with_playwright(url, wait_for_selectors=[
                            '.trustpilot-widget',
                            '[class*="trustpilot"]',
                            '[class*="TrustBox"]',
                            '[class*="review"]',
                            '[data-widget]'
                        ])
                    )
                finally:
                    loop.close()

            if not html:
                return "", []

            soup = BeautifulSoup(html, 'html.parser')

            # Extract Trustpilot reviews BEFORE removing iframes
            reviews = self.extract_trustpilot_reviews(soup)

            # Now remove unwanted elements for text extraction
            for element in soup(['script', 'style', 'nav', 'footer', 'header',
                                'aside', 'form', 'noscript']):
                element.decompose()

            # Extract text content using existing priority system
            text_content = self._extract_prioritized_content(soup)

            return text_content, reviews

        except Exception as e:
            print(f"Playwright scraping failed for {url}: {e}")
            import traceback
            traceback.print_exc()
            return "", []

    def _run_playwright_sync(self, url):
        """Helper to run Playwright in a new thread with its own event loop."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.scrape_with_playwright(url, wait_for_selectors=[
                    '.trustpilot-widget',
                    '[class*="trustpilot"]',
                    '[class*="TrustBox"]',
                    '[class*="review"]'
                ])
            )
        finally:
            loop.close()

    def _extract_prioritized_content(self, soup):
        """Extract text content using priority system (extracted from scrape_website)."""
        high_priority = []
        medium_priority = []
        regular_text = []

        def has_content(element):
            if not element:
                return False
            return len(element.find_all(['p', 'h1', 'h2', 'h3', 'li'])) > 0

        main_content = None
        for candidate in [soup.find('main'), soup.find('article'), soup.find('body')]:
            if has_content(candidate):
                main_content = candidate
                break

        if not main_content:
            main_content = soup.find('body')

        if main_content:
            # Extract headings
            for heading in main_content.find_all(['h1', 'h2', 'h3']):
                text = heading.get_text(strip=True)
                if text and len(text) > 3:
                    formatted = f"## {text}"
                    level = self._get_priority_level(text)
                    if level == 2:
                        high_priority.append(formatted)
                    elif level == 1:
                        medium_priority.append(formatted)
                    else:
                        regular_text.append(formatted)

            # Extract paragraphs
            for p in main_content.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    level = self._get_priority_level(text)
                    if level == 2:
                        high_priority.append(text)
                    elif level == 1:
                        medium_priority.append(text)
                    else:
                        regular_text.append(text)

            # Extract list items
            for li in main_content.find_all('li'):
                text = li.get_text(strip=True)
                level = self._get_priority_level(text)
                max_li_len = 400 if level > 0 else 200
                if text and len(text) > 10 and len(text) < max_li_len:
                    formatted = f"• {text}"
                    if level == 2:
                        high_priority.append(formatted)
                    elif level == 1:
                        medium_priority.append(formatted)
                    else:
                        regular_text.append(formatted)

        all_text = high_priority + medium_priority + regular_text
        full_text = '\n'.join(all_text)
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        full_text = re.sub(r' {2,}', ' ', full_text)

        if len(full_text) > self.max_content_length:
            full_text = full_text[:self.max_content_length] + "..."

        return full_text.strip()

    def extract_trustpilot_reviews(self, soup):
        """
        Extract reviews from rendered Trustpilot widget content.
        Also handles Elementor testimonial carousels.

        Args:
            soup: BeautifulSoup object with rendered HTML

        Returns:
            list: List of review dicts with author, rating, text, platform
        """
        reviews = []

        # === ELEMENTOR TESTIMONIALS (Priority - very common in Danish websites) ===
        # Structure: .elementor-testimonial > .elementor-testimonial__text + .elementor-testimonial__name
        elementor_testimonials = soup.select('.elementor-testimonial')

        seen_texts = set()  # Track unique reviews (avoid duplicates from swiper duplicates)

        for testimonial in elementor_testimonials:
            # Skip duplicate slides in Swiper carousel
            parent = testimonial.find_parent(class_=lambda x: x and 'swiper-slide-duplicate' in x if x else False)
            if parent:
                continue

            # Extract text content
            text_elem = testimonial.select_one('.elementor-testimonial__text')
            if not text_elem:
                continue

            # Get full text and clean it
            full_text = text_elem.get_text(separator=' ', strip=True)

            # Extract title from h6 if present
            title_elem = text_elem.select_one('h6')
            title = title_elem.get_text(strip=True) if title_elem else ''

            # Clean text: remove star characters and title
            clean_text = full_text
            clean_text = re.sub(r'[★☆]{2,}', '', clean_text)  # Remove star sequences
            if title:
                clean_text = clean_text.replace(title, '', 1)
            clean_text = clean_text.strip()

            # Skip if too short or already seen
            if len(clean_text) < 20:
                continue
            text_key = clean_text[:100]
            if text_key in seen_texts:
                continue
            seen_texts.add(text_key)

            # Extract author name
            name_elem = testimonial.select_one('.elementor-testimonial__name')
            author = name_elem.get_text(strip=True) if name_elem else 'Anonym'

            # Detect platform from title element
            title_platform = testimonial.select_one('.elementor-testimonial__title')
            platform = 'Trustpilot'
            if title_platform:
                platform_text = title_platform.get_text(strip=True).lower()
                if 'google' in platform_text:
                    platform = 'Google'
                elif 'facebook' in platform_text:
                    platform = 'Facebook'

            # Count stars (★ characters in text)
            star_count = full_text.count('★')
            rating = star_count if star_count >= 1 and star_count <= 5 else 5

            # Build review with title as heading
            review_text = f"{title}\n{clean_text}" if title else clean_text

            reviews.append({
                'author': author if len(author) < 50 else author[:47] + '...',
                'rating': rating,
                'text': review_text,  # Full review text without truncation
                'platform': platform
            })

        # If Elementor testimonials found, return them (most reliable)
        if reviews:
            return reviews

        # === FALLBACK: Common Trustpilot widget selectors ===
        trustpilot_selectors = [
            '.trustpilot-widget',
            '[data-widget="true"]',
            '.tp-widget',
            '[class*="TrustBox"]',
            '[class*="trustpilot"]',
            '.reviews-widget',
            '[data-testid*="review"]'
        ]

        # Find all potential review containers
        review_containers = []
        for selector in trustpilot_selectors:
            containers = soup.select(selector)
            review_containers.extend(containers)

        # Also look for common review patterns in the whole document
        all_review_elements = soup.select('[class*="review"], [class*="Review"], [class*="testimonial"]')

        for container in review_containers + all_review_elements:
            # Try to find individual review items
            review_items = container.select(
                '[class*="review-card"], [class*="ReviewCard"], '
                '[class*="review-item"], [class*="ReviewItem"], '
                '[data-review], article'
            )

            # If no specific items found, treat the container itself as a review
            if not review_items:
                review_items = [container]

            for item in review_items:
                # Extract author name
                author_elem = item.select_one(
                    '[class*="name"], [class*="author"], [class*="Name"], [class*="Author"], '
                    '[class*="consumer"], [class*="Consumer"]'
                )
                author = author_elem.get_text(strip=True) if author_elem else None

                # Extract review text
                text_elem = item.select_one(
                    '[class*="review-text"], [class*="ReviewText"], '
                    '[class*="content"], [class*="Content"], '
                    '[class*="body"], [class*="Body"], p'
                )
                text = text_elem.get_text(strip=True) if text_elem else None

                # Extract rating
                rating = self._parse_star_rating(item)

                # Only add if we have meaningful content
                if text and len(text) > 20:
                    # Avoid duplicates (check first 100 chars)
                    if not any(r['text'][:100] == text[:100] for r in reviews):
                        reviews.append({
                            'author': author if author and len(author) < 50 else 'Anonym',
                            'rating': rating,
                            'text': text,  # Full review text without truncation
                            'platform': 'Trustpilot'
                        })

        return reviews

    def extract_review_iframes(self, soup):
        """
        Extract review widget iframes (Trustpilot, Google Reviews, etc.).

        Detects iframes for common review platforms and returns their details
        so they can be displayed in a dedicated section.

        Args:
            soup: BeautifulSoup object with HTML

        Returns:
            list: List of iframe dicts with platform, src, and embed_code
        """
        review_iframes = []

        # Known review platform iframe patterns
        iframe_patterns = {
            'trustpilot': [
                'trustpilot.com',
                'widget.trustpilot.com',
                'tp.widget',
            ],
            'google': [
                'google.com/maps',
                'maps.google.com',
                'google.com/reviews',
            ],
            'facebook': [
                'facebook.com/plugins/page',
                'facebook.com/plugins/review',
            ],
            'yelp': [
                'yelp.com/embed',
            ],
            'tripadvisor': [
                'tripadvisor.com/WidgetEmbed',
            ],
            'anmeldhåndværker': [
                'anmeldhaandvaerker.dk',
            ],
            'byggeri_rating': [
                'byggerirating.dk',
            ],
        }

        # Find all iframes
        iframes = soup.find_all('iframe')

        for iframe in iframes:
            src = iframe.get('src', '') or iframe.get('data-src', '')
            if not src:
                continue

            src_lower = src.lower()

            # Check against known patterns
            detected_platform = None
            for platform, patterns in iframe_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in src_lower:
                        detected_platform = platform
                        break
                if detected_platform:
                    break

            if detected_platform:
                # Get iframe dimensions
                width = iframe.get('width', '100%')
                height = iframe.get('height', '400')

                # Build embed code
                embed_code = str(iframe)

                review_iframes.append({
                    'platform': detected_platform.title(),
                    'src': src,
                    'width': width,
                    'height': height,
                    'embed_code': embed_code,
                })

        # Also look for Trustpilot TrustBox widgets (not iframes but data-attributes)
        trustbox_widgets = soup.select('[data-locale][data-template-id][data-businessunit-id]')
        for widget in trustbox_widgets:
            business_unit_id = widget.get('data-businessunit-id', '')
            template_id = widget.get('data-template-id', '')
            locale = widget.get('data-locale', 'da-DK')

            if business_unit_id:
                review_iframes.append({
                    'platform': 'Trustpilot',
                    'src': f'https://widget.trustpilot.com/trustboxes/{template_id}/index.html?businessunitId={business_unit_id}&locale={locale}',
                    'width': widget.get('data-style-width', '100%'),
                    'height': widget.get('data-style-height', '400px'),
                    'embed_code': str(widget),
                    'widget_type': 'trustbox',
                })

        if review_iframes:
            print(f"[WebsiteScraper] Found {len(review_iframes)} review iframes/widgets")

        return review_iframes

    def _parse_star_rating(self, element):
        """
        Parse star rating from element.

        Looks for:
        - aria-label attributes like "4 out of 5 stars"
        - data-rating attributes
        - Star icon counts
        - Rating text like "4.5" or "5/5"
        """
        if not element:
            return 5

        # Check for data-rating attribute
        data_rating = element.get('data-rating') or element.get('data-score')
        if data_rating:
            try:
                return float(data_rating)
            except ValueError:
                pass

        # Check for aria-label like "4 out of 5 stars" or "Rating: 5"
        for attr in ['aria-label', 'title']:
            label = element.get(attr, '')
            if label:
                match = re.search(r'(\d+(?:[.,]\d+)?)', label)
                if match:
                    return float(match.group(1).replace(',', '.'))

        # Look for rating element inside
        rating_elem = element.select_one('[class*="rating"], [class*="star"], [data-rating]')
        if rating_elem:
            # Check attributes
            for attr in ['data-rating', 'data-score', 'aria-label', 'title']:
                val = rating_elem.get(attr, '')
                if val:
                    match = re.search(r'(\d+(?:[.,]\d+)?)', str(val))
                    if match:
                        return float(match.group(1).replace(',', '.'))

            # Check text content
            rating_text = rating_elem.get_text(strip=True)
            match = re.search(r'(\d+(?:[.,]\d+)?)', rating_text)
            if match:
                return float(match.group(1).replace(',', '.'))

        # Count filled star icons as fallback
        stars = element.select('[class*="star"][class*="full"], [class*="star"][class*="fill"], .star-fill')
        if stars:
            return len(stars)

        # Default to 5 stars
        return 5

    def extract_all_sections(self, soup):
        """
        Udtræk ALLE strukturerede sektioner fra HTML.
        Finder H1/H2/H3 headers og tilhørende indhold.
        Håndterer moderne page builders (Elementor, etc.) med nested div-strukturer.

        Args:
            soup: BeautifulSoup objekt med HTML

        Returns:
            list: [{'tag': 'h1', 'header': 'Overskrift', 'content': 'Tekst...'}]
        """
        from copy import deepcopy

        sections = []

        # Find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if not main_content:
            return []

        # Lav en DEEP kopi for at undgå at modificere original soup
        work_soup = deepcopy(main_content)

        # Fjern navigation, footer, aside etc. fra arbejdskopi
        for element in work_soup.find_all(['nav', 'footer', 'aside', 'script', 'style', 'noscript', 'iframe', 'form', 'header']):
            element.decompose()

        # Find alle headers (h1, h2, h3, h4) - inkluder h4 for mere granularitet
        headers = work_soup.find_all(['h1', 'h2', 'h3', 'h4'])

        # Hvis ingen headers, saml al tekst som én sektion
        if not headers:
            all_paragraphs = work_soup.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in all_paragraphs if len(p.get_text(strip=True)) > 20])
            if content:
                sections.append({
                    'tag': 'p',
                    'header': '',
                    'content': content
                })
            return sections

        # Byg liste af alle headers med deres positioner
        header_elements = []
        for header in headers:
            header_text = header.get_text(strip=True)
            if header_text and len(header_text) >= 2:
                header_elements.append({
                    'element': header,
                    'tag': header.name,
                    'text': header_text
                })

        # Byg set af alle header-tekster for at stoppe korrekt
        all_header_texts = {h['text'] for h in header_elements}

        # For hver header, find indhold EFTER den (ikke kun siblings - også nested content)
        for i, header_info in enumerate(header_elements):
            header = header_info['element']
            header_text = header_info['text']
            header_tag = header_info['tag']

            # Find næste header tekst for at vide hvornår vi skal stoppe
            next_header_text = header_elements[i + 1]['text'] if i + 1 < len(header_elements) else None

            # Saml indhold mellem denne header og næste header
            content_parts = []
            seen_texts = set()  # Undgå duplikater
            passed_next_header = False

            # Brug find_all_next() for at finde ALT indhold efter headeren (uanset nesting)
            for elem in header.find_all_next(['p', 'li', 'td', 'h1', 'h2', 'h3', 'h4']):
                # Stop ved næste header element
                if elem.name in ['h1', 'h2', 'h3', 'h4']:
                    elem_text = elem.get_text(strip=True)
                    # Hvis dette er en anden header (ikke os selv), stop
                    if elem_text != header_text and elem_text in all_header_texts:
                        break
                    continue

                # Hent tekst fra content elementer
                if elem.name in ['p', 'li', 'td']:
                    text = elem.get_text(strip=True)
                    # Undgå korte tekster og duplikater
                    if text and len(text) > 15 and text not in seen_texts:
                        # Tjek at denne tekst ikke er en del af en allerede set tekst
                        is_duplicate = any(text in seen or seen in text for seen in seen_texts)
                        if not is_duplicate:
                            content_parts.append(text)
                            seen_texts.add(text)

            # Tilføj sektion hvis der er indhold
            if content_parts:
                sections.append({
                    'tag': header_tag,
                    'header': header_text,
                    'content': '\n\n'.join(content_parts)
                })

        # Fallback: Hvis ingen sektioner blev oprettet, saml al tekst
        if not sections:
            all_paragraphs = work_soup.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in all_paragraphs if len(p.get_text(strip=True)) > 20])
            if content:
                sections.append({
                    'tag': 'p',
                    'header': '',
                    'content': content
                })

        # DEDUPLICATE sections - page builders often repeat content for responsive views/sliders
        # Keep only unique sections based on header + first 100 chars of content
        seen_sections = set()
        unique_sections = []
        for section in sections:
            # Create a key from header and first 100 chars of content
            key = (section['header'].lower().strip(), section['content'][:100].lower().strip())
            if key not in seen_sections:
                seen_sections.add(key)
                unique_sections.append(section)

        if len(unique_sections) < len(sections):
            print(f"[WebsiteScraper] Deduplicated {len(sections) - len(unique_sections)} duplicate sections, {len(unique_sections)} remaining")

        return unique_sections

    def _element_comes_after(self, reference, element):
        """Check if element comes after reference in document order."""
        # Simple check - compare source positions if available
        ref_pos = str(reference).find(reference.get_text(strip=True)[:20] if reference.get_text(strip=True) else '')
        elem_pos = str(element).find(element.get_text(strip=True)[:20] if element.get_text(strip=True) else '')
        return elem_pos > ref_pos

    def _detect_review_section_position(self, soup, sections):
        """
        Detect WHERE on the page reviews/testimonials appear relative to content sections.

        Args:
            soup: BeautifulSoup object with HTML
            sections: List of extracted sections [{'tag', 'header', 'content'}]

        Returns:
            int or None: Section index AFTER which reviews appear, or None if not detected
        """
        if not sections:
            return None

        # Find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if not main_content:
            return None

        # Selectors for review/testimonial containers
        review_selectors = [
            '.elementor-testimonial',
            '.elementor-widget-testimonial-carousel',
            '[class*="testimonial"]',
            '.trustpilot-widget',
            '[class*="trustpilot"]',
            '[class*="review"]',
            '.tp-widget',
        ]

        # Find first review element
        review_element = None
        for selector in review_selectors:
            review_element = main_content.select_one(selector)
            if review_element:
                break

        if not review_element:
            return None

        # Get all headers in document order
        headers = main_content.find_all(['h1', 'h2', 'h3', 'h4'])

        # Build map of header text to index (matching sections array)
        section_header_texts = [s['header'].strip().lower() for s in sections if s.get('header')]

        # Find which header comes BEFORE the review element
        # by checking all headers and finding the last one before reviews
        last_header_before_review = None
        last_header_index = -1

        for header in headers:
            header_text = header.get_text(strip=True).lower()

            # Check if this header matches any section
            section_index = None
            for i, section_text in enumerate(section_header_texts):
                if header_text == section_text or header_text in section_text or section_text in header_text:
                    section_index = i
                    break

            if section_index is None:
                continue

            # Check if this header comes before the review element
            # Use sourceline if available, otherwise string position
            try:
                header_pos = header.sourceline if hasattr(header, 'sourceline') and header.sourceline else 0
                review_pos = review_element.sourceline if hasattr(review_element, 'sourceline') and review_element.sourceline else 0

                if header_pos and review_pos:
                    if header_pos < review_pos:
                        last_header_before_review = header
                        last_header_index = section_index
                else:
                    # Fallback: check document order using parent traversal
                    # Get all elements in document order
                    all_elements = list(main_content.descendants)
                    try:
                        header_doc_pos = all_elements.index(header) if header in all_elements else -1
                        review_doc_pos = all_elements.index(review_element) if review_element in all_elements else -1

                        if header_doc_pos >= 0 and review_doc_pos >= 0 and header_doc_pos < review_doc_pos:
                            last_header_before_review = header
                            last_header_index = section_index
                    except (ValueError, AttributeError):
                        pass
            except Exception:
                pass

        if last_header_index >= 0:
            print(f"[WebsiteScraper] Reviews detected after section {last_header_index}: '{sections[last_header_index].get('header', '')[:50]}'")
            return last_header_index

        return None

    def classify_sections_with_ai(self, sections):
        """
        Use AI to classify sections and identify which ones contain customer reviews/testimonials.

        Args:
            sections: List of sections [{'header': str, 'content': str, 'tag': str}]

        Returns:
            dict: {
                'reviews': list of review dicts,
                'review_section_indices': list of section indices that are reviews
            }
        """
        if not sections or not self.openai_client:
            return {'reviews': [], 'review_section_indices': []}

        # Build sections text for AI analysis
        sections_text = ""
        for i, section in enumerate(sections):
            header = section.get('header', '').strip()
            content = section.get('content', '').strip()[:500]  # Limit content length
            sections_text += f"\n[SEKTION {i}]\nOverskrift: {header}\nIndhold: {content}\n"

        # Get prompt from database (required)
        db_prompt, model_settings = self._get_prompt_from_db('classify_reviews')

        if not db_prompt:
            print("[WebsiteScraper] Prompt 'classify_reviews' ikke fundet i database. Kør: python manage.py seed_prompts")
            return {'reviews': [], 'review_section_indices': []}

        prompt = db_prompt.format(sections_text=sections_text)
        model = model_settings.get('model') or 'gpt-4o-mini'
        temperature = model_settings.get('temperature', 0.1)
        max_tokens = model_settings.get('max_tokens', 2000)

        try:
            # Select client based on model type
            if model.startswith('sonar'):
                # Use Perplexity client for sonar models
                perplexity_key = getattr(settings, 'PERPLEXITY_API_KEY', None)
                if perplexity_key:
                    client = OpenAI(api_key=perplexity_key, base_url="https://api.perplexity.ai")
                else:
                    # Fallback to OpenAI
                    client = self.openai_client
                    model = 'gpt-4o-mini'
            else:
                client = self.openai_client

            if not client:
                return {'reviews': [], 'review_section_indices': []}

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Du er en ekspert i at analysere website-indhold og identificere kundeanmeldelser. Svar KUN med valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            result_text = response.choices[0].message.content.strip()

            # Clean up JSON if wrapped in markdown code blocks
            if result_text.startswith('```'):
                result_text = re.sub(r'^```(?:json)?\s*', '', result_text)
                result_text = re.sub(r'\s*```$', '', result_text)

            result = json.loads(result_text)

            reviews = result.get('reviews', [])
            indices = result.get('review_section_indices', [])

            if reviews:
                print(f"[WebsiteScraper] AI identified {len(reviews)} reviews in sections: {indices}")

            return {
                'reviews': reviews,
                'review_section_indices': indices
            }

        except json.JSONDecodeError as e:
            print(f"[WebsiteScraper] AI review classification JSON error: {e}")
            return {'reviews': [], 'review_section_indices': []}
        except Exception as e:
            print(f"[WebsiteScraper] AI review classification error: {e}")
            return {'reviews': [], 'review_section_indices': []}

    def _merge_reviews(self, html_reviews, ai_reviews):
        """
        Merge reviews from HTML detection and AI classification, avoiding duplicates.

        Args:
            html_reviews: Reviews from extract_trustpilot_reviews()
            ai_reviews: Reviews from classify_sections_with_ai()

        Returns:
            list: Combined unique reviews
        """
        if not html_reviews and not ai_reviews:
            return []

        if not html_reviews:
            return ai_reviews

        if not ai_reviews:
            return html_reviews

        # Use HTML reviews as base (they have better structure)
        merged = list(html_reviews)
        seen_texts = {r.get('text', '')[:50].lower() for r in html_reviews}

        # Add AI reviews that aren't duplicates
        for review in ai_reviews:
            text_key = review.get('text', '')[:50].lower()
            if text_key and text_key not in seen_texts:
                merged.append(review)
                seen_texts.add(text_key)

        return merged

    def scrape_with_meta(self, url, timeout=10):
        """
        Fetch and extract text content, meta tags, structured sections, AND reviews from a website.

        Args:
            url: Website URL to scrape
            timeout: Request timeout in seconds

        Returns:
            dict: {
                'content': str,
                'meta_title': str or None,
                'meta_description': str or None,
                'sections': list of {'tag', 'header', 'content'},
                'reviews': list of review dicts (from Elementor testimonials etc.)
            }
        """
        if not url:
            return {'content': '', 'meta_title': None, 'meta_description': None, 'sections': [], 'reviews': [], 'review_section_position': None, 'review_iframes': []}

        # Ensure URL has protocol
        if not url.startswith('http'):
            url = 'https://' + url

        # Try multiple user agents if first attempt fails
        response = None
        last_error = None

        for i, user_agent in enumerate(self.user_agents):
            try:
                headers = {**self.base_headers, 'User-Agent': user_agent}
                response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                response.raise_for_status()

                # Check if we actually got HTML content
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type or len(response.content) > 100:
                    break  # Success, exit retry loop

            except requests.RequestException as e:
                last_error = e
                continue

        if response is None or response.status_code != 200:
            return {'content': '', 'meta_title': None, 'meta_description': None, 'sections': [], 'reviews': [], 'review_section_position': None, 'review_iframes': []}

        try:
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract meta tags BEFORE removing elements
            meta_title = None
            meta_description = None

            # Get title
            title_tag = soup.find('title')
            if title_tag:
                meta_title = title_tag.get_text(strip=True)

            # Get meta description
            meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_desc_tag:
                meta_description = meta_desc_tag.get('content', '').strip()

            # Extract structured sections BEFORE modifying soup
            sections = self.extract_all_sections(soup)

            # Extract review iframes (Trustpilot, Google, etc.)
            review_iframes = self.extract_review_iframes(soup)

            # Extract reviews via HTML detection (Elementor testimonials, Trustpilot widgets, etc.)
            # NOTE: AI classification is now done in batch AFTER all pages are crawled (in ComprehensiveWebsiteScraper)
            html_reviews = self.extract_trustpilot_reviews(soup)
            if html_reviews:
                print(f"[WebsiteScraper] HTML detection found {len(html_reviews)} reviews from {url}")

            # Determine review section position based on HTML detection
            review_section_position = None
            if html_reviews:
                review_section_position = self._detect_review_section_position(soup, sections)

            # Now get content using existing method (which modifies soup)
            content = self.scrape_website(url, timeout)

            return {
                'content': content,
                'meta_title': meta_title,
                'meta_description': meta_description,
                'sections': sections,
                'reviews': html_reviews,  # Only HTML-detected reviews (AI classification happens in batch later)
                'review_section_position': review_section_position,
                'review_iframes': review_iframes
            }

        except Exception as e:
            print(f"Website parsing error for {url}: {e}")
            return {'content': '', 'meta_title': None, 'meta_description': None, 'sections': [], 'reviews': [], 'review_section_position': None, 'review_iframes': []}


class USPAnalyzer:
    """Analyze website content to extract and match USPs."""

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        perplexity_key = settings.PERPLEXITY_API_KEY

        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

        if perplexity_key:
            self.perplexity_client = OpenAI(
                api_key=perplexity_key,
                base_url="https://api.perplexity.ai"
            )
        else:
            self.perplexity_client = None

        if not self.client and not self.perplexity_client:
            raise ValueError("Neither OPENAI_API_KEY nor PERPLEXITY_API_KEY is configured")

    def _get_prompt_from_db(self, prompt_type):
        """Get prompt template and settings from database."""
        try:
            from ai_integration.models import AIPromptTemplate
            prompt = AIPromptTemplate.objects.filter(
                prompt_type=prompt_type,
                is_active=True
            ).first()
            if prompt and prompt.prompt_text:
                return prompt.get_prompt_text(), prompt.model_settings or {}
        except Exception as e:
            print(f"Warning: Could not load prompt from DB: {e}")
        return None, None

    def analyze_for_usps(self, website_content, usp_templates):
        """
        Analyze scraped content and match against USP templates.

        Args:
            website_content: Scraped text from WebsiteScraper
            usp_templates: List of dicts with 'id', 'text', 'keywords', 'category'

        Returns:
            Dict with 'matched_usps', 'custom_usps', 'extracted_facts'
        """
        if not website_content:
            return {'matched_usps': [], 'custom_usps': [], 'extracted_facts': {}}

        # Format templates for prompt (limit to prevent token overflow)
        templates_text = "\n".join([
            f"ID:{t['id']} | Tekst: {t['text']} | Kategori: {t.get('category', 'Andet')}"
            for t in usp_templates[:60]
        ])

        # Get prompt from database (required)
        db_prompt, model_settings = self._get_prompt_from_db('extract_usps')

        if not db_prompt:
            print("[USPAnalyzer] Prompt 'extract_usps' ikke fundet i database. Kør: python manage.py seed_prompts")
            return {'matched_usps': [], 'custom_usps': [], 'extracted_facts': {}}

        prompt = db_prompt.format(
            website_content=website_content[:5000],
            templates_text=templates_text
        )

        # Get model from settings
        selected_model = model_settings.get('model') or 'gpt-4.1'
        temperature = model_settings.get('temperature', 0.3)
        max_tokens = model_settings.get('max_tokens', 2000)

        # Determine which client to use based on model
        clients_to_try = []
        if selected_model.startswith('sonar'):
            # Perplexity model selected - try Perplexity first
            if self.perplexity_client:
                clients_to_try.append(('perplexity', self.perplexity_client, selected_model))
            if self.client:
                clients_to_try.append(('openai', self.client, 'gpt-4.1'))
        else:
            # OpenAI model selected - try OpenAI first
            if self.client:
                clients_to_try.append(('openai', self.client, selected_model))
            if self.perplexity_client:
                clients_to_try.append(('perplexity', self.perplexity_client, 'sonar'))

        last_error = None
        for provider, client, model in clients_to_try:
            try:
                print(f"[USPAnalyzer] Trying {provider} ({model})...")
                response = client.chat.completions.create(
                    **build_completion_kwargs(model, [{"role": "user", "content": prompt}], temperature, max_tokens)
                )

                content = response.choices[0].message.content.strip()

                # Parse JSON response
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    match = re.search(r'\{.*\}', content, re.DOTALL)
                    if match:
                        result = json.loads(match.group())
                    else:
                        result = {'matched_usps': [], 'custom_usps': [], 'extracted_facts': {}}

                # Ensure required keys exist
                if 'matched_usps' not in result:
                    result['matched_usps'] = []
                if 'custom_usps' not in result:
                    result['custom_usps'] = []
                if 'extracted_facts' not in result:
                    result['extracted_facts'] = {}

                print(f"[USPAnalyzer] Success with {provider}")
                return result

            except Exception as e:
                error_str = str(e).lower()
                last_error = e
                print(f"[USPAnalyzer] {provider} failed: {e}")

                # If quota exceeded or rate limited, try next provider
                if 'quota' in error_str or 'rate' in error_str or '429' in error_str:
                    print(f"[USPAnalyzer] Quota/rate limit hit, trying next provider...")
                    continue
                else:
                    # Other errors - still try next provider
                    continue

        print(f"USP Analysis error (all providers failed): {last_error}")
        return {'matched_usps': [], 'custom_usps': [], 'extracted_facts': {}}


class ServiceDetector:
    """Detect services/industries from website content using AI."""

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        perplexity_key = settings.PERPLEXITY_API_KEY

        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

        if perplexity_key:
            self.perplexity_client = OpenAI(
                api_key=perplexity_key,
                base_url="https://api.perplexity.ai"
            )
        else:
            self.perplexity_client = None

        if not self.client and not self.perplexity_client:
            raise ValueError("Neither OPENAI_API_KEY nor PERPLEXITY_API_KEY is configured")

    def _get_prompt_from_db(self, prompt_type):
        """Get prompt template and settings from database."""
        try:
            from ai_integration.models import AIPromptTemplate
            prompt = AIPromptTemplate.objects.filter(
                prompt_type=prompt_type,
                is_active=True
            ).first()
            if prompt and prompt.prompt_text:
                return prompt.get_prompt_text(), prompt.model_settings or {}
        except Exception as e:
            print(f"Warning: Could not load prompt from DB: {e}")
        return None, None

    def detect_services(self, website_content: str, available_services: list) -> dict:
        """
        Analyze scraped content and detect which services the company offers.

        Args:
            website_content: Scraped text from website
            available_services: List of dicts with 'id', 'name', 'industry_name', 'description'

        Returns:
            Dict with 'detected_services', 'detected_industries', 'confidence_scores'
        """
        if not website_content or not available_services:
            return {
                'detected_services': [],
                'detected_industries': [],
                'confidence_scores': {}
            }

        # Group services by industry for better prompting
        industries = {}
        for svc in available_services:
            industry = svc.get('industry_name', 'Andet')
            if industry not in industries:
                industries[industry] = []
            industries[industry].append(svc)

        # Format services for prompt
        services_text = ""
        for industry, svcs in industries.items():
            services_text += f"\n{industry}:\n"
            for svc in svcs:
                services_text += f"  - ID:{svc['id']} | {svc['name']}"
                if svc.get('description'):
                    services_text += f" ({svc['description'][:50]}...)"
                services_text += "\n"

        # Build list of industry names
        industry_names = list(industries.keys())

        # Use up to 50,000 chars of content for AI analysis
        content_for_analysis = website_content[:50000]

        # Get prompt from database (required)
        db_prompt, model_settings = self._get_prompt_from_db('detect_services')

        if not db_prompt:
            print("[ServiceDetector] Prompt 'detect_services' ikke fundet i database. Kør: python manage.py seed_prompts")
            return {
                'detected_services': [],
                'suggested_services': [],
                'detected_industries': [],
                'primary_industry': None,
                'confidence_scores': {}
            }

        prompt = db_prompt.format(
            content_for_analysis=content_for_analysis,
            industry_names=', '.join(industry_names),
            services_text=services_text
        )

        # Get model from settings
        selected_model = model_settings.get('model') or 'gpt-4.1'
        temperature = model_settings.get('temperature', 0.2)
        max_tokens = model_settings.get('max_tokens', 2000)

        # Determine which client to use based on model
        clients_to_try = []
        if selected_model.startswith('sonar'):
            # Perplexity model selected - try Perplexity first
            if self.perplexity_client:
                clients_to_try.append(('perplexity', self.perplexity_client, selected_model))
            if self.client:
                clients_to_try.append(('openai', self.client, 'gpt-4.1'))
        else:
            # OpenAI model selected - try OpenAI first
            if self.client:
                clients_to_try.append(('openai', self.client, selected_model))
            if self.perplexity_client:
                clients_to_try.append(('perplexity', self.perplexity_client, 'sonar'))

        last_error = None
        for provider, client, model in clients_to_try:
            try:
                print(f"[ServiceDetector] Trying {provider} ({model})...")
                response = client.chat.completions.create(
                    **build_completion_kwargs(model, [{"role": "user", "content": prompt}], temperature, max_tokens)
                )

                content = response.choices[0].message.content.strip()

                # Parse JSON response
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    match = re.search(r'\{.*\}', content, re.DOTALL)
                    if match:
                        result = json.loads(match.group())
                    else:
                        result = {
                            'detected_services': [],
                            'detected_industries': [],
                            'primary_industry': None
                        }

                # Ensure required keys exist
                if 'detected_services' not in result:
                    result['detected_services'] = []
                if 'suggested_services' not in result:
                    result['suggested_services'] = []
                if 'detected_industries' not in result:
                    result['detected_industries'] = []
                if 'primary_industry' not in result:
                    result['primary_industry'] = None

                # Build confidence scores dict
                result['confidence_scores'] = {
                    svc['service_id']: svc['confidence']
                    for svc in result['detected_services']
                }

                print(f"[ServiceDetector] Success with {provider}")
                return result

            except Exception as e:
                error_str = str(e).lower()
                last_error = e
                print(f"[ServiceDetector] {provider} failed: {e}")

                # If quota exceeded or rate limited, try next provider
                if 'quota' in error_str or 'rate' in error_str or '429' in error_str:
                    print(f"[ServiceDetector] Quota/rate limit hit, trying next provider...")
                    continue
                else:
                    # Other errors - still try next provider
                    continue

        print(f"Service Detection error (all providers failed): {last_error}")
        return {
            'detected_services': [],
            'suggested_services': [],
            'detected_industries': [],
            'primary_industry': None,
            'confidence_scores': {}
        }


class PerplexityResearcher:
    """Research company information using Perplexity web search."""

    def __init__(self):
        api_key = settings.PERPLEXITY_API_KEY
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY is not configured")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )

    def _get_prompt_from_db(self, prompt_type):
        """
        Get prompt template and settings from database.

        Returns tuple of (prompt_text, model_settings) or (None, None) if not found.
        """
        try:
            from ai_integration.models import AIPromptTemplate
            prompt = AIPromptTemplate.objects.filter(
                prompt_type=prompt_type,
                is_active=True
            ).first()
            if prompt and prompt.prompt_text:
                return prompt.get_prompt_text(), prompt.model_settings or {}
        except Exception as e:
            print(f"Warning: Could not load prompt from DB: {e}")
        return None, None

    def research_company(self, website_url, industries, services):
        """
        Search for company information online.

        Args:
            website_url: Company website URL
            industries: List of industry names
            services: List of service names

        Returns:
            str: Summary of found information about the company
        """
        # Build search query context
        industry_text = ', '.join(industries) if industries else 'Ikke angivet'
        service_text = ', '.join(services[:5]) if services else 'Ikke angivet'

        # Get prompt from database (required)
        db_prompt, model_settings = self._get_prompt_from_db('perplexity_research')

        if not db_prompt:
            print("[PerplexityResearcher] Prompt 'perplexity_research' ikke fundet i database. Kør: python manage.py seed_prompts")
            return ""

        prompt = db_prompt.format(
            website_url=website_url if website_url else 'Ikke angivet',
            industries=industry_text,
            services=service_text
        )
        model = model_settings.get('model') or 'sonar'
        temperature = model_settings.get('temperature', 0.3)
        max_tokens = model_settings.get('max_tokens', 800)

        try:
            response = self.client.chat.completions.create(
                **build_completion_kwargs(model, [{"role": "user", "content": prompt}], temperature, max_tokens)
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Return empty string if research fails - generation continues without it
            print(f"Perplexity research failed: {e}")
            return ""


class DescriptionGenerator:
    """Generate Google Ads descriptions using OpenAI GPT-4 with Perplexity fallback."""

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        perplexity_key = settings.PERPLEXITY_API_KEY

        if api_key and api_key != 'your_openai_api_key_here':
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

        if perplexity_key:
            self.perplexity_client = OpenAI(
                api_key=perplexity_key,
                base_url="https://api.perplexity.ai"
            )
        else:
            self.perplexity_client = None

        if not self.client and not self.perplexity_client:
            raise ValueError("Neither OPENAI_API_KEY nor PERPLEXITY_API_KEY is configured. Please set at least one in your .env file.")

    def _make_completion_with_fallback(self, prompt, model_settings, method_name):
        """
        Make a completion request trying OpenAI first, then falling back to Perplexity.

        Args:
            prompt: The prompt text
            model_settings: Dict with 'model', 'temperature', 'max_tokens'
            method_name: Name of the calling method for logging

        Returns:
            The message content from the response
        """
        openai_model = model_settings.get('model') or 'gpt-4.1'
        temperature = model_settings.get('temperature') or 0.7
        max_tokens = model_settings.get('max_tokens') or 500

        # Build list of clients to try
        clients_to_try = []
        if self.client:
            clients_to_try.append(('openai', self.client, openai_model))
        if self.perplexity_client:
            clients_to_try.append(('perplexity', self.perplexity_client, 'sonar'))

        last_error = None
        for provider, client, model in clients_to_try:
            try:
                print(f"[{method_name}] Trying {provider} ({model})...")
                response = client.chat.completions.create(
                    **build_completion_kwargs(model, [{"role": "user", "content": prompt}], temperature, max_tokens)
                )
                content = response.choices[0].message.content.strip()
                print(f"[{method_name}] Success with {provider}")
                return content

            except Exception as e:
                error_str = str(e).lower()
                last_error = e
                print(f"[{method_name}] {provider} failed: {e}")

                # If quota exceeded or rate limited, try next provider
                if 'quota' in error_str or 'rate' in error_str or '429' in error_str:
                    print(f"[{method_name}] Quota/rate limit hit, trying next provider...")
                    continue
                else:
                    # Other errors - still try next provider
                    continue

        raise Exception(f"All providers failed. Last error: {last_error}")

    def _get_prompt_from_db(self, prompt_type):
        """
        Get prompt template and settings from database.

        Returns tuple of (prompt_text, model_settings) or (None, None) if not found.
        """
        try:
            from ai_integration.models import AIPromptTemplate
            prompt = AIPromptTemplate.objects.filter(
                prompt_type=prompt_type,
                is_active=True
            ).first()
            if prompt and prompt.prompt_text:
                return prompt.get_prompt_text(), prompt.model_settings or {}
        except Exception as e:
            print(f"Warning: Could not load prompt from DB: {e}")
        return None, None

    def generate_descriptions(self, service_name, industry_name, usps, keywords):
        """
        Generate 4 unique Google Ads descriptions.

        Args:
            service_name: Name of the service (e.g., "VVS", "Elektriker")
            industry_name: Name of the industry (e.g., "Håndværk")
            usps: List of USP texts
            keywords: List of keywords for the ad group

        Returns:
            List of 4 description strings, each max 90 characters
        """
        # Build context for the prompt - include all keywords
        if keywords:
            keywords_numbered = '\n'.join([f"{i+1}. {kw}" for i, kw in enumerate(keywords[:8])])
        else:
            keywords_numbered = "Ingen søgeord angivet"

        # Formatér USPs som nummereret liste
        if usps:
            usps_numbered = '\n'.join([f"{i+1}. {usp}" for i, usp in enumerate(usps)])
        else:
            usps_numbered = "Ingen USP'er valgt"

        # Formatér services som bullet liste
        if keywords:
            services_list = '\n'.join([f"- {kw}" for kw in keywords[:8]])
        else:
            services_list = f"- {service_name}"

        # Get prompt from database (required)
        db_prompt, model_settings = self._get_prompt_from_db('generate_descriptions')

        if not db_prompt:
            print("[DescriptionGenerator] Prompt 'generate_descriptions' ikke fundet i database. Kør: python manage.py seed_prompts")
            return []

        prompt = db_prompt.format(
            usps_numbered=usps_numbered,
            services_list=services_list,
            service_name=service_name,
            industry_name=industry_name,
            keywords_numbered=keywords_numbered
        )
        model_settings = {
            'model': model_settings.get('model') or 'gpt-4.1',
            'temperature': model_settings.get('temperature', 0.8),
            'max_tokens': model_settings.get('max_tokens', 500)
        }

        try:
            content = self._make_completion_with_fallback(prompt, model_settings, 'generate_descriptions')

            # Try to parse as JSON
            try:
                descriptions = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON array from response
                match = re.search(r'\[.*?\]', content, re.DOTALL)
                if match:
                    descriptions = json.loads(match.group())
                else:
                    # Fallback: split by newlines and clean up
                    lines = [line.strip().strip('"\'') for line in content.split('\n') if line.strip()]
                    descriptions = [line for line in lines if len(line) > 20][:4]

            # Validate and ensure max 4 descriptions, each max 90 chars
            validated = []
            for desc in descriptions[:4]:
                if isinstance(desc, str) and len(desc.strip()) > 0:
                    # Truncate if over 90 characters
                    clean_desc = desc.strip()[:90]
                    validated.append(clean_desc)

            # Ensure we have exactly 4 descriptions
            while len(validated) < 4:
                validated.append(f"Kontakt os for professionel {service_name} service. Ring i dag!")

            return validated[:4]

        except Exception as e:
            raise Exception(f"Fejl ved AI-generering: {str(e)}")

    def generate_meta_tags(self, service_name, usps, few_shot_examples=None):
        """
        Generate 7 unique SEO meta titles and 7 meta descriptions.

        Args:
            service_name: Name of the service (e.g., "VVS", "Elektriker")
            usps: List of USP texts
            few_shot_examples: Optional list of dicts with 'meta_title' and 'meta_description' keys
                              Used as few-shot examples to guide the AI's style and tone

        Returns:
            Dict with 'meta_titles' (list of 7) and 'meta_descriptions' (list of 7)
        """
        # Formatér USPs som nummereret liste
        if usps:
            usps_numbered = '\n'.join([f"{i+1}. {usp}" for i, usp in enumerate(usps[:5])])
        else:
            usps_numbered = "Ingen USP'er valgt"

        # Build few-shot examples section if provided
        examples_section = ""
        if few_shot_examples and len(few_shot_examples) > 0:
            examples_section = "\n\n=== REFERENCE EKSEMPLER (brug disse som inspiration til stil og tone) ===\n"
            for i, ex in enumerate(few_shot_examples, 1):
                examples_section += f"\nEksempel {i}:\n"
                examples_section += f"Meta titel: {ex.get('meta_title', '')}\n"
                examples_section += f"Meta beskrivelse: {ex.get('meta_description', '')}\n"
            examples_section += "\n=== SLUT PÅ EKSEMPLER ===\n"
            examples_section += "VIGTIGT: Generér nye, unikke meta tags der følger samme stil og tone som eksemplerne ovenfor.\n"

        few_shot_instruction = "7. Følg stil og tone fra reference eksemplerne" if few_shot_examples else ""
        default_examples = "" if few_shot_examples else f'''EKSEMPLER på meta titler (50-60 tegn):
- "Professionel {service_name} i {{BYNAVN}} - Hurtig Service"
- "{{BYNAVN}} {service_name} Ekspert - Gratis Tilbud"
- "Autoriseret {service_name} i {{BYNAVN}} - Ring Nu"

EKSEMPLER på meta beskrivelser (150-160 tegn):
- "Leder du efter professionel {service_name} i {{BYNAVN}}? Vi tilbyder hurtig service og fair priser. Ring for gratis tilbud!"
- "{service_name} eksperter i {{BYNAVN}} med mange års erfaring. Kvalitetsarbejde og tilfredse kunder. Kontakt os idag."
'''

        # Get prompt from database (required)
        db_prompt, model_settings = self._get_prompt_from_db('generate_meta_tags')

        if not db_prompt:
            print("[MetaTagGenerator] Prompt 'generate_meta_tags' ikke fundet i database. Kør: python manage.py seed_prompts")
            return {'meta_titles': [], 'meta_descriptions': []}

        prompt = db_prompt.format(
            service_name=service_name,
            usps_numbered=usps_numbered,
            examples_section=examples_section,
            few_shot_instruction=few_shot_instruction,
            default_examples=default_examples
        )
        model_settings = {
            'model': model_settings.get('model') or 'gpt-4.1',
            'temperature': model_settings.get('temperature', 0.9),
            'max_tokens': model_settings.get('max_tokens', 2000)
        }

        try:
            content = self._make_completion_with_fallback(prompt, model_settings, 'generate_meta_tags')

            # Try to parse as JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON object from response
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    result = json.loads(match.group())
                else:
                    raise Exception("Kunne ikke parse AI respons som JSON")

            # Validate meta_titles
            meta_titles = result.get('meta_titles', [])
            validated_titles = []
            for title in meta_titles[:7]:
                if isinstance(title, str) and len(title.strip()) > 0:
                    # Ensure {BYNAVN} is present
                    clean_title = title.strip()
                    if '{BYNAVN}' not in clean_title:
                        clean_title = clean_title + ' {BYNAVN}'
                    validated_titles.append(clean_title)

            # Validate meta_descriptions
            meta_descriptions = result.get('meta_descriptions', [])
            validated_descriptions = []
            for desc in meta_descriptions[:7]:
                if isinstance(desc, str) and len(desc.strip()) > 0:
                    clean_desc = desc.strip()
                    if '{BYNAVN}' not in clean_desc:
                        clean_desc = clean_desc.replace(service_name, f'{service_name} i {{BYNAVN}}', 1)
                    validated_descriptions.append(clean_desc)

            # Ensure we have exactly 7 of each
            while len(validated_titles) < 7:
                validated_titles.append(f'Professionel {service_name} i {{BYNAVN}} - Ring for tilbud')
            while len(validated_descriptions) < 7:
                validated_descriptions.append(f'Kontakt os for professionel {service_name} i {{BYNAVN}}. Hurtig service og fair priser. Ring for gratis tilbud!')

            return {
                'meta_titles': validated_titles[:7],
                'meta_descriptions': validated_descriptions[:7]
            }

        except Exception as e:
            raise Exception(f"Fejl ved AI meta tag generering: {str(e)}")

    def generate_seo_meta_tags(self, service_name, usps, seo_keywords=None, few_shot_examples=None):
        """
        Generate SEO meta title and description WITHOUT {BYNAVN} placeholder.

        Used for SEO Information section where city names should only appear
        if the keyword contains a city (e.g., "Elektriker København").

        Args:
            service_name: Name of the service (e.g., "Elektriker")
            usps: List of USP texts
            seo_keywords: Optional list of SEO keywords (may contain city names)
            few_shot_examples: Optional list of dicts with 'meta_title' and 'meta_description'

        Returns:
            Dict with 'meta_title' (string) and 'meta_description' (string)
        """
        # Format USPs
        if usps:
            usps_formatted = '\n'.join([f"- {usp}" for usp in usps[:5]])
        else:
            usps_formatted = "Ingen USP'er angivet"

        # Format SEO keywords if provided
        keywords_section = ""
        if seo_keywords and len(seo_keywords) > 0:
            keywords_formatted = ', '.join(seo_keywords[:10])
            keywords_section = f"\nSEO Søgeord: {keywords_formatted}\n"

        # Build few-shot examples section
        examples_section = ""
        if few_shot_examples and len(few_shot_examples) > 0:
            examples_section = "\n\n=== VIGTIGE REFERENCE EKSEMPLER ===\n"
            examples_section += "Du SKAL følge samme stil, tone og struktur som disse eksempler:\n\n"
            for i, ex in enumerate(few_shot_examples, 1):
                examples_section += f"Eksempel {i}:\n"
                examples_section += f"  Titel: {ex.get('meta_title', '')}\n"
                examples_section += f"  Beskrivelse: {ex.get('meta_description', '')}\n\n"
            examples_section += "=== SLUT PÅ EKSEMPLER ===\n"
            examples_section += "\nKRITISK: Generér meta tags der ligner eksemplerne i stil og tone!\n"

        few_shot_instruction = "6. FØLG stilen fra reference eksemplerne nøje!" if few_shot_examples else ""
        default_examples = "" if few_shot_examples else f'''EKSEMPEL på god meta titel:
"{service_name} med +15 års erfaring - Hurtig service - Ring nu"

EKSEMPEL på god meta beskrivelse:
"Professionel {service_name} med fokus på kvalitet og kundeservice. Vi tilbyder hurtig service og fair priser. Kontakt os for et uforpligtende tilbud!"
'''

        # Get prompt from database (required)
        db_prompt, model_settings = self._get_prompt_from_db('generate_seo_meta_tags')

        if not db_prompt:
            print("[MetaTagGenerator] Prompt 'generate_seo_meta_tags' ikke fundet i database. Kør: python manage.py seed_prompts")
            return {'meta_title': '', 'meta_description': ''}

        prompt = db_prompt.format(
            service_name=service_name,
            usps_formatted=usps_formatted,
            keywords_section=keywords_section,
            examples_section=examples_section,
            few_shot_instruction=few_shot_instruction,
            default_examples=default_examples
        )
        model_settings = {
            'model': model_settings.get('model') or 'gpt-4.1',
            'temperature': model_settings.get('temperature', 0.7),
            'max_tokens': model_settings.get('max_tokens', 500)
        }

        try:
            content = self._make_completion_with_fallback(prompt, model_settings, 'generate_seo_meta_tags')

            # Try to parse as JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON object from response
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    result = json.loads(match.group())
                else:
                    raise Exception("Kunne ikke parse AI respons som JSON")

            meta_title = result.get('meta_title', '').strip()
            meta_description = result.get('meta_description', '').strip()

            # Ensure we have valid output
            if not meta_title:
                meta_title = f"Professionel {service_name} - Kvalitet og Service"
            if not meta_description:
                meta_description = f"Kontakt os for professionel {service_name}. Vi tilbyder kvalitetsarbejde og god kundeservice. Ring for et uforpligtende tilbud!"

            return {
                'meta_title': meta_title[:70],  # Truncate if too long
                'meta_description': meta_description[:170]
            }

        except Exception as e:
            raise Exception(f"Fejl ved SEO meta tag generering: {str(e)}")

    def generate_company_description(self, website_url, industries, services, usps, geographic_areas, online_research=None, website_content=None):
        """
        Generate a company description using AI based on collected wizard data.

        Args:
            website_url: Company website URL
            industries: List of industry names
            services: List of service names
            usps: List of USP texts
            geographic_areas: List of geographic region/city names
            online_research: Optional string with research results from Perplexity
            website_content: Optional string with scraped website content

        Returns:
            Dict with 'description' (string) and 'key_points' (list)
        """
        # Format industries
        if industries:
            industries_text = ', '.join(industries)
        else:
            industries_text = "Ikke angivet"

        # Format services
        if services:
            services_text = '\n'.join([f"- {s}" for s in services[:10]])
        else:
            services_text = "Ikke angivet"

        # Format USPs
        if usps:
            usps_text = '\n'.join([f"- {usp}" for usp in usps])
        else:
            usps_text = "Ikke angivet"

        # Format geographic areas
        if geographic_areas:
            geo_text = ', '.join(geographic_areas[:15])
        else:
            geo_text = "Landsdækkende"

        # Format website content section if available
        website_section = ""
        if website_content:
            website_section = f"""

INDHOLD FRA VIRKSOMHEDENS HJEMMESIDE:
{website_content}

VIGTIGT: Dette er den faktiske tekst fra virksomhedens hjemmeside. Brug disse konkrete
detaljer (anmeldelser, års erfaring, certificeringer, medarbejdere, osv.) til at gøre
beskrivelsen mere specifik og troværdig."""

        # Format online research section if available
        research_section = ""
        if online_research:
            research_section = f"""

ONLINE RESEARCH (fra nylige web-søgninger):
{online_research}

Brug informationen fra online research til at supplere med eksterne anmeldelser og omtaler."""

        # Get prompt from database (required)
        db_prompt, model_settings = self._get_prompt_from_db('generate_company_description')

        if not db_prompt:
            print("[DescriptionGenerator] Prompt 'generate_company_description' ikke fundet i database. Kør: python manage.py seed_prompts")
            return {'description': '', 'key_points': [], 'profile': {}}

        prompt = db_prompt.format(
            website_url=website_url if website_url else 'Ikke angivet',
            industries=industries_text,
            services=services_text,
            usps=usps_text,
            geographic_areas=geo_text,
            website_content=website_section,
            online_research=research_section
        )
        model_settings = {
            'model': model_settings.get('model') or 'gpt-4.1',
            'temperature': model_settings.get('temperature', 0.7),
            'max_tokens': model_settings.get('max_tokens', 2000)
        }

        try:
            content = self._make_completion_with_fallback(prompt, model_settings, 'generate_company_description')

            # Try to parse as JSON with robust error handling
            result = None
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                # Try to extract JSON object from response
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    json_str = match.group()
                    # Clean up common JSON issues
                    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # Remove trailing commas
                    json_str = json_str.replace('```json', '').replace('```', '')  # Remove markdown
                    try:
                        result = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Last resort: extract description with regex
                        desc_match = re.search(r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"', content)
                        if desc_match:
                            result = {
                                'description': desc_match.group(1).encode().decode('unicode_escape'),
                                'key_points': [],
                                'profile': {}
                            }
                        else:
                            print(f"JSON parse error: {e}")
                            print(f"Content (first 500 chars): {content[:500]}")
                            raise Exception(f"Kunne ikke parse AI respons som JSON")
                else:
                    raise Exception("Kunne ikke finde JSON i AI respons")

            description = result.get('description', '').strip()
            key_points = result.get('key_points', [])
            profile = result.get('profile', {})

            # Validate description
            if not description:
                description = f"Vi er en professionel virksomhed inden for {industries_text}. Vi tilbyder kvalitetsydelser og god kundeservice."

            # Validate key_points
            if not isinstance(key_points, list):
                key_points = []
            key_points = [str(p).strip() for p in key_points if p][:5]

            # Validate profile - ensure it's a dict
            if not isinstance(profile, dict):
                profile = {}

            return {
                'description': description,
                'key_points': key_points,
                'profile': profile,
                'model_used': model_settings.get('model', 'unknown')
            }

        except Exception as e:
            raise Exception(f"Fejl ved generering af virksomhedsbeskrivelse: {str(e)}")

    def generate_page_seo_content(self, action, service_name, industry=None, usps=None, company_name=None,
                                   company_profile=None, city=None,
                                   existing_content=None, existing_meta_title=None, existing_meta_description=None):
        """
        Generate or rewrite SEO content for a service page.

        Args:
            action: 'generate_new' or 'rewrite'
            service_name: Name of the service
            industry: Industry name (for new pages)
            usps: List of USP strings
            company_name: Company name (for new pages)
            company_profile: Dict with company info (website, trustpilot, differentiation, etc.)
            city: Primary city/area for local SEO
            existing_content: Existing page content (for rewrite)
            existing_meta_title: Current meta title (for rewrite)
            existing_meta_description: Current meta description (for rewrite)

        Returns:
            Dict with 'meta_title', 'meta_description', 'intro_text'
        """
        # Format USPs
        if usps:
            usps_text = '\n'.join([f"{i+1}. {usp}" for i, usp in enumerate(usps)])
        else:
            usps_text = "Ikke angivet"

        # Format company profile as readable text
        if company_profile and isinstance(company_profile, dict):
            profile_parts = []
            if company_profile.get('navn') or company_profile.get('name'):
                profile_parts.append(f"Navn: {company_profile.get('navn') or company_profile.get('name')}")
            if company_profile.get('website'):
                profile_parts.append(f"Website: {company_profile.get('website')}")
            if company_profile.get('trovaerdighed') or company_profile.get('trustworthiness'):
                trust = company_profile.get('trovaerdighed') or company_profile.get('trustworthiness', {})
                if trust.get('trustpilot_score'):
                    profile_parts.append(f"Trustpilot: {trust.get('trustpilot_score')}")
                if trust.get('aar_i_branchen'):
                    profile_parts.append(f"År i branchen: {trust.get('aar_i_branchen')}")
            if company_profile.get('differentiering') or company_profile.get('differentiation'):
                diff = company_profile.get('differentiering') or company_profile.get('differentiation', [])
                if diff:
                    profile_parts.append(f"Differentiering: {', '.join(diff[:3])}")
            company_profile_text = '\n'.join(profile_parts) if profile_parts else 'Ikke angivet'
        else:
            company_profile_text = 'Ikke angivet'

        # Choose prompt type based on action
        if action == 'rewrite':
            prompt_type = 'rewrite_page_content'
            db_prompt, model_settings = self._get_prompt_from_db(prompt_type)

            if not db_prompt:
                print(f"[SEOContentGenerator] Prompt '{prompt_type}' ikke fundet i database. Kør: python manage.py seed_prompts")
                return {'meta_title': '', 'meta_description': '', 'intro_text': '', 'reviews': []}

            prompt = db_prompt.format(
                service_name=service_name,
                existing_content=existing_content or 'Ikke angivet',
                existing_meta_title=existing_meta_title or 'Ikke angivet',
                existing_meta_description=existing_meta_description or 'Ikke angivet',
                usps=usps_text
            )
        else:  # generate_new
            prompt_type = 'generate_page_content'
            db_prompt, model_settings = self._get_prompt_from_db(prompt_type)

            if not db_prompt:
                print(f"[SEOContentGenerator] Prompt '{prompt_type}' ikke fundet i database. Kør: python manage.py seed_prompts")
                return {'meta_title': '', 'meta_description': '', 'intro_text': '', 'reviews': []}

            prompt = db_prompt.format(
                service_name=service_name,
                industry=industry or 'Ikke angivet',
                usps=usps_text,
                company_name=company_name or 'Virksomheden',
                company_profile=company_profile_text,
                city=city or 'Danmark'
            )

        # Get model settings
        model = model_settings.get('model') or 'gpt-4.1'
        temperature = model_settings.get('temperature', 0.7)
        max_tokens = model_settings.get('max_tokens', 1200)

        try:
            # Try OpenAI first
            response = self.client.chat.completions.create(
                **build_completion_kwargs(model, [{"role": "user", "content": prompt}], temperature, max_tokens)
            )
            ai_response = response.choices[0].message.content.strip()
        except Exception as openai_error:
            print(f"OpenAI error in generate_page_seo_content: {openai_error}")
            # Try Perplexity fallback
            if self.perplexity_client:
                try:
                    response = self.perplexity_client.chat.completions.create(
                        model='sonar',
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    ai_response = response.choices[0].message.content.strip()
                except Exception as perplexity_error:
                    raise Exception(f"Both OpenAI and Perplexity failed: {openai_error}, {perplexity_error}")
            else:
                raise openai_error

        # Parse JSON response
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', ai_response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(ai_response)

            return {
                'meta_title': result.get('meta_title', '')[:70],
                'meta_description': result.get('meta_description', '')[:170],
                'intro_text': result.get('intro_text', ''),
                'reviews': result.get('reviews', [])
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract content manually
            return {
                'meta_title': f"Professionel {service_name}",
                'meta_description': f"Kontakt os for professionel {service_name}. Kvalitetsarbejde og god service.",
                'intro_text': ai_response,
                'reviews': []
            }


class ComprehensiveWebsiteScraper:
    """
    Scraper der henter indhold fra hele hjemmesiden via sitemap.
    Understøtter valgfri dybde (10, 50, 100, eller alle sider).
    """

    # Patterns for priority pages (scraped first)
    PRIORITY_PATTERNS = [
        r'/$',              # Forside
        r'/om-os/?$',       # Om os
        r'/about/?$',
        r'/om/?$',
        r'/kontakt/?$',     # Kontakt
        r'/contact/?$',
        r'/services?/?$',   # Services/ydelser
        r'/ydelser/?$',
        r'/priser/?$',      # Priser
        r'/prices?/?$',
        r'/faq/?$',         # FAQ
        r'/team/?$',        # Team
        r'/medarbejdere/?$',
    ]

    def __init__(self, cache_days=7):
        self.page_scraper = WebsiteScraper(max_content_length=8000)
        self.cache_days = cache_days

    def scrape_website(self, url, max_pages=10, client_id=None, use_playwright=False):
        """
        Scrape a website comprehensively.

        Args:
            url: Website URL to scrape
            max_pages: Maximum pages to scrape (10, 50, 100, or 0/None for all)
            client_id: If set, save permanently to Client model
            use_playwright: DEPRECATED - no longer used, review iframes are detected automatically

        Returns:
            Dict with scraped data structure including review_iframes
        """
        from campaigns.sitemap_service import SitemapCrawler
        from django.core.cache import cache
        from django.utils import timezone
        import hashlib

        # Ensure URL has protocol
        if not url.startswith('http'):
            url = 'https://' + url

        # Generate cache key for non-client scrapes
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        cache_key = f'scrape_{url_hash}_{max_pages}'

        # Check for existing data
        existing_data = self._get_existing_data(url, client_id, cache_key)
        if existing_data:
            print(f"[ComprehensiveScraper] Using cached data for {url}")
            return existing_data

        print(f"[ComprehensiveScraper] Starting scrape of {url} (max_pages={max_pages})")

        # Discover sitemap URLs
        sitemap_crawler = SitemapCrawler(url)
        success, sitemap_urls, message = sitemap_crawler.crawl_all_urls()

        if not success or not sitemap_urls:
            print(f"[ComprehensiveScraper] Sitemap discovery failed: {message}")
            # Fallback: just scrape the main URL
            sitemap_urls = [url]

        print(f"[ComprehensiveScraper] Found {len(sitemap_urls)} URLs in sitemap")

        # If sitemap is limited (<20 pages), also crawl internal links from homepage
        if len(sitemap_urls) < 20:
            print("[ComprehensiveScraper] Sitemap limited, discovering internal links...")
            internal_links = self._discover_internal_links(url, sitemap_urls)
            if internal_links:
                sitemap_urls = list(set(sitemap_urls + internal_links))
                print(f"[ComprehensiveScraper] After link discovery: {len(sitemap_urls)} URLs")

        # Prioritize and limit URLs
        urls_to_scrape = self._get_prioritized_urls(sitemap_urls, max_pages, url)

        print(f"[ComprehensiveScraper] Will scrape {len(urls_to_scrape)} pages")

        # Scrape each page
        pages_data = {}
        combined_content_parts = []
        all_extracted_reviews = []  # Store reviews (from Playwright OR normal scraping)
        all_review_iframes = []  # Store review iframes (Trustpilot, Google etc.)

        for i, page_url in enumerate(urls_to_scrape):
            try:
                print(f"[ComprehensiveScraper] Scraping ({i+1}/{len(urls_to_scrape)}): {page_url}")

                # Scrape page with meta info, sections, reviews, and iframes
                scraped = self.page_scraper.scrape_with_meta(page_url)

                # Extract reviews (Elementor testimonials, Trustpilot widgets etc.)
                page_reviews = scraped.get('reviews', [])
                if page_reviews:
                    all_extracted_reviews.extend(page_reviews)

                # Extract review iframes (Trustpilot, Google etc.) - primarily from main page
                page_iframes = scraped.get('review_iframes', [])
                if page_iframes:
                    all_review_iframes.extend(page_iframes)
                    print(f"[ComprehensiveScraper] Found {len(page_iframes)} review iframes on {page_url}")

                content = scraped.get('content', '')

                if content:
                    # Get relative path
                    from urllib.parse import urlparse
                    path = urlparse(page_url).path or '/'

                    page_info = {
                        'url': page_url,
                        'path': path,
                        'content': content,
                        'meta_title': scraped.get('meta_title'),
                        'meta_description': scraped.get('meta_description'),
                        'page_type': self._detect_page_type(path),
                        'sections': scraped.get('sections', []),  # Strukturerede sektioner fra siden
                        'review_section_position': scraped.get('review_section_position'),  # Position af reviews på siden
                    }
                    pages_data[path] = page_info
                    combined_content_parts.append(f"--- {path} ---\n{content}")

            except Exception as e:
                print(f"[ComprehensiveScraper] Error scraping {page_url}: {e}")
                continue

        # Combine all content
        combined_content = '\n\n'.join(combined_content_parts)

        # Create service summary - a condensed view of ALL pages for service detection
        # This ensures we capture service names from all pages even if content is truncated
        service_summary_parts = []
        for path, page_info in pages_data.items():
            content = page_info.get('content', '')
            # Extract first 500 chars from each page - enough to get title/headings
            summary = content[:500] if len(content) > 500 else content
            service_summary_parts.append(f"[{path}] {summary}")

        service_summary = '\n'.join(service_summary_parts)

        # Truncate combined content if too long (for AI analysis)
        # Increased from 15000 to 100000 to capture more service-relevant content
        max_combined_length = 100000
        if len(combined_content) > max_combined_length:
            combined_content = combined_content[:max_combined_length] + "\n... (trunkeret)"

        # BATCH AI Classification: Collect all sections from all pages and classify in ONE call
        # This is much faster than calling AI per page
        all_sections_for_ai = []
        for path, page_info in pages_data.items():
            for i, section in enumerate(page_info.get('sections', [])):
                all_sections_for_ai.append({
                    'page': path,
                    'index': i,
                    **section
                })

        # Run ONE AI classification on all sections (if any exist)
        if all_sections_for_ai:
            print(f"[ComprehensiveScraper] Running batch AI classification on {len(all_sections_for_ai)} sections from {len(pages_data)} pages...")
            ai_result = self.page_scraper.classify_sections_with_ai(all_sections_for_ai)
            ai_reviews = ai_result.get('reviews', [])
            if ai_reviews:
                print(f"[ComprehensiveScraper] AI found {len(ai_reviews)} additional reviews")
                # Merge with HTML-detected reviews (avoiding duplicates)
                all_extracted_reviews = self.page_scraper._merge_reviews(all_extracted_reviews, ai_reviews)

        # Build result structure
        result = {
            'url': url,
            'scraped_at': timezone.now().isoformat(),
            'max_pages': max_pages,
            'sitemap_urls_count': len(sitemap_urls),
            'pages_scraped': len(pages_data),
            'pages': pages_data,
            'combined_content': combined_content,
            'service_summary': service_summary,  # Condensed summary for service detection
            'extracted_reviews': all_extracted_reviews,  # Reviews from Trustpilot/Google etc.
            'review_iframes': all_review_iframes,  # Review widget iframes (Trustpilot, Google etc.)
        }

        # Save data
        self._save_data(result, client_id, cache_key)

        return result

    def _get_existing_data(self, url, client_id, cache_key):
        """Check for existing scraped data."""
        from django.core.cache import cache

        # Check Client model first if client_id provided
        if client_id:
            try:
                from campaigns.models import Client
                client = Client.objects.get(id=client_id)
                if client.scraped_data and client.website_url == url:
                    return client.scraped_data
            except Exception:
                pass

        # Check cache
        cached = cache.get(cache_key)
        if cached:
            return cached

        return None

    def _save_data(self, data, client_id, cache_key):
        """Save scraped data to Client model or cache."""
        from django.core.cache import cache
        from django.utils import timezone

        if client_id:
            # Save permanently to Client model
            try:
                from campaigns.models import Client
                client = Client.objects.get(id=client_id)
                client.scraped_data = data
                client.scraped_at = timezone.now()
                client.save(update_fields=['scraped_data', 'scraped_at'])
                print(f"[ComprehensiveScraper] Saved to Client {client_id}")
            except Exception as e:
                print(f"[ComprehensiveScraper] Error saving to Client: {e}")
                # Fallback to cache
                cache.set(cache_key, data, timeout=self.cache_days * 24 * 60 * 60)
        else:
            # Save to cache (7 days)
            cache.set(cache_key, data, timeout=self.cache_days * 24 * 60 * 60)
            print(f"[ComprehensiveScraper] Saved to cache (key={cache_key})")

    def _get_prioritized_urls(self, sitemap_urls, max_pages, base_url):
        """
        Sort URLs by priority - key pages first, then the rest.

        Args:
            sitemap_urls: List of all URLs from sitemap
            max_pages: Maximum pages to return (0 or None for all)
            base_url: The base URL to ensure it's included

        Returns:
            List of URLs to scrape, prioritized
        """
        from urllib.parse import urlparse

        # Ensure base URL is included
        base_parsed = urlparse(base_url)
        base_domain = base_parsed.netloc

        # Filter to same domain only
        same_domain_urls = [u for u in sitemap_urls
                           if urlparse(u).netloc == base_domain]

        # Separate priority and regular URLs
        priority_urls = []
        regular_urls = []

        for url in same_domain_urls:
            path = urlparse(url).path
            is_priority = any(re.search(pattern, path, re.IGNORECASE)
                             for pattern in self.PRIORITY_PATTERNS)
            if is_priority:
                priority_urls.append(url)
            else:
                regular_urls.append(url)

        # Ensure base URL is first
        if base_url not in priority_urls:
            priority_urls.insert(0, base_url)

        # Combine: priority first, then regular
        all_urls = priority_urls + regular_urls

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in all_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        # Apply limit
        if max_pages and max_pages > 0:
            return unique_urls[:max_pages]

        return unique_urls

    def _detect_page_type(self, path):
        """Detect page type from URL path."""
        path_lower = path.lower()

        if path == '/' or path == '':
            return 'forside'
        elif any(x in path_lower for x in ['/om-os', '/about', '/om/']):
            return 'om_os'
        elif any(x in path_lower for x in ['/kontakt', '/contact']):
            return 'kontakt'
        elif any(x in path_lower for x in ['/service', '/ydelse']):
            return 'services'
        elif any(x in path_lower for x in ['/pris', '/price']):
            return 'priser'
        elif any(x in path_lower for x in ['/faq', '/spoergsmaal']):
            return 'faq'
        elif any(x in path_lower for x in ['/blog', '/nyheder', '/news']):
            return 'blog'
        else:
            return 'andet'

    def _discover_internal_links(self, base_url, existing_urls):
        """
        Discover internal links by scraping the homepage.
        Used as a fallback when sitemap is limited.

        Args:
            base_url: The base website URL
            existing_urls: URLs already found in sitemap

        Returns:
            List of new internal URLs found
        """
        from urllib.parse import urlparse, urljoin
        from bs4 import BeautifulSoup
        import requests

        discovered_urls = []

        try:
            # Scrape homepage for links
            response = requests.get(base_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; GoogleAdsBuilder/1.0)'
            })
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            base_parsed = urlparse(base_url)
            base_domain = base_parsed.netloc

            # Find all links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')

                # Skip empty, anchors, tel, mailto, javascript
                if not href or href.startswith(('#', 'tel:', 'mailto:', 'javascript:')):
                    continue

                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)

                # Only include same domain
                if parsed.netloc != base_domain:
                    continue

                # Skip file extensions
                path_lower = parsed.path.lower()
                if any(path_lower.endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.gif', '.zip']):
                    continue

                # Normalize URL (remove trailing slash for comparison)
                normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
                if not normalized_url.endswith('/'):
                    normalized_url += '/'

                # Also check without trailing slash
                url_variants = [
                    full_url,
                    full_url.rstrip('/'),
                    full_url.rstrip('/') + '/'
                ]

                # Skip if already in existing URLs
                if any(v in existing_urls for v in url_variants):
                    continue

                if full_url not in discovered_urls:
                    discovered_urls.append(full_url)

            print(f"[ComprehensiveScraper] Discovered {len(discovered_urls)} new internal links")

        except Exception as e:
            print(f"[ComprehensiveScraper] Error discovering internal links: {e}")

        return discovered_urls
