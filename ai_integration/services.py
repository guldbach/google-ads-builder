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


# ============================================================================
# Layout Extraction Classes for Wireframe Generation
# ============================================================================

class PageBuilderDetector:
    """
    Detect which page builder was used to create a webpage.
    Supports Elementor, Divi, WPBakery, Beaver Builder, and generic detection.
    """

    BUILDER_SIGNATURES = {
        'elementor': {
            'classes': ['.elementor-section', '.elementor-column', '.elementor-widget', '.elementor'],
            'data_attrs': ['data-element_type', 'data-settings', 'data-id'],
            'scripts': ['elementor-frontend', 'elementor-common'],
        },
        'divi': {
            'classes': ['.et_pb_section', '.et_pb_row', '.et_pb_column', '.et_pb_module'],
            'data_attrs': ['data-et-multi-view'],
            'scripts': ['et-builder', 'divi'],
        },
        'wpbakery': {
            'classes': ['.vc_row', '.vc_column', '.wpb_wrapper', '.vc_inner'],
            'data_attrs': ['data-vc-full-width', 'data-vc-stretch-content'],
            'scripts': ['js_composer', 'wpb_composer'],
        },
        'beaver_builder': {
            'classes': ['.fl-row', '.fl-col', '.fl-module'],
            'data_attrs': ['data-node'],
            'scripts': ['fl-builder'],
        },
    }

    def detect(self, soup: BeautifulSoup) -> dict:
        """
        Detect page builder from HTML.

        Args:
            soup: BeautifulSoup object of the page HTML

        Returns:
            dict with 'builder', 'confidence', 'indicators_found'
        """
        results = {}

        for builder_name, signatures in self.BUILDER_SIGNATURES.items():
            score = 0
            indicators = []

            # Check CSS classes
            for css_class in signatures['classes']:
                selector = css_class.replace('.', '')
                elements = soup.find_all(class_=lambda x: x and selector in str(x))
                if elements:
                    score += len(elements)
                    indicators.append(f"class:{css_class}={len(elements)}")

            # Check data attributes
            for data_attr in signatures['data_attrs']:
                elements = soup.find_all(attrs={data_attr: True})
                if elements:
                    score += len(elements) * 2  # Data attrs weighted higher
                    indicators.append(f"attr:{data_attr}={len(elements)}")

            # Check scripts
            for script_name in signatures['scripts']:
                scripts = soup.find_all('script', src=lambda x: x and script_name in str(x))
                if scripts:
                    score += 10  # Scripts are strong indicators
                    indicators.append(f"script:{script_name}")

            results[builder_name] = {
                'score': score,
                'indicators': indicators
            }

        # Find the best match
        best_builder = None
        best_score = 0
        best_indicators = []

        for builder_name, data in results.items():
            if data['score'] > best_score:
                best_score = data['score']
                best_builder = builder_name
                best_indicators = data['indicators']

        # Calculate confidence (normalize to 0-1)
        confidence = min(best_score / 50.0, 1.0) if best_score > 0 else 0

        # If no builder detected with confidence, check for generic grid systems
        if confidence < 0.3:
            generic_check = self._check_generic_grid(soup)
            if generic_check['found']:
                return {
                    'builder': 'generic',
                    'confidence': generic_check['confidence'],
                    'indicators_found': generic_check['indicators']
                }

        return {
            'builder': best_builder if confidence > 0.1 else None,
            'confidence': confidence,
            'indicators_found': best_indicators
        }

    def _check_generic_grid(self, soup: BeautifulSoup) -> dict:
        """Check for generic CSS grid frameworks (Bootstrap, Tailwind, Foundation)."""
        indicators = []
        score = 0

        # Bootstrap
        bootstrap_cols = soup.find_all(class_=lambda x: x and any(
            c in str(x) for c in ['col-md-', 'col-lg-', 'col-sm-', 'col-xs-', 'col-12', 'col-6', 'col-4']
        ))
        if bootstrap_cols:
            score += len(bootstrap_cols)
            indicators.append(f"bootstrap-grid={len(bootstrap_cols)}")

        # Tailwind
        tailwind_cols = soup.find_all(class_=lambda x: x and any(
            c in str(x) for c in ['w-1/2', 'w-1/3', 'w-2/3', 'w-1/4', 'w-3/4', 'w-full', 'md:w-', 'lg:w-']
        ))
        if tailwind_cols:
            score += len(tailwind_cols)
            indicators.append(f"tailwind-grid={len(tailwind_cols)}")

        # Foundation
        foundation_cols = soup.find_all(class_=lambda x: x and any(
            c in str(x) for c in ['large-', 'medium-', 'small-', 'cell']
        ))
        if foundation_cols:
            score += len(foundation_cols)
            indicators.append(f"foundation-grid={len(foundation_cols)}")

        return {
            'found': score > 0,
            'confidence': min(score / 20.0, 0.8),
            'indicators': indicators
        }


# Elementor widget type mapping til generiske kategorier
WIDGET_CATEGORY_MAP = {
    # Karruseller (alle typer)
    'testimonial-carousel': 'carousel',
    'nested-carousel': 'carousel',
    'media-carousel': 'carousel',
    'slides': 'carousel',
    'image-carousel': 'carousel',

    # Formularer
    'form': 'form',
    'wp-form': 'form',
    'wpforms': 'form',
    'contact-form-7': 'form',

    # Tekst elementer
    'heading': 'heading',
    'text-editor': 'text',

    # Lister
    'icon-list': 'list',
    'icon-box': 'card',
    'price-list': 'list',

    # Billeder
    'image': 'image',
    'image-box': 'image_card',
    'image-gallery': 'gallery',

    # Interaktive
    'toggle': 'accordion',
    'accordion': 'accordion',
    'tabs': 'tabs',

    # Buttons
    'button': 'button',
    'call-to-action': 'cta',

    # Video
    'video': 'video',
    'video-playlist': 'video',

    # Reviews/Testimonials
    'testimonial': 'testimonial',
    'reviews': 'testimonial',

    # Navigation
    'nav-menu': 'navigation',
    'menu': 'navigation',

    # Dividers og spacers
    'divider': 'spacer',
    'spacer': 'spacer',

    # Social
    'social-icons': 'social',
    'share-buttons': 'social',

    # Flip boxes og cards
    'flip-box': 'flip_card',
    'call-to-action': 'cta',
}


class VisionLayoutAnalyzer:
    """
    AI Vision-baseret layout analyse via GPT-4o.
    Tager screenshot af website og analyserer visuelt layout.
    """

    LAYOUT_ANALYSIS_PROMPT = """Analyser denne webside screenshot og identificer den visuelle layout-struktur.

Du skal returnere en JSON-struktur der beskriver HVER synlig sektion på siden.

For HVER sektion, angiv:
1. type: hero, services, testimonials, reviews, contact, contact_form, about, cta, text, gallery, team, pricing, faq, footer
2. header: Hovedoverskriften i sektionen (hvis synlig)
3. subheader: Underoverskrift (hvis synlig)
4. content: Kort beskrivelse af indholdet
5. width: Sektionens bredde - "1/1" (fuld bredde), "1/2", "1/3", "1/4", "2/3", "3/4"
6. columns: Hvis sektionen har flere kolonner, beskriv hver kolonne

VIGTIGE REGLER:
- Spring IKKE header/navigation over - men marker dem som type: "header"
- Spring IKKE footer over - marker som type: "footer"
- Identificer kontaktformularer (type: "contact_form") og beskriv felterne
- Identificer anmeldelser/testimonials (type: "reviews" eller "testimonials")
- Identificer CTA-sektioner med knapper (type: "cta")
- Estimer kolonnebredder baseret på det visuelle layout

Returner KUN valid JSON (ingen markdown code blocks):
{
    "page_type": "frontpage|service|contact|about|other",
    "sections": [
        {
            "order": 1,
            "type": "hero",
            "header": "Velkommen til vores virksomhed",
            "subheader": "Vi hjælper dig med...",
            "content": "Hero sektion med stor overskrift og CTA knap",
            "width": "1/1",
            "has_cta": true,
            "cta_text": "Kontakt os"
        },
        {
            "order": 2,
            "type": "services",
            "header": "Vores ydelser",
            "width": "1/1",
            "columns": [
                {"width": "1/3", "content": "Service 1 beskrivelse"},
                {"width": "1/3", "content": "Service 2 beskrivelse"},
                {"width": "1/3", "content": "Service 3 beskrivelse"}
            ]
        },
        {
            "order": 3,
            "type": "contact_form",
            "header": "Kontakt os",
            "width": "1/2",
            "fields": ["Navn", "Email", "Telefon", "Besked"],
            "button_text": "Send"
        }
    ]
}"""

    def __init__(self, cache_dir: str = None):
        """
        Initialize Vision Layout Analyzer.

        Args:
            cache_dir: Directory for screenshot caching. Defaults to /tmp/vision_layout_cache
        """
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.cache_dir = cache_dir or '/tmp/vision_layout_cache'
        self.cache_ttl_hours = 24  # Cache screenshots for 24 hours

        # Ensure cache directory exists
        import os
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, url: str) -> str:
        """Generate cache file path for URL."""
        import hashlib
        import os
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.png")

    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cached screenshot is still valid."""
        import os
        from datetime import datetime, timedelta

        if not os.path.exists(cache_path):
            return False

        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - file_time < timedelta(hours=self.cache_ttl_hours)

    async def capture_screenshot(self, url: str, use_cache: bool = True) -> bytes:
        """
        Capture full-page screenshot using Playwright.

        Args:
            url: URL to screenshot
            use_cache: If True, use cached screenshot if available

        Returns:
            Screenshot bytes (PNG format)
        """
        from playwright.async_api import async_playwright
        import os

        cache_path = self._get_cache_path(url)

        # Check cache
        if use_cache and self._is_cache_valid(cache_path):
            print(f"[VisionLayout] Using cached screenshot for {url}")
            with open(cache_path, 'rb') as f:
                return f.read()

        print(f"[VisionLayout] Capturing screenshot for {url}...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={'width': 1280, 'height': 800})

            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)  # Wait for dynamic content

                screenshot_bytes = await page.screenshot(full_page=True)

                # Cache screenshot
                with open(cache_path, 'wb') as f:
                    f.write(screenshot_bytes)
                print(f"[VisionLayout] Screenshot cached at {cache_path}")

                return screenshot_bytes

            except Exception as e:
                print(f"[VisionLayout] Screenshot failed for {url}: {e}")
                raise
            finally:
                await browser.close()

    def capture_screenshot_sync(self, url: str, use_cache: bool = True) -> bytes:
        """Synchronous wrapper for capture_screenshot."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(self.capture_screenshot(url, use_cache))
                )
                return future.result(timeout=60)
        except RuntimeError:
            return asyncio.run(self.capture_screenshot(url, use_cache))

    def analyze_layout(self, screenshot_bytes: bytes, max_retries: int = 3) -> dict:
        """
        Analyze screenshot using GPT-4o Vision.

        Args:
            screenshot_bytes: PNG screenshot bytes
            max_retries: Number of retries on failure

        Returns:
            Dict with 'page_type' and 'sections' array
        """
        import base64
        import time

        image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        for attempt in range(max_retries):
            try:
                print(f"[VisionLayout] Sending to GPT-4o Vision (attempt {attempt + 1}/{max_retries})...")

                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                            },
                            {
                                "type": "text",
                                "text": self.LAYOUT_ANALYSIS_PROMPT
                            }
                        ]
                    }],
                    max_tokens=4096,
                    timeout=120.0
                )

                response_text = response.choices[0].message.content

                # Parse JSON response
                if response_text.startswith('```'):
                    response_text = response_text.split('```')[1]
                    if response_text.startswith('json'):
                        response_text = response_text[4:]

                result = json.loads(response_text.strip())
                print(f"[VisionLayout] Detected {len(result.get('sections', []))} sections")
                return result

            except json.JSONDecodeError as e:
                print(f"[VisionLayout] JSON parse error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return {'page_type': 'unknown', 'sections': []}

            except Exception as e:
                print(f"[VisionLayout] API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise

        return {'page_type': 'unknown', 'sections': []}

    def convert_to_flat_sections(self, vision_result: dict, existing_content: dict = None) -> list:
        """
        Convert Vision API result to flat_sections format.

        Args:
            vision_result: Result from analyze_layout()
            existing_content: Optional dict with scraped text content to enrich sections

        Returns:
            List of flat_sections ready for campaign_builder_wizard.html
        """
        import time
        import random
        import string

        def generate_id(prefix: str) -> str:
            timestamp = int(time.time() * 1000)
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
            return f"{prefix}_{timestamp}_{random_str}"

        flat_sections = []

        for section in vision_result.get('sections', []):
            section_type = section.get('type', 'text')

            # Skip header and footer for wireframe
            if section_type in ['header', 'footer', 'navigation']:
                continue

            # Handle multi-column sections
            columns = section.get('columns', [])
            if columns:
                for col in columns:
                    flat_sections.append({
                        'id': generate_id('section'),
                        'type': section_type,
                        'width': col.get('width', '1/1'),
                        'header': section.get('header', ''),
                        'subheader': section.get('subheader', ''),
                        'content': col.get('content', ''),
                        'position': len(flat_sections),
                        'contents': [{
                            'id': generate_id('content'),
                            'type': section_type,
                            'header': section.get('header', ''),
                            'content': col.get('content', ''),
                        }]
                    })
            else:
                # Single column section
                contents = [{
                    'id': generate_id('content'),
                    'type': section_type,
                    'header': section.get('header', ''),
                    'subheader': section.get('subheader', ''),
                    'content': section.get('content', ''),
                }]

                # Add special fields for specific types
                if section_type == 'contact_form':
                    contents[0]['fields'] = section.get('fields', [])
                    contents[0]['button_text'] = section.get('button_text', 'Send')

                if section_type in ['reviews', 'testimonials']:
                    contents[0]['reviews'] = section.get('reviews', [])

                if section.get('has_cta'):
                    contents[0]['has_cta'] = True
                    contents[0]['cta_text'] = section.get('cta_text', '')

                flat_sections.append({
                    'id': generate_id('section'),
                    'type': section_type,
                    'width': section.get('width', '1/1'),
                    'header': section.get('header', ''),
                    'subheader': section.get('subheader', ''),
                    'content': section.get('content', ''),
                    'position': len(flat_sections),
                    'contents': contents
                })

        return flat_sections

    def analyze_url(self, url: str, use_cache: bool = True) -> dict:
        """
        Complete workflow: screenshot → vision analysis → flat_sections.

        Args:
            url: URL to analyze
            use_cache: If True, use cached screenshot

        Returns:
            Dict with 'flat_sections', 'page_type', 'vision_raw'
        """
        try:
            screenshot = self.capture_screenshot_sync(url, use_cache)
            vision_result = self.analyze_layout(screenshot)
            flat_sections = self.convert_to_flat_sections(vision_result)

            return {
                'flat_sections': flat_sections,
                'page_type': vision_result.get('page_type', 'unknown'),
                'vision_raw': vision_result,
                'success': True
            }
        except Exception as e:
            print(f"[VisionLayout] analyze_url failed for {url}: {e}")
            return {
                'flat_sections': [],
                'page_type': 'unknown',
                'vision_raw': None,
                'success': False,
                'error': str(e)
            }


class ElementorLayoutExtractor:
    """
    Extract layout structure from Elementor-built pages.
    Supports both classic structure (.elementor-section/.elementor-column)
    and new container structure (e-con, introduced in Elementor 3.6+).
    """

    # Elementor width mapping (percentage to fraction)
    WIDTH_MAP = {
        100: '1/1',
        83.33: '1/1',  # Close to full
        75: '3/4',
        66.666: '2/3',
        66.67: '2/3',
        66.66: '2/3',
        60: '2/3',
        50: '1/2',
        40: '1/3',
        33.333: '1/3',
        33.33: '1/3',
        33.34: '1/3',
        25: '1/4',
        20: '1/4',
        16.66: '1/6',
    }

    def extract_layout(self, soup: BeautifulSoup) -> list:
        """
        Extract layout structure from Elementor HTML.

        Returns:
            List of sections with width and content info:
            [
                {
                    'width': '1/3',
                    'html_content': str,
                    'header': str or None,
                    'text_content': str,
                    'has_testimonials': bool,
                    'has_form': bool,
                    'has_images': bool,
                    'position': int,
                }
            ]
        """
        # Try new container structure first (Elementor 3.6+)
        sections = self._extract_from_new_containers(soup)

        # If no sections found, try classic structure
        if not sections:
            sections = self._extract_from_classic_structure(soup)

        return sections

    def _should_skip_section(self, element) -> bool:
        """
        Check if a section should be skipped (headers, footers, popups, sticky elements).

        Returns True if the section should be excluded from wireframe extraction.
        """
        # Check if inside header, footer, or popup
        wrapper = element.find_parent(attrs={'data-elementor-type': True})
        if wrapper:
            elementor_type = wrapper.get('data-elementor-type', '').lower()
            # Skip header, footer, popup, and template types - only include wp-page/wp-post content
            if elementor_type in ['header', 'footer', 'popup', 'section', 'loop-item']:
                return True

        # Check element's own data-elementor-type attribute
        own_type = element.get('data-elementor-type', '').lower()
        if own_type in ['header', 'footer', 'popup']:
            return True

        # Check if element has elementor-popup-modal class or is inside one
        if element.find_parent(class_=lambda x: x and 'popup' in str(x).lower()):
            return True

        # Check for CSS classes indicating sticky/fixed elements
        classes = ' '.join(element.get('class', []))
        if 'elementor-sticky' in classes or 'e-sticky' in classes:
            return True

        # Check inline style for position: fixed/sticky
        style = element.get('style', '').lower()
        if 'position: fixed' in style or 'position:fixed' in style:
            return True
        if 'position: sticky' in style or 'position:sticky' in style:
            return True

        return False

    def _extract_from_new_containers(self, soup: BeautifulSoup) -> list:
        """
        Extract layout from new Elementor container structure (e-con, 3.6+).
        Uses e-con with e-parent/e-child classes and flex layouts.
        Filters out header, footer, popup, and sticky sections.
        """
        sections = []
        position = 0

        # Find parent containers (top-level e-con with e-parent class)
        # These are in the main content area, not header/footer
        main_content = soup.find('main') or soup.find(id='content') or soup.find(class_='site-main') or soup

        # Find all parent containers
        parent_containers = main_content.find_all(class_=lambda x: x and 'e-con' in str(x) and 'e-parent' in str(x))

        if not parent_containers:
            # Alternative: find containers with data-element_type="container" that have child containers
            parent_containers = main_content.find_all(attrs={'data-element_type': 'container'})
            parent_containers = [p for p in parent_containers if p.find(class_=lambda x: x and 'e-child' in str(x))]

        for parent in parent_containers:
            # Skip header, footer, popup, and sticky sections
            if self._should_skip_section(parent):
                continue
            # Find child containers (columns) within this parent
            children = parent.find_all(class_=lambda x: x and 'e-con' in str(x) and 'e-child' in str(x), recursive=False)

            # If parent has direct e-child containers, process them as columns
            if children:
                # Calculate widths based on number of children (flex layout)
                num_children = len(children)
                for child in children:
                    width = self._get_container_width(child, num_children)
                    section_data = self._extract_section_data(child, width, position)
                    if section_data.get('text_content', '').strip():  # Only add if has content
                        sections.append(section_data)
                        position += 1
            else:
                # Parent container without children - treat as single column section
                width = '1/1'
                section_data = self._extract_section_data(parent, width, position)
                if section_data.get('text_content', '').strip():
                    sections.append(section_data)
                    position += 1

        return sections

    def _extract_from_classic_structure(self, soup: BeautifulSoup) -> list:
        """Extract layout from classic Elementor section/column structure.
        Filters out header, footer, popup, and sticky sections."""
        sections = []
        position = 0

        # Find all Elementor sections (top-level)
        elementor_sections = soup.find_all(class_=lambda x: x and 'elementor-section' in str(x) and 'elementor-inner-section' not in str(x))

        for section in elementor_sections:
            # Skip header, footer, popup, and sticky sections
            if self._should_skip_section(section):
                continue

            # Find columns within this section
            columns = section.find_all(class_=lambda x: x and 'elementor-column' in str(x), recursive=False)

            # If no direct columns, try finding them in section wrap
            if not columns:
                section_wrap = section.find(class_=lambda x: x and 'elementor-container' in str(x))
                if section_wrap:
                    columns = section_wrap.find_all(class_=lambda x: x and 'elementor-column' in str(x), recursive=False)

            # If still no columns, treat entire section as one column
            if not columns:
                columns = [section]

            for column in columns:
                width = self._get_column_width(column)
                section_data = self._extract_section_data(column, width, position)
                if section_data.get('text_content', '').strip():
                    sections.append(section_data)
                    position += 1

        return sections

    def _extract_section_data(self, element, width: str, position: int) -> dict:
        """Extract comprehensive section data from an element including all content."""
        html_content = str(element)
        text_content = element.get_text(separator=' ', strip=True)

        # Find all headers with their tag types
        headers = []
        header = None
        subheader = None
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for header_elem in element.find_all(tag):
                header_text = header_elem.get_text(strip=True)
                if header_text:
                    headers.append({'tag': tag, 'text': header_text})
                    if header is None:
                        header = header_text
                    elif subheader is None and tag in ['h3', 'h4', 'h5', 'h6']:
                        subheader = header_text

        # Extract all paragraphs with full text
        paragraphs = []
        for p in element.find_all('p'):
            p_text = p.get_text(strip=True)
            if p_text and len(p_text) > 10:  # Skip very short paragraphs
                paragraphs.append(p_text)

        # Extract all images with URLs and alt text
        images = []
        for img in element.find_all('img'):
            src = img.get('src', '')
            if src and not src.startswith('data:'):  # Skip data URLs
                images.append({
                    'src': src,
                    'alt': img.get('alt', ''),
                    'width': img.get('width', ''),
                    'height': img.get('height', ''),
                })

        # Extract all buttons and links with text and href
        buttons = []
        for btn in element.find_all(['a', 'button']):
            btn_text = btn.get_text(strip=True)
            if btn_text:
                # Check if it's a button-style link
                classes = ' '.join(btn.get('class', []))
                is_button = 'button' in classes.lower() or btn.name == 'button'
                buttons.append({
                    'text': btn_text,
                    'href': btn.get('href', ''),
                    'is_button': is_button,
                })

        # Extract list items (for USPs, trust badges, features)
        # PRIORITET 1: Elementor icon-list-text (mest præcis)
        list_items = []
        for icon_text in element.find_all(class_='elementor-icon-list-text'):
            text = icon_text.get_text(strip=True)
            if text and text not in list_items:
                list_items.append(text)

        # PRIORITET 2: Standard <li> tags (hvis ikke allerede fundet)
        if not list_items:
            for li in element.find_all('li'):
                li_text = li.get_text(strip=True)
                if li_text and li_text not in list_items:
                    list_items.append(li_text)

        # Check for special content types
        has_testimonials = bool(element.find(class_=lambda x: x and any(
            t in str(x).lower() for t in ['testimonial', 'review', 'trustpilot']
        )))
        has_form = bool(element.find(['form', 'input']) or element.find(class_=lambda x: x and 'form' in str(x).lower()))
        has_images = len(images) > 0

        # NY: Detekter H1 tag (for hero-sektion prioritering)
        has_h1 = bool(element.find('h1'))

        # NY: Detekter carousel/slider
        has_carousel = bool(element.find(class_=lambda x: x and any(
            c in str(x).lower() for c in ['swiper', 'carousel', 'slider', 'e-n-carousel']
        )))

        # NY: Detekter Elementor widgets
        widgets = self._detect_widgets(element)

        return {
            'width': width,
            'html_content': html_content,
            'header': header,
            'subheader': subheader,
            'headers': headers,  # All headers with tags
            'paragraphs': paragraphs,  # Full paragraph texts
            'images': images,  # Image data with URLs
            'buttons': buttons,  # Button/link data
            'list_items': list_items,  # USPs, trust badges, etc.
            'text_content': text_content[:3000],  # Increased limit
            'has_testimonials': has_testimonials,
            'has_form': has_form,
            'has_images': has_images,
            'has_h1': has_h1,  # NY: For hero-detektion
            'has_carousel': has_carousel,  # NY: For carousel-detektion
            'widgets': widgets,  # NY: Detaljeret widget-info
            'position': position,
        }

    def _detect_widgets(self, element) -> list:
        """
        Detekter alle Elementor widgets i en sektion.
        Returnerer liste med widget-type, kategori og ekstraheret indhold.
        """
        widgets = []

        # Find alle elementer med data-widget_type attribut
        for widget_elem in element.find_all(attrs={'data-widget_type': True}):
            widget_type_full = widget_elem.get('data-widget_type', '')
            # Fjern .default suffix (fx 'heading.default' -> 'heading')
            widget_type = widget_type_full.split('.')[0]

            if not widget_type:
                continue

            # Map til generisk kategori
            category = WIDGET_CATEGORY_MAP.get(widget_type, 'generic')

            # Ekstraher widget-specifikt indhold
            widget_content = self._extract_widget_content(widget_elem, widget_type, category)

            widgets.append({
                'type': widget_type,
                'category': category,
                'content': widget_content
            })

        return widgets

    def _extract_widget_content(self, widget_elem, widget_type: str, category: str) -> dict:
        """
        Ekstraher indhold baseret på widget-type.
        Returnerer struktureret data for hvert widget-type.
        """
        content = {}

        if category == 'heading':
            # Find overskrift-tag og tekst
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                header = widget_elem.find(tag)
                if header:
                    content['tag'] = tag
                    content['text'] = header.get_text(strip=True)
                    break

        elif category == 'text':
            # Tekst-editor indhold (paragraffer)
            paragraphs = []
            for p in widget_elem.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            content['paragraphs'] = paragraphs

        elif category == 'list':
            # Icon-list items
            items = []
            for item in widget_elem.find_all(class_='elementor-icon-list-text'):
                text = item.get_text(strip=True)
                if text:
                    items.append(text)
            # Fallback til li tags
            if not items:
                for li in widget_elem.find_all('li'):
                    text = li.get_text(strip=True)
                    if text:
                        items.append(text)
            content['items'] = items

        elif category == 'image':
            # Billede URL og alt tekst
            img = widget_elem.find('img')
            if img:
                content['src'] = img.get('src', '')
                content['alt'] = img.get('alt', '')

        elif category == 'button' or category == 'cta':
            # Button tekst og link
            link = widget_elem.find('a')
            if link:
                content['text'] = link.get_text(strip=True)
                content['href'] = link.get('href', '')

        elif category == 'form':
            # Form felter
            fields = []
            for inp in widget_elem.find_all(['input', 'textarea', 'select']):
                field_type = inp.get('type', inp.name)
                field_name = inp.get('name', '')
                placeholder = inp.get('placeholder', '')
                if field_name or placeholder:
                    fields.append({
                        'type': field_type,
                        'name': field_name,
                        'placeholder': placeholder
                    })
            content['fields'] = fields

        elif category == 'carousel':
            # Carousel items
            items = []
            # Prøv at finde swiper slides
            for slide in widget_elem.find_all(class_=lambda x: x and 'swiper-slide' in str(x)):
                slide_content = {}
                # Overskrift i slide
                for tag in ['h2', 'h3', 'h4', 'h5']:
                    h = slide.find(tag)
                    if h:
                        slide_content['title'] = h.get_text(strip=True)
                        break
                # Tekst i slide
                p = slide.find('p')
                if p:
                    slide_content['text'] = p.get_text(strip=True)
                # Button i slide
                btn = slide.find('a', class_=lambda x: x and 'button' in str(x).lower())
                if btn:
                    slide_content['button'] = btn.get_text(strip=True)
                    slide_content['button_href'] = btn.get('href', '')
                # Billede i slide
                img = slide.find('img')
                if img:
                    slide_content['image'] = img.get('src', '')

                if slide_content:
                    items.append(slide_content)

            # Fallback: e-child containers (nested carousel)
            if not items:
                for child in widget_elem.find_all(class_=lambda x: x and 'e-child' in str(x)):
                    child_content = {}
                    for tag in ['h3', 'h4', 'h5']:
                        h = child.find(tag)
                        if h:
                            child_content['title'] = h.get_text(strip=True)
                            break
                    p = child.find('p')
                    if p:
                        child_content['text'] = p.get_text(strip=True)
                    if child_content:
                        items.append(child_content)

            content['items'] = items

        elif category == 'testimonial':
            # Testimonial indhold
            content['text'] = ''
            content['author'] = ''
            # Prøv forskellige strukturer
            text_elem = widget_elem.find(class_=lambda x: x and 'testimonial-content' in str(x).lower())
            if text_elem:
                content['text'] = text_elem.get_text(strip=True)
            author_elem = widget_elem.find(class_=lambda x: x and 'testimonial-name' in str(x).lower())
            if author_elem:
                content['author'] = author_elem.get_text(strip=True)

        elif category == 'flip_card':
            # Flip box - front og back indhold
            front = widget_elem.find(class_=lambda x: x and 'flip-box-front' in str(x).lower())
            back = widget_elem.find(class_=lambda x: x and 'flip-box-back' in str(x).lower())
            if front:
                content['front_title'] = ''
                content['front_text'] = ''
                h = front.find(['h3', 'h4'])
                if h:
                    content['front_title'] = h.get_text(strip=True)
                p = front.find('p')
                if p:
                    content['front_text'] = p.get_text(strip=True)
            if back:
                content['back_title'] = ''
                content['back_text'] = ''
                h = back.find(['h3', 'h4'])
                if h:
                    content['back_title'] = h.get_text(strip=True)
                p = back.find('p')
                if p:
                    content['back_text'] = p.get_text(strip=True)

        elif category == 'accordion' or category == 'tabs':
            # Accordion/tabs items
            items = []
            # Elementor accordion structure
            for item in widget_elem.find_all(class_=lambda x: x and ('accordion-item' in str(x).lower() or 'tab-title' in str(x).lower())):
                title = item.get_text(strip=True)
                if title:
                    items.append({'title': title})
            content['items'] = items

        elif category == 'card':
            # Icon-box / info card
            content['icon'] = ''
            content['title'] = ''
            content['text'] = ''
            # Prøv at finde indhold
            for tag in ['h3', 'h4', 'h5']:
                h = widget_elem.find(tag)
                if h:
                    content['title'] = h.get_text(strip=True)
                    break
            p = widget_elem.find('p')
            if p:
                content['text'] = p.get_text(strip=True)
            # Icon (ofte en i-tag eller svg)
            icon = widget_elem.find('i') or widget_elem.find('svg')
            if icon:
                icon_class = ' '.join(icon.get('class', []))
                content['icon'] = icon_class

        # Map category to _inferred_type for UI display
        category_to_inferred = {
            'heading': 'text_with_title',
            'text': 'text_long',
            'list': 'list',
            'image': 'image',
            'button': 'text_short',
            'cta': 'text_with_title',
            'form': 'form',
            'carousel': 'gallery',
            'testimonial': 'text_with_title',
            'flip_card': 'mixed',
            'accordion': 'accordion',
            'tabs': 'accordion',
            'card': 'text_with_title',
            'gallery': 'gallery',
            'video': 'mixed',
            'logo_slider': 'gallery',
            'divider': 'empty',
            'spacer': 'empty',
        }
        content['_inferred_type'] = category_to_inferred.get(category, 'text_long')

        return content

    def _get_container_width(self, container, num_siblings: int = 1) -> str:
        """
        Get width from new container structure.
        Checks CSS custom properties, data-settings, and flex basis.
        """
        # Method 1: Check for --container-widget-width or --width in data-settings
        data_settings = container.get('data-settings', '{}')
        try:
            settings = json.loads(data_settings)
            # Check for flex_size settings
            if 'flex_size' in settings:
                return self._normalize_width(float(settings['flex_size']))
            if 'content_width' in settings:
                width_val = settings['content_width'].get('size', 100)
                return self._normalize_width(float(width_val))
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass

        # Method 2: Check inline style for width or flex-basis
        style = container.get('style', '')
        flex_match = re.search(r'flex-basis:\s*([\d.]+)%', style)
        if flex_match:
            return self._normalize_width(float(flex_match.group(1)))

        width_match = re.search(r'(?<!max-)width:\s*([\d.]+)%', style)
        if width_match:
            return self._normalize_width(float(width_match.group(1)))

        # Method 3: Check CSS custom property in style
        css_var_match = re.search(r'--container-widget-width:\s*([\d.]+)%', style)
        if css_var_match:
            return self._normalize_width(float(css_var_match.group(1)))

        # Method 4: Infer from number of siblings (common flex patterns)
        if num_siblings > 1:
            # Common patterns: 2 columns = 1/2, 3 columns = 1/3, 4 columns = 1/4
            width_map = {2: '1/2', 3: '1/3', 4: '1/4', 5: '1/4', 6: '1/6'}
            return width_map.get(num_siblings, '1/1')

        # Default
        return '1/1'

    def _get_column_width(self, column_element) -> str:
        """
        Extract column width from Elementor column.
        Checks data-settings, inline styles, and CSS classes.
        """
        # Method 1: Check data-settings JSON
        data_settings = column_element.get('data-settings')
        if data_settings:
            try:
                settings = json.loads(data_settings)
                if '_column_size' in settings:
                    return self._normalize_width(float(settings['_column_size']))
            except (json.JSONDecodeError, ValueError):
                pass

        # Method 2: Check CSS classes for width patterns
        classes = column_element.get('class', [])
        if isinstance(classes, list):
            classes = ' '.join(classes)

        # Elementor uses classes like "elementor-col-33"
        width_match = re.search(r'elementor-col-(\d+)', classes)
        if width_match:
            return self._normalize_width(float(width_match.group(1)))

        # Method 3: Check inline style
        style = column_element.get('style', '')
        width_style = re.search(r'width:\s*([\d.]+)%', style)
        if width_style:
            return self._normalize_width(float(width_style.group(1)))

        # Default to full width
        return '1/1'

    def _normalize_width(self, width_percent: float) -> str:
        """Convert percentage width to fraction string."""
        # Find closest match in WIDTH_MAP
        closest_key = min(self.WIDTH_MAP.keys(), key=lambda x: abs(x - width_percent))
        if abs(closest_key - width_percent) < 5:  # Within 5% tolerance
            return self.WIDTH_MAP[closest_key]

        # If no close match, calculate based on 12-column grid
        cols = round(width_percent / 100 * 12)
        cols = max(1, min(12, cols))  # Clamp to 1-12

        fraction_map = {
            12: '1/1', 11: '1/1', 10: '1/1',
            9: '3/4', 8: '2/3', 7: '2/3',
            6: '1/2', 5: '1/2',
            4: '1/3', 3: '1/4', 2: '1/6', 1: '1/6'
        }
        return fraction_map.get(cols, '1/1')


class DiviLayoutExtractor:
    """
    Extract layout structure from Divi-built pages.
    Parses .et_pb_section, .et_pb_row, .et_pb_column classes.
    """

    # Divi uses class-based column widths
    DIVI_WIDTH_CLASSES = {
        'et_pb_column_4_4': '1/1',
        'et_pb_column_3_4': '3/4',
        'et_pb_column_2_3': '2/3',
        'et_pb_column_1_2': '1/2',
        'et_pb_column_1_3': '1/3',
        'et_pb_column_1_4': '1/4',
        'et_pb_column_1_5': '1/4',
        'et_pb_column_1_6': '1/6',
        'et_pb_column_2_5': '1/3',
        'et_pb_column_3_5': '1/2',
    }

    def extract_layout(self, soup: BeautifulSoup) -> list:
        """Extract layout from Divi HTML structure."""
        sections = []
        position = 0

        # Find all Divi sections
        divi_sections = soup.find_all(class_=lambda x: x and 'et_pb_section' in str(x))

        for section in divi_sections:
            # Find rows within this section
            rows = section.find_all(class_=lambda x: x and 'et_pb_row' in str(x), recursive=False)

            for row in rows:
                # Find columns
                columns = row.find_all(class_=lambda x: x and 'et_pb_column' in str(x), recursive=False)

                for column in columns:
                    width = self._get_column_width(column)
                    text_content = column.get_text(separator=' ', strip=True)

                    # Find header
                    header = None
                    for tag in ['h1', 'h2', 'h3', 'h4']:
                        header_elem = column.find(tag)
                        if header_elem:
                            header = header_elem.get_text(strip=True)
                            break

                    # Check for special content
                    has_testimonials = bool(column.find(class_=lambda x: x and 'testimonial' in str(x).lower()))
                    has_form = bool(column.find(['form', 'input']) or column.find(class_=lambda x: x and 'form' in str(x).lower()))
                    has_images = bool(column.find('img'))

                    sections.append({
                        'width': width,
                        'html_content': str(column),
                        'header': header,
                        'text_content': text_content[:2000],
                        'has_testimonials': has_testimonials,
                        'has_form': has_form,
                        'has_images': has_images,
                        'position': position,
                    })
                    position += 1

        return sections

    def _get_column_width(self, column_element) -> str:
        """Extract width from Divi column classes."""
        classes = column_element.get('class', [])
        if isinstance(classes, list):
            classes = ' '.join(classes)

        for divi_class, width in self.DIVI_WIDTH_CLASSES.items():
            if divi_class in classes:
                return width

        return '1/1'


class WPBakeryLayoutExtractor:
    """
    Extract layout structure from WPBakery (Visual Composer) pages.
    Parses .vc_row, .vc_column with vc_col-sm-* classes for widths.
    """

    # WPBakery uses Bootstrap-like 12-column grid
    VC_WIDTH_CLASSES = {
        'vc_col-sm-12': '1/1',
        'vc_col-sm-10': '1/1',
        'vc_col-sm-9': '3/4',
        'vc_col-sm-8': '2/3',
        'vc_col-sm-7': '2/3',
        'vc_col-sm-6': '1/2',
        'vc_col-sm-5': '1/2',
        'vc_col-sm-4': '1/3',
        'vc_col-sm-3': '1/4',
        'vc_col-sm-2': '1/6',
        'vc_col-sm-1': '1/6',
    }

    def extract_layout(self, soup: BeautifulSoup) -> list:
        """Extract layout from WPBakery HTML structure."""
        sections = []
        position = 0

        # Find all WPBakery rows
        vc_rows = soup.find_all(class_=lambda x: x and 'vc_row' in str(x))

        for row in vc_rows:
            # Find columns
            columns = row.find_all(class_=lambda x: x and 'vc_column' in str(x) or 'vc_col-' in str(x), recursive=False)

            for column in columns:
                width = self._get_column_width(column)
                text_content = column.get_text(separator=' ', strip=True)

                # Find header
                header = None
                for tag in ['h1', 'h2', 'h3', 'h4']:
                    header_elem = column.find(tag)
                    if header_elem:
                        header = header_elem.get_text(strip=True)
                        break

                # Check for special content
                has_testimonials = bool(column.find(class_=lambda x: x and 'testimonial' in str(x).lower()))
                has_form = bool(column.find(['form', 'input']) or column.find(class_=lambda x: x and 'form' in str(x).lower()))
                has_images = bool(column.find('img'))

                sections.append({
                    'width': width,
                    'html_content': str(column),
                    'header': header,
                    'text_content': text_content[:2000],
                    'has_testimonials': has_testimonials,
                    'has_form': has_form,
                    'has_images': has_images,
                    'position': position,
                })
                position += 1

        return sections

    def _get_column_width(self, column_element) -> str:
        """Extract width from WPBakery column classes."""
        classes = column_element.get('class', [])
        if isinstance(classes, list):
            classes = ' '.join(classes)

        for vc_class, width in self.VC_WIDTH_CLASSES.items():
            if vc_class in classes:
                return width

        return '1/1'


class GenericLayoutExtractor:
    """
    Extract layout from generic HTML/CSS when no specific builder detected.
    Looks for common grid patterns, flexbox containers, and Bootstrap classes.
    """

    # Common CSS grid/flex patterns
    BOOTSTRAP_WIDTHS = {
        'col-12': '1/1', 'col-lg-12': '1/1', 'col-md-12': '1/1', 'col-sm-12': '1/1',
        'col-10': '1/1', 'col-lg-10': '1/1', 'col-md-10': '1/1',
        'col-9': '3/4', 'col-lg-9': '3/4', 'col-md-9': '3/4',
        'col-8': '2/3', 'col-lg-8': '2/3', 'col-md-8': '2/3',
        'col-7': '2/3', 'col-lg-7': '2/3', 'col-md-7': '2/3',
        'col-6': '1/2', 'col-lg-6': '1/2', 'col-md-6': '1/2',
        'col-5': '1/2', 'col-lg-5': '1/2', 'col-md-5': '1/2',
        'col-4': '1/3', 'col-lg-4': '1/3', 'col-md-4': '1/3',
        'col-3': '1/4', 'col-lg-3': '1/4', 'col-md-3': '1/4',
        'col-2': '1/6', 'col-lg-2': '1/6', 'col-md-2': '1/6',
    }

    TAILWIND_WIDTHS = {
        'w-full': '1/1',
        'w-1/2': '1/2',
        'w-1/3': '1/3',
        'w-2/3': '2/3',
        'w-1/4': '1/4',
        'w-3/4': '3/4',
    }

    def extract_layout(self, soup: BeautifulSoup) -> list:
        """
        Attempt to extract layout from generic HTML.
        Falls back to treating each section as full-width.
        """
        sections = []
        position = 0

        # Try Bootstrap grid
        rows = soup.find_all(class_=lambda x: x and 'row' in str(x).split())

        for row in rows:
            # Find columns
            columns = row.find_all(class_=lambda x: x and any(c in str(x) for c in ['col-', 'col ']), recursive=False)

            for column in columns:
                width = self._get_column_width(column)
                text_content = column.get_text(separator=' ', strip=True)

                if not text_content.strip():
                    continue

                # Find header
                header = None
                for tag in ['h1', 'h2', 'h3', 'h4']:
                    header_elem = column.find(tag)
                    if header_elem:
                        header = header_elem.get_text(strip=True)
                        break

                # Check for special content
                has_testimonials = bool(column.find(class_=lambda x: x and any(
                    t in str(x).lower() for t in ['testimonial', 'review']
                )))
                has_form = bool(column.find(['form', 'input']))
                has_images = bool(column.find('img'))

                sections.append({
                    'width': width,
                    'html_content': str(column),
                    'header': header,
                    'text_content': text_content[:2000],
                    'has_testimonials': has_testimonials,
                    'has_form': has_form,
                    'has_images': has_images,
                    'position': position,
                })
                position += 1

        return sections

    def _get_column_width(self, column_element) -> str:
        """Extract width from generic CSS classes."""
        classes = column_element.get('class', [])
        if isinstance(classes, list):
            classes = ' '.join(classes)

        # Check Bootstrap
        for bs_class, width in self.BOOTSTRAP_WIDTHS.items():
            if bs_class in classes:
                return width

        # Check Tailwind
        for tw_class, width in self.TAILWIND_WIDTHS.items():
            if tw_class in classes:
                return width

        return '1/1'


class ContentTypeClassifier:
    """
    Classify section content into block types.
    Uses pattern matching for heuristic classification.
    """

    # Content type indicators (heuristic-based)
    TYPE_PATTERNS = {
        'hero': {
            'header_patterns': [
                r'din\s+lokale', r'velkommen\s+til', r'vi\s+er\s+din',
                r'din\s+(?:el-?installatør|elektriker|vvs|maler|tømrer|håndværker)',
                r'professionel\s+(?:el-?installatør|elektriker|vvs|maler|tømrer|håndværker)'
            ],
            'content_patterns': [
                r'\d+\s*års?\s*erfaring', r'autoriseret', r'garanti',
                r'gratis\s+tilbud', r'ring\s+til\s+os', r'kontakt\s+os\s+i\s+dag'
            ],
        },
        'reviews': {
            'header_patterns': [
                r'anmeldelse', r'hvad\s+siger', r'kunder?\s+siger', r'testimonial',
                r'trustpilot', r'google\s+anmeldelse', r'kundeanmeldelse',
                r'stjerne', r'bedømmelse'
            ],
            'content_patterns': [
                r'\d\s*stjerner?', r'\d+/\d+', r'★', r'⭐',
                r'"[^"]{20,}"', r'«[^»]{20,}»'  # Quoted text
            ],
        },
        'contact_form': {
            'header_patterns': [
                r'kontakt', r'skriv\s+til', r'send\s+besked', r'få\s+tilbud',
                r'kontakt\s*(?:os|mig)', r'book\s+(?:tid|møde)', r'gratis\s+tilbud'
            ],
            'content_patterns': [
                r'udfyld', r'formular', r'email|e-mail', r'telefon', r'besked'
            ],
        },
        'usp_header': {
            'header_patterns': [
                r'^(?:vi\s+)?(?:tilbyder|leverer|sikrer)', r'hvorfor\s+vælge',
                r'fordele', r'vores\s+(?:fordele|styrker)', r'det\s+får\s+du',
                r'hvad\s+(?:kan|gør|tilbyder)\s+(?:vi|vores)'
            ],
            'content_patterns': [
                r'✓|✔|•|\*', r'\d+\s*års?\s*erfaring', r'garanti',
                r'gratis', r'hurtig', r'professionel'
            ],
        },
        'cta': {
            'header_patterns': [
                r'kom\s+i\s+gang', r'bestil', r'book\s+nu', r'ring\s+(?:nu|i\s+dag)',
                r'gratis\s+(?:tilbud|konsultation)', r'klar\s+til'
            ],
            'content_patterns': [
                r'(?:ring|kontakt)\s+(?:nu|i\s+dag)', r'\d{2}\s*\d{2}\s*\d{2}\s*\d{2}'  # Phone number
            ],
        },
    }

    def classify(self, header: str, content: str, has_testimonials: bool = False,
                 has_form: bool = False, has_images: bool = False,
                 has_h1: bool = False, has_carousel: bool = False,
                 widgets: list = None, list_items: list = None) -> dict:
        """
        Classify a section's content type.

        Args:
            header: Section header text
            content: Section content text
            has_testimonials: Whether testimonial elements were detected
            has_form: Whether form elements were detected
            has_images: Whether images were detected
            has_h1: Whether H1 tag was detected (prioritizes hero)
            has_carousel: Whether carousel/slider was detected
            widgets: List of detected Elementor widgets
            list_items: List of extracted list items (from icon-list or li tags)

        Returns:
            {
                'type': str,  # 'hero', 'carousel', 'usp_header', 'text', 'reviews', 'contact_form', 'cta', 'image'
                'confidence': float,
                'matched_patterns': list,
            }
        """
        # Check if we have actual list items (for USP sections)
        has_list_items = bool(list_items and len(list_items) > 0)

        # Check if widgets include a list type
        has_list_widget = False
        if widgets:
            has_list_widget = any(w.get('category') == 'list' for w in widgets)

        # PRIORITET 1: H1 tag = Hero sektion (uanset andre elementer som form)
        if has_h1:
            return {
                'type': 'hero',
                'confidence': 1.0,
                'matched_patterns': ['element:h1']
            }

        # PRIORITET 2: Carousel detektion
        if has_carousel:
            return {
                'type': 'carousel',
                'confidence': 0.9,
                'matched_patterns': ['element:carousel']
            }

        # PRIORITET 3: Widget-baseret klassificering
        if widgets:
            # Tæl widget-kategorier for at bestemme sektion-type
            category_counts = {}
            for widget in widgets:
                cat = widget.get('category', 'generic')
                category_counts[cat] = category_counts.get(cat, 0) + 1

            # Carousel widgets (nested-carousel, testimonial-carousel, etc.)
            if category_counts.get('carousel', 0) > 0:
                return {
                    'type': 'carousel',
                    'confidence': 0.9,
                    'matched_patterns': ['widget:carousel']
                }

            # Testimonial widgets
            if category_counts.get('testimonial', 0) > 0:
                return {
                    'type': 'reviews',
                    'confidence': 0.9,
                    'matched_patterns': ['widget:testimonial']
                }

            # Accordion/tabs
            if category_counts.get('accordion', 0) > 0:
                return {
                    'type': 'accordion',
                    'confidence': 0.9,
                    'matched_patterns': ['widget:accordion']
                }

            if category_counts.get('tabs', 0) > 0:
                return {
                    'type': 'tabs',
                    'confidence': 0.9,
                    'matched_patterns': ['widget:tabs']
                }

            # Flip cards
            if category_counts.get('flip_card', 0) > 0:
                return {
                    'type': 'flip_cards',
                    'confidence': 0.9,
                    'matched_patterns': ['widget:flip_card']
                }

        header_lower = (header or '').lower()
        content_lower = (content or '').lower()[:1000]  # Limit for matching

        scores = {}
        matched = {}

        # Check each type
        for content_type, patterns in self.TYPE_PATTERNS.items():
            score = 0
            type_matched = []

            # Check header patterns
            for pattern in patterns.get('header_patterns', []):
                if re.search(pattern, header_lower, re.IGNORECASE):
                    score += 3
                    type_matched.append(f"header:{pattern}")

            # Check content patterns
            for pattern in patterns.get('content_patterns', []):
                if re.search(pattern, content_lower, re.IGNORECASE):
                    score += 1
                    type_matched.append(f"content:{pattern}")

            scores[content_type] = score
            matched[content_type] = type_matched

        # Boost based on detected elements
        if has_testimonials:
            scores['reviews'] = scores.get('reviews', 0) + 5
            matched.setdefault('reviews', []).append('element:testimonial')

        if has_form:
            scores['contact_form'] = scores.get('contact_form', 0) + 5
            matched.setdefault('contact_form', []).append('element:form')

        # Find best match
        best_type = 'text'  # Default
        best_score = 0

        for content_type, score in scores.items():
            # VIGTIG: usp_header kræver faktiske list_items eller list widget
            # Ellers falder den tilbage til 'text'
            if content_type == 'usp_header' and not has_list_items and not has_list_widget:
                continue  # Skip usp_header hvis ingen list items

            if score > best_score:
                best_score = score
                best_type = content_type

        # Confidence based on score
        confidence = min(best_score / 10.0, 1.0)

        # If only images and low text, mark as image
        if has_images and len(content_lower) < 50 and best_score < 2:
            best_type = 'image'
            confidence = 0.7

        return {
            'type': best_type,
            'confidence': confidence,
            'matched_patterns': matched.get(best_type, [])
        }

    def classify_batch(self, sections: list) -> list:
        """Classify multiple sections."""
        results = []
        for section in sections:
            classification = self.classify(
                header=section.get('header', ''),
                content=section.get('text_content', ''),
                has_testimonials=section.get('has_testimonials', False),
                has_form=section.get('has_form', False),
                has_images=section.get('has_images', False),
                has_h1=section.get('has_h1', False),
                has_carousel=section.get('has_carousel', False),
                widgets=section.get('widgets', []),
                list_items=section.get('list_items', [])
            )
            results.append({
                **section,
                'content_type': classification['type'],
                'type_confidence': classification['confidence'],
                'matched_patterns': classification['matched_patterns']
            })
        return results


class SectionClassifier:
    """
    AI-powered section classifier that identifies section types and extracts
    structured values (stats, USPs, etc.) from website sections.

    Section types supported:
    - hero: Main headline/header section
    - stats: Statistics/numbers (+1200 customers, 5 stars, etc.)
    - services: List of services/offerings
    - about: About the company text
    - testimonials: Customer reviews/testimonials
    - team: Team members
    - process: Work process/steps
    - cta: Call to action
    - faq: Frequently asked questions
    - contact: Contact information
    - gallery: Image gallery
    - pricing: Pricing tables
    - features: Features/benefits list
    - partners: Partner/client logos
    - blog: Blog/news section
    - other: Unclassified
    """

    SECTION_TYPES = [
        'hero', 'stats', 'services', 'about', 'testimonials', 'team',
        'process', 'cta', 'faq', 'contact', 'gallery', 'pricing',
        'features', 'partners', 'blog', 'other'
    ]

    def __init__(self):
        from django.conf import settings
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.openai_client = None
        if self.openai_api_key:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=self.openai_api_key)

    def _get_prompt_from_db(self, prompt_type):
        """Get prompt template from database."""
        from .models import AIPromptTemplate

        try:
            template = AIPromptTemplate.objects.filter(
                prompt_type=prompt_type,
                is_active=True
            ).first()

            if template:
                return template.get_prompt_text(), template.model_settings
            return None, {}
        except Exception as e:
            print(f"[SectionClassifier] Error loading prompt: {e}")
            return None, {}

    def classify_sections(self, sections: list, page_url: str = '') -> list:
        """
        Classify multiple sections using AI.

        Args:
            sections: List of section dicts with 'header' and 'content' keys
            page_url: Optional URL for context

        Returns:
            List of classified section dicts with added:
                - section_type: str
                - ai_confidence: float (0-1)
                - extracted_values: dict (stats, etc.)
        """
        if not sections:
            return []

        if not self.openai_client:
            print("[SectionClassifier] OpenAI client not available - using heuristic classification")
            return self._classify_heuristic(sections)

        # Build sections text for AI
        sections_text = self._build_sections_text(sections)

        # Get prompt from database or use default
        db_prompt, model_settings = self._get_prompt_from_db('classify_sections')

        if not db_prompt:
            # Use hardcoded default prompt
            prompt = self._get_default_prompt(sections_text, page_url)
        else:
            prompt = db_prompt.format(sections_text=sections_text, page_url=page_url)

        model = model_settings.get('model') or 'gpt-4o-mini'
        temperature = model_settings.get('temperature', 0.2)
        max_tokens = model_settings.get('max_tokens', 4000)

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": """Du er en ekspert i at analysere website-indhold og klassificere sektioner.
Du identificerer sektionstyper og ekstraherer strukturerede værdier.
Svar KUN med valid JSON."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=120.0  # 120 sekunder timeout for store websites
            )

            result_text = response.choices[0].message.content.strip()

            # Clean up JSON if wrapped in markdown code blocks
            if result_text.startswith('```'):
                result_text = re.sub(r'^```(?:json)?\s*', '', result_text)
                result_text = re.sub(r'\s*```$', '', result_text)

            ai_result = json.loads(result_text)
            classified = ai_result.get('sections', [])

            # Merge AI results with original sections
            return self._merge_classifications(sections, classified)

        except json.JSONDecodeError as e:
            print(f"[SectionClassifier] JSON parse error: {e}")
            return self._classify_heuristic(sections)
        except Exception as e:
            print(f"[SectionClassifier] AI classification error: {e}")
            return self._classify_heuristic(sections)

    def _build_sections_text(self, sections: list) -> str:
        """Build formatted text for AI analysis."""
        text_parts = []
        for i, section in enumerate(sections):
            header = section.get('header', '').strip()
            content = section.get('content', '').strip()[:800]  # Limit per section
            text_parts.append(f"[SEKTION {i}]\nOverskrift: {header}\nIndhold: {content}\n")
        return '\n'.join(text_parts)

    def _get_default_prompt(self, sections_text: str, page_url: str) -> str:
        """Return default classification prompt."""
        return f"""Analysér følgende sektioner fra en hjemmeside og klassificér hver sektion.

URL: {page_url}

SEKTIONER:
{sections_text}

For HVER sektion, identificér:
1. section_type: En af følgende typer:
   - hero: Hovedoverskrift/header sektion med primært budskab
   - stats: Statistikker/tal (fx "+1200 kunder", "5 stjerner", "20 års erfaring")
   - services: Liste af ydelser/services
   - about: Om virksomheden tekst
   - testimonials: Kundeanmeldelser/udtalelser
   - team: Teammedlemmer
   - process: Arbejdsproces/steps
   - cta: Call to action (kontakt os, få tilbud)
   - faq: Ofte stillede spørgsmål
   - contact: Kontaktinformation
   - gallery: Billede galleri
   - pricing: Priser/prisliste
   - features: Features/fordele liste
   - partners: Partnere/kunde logoer
   - blog: Blog/nyheder
   - other: Andet/uklassificeret

2. confidence: Tal fra 0.0 til 1.0 der angiver sikkerhed

3. extracted_values: For stats-sektioner, ekstraher strukturerede værdier:
   - Tal med labels (fx {{"number": "+1200", "label": "loyale kunder"}})
   - Ratings (fx {{"rating": "5", "platform": "Trustpilot"}})
   - Års erfaring (fx {{"years": "20", "type": "erfaring"}})

Svar i dette JSON format:
{{
    "sections": [
        {{
            "index": 0,
            "section_type": "hero",
            "confidence": 0.95,
            "extracted_values": {{}}
        }},
        {{
            "index": 1,
            "section_type": "stats",
            "confidence": 0.9,
            "extracted_values": {{
                "stats": [
                    {{"number": "+1200", "label": "loyale kunder"}},
                    {{"number": "5", "label": "stjerner på Trustpilot"}},
                    {{"number": "+50", "label": "dygtige fagfolk"}}
                ]
            }}
        }}
    ]
}}"""

    def _merge_classifications(self, original_sections: list, ai_classifications: list) -> list:
        """Merge AI classifications back into original sections."""
        # Build index lookup for AI results
        ai_by_index = {c.get('index', i): c for i, c in enumerate(ai_classifications)}

        result = []
        for i, section in enumerate(original_sections):
            ai_data = ai_by_index.get(i, {})
            classified = {
                **section,
                'section_type': ai_data.get('section_type', 'other'),
                'ai_confidence': ai_data.get('confidence', 0.0),
                'extracted_values': ai_data.get('extracted_values', {})
            }
            result.append(classified)

        return result

    def _classify_heuristic(self, sections: list) -> list:
        """Fallback heuristic classification when AI is not available."""
        classifier = ContentTypeClassifier()
        result = []

        for section in sections:
            header = section.get('header', '')
            content = section.get('content', '')

            # Use existing ContentTypeClassifier
            classification = classifier.classify(
                header=header,
                content=content,
                has_h1=section.get('has_h1', False),
                has_testimonials=section.get('has_testimonials', False),
                has_form=section.get('has_form', False)
            )

            # Map ContentTypeClassifier types to SectionClassifier types
            type_mapping = {
                'hero': 'hero',
                'reviews': 'testimonials',
                'contact_form': 'contact',
                'usp_header': 'features',
                'cta': 'cta',
                'text': 'other',
                'image': 'gallery',
                'carousel': 'testimonials',
            }

            section_type = type_mapping.get(classification['type'], 'other')

            # Try to detect stats heuristically
            stats_patterns = [
                r'\+?\d+\s*(?:år|års|years?)',
                r'\+?\d+\s*(?:kunder?|customers?)',
                r'\d+[,.]?\d*\s*(?:stjerner?|stars?)',
                r'\+?\d+\s*(?:projekter?|projects?)',
                r'\d+/\d+\s*(?:rating|anmeldelse)',
            ]

            combined_text = f"{header} {content}".lower()
            stats_matches = sum(1 for p in stats_patterns if re.search(p, combined_text, re.IGNORECASE))
            if stats_matches >= 2:
                section_type = 'stats'

            classified = {
                **section,
                'section_type': section_type,
                'ai_confidence': classification['confidence'],
                'extracted_values': {}
            }
            result.append(classified)

        return result

    def save_classifications(self, client_id: int, page_url: str, classified_sections: list):
        """
        Save classified sections to database.

        Args:
            client_id: Client ID to link sections to
            page_url: URL of the page
            classified_sections: List of classified section dicts
        """
        from .models import ClassifiedSection
        from campaigns.models import Client
        from urllib.parse import urlparse

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            print(f"[SectionClassifier] Client {client_id} not found")
            return []

        path = urlparse(page_url).path or '/'
        saved = []

        for i, section in enumerate(classified_sections):
            classified = ClassifiedSection.objects.create(
                client=client,
                page_url=page_url,
                page_path=path,
                section_type=section.get('section_type', 'other'),
                section_index=i,
                ai_confidence=section.get('ai_confidence', 0.0),
                original_header=section.get('header', '')[:500],
                original_content=section.get('content', ''),
                extracted_values=section.get('extracted_values', {})
            )
            saved.append(classified)

        print(f"[SectionClassifier] Saved {len(saved)} classified sections for {page_url}")
        return saved


class FlatSectionsConverter:
    """
    Convert extracted layout and content into flatSections structure.
    Matches the JavaScript structure used in campaign_builder_wizard.html.
    """

    def __init__(self):
        self.content_classifier = ContentTypeClassifier()

    def convert(self, layout_sections: list, reviews: list = None) -> list:
        """
        Convert extracted data to flatSections format.

        Args:
            layout_sections: From layout extractors (with width info)
            reviews: Optional extracted reviews to inject

        Returns:
            flatSections structure matching JavaScript format
        """
        import time
        import random
        import string

        flat_sections = []
        reviews_injected = False

        # Classify content types for all sections
        classified_sections = self.content_classifier.classify_batch(layout_sections)

        for i, section in enumerate(classified_sections):
            section_id = self._generate_section_id()
            content_type = section.get('content_type', 'text')

            # Create content block with full section data
            block = self._create_content_block(
                content_type=content_type,
                section_data=section,  # Pass full section data
                reviews=reviews if content_type == 'reviews' and reviews else None
            )

            # Track if we injected reviews
            if content_type == 'reviews' and reviews:
                reviews_injected = True

            flat_sections.append({
                'id': section_id,
                'width': section.get('width', '1/1'),
                'position': section.get('position', i),  # Bevar position for korrekt rækkefølge
                'contents': [block]
            })

        # If reviews weren't placed but we have them, add as separate section
        if reviews and not reviews_injected:
            review_block = self._create_content_block(
                content_type='reviews',
                section_data={'header': 'Hvad siger vores kunder'},
                reviews=reviews
            )
            flat_sections.append({
                'id': self._generate_section_id(),
                'width': '1/1',
                'position': len(flat_sections),  # Placer reviews til sidst
                'contents': [review_block]
            })

        # Sortér efter original DOM position for korrekt rækkefølge
        flat_sections.sort(key=lambda x: x.get('position', 0))
        return flat_sections

    def _generate_section_id(self) -> str:
        """Generate unique section ID: sec_<timestamp>_<random>"""
        import time
        import random
        import string
        timestamp = int(time.time() * 1000)
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
        return f"sec_{timestamp}_{random_str}"

    def _generate_block_id(self) -> str:
        """Generate unique block ID: block_<timestamp>_<random>"""
        import time
        import random
        import string
        timestamp = int(time.time() * 1000)
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
        return f"block_{timestamp}_{random_str}"

    def _map_content_type_to_inferred(self, content_type: str) -> str:
        """
        Map FlatSectionsConverter content types to UI _inferred_type.

        UI'ens INFERRED_DISPLAY_MAP understøtter:
        - 'form', 'accordion', 'gallery', 'image', 'list', 'link_list'
        - 'text_with_title', 'text_long', 'text_short', 'mixed', 'empty'
        """
        mapping = {
            'usp_header': 'list',           # USPs vises som liste
            'hero': 'text_with_title',      # Hero har titel + tekst
            'text': 'text_long',            # Tekst sektioner
            'reviews': 'text_with_title',   # Reviews som tekst (ingen testimonial i map)
            'contact_form': 'form',         # Kontaktformular
            'cta': 'text_with_title',       # CTA som tekst (ingen button i map)
            'image': 'image',               # Billeder
            'carousel': 'gallery',          # Karrusel som galleri
            'accordion': 'accordion',       # Accordion
            'gallery': 'gallery',           # Galleri
        }
        return mapping.get(content_type, 'text_long')  # Default til tekst

    def _create_content_block(self, content_type: str, section_data: dict, reviews: list = None) -> dict:
        """
        Create a content block with type-specific properties preserving full content.

        Args:
            content_type: The classified content type (usp_header, text, reviews, etc.)
            section_data: Full section data including paragraphs, images, buttons, list_items
            reviews: Optional reviews data for review sections

        Returns block matching createNewSection() in JavaScript with full content preserved.
        """
        header = section_data.get('header', '')
        subheader = section_data.get('subheader', '')
        paragraphs = section_data.get('paragraphs', [])
        images = section_data.get('images', [])
        buttons = section_data.get('buttons', [])
        list_items = section_data.get('list_items', [])
        text_content = section_data.get('text_content', '')

        block = {
            'id': self._generate_block_id(),
            'type': content_type,
            '_inferred_type': self._map_content_type_to_inferred(content_type),
        }

        if content_type == 'usp_header':
            # Use list_items for USPs if available, otherwise extract from content
            usps = list_items[:6] if list_items else self._extract_usps_from_content(text_content)
            intro_text = paragraphs[0] if paragraphs else ''
            block.update({
                'headline': header or 'Vores fordele',
                'subheadline': subheader or '',
                'intro': intro_text,
                'usps': usps[:6] if usps else ['Professionel service', 'Konkurrencedygtige priser', 'Hurtig levering', 'Garanti på arbejdet'],
                'paragraphs': paragraphs,
                'images': images,
                'buttons': buttons,
            })

        elif content_type == 'text':
            # Preserve full paragraph content
            full_content = '\n\n'.join(paragraphs) if paragraphs else text_content
            block.update({
                'header': header or '',
                'subheader': subheader or '',
                'content': full_content,
                'paragraphs': paragraphs,
                'images': images,
                'buttons': buttons,
                'list_items': list_items,
            })

        elif content_type == 'reviews':
            block.update({
                'header': header or 'Hvad siger vores kunder',
                'subheader': subheader or '',
                'reviews': reviews if reviews else [
                    {'author': '', 'rating': 5, 'text': '', 'platform': 'Trustpilot'}
                ],
                'paragraphs': paragraphs,
            })

        elif content_type == 'contact_form':
            # Extract button text from buttons if available
            form_button = next((b['text'] for b in buttons if b.get('is_button')), 'Send besked')
            intro_text = paragraphs[0] if paragraphs else ''
            block.update({
                'header': header or 'Kontakt os',
                'subheader': subheader or intro_text or 'Udfyld formularen og vi vender tilbage inden for 24 timer',
                'intro': intro_text,
                'fields': ['name', 'email', 'phone', 'message'],
                'button_text': form_button,
                'list_items': list_items,  # Trust badges etc.
                'images': images,
            })

        elif content_type == 'cta':
            # Extract button text and href from buttons
            cta_button = buttons[0] if buttons else {}
            block.update({
                'headline': header or 'Klar til at komme i gang?',
                'subheadline': subheader or paragraphs[0] if paragraphs else 'Få et uforpligtende tilbud i dag',
                'button_text': cta_button.get('text', 'Få gratis tilbud'),
                'button_href': cta_button.get('href', ''),
                'button_style': 'primary',
                'paragraphs': paragraphs,
            })

        elif content_type == 'hero':
            # Hero section - preserve all content including trust badges
            usps = list_items[:6] if list_items else self._extract_usps_from_content(text_content)
            intro_text = paragraphs[0] if paragraphs else ''
            cta_button = next((b for b in buttons if b.get('is_button')), buttons[0] if buttons else {})
            block.update({
                'type': 'usp_header',  # Map to usp_header for JS rendering
                'headline': header or 'Velkommen',
                'subheadline': subheader or '',
                'intro': intro_text,
                'usps': usps[:6] if usps else ['Professionel service', 'Hurtig responstid', 'Konkurrencedygtige priser', 'Garanti på arbejdet'],
                'paragraphs': paragraphs,
                'images': images,
                'buttons': buttons,
                'button_text': cta_button.get('text', ''),
                'button_href': cta_button.get('href', ''),
                'is_hero': True,
            })

        elif content_type == 'image':
            # Use first image if available
            first_image = images[0] if images else {}
            block.update({
                'layout': 'landscape',
                'src': first_image.get('src', ''),
                'alt_text': first_image.get('alt', '') or header or '',
                'caption': paragraphs[0] if paragraphs else '',
                'images': images,  # All images
            })

        elif content_type == 'carousel':
            # Carousel/slider sektion - ekstraher items fra widgets
            widgets = section_data.get('widgets', [])
            carousel_items = []

            # Find carousel widget og ekstraher items
            for widget in widgets:
                if widget.get('category') == 'carousel':
                    carousel_items = widget.get('content', {}).get('items', [])
                    break

            # Fallback: byg items fra child sections hvis ingen widget items
            if not carousel_items and paragraphs:
                for p in paragraphs[:5]:
                    carousel_items.append({'text': p})

            block.update({
                'header': header or 'Vores services',
                'subheader': subheader or '',
                'carousel_items': carousel_items,
                'images': images,
                'buttons': buttons,
                'widgets': widgets,  # Bevar fuld widget-data
            })

        elif content_type == 'accordion':
            # Accordion sektion
            widgets = section_data.get('widgets', [])
            accordion_items = []

            for widget in widgets:
                if widget.get('category') == 'accordion':
                    accordion_items = widget.get('content', {}).get('items', [])
                    break

            block.update({
                'header': header or '',
                'subheader': subheader or '',
                'accordion_items': accordion_items,
                'paragraphs': paragraphs,
                'widgets': widgets,
            })

        elif content_type == 'tabs':
            # Tabs sektion
            widgets = section_data.get('widgets', [])
            tab_items = []

            for widget in widgets:
                if widget.get('category') == 'tabs':
                    tab_items = widget.get('content', {}).get('items', [])
                    break

            block.update({
                'header': header or '',
                'subheader': subheader or '',
                'tab_items': tab_items,
                'paragraphs': paragraphs,
                'widgets': widgets,
            })

        elif content_type == 'flip_cards':
            # Flip box sektion
            widgets = section_data.get('widgets', [])
            flip_cards = []

            for widget in widgets:
                if widget.get('category') == 'flip_card':
                    content = widget.get('content', {})
                    flip_cards.append({
                        'front_title': content.get('front_title', ''),
                        'front_text': content.get('front_text', ''),
                        'back_title': content.get('back_title', ''),
                        'back_text': content.get('back_text', ''),
                    })

            block.update({
                'header': header or '',
                'subheader': subheader or '',
                'flip_cards': flip_cards,
                'images': images,
                'widgets': widgets,
            })

        # Tilføj widgets til alle block types for maksimal fleksibilitet
        if 'widgets' not in block and section_data.get('widgets'):
            block['widgets'] = section_data.get('widgets', [])

        return block

    def _extract_usps_from_content(self, content: str) -> list:
        """Extract USP bullet points from content text."""
        usps = []

        # Look for bullet points (•, *, ✓, ✔, -)
        bullet_patterns = [
            r'[•\*✓✔\-]\s*([^\n•\*✓✔\-]{5,50})',
            r'\n\s*[\-\*•]\s*([^\n]{5,50})',
        ]

        for pattern in bullet_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                cleaned = match.strip()
                if cleaned and len(cleaned) > 5:
                    usps.append(cleaned)

        return usps[:4]  # Max 4 USPs


class WebsiteScraper:
    """
    Scrape and extract text content from websites.

    Features:
    - Static crawl with requests + BeautifulSoup
    - Playwright fallback for JavaScript-rendered content
    - Automatic detection of empty/insufficient content triggering fallback
    """

    # Minimum content length to consider scrape successful
    MIN_CONTENT_LENGTH = 100
    # Minimum number of sections to consider extraction successful
    MIN_SECTIONS_COUNT = 1

    def __init__(self, max_content_length=6000, use_playwright_fallback=True):
        self.max_content_length = max_content_length
        self.use_playwright_fallback = use_playwright_fallback
        self._universal_crawler = None
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

    @property
    def universal_crawler(self):
        """Lazy-load UniversalCrawler only when needed."""
        if self._universal_crawler is None:
            from crawler.universal_crawler import UniversalCrawler
            self._universal_crawler = UniversalCrawler(timeout=30000)
        return self._universal_crawler

    def _scrape_with_playwright(self, url: str) -> dict:
        """
        Fallback scraper using Playwright for JavaScript-rendered content.

        Args:
            url: URL to scrape

        Returns:
            Dict with content, sections, meta info, etc.
        """
        try:
            result = self.universal_crawler.crawl_page(url)
            if 'error' in result:
                print(f"[WebsiteScraper] Playwright error: {result['error']}")
                return None

            # Convert UniversalCrawler format to WebsiteScraper format
            sections = []
            for section in result.get('sections', []):
                # Only include sections with actual content
                if section.get('content') and len(section.get('content', [])) > 0:
                    content_text = '\n'.join(section.get('content', []))
                    if len(content_text.strip()) > 10:  # Skip very short sections
                        sections.append({
                            'tag': section.get('tag', 'h2'),
                            'header': section.get('heading', ''),
                            'content': content_text
                        })

            return {
                'content': result.get('main_content', ''),
                'meta_title': result.get('title', ''),
                'meta_description': result.get('meta_description', ''),
                'sections': sections,
                'reviews': result.get('reviews', []),
                'usps': result.get('usps', []),
                'html': result.get('html', ''),
                'used_playwright': True
            }
        except Exception as e:
            print(f"[WebsiteScraper] Playwright fallback failed: {e}")
            return None

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
                max_tokens=max_tokens,
                timeout=120.0  # 120 sekunder timeout for store websites
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

    def extract_layout_to_flat_sections(self, soup: BeautifulSoup, existing_sections: list = None, reviews: list = None) -> dict:
        """
        Main entry point: Extract page layout and convert to flatSections.

        New approach (Elementor-native):
        1. For Elementor sites: Use ElementorJsonExtractor to preserve structure 1:1
        2. Convert to flatSections format for wireframe visualization
        3. Store raw Elementor JSON for export

        Args:
            soup: BeautifulSoup object of page HTML
            existing_sections: Optional pre-extracted sections from extract_all_sections()
            reviews: Optional pre-extracted reviews

        Returns:
            dict with:
                'flat_sections': flatSections structure ready for campaign_builder_wizard.html
                'builder_detected': dict with builder info
                'sections_count': number of sections extracted
                'elementor_json': Raw Elementor JSON for export (only for Elementor sites)
        """
        from .elementor_extractor import ElementorJsonExtractor, get_display_info

        # Detect page builder
        detector = PageBuilderDetector()
        builder_info = detector.detect(soup)

        print(f"[LayoutExtractor] Detected builder: {builder_info['builder']} (confidence: {builder_info['confidence']:.2f})")

        elementor_json = None
        flat_sections = []

        # NEW: For Elementor sites, use the new native extractor
        if builder_info['builder'] == 'elementor' and builder_info['confidence'] > 0.3:
            extractor = ElementorJsonExtractor()
            elementor_json = extractor.extract(soup)
            print(f"[LayoutExtractor] Elementor JSON extracted {len(elementor_json.get('content', []))} top-level elements")

            # Convert Elementor JSON to flatSections format
            flat_sections = self._convert_elementor_to_flat_sections(elementor_json, reviews)
            print(f"[LayoutExtractor] Converted to {len(flat_sections)} flatSections")

        else:
            # Fallback to old approach for non-Elementor sites
            layout_sections = []

            if builder_info['builder'] == 'divi' and builder_info['confidence'] > 0.3:
                extractor = DiviLayoutExtractor()
                layout_sections = extractor.extract_layout(soup)
                print(f"[LayoutExtractor] Divi extracted {len(layout_sections)} sections")

            elif builder_info['builder'] == 'wpbakery' and builder_info['confidence'] > 0.3:
                extractor = WPBakeryLayoutExtractor()
                layout_sections = extractor.extract_layout(soup)
                print(f"[LayoutExtractor] WPBakery extracted {len(layout_sections)} sections")

            elif builder_info['builder'] == 'generic':
                extractor = GenericLayoutExtractor()
                layout_sections = extractor.extract_layout(soup)
                print(f"[LayoutExtractor] Generic grid extracted {len(layout_sections)} sections")

            # If no builder layout detected, fall back to existing sections with default widths
            if not layout_sections and existing_sections:
                print("[LayoutExtractor] No builder layout found, using existing sections with default widths")
                for i, section in enumerate(existing_sections):
                    layout_sections.append({
                        'width': '1/1',
                        'header': section.get('header', ''),
                        'text_content': section.get('content', ''),
                        'has_testimonials': False,
                        'has_form': False,
                        'has_images': False,
                        'position': i,
                    })

            # Filter out empty sections
            layout_sections = [s for s in layout_sections if s.get('text_content', '').strip() or s.get('header', '').strip()]

            # Convert to flatSections using old converter
            converter = FlatSectionsConverter()
            flat_sections = converter.convert(layout_sections, reviews)

        result = {
            'flat_sections': flat_sections,
            'builder_detected': builder_info,
            'sections_count': len(flat_sections)
        }

        # Include Elementor JSON for export if available
        if elementor_json:
            result['elementor_json'] = elementor_json

        return result

    def _convert_elementor_to_flat_sections(self, elementor_json: dict, reviews: list = None) -> list:
        """
        Convert Elementor JSON structure to flatSections format for wireframe visualization.

        IMPORTANT: Each top-level container becomes ONE visual section.
        Widgets within the same container are grouped together.

        Args:
            elementor_json: Extracted Elementor JSON from ElementorJsonExtractor
            reviews: Optional pre-extracted reviews

        Returns:
            list of flatSections matching campaign_builder_wizard.html format
        """
        from .elementor_extractor import get_display_info
        import time
        import random
        import string

        def generate_id(prefix: str) -> str:
            timestamp = int(time.time() * 1000)
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
            return f"{prefix}_{timestamp}_{random_str}"

        def collect_all_widgets(element: dict) -> list:
            """Recursively collect ALL widgets from an element and its children."""
            widgets = []

            if element.get('elType') == 'widget':
                widgets.append(element)

            for child in element.get('elements', []):
                widgets.extend(collect_all_widgets(child))

            return widgets

        def get_column_structure(element: dict) -> list:
            """Get the column structure of a container (child containers with their widths)."""
            columns = []
            children = element.get('elements', [])

            # Count container children to determine default widths
            container_children = [c for c in children if c.get('elType') in ['container', 'section', 'column']]
            num_columns = len(container_children)

            # Default widths based on column count
            default_widths = {
                1: '1/1',
                2: '1/2',
                3: '1/3',
                4: '1/4',
                5: '1/5',
                6: '1/6'
            }
            default_width = default_widths.get(num_columns, '1/1')

            for child in children:
                if child.get('elType') in ['container', 'section', 'column']:
                    settings = child.get('settings', {})
                    # Try to get width from settings, fall back to calculated default
                    width = self._calculate_element_width(settings, default_width)
                    child_widgets = collect_all_widgets(child)

                    column_data = {
                        'width': width,
                        'widgets': child_widgets,
                        'id': child.get('id', generate_id('col'))
                    }

                    # Check for background image on empty containers
                    if child.get('hasBackgroundImage') and not child_widgets:
                        column_data['hasBackgroundImage'] = True
                        column_data['backgroundImage'] = child.get('backgroundImage', {})

                    columns.append(column_data)

            return columns

        def determine_section_type(widgets: list) -> dict:
            """Determine the primary type of a section based on its widgets."""
            widget_types = [w.get('widgetType', '') for w in widgets]

            # Check for hero section (H1 + icon-list/USPs)
            has_heading = any(t == 'heading' for t in widget_types)
            has_icon_list = any(t == 'icon-list' for t in widget_types)
            has_form = any(t in ['form', 'wpforms', 'contact-form-7'] for t in widget_types)
            has_carousel = any('carousel' in t for t in widget_types)
            has_testimonial = any('testimonial' in t for t in widget_types)
            has_image = any(t == 'image' for t in widget_types)
            has_text = any(t == 'text-editor' for t in widget_types)

            # Check for logo slider (media-carousel with only images)
            is_logo_slider = False
            for w in widgets:
                if w.get('widgetType') == 'media-carousel':
                    carousel_type = w.get('content', {}).get('carousel_type', '')
                    if carousel_type == 'logo_slider':
                        is_logo_slider = True
                        break

            # Check for H1 in heading widgets
            has_h1 = False
            for w in widgets:
                if w.get('widgetType') == 'heading':
                    content = w.get('content', {})
                    if content.get('tag') == 'h1':
                        has_h1 = True
                        break

            # Determine primary type
            if has_h1 and has_icon_list:
                return {'type': 'hero', 'color': 'green'}
            elif has_form:
                return {'type': 'contact_form', 'color': 'blue'}
            elif has_testimonial or (has_carousel and 'testimonial' in str(widget_types)):
                return {'type': 'reviews', 'color': 'amber'}
            elif is_logo_slider:
                return {'type': 'logo_slider', 'color': 'indigo'}
            elif has_carousel:
                return {'type': 'carousel', 'color': 'blue'}
            elif has_icon_list:
                return {'type': 'list', 'color': 'green'}
            # Image-only column (no text or heading)
            elif has_image and not has_text and not has_heading:
                return {'type': 'image', 'color': 'slate'}
            elif has_heading:
                return {'type': 'text', 'color': 'gray'}
            else:
                # Check for inferred types from generic content extraction
                for widget in widgets:
                    widget_content = widget.get('content', {})
                    inferred_type = widget_content.get('_inferred_type', '')
                    if inferred_type:
                        inferred_type_map = {
                            'form': {'type': 'contact_form', 'color': 'purple'},
                            'accordion': {'type': 'accordion', 'color': 'purple'},
                            'gallery': {'type': 'gallery', 'color': 'blue'},
                            'image': {'type': 'image', 'color': 'gray'},
                            'list': {'type': 'list', 'color': 'green'},
                            'link_list': {'type': 'list', 'color': 'cyan'},
                            'text_with_title': {'type': 'text', 'color': 'gray'},
                            'text_long': {'type': 'text', 'color': 'gray'},
                            'text_short': {'type': 'text', 'color': 'gray'},
                            'mixed': {'type': 'generic', 'color': 'orange'},
                        }
                        if inferred_type in inferred_type_map:
                            return inferred_type_map[inferred_type]
                return {'type': 'generic', 'color': 'gray'}

        def create_section_content(widgets: list, section_type: dict) -> dict:
            """Create the content dict for a section based on its widgets."""
            # Map section type to _inferred_type for UI display
            type_to_inferred = {
                'hero': 'text_with_title',
                'usp_header': 'list',
                'text': 'text_long',
                'reviews': 'text_with_title',
                'contact_form': 'form',
                'form': 'form',
                'cta': 'text_with_title',
                'image': 'image',
                'carousel': 'gallery',
                'gallery': 'gallery',
                'accordion': 'accordion',
                'list': 'list',
                'generic': 'mixed',
                'header': 'text_with_title',
                'button': 'text_short',
                'video': 'mixed',
                'testimonial': 'text_with_title',
            }
            content = {
                'type': section_type['type'],
                'color': section_type['color'],
                '_inferred_type': type_to_inferred.get(section_type['type'], 'text_long'),
                'widgets': []  # Store widget info for reference
            }

            # Extract key content from widgets
            for w in widgets:
                widget_type = w.get('widgetType', '')
                widget_content = w.get('content', {})

                if widget_type == 'heading':
                    tag = widget_content.get('tag', 'h2')
                    title = widget_content.get('title', '')
                    if tag == 'h1' and not content.get('headline'):
                        content['headline'] = title
                        content['is_hero'] = True
                    elif not content.get('header'):
                        content['header'] = title
                    content['widgets'].append({'type': 'heading', 'tag': tag, 'title': title})

                elif widget_type == 'text-editor':
                    text = widget_content.get('text', '')
                    if not content.get('content'):
                        content['content'] = text  # Used by renderFlatText
                        content['intro'] = text    # Backwards compatibility
                    else:
                        # Append additional paragraphs
                        content['content'] += '\n\n' + text
                        content['intro'] = content['content']
                    content['widgets'].append({'type': 'text', 'text': text[:200]})

                elif widget_type == 'icon-list':
                    items = widget_content.get('items', [])
                    if items:
                        content['usps'] = items
                        content['list_items'] = items
                    content['widgets'].append({'type': 'list', 'items': items})

                elif widget_type in ['form', 'wpforms', 'contact-form-7']:
                    fields = widget_content.get('fields', [])
                    content['fields'] = [f.get('name') or f.get('type') for f in fields]
                    content['widgets'].append({'type': 'form', 'fields': len(fields)})

                elif 'carousel' in widget_type or 'testimonial' in widget_type:
                    items = widget_content.get('items', [])
                    carousel_type = widget_content.get('carousel_type', 'content')

                    if 'testimonial' in widget_type or carousel_type == 'testimonial':
                        content['reviews'] = items
                        content['widgets'].append({'type': 'carousel', 'subtype': 'testimonial', 'slides': len(items)})
                    elif carousel_type == 'logo_slider':
                        # Extract logo images
                        content['logos'] = [item.get('image', '') for item in items if item.get('image')]
                        content['logo_count'] = len(content['logos'])
                        content['widgets'].append({'type': 'carousel', 'subtype': 'logo_slider', 'slides': len(items)})
                    else:
                        content['carousel_items'] = items
                        content['widgets'].append({'type': 'carousel', 'subtype': carousel_type, 'slides': len(items)})

                    content['total_slides'] = len(items)
                    content['carousel_type'] = carousel_type

                elif widget_type == 'button':
                    btn_text = widget_content.get('text', '')
                    if not content.get('button_text'):
                        content['button_text'] = btn_text
                    content['widgets'].append({'type': 'button', 'text': btn_text})

                elif widget_type == 'image':
                    img_src = widget_content.get('src', '')
                    img_alt = widget_content.get('alt', '')
                    # For image-only sections, set src/alt on content
                    if section_type['type'] == 'image' and not content.get('src'):
                        content['src'] = img_src
                        content['alt_text'] = img_alt
                    content['widgets'].append({'type': 'image', 'src': img_src, 'alt': img_alt})

                elif widget_type in ['accordion', 'toggle', 'pp-advanced-accordion']:
                    items = widget_content.get('items', [])
                    if items:
                        content['accordion_items'] = items
                    content['widgets'].append({'type': 'accordion', 'items': len(items)})

                else:
                    # Handle unknown widgets with generic content extraction
                    inferred_type = widget_content.get('_inferred_type', 'empty')

                    # Pass through widgetType for display
                    content['widgetType'] = widget_type

                    # Extract generic content fields
                    if widget_content.get('title') and not content.get('header'):
                        content['header'] = widget_content.get('title', '')
                        content['headline'] = widget_content.get('title', '')

                    if widget_content.get('text') and not content.get('content'):
                        content['content'] = widget_content.get('text', '')
                        content['intro'] = widget_content.get('text', '')

                    if widget_content.get('items') and not content.get('list_items'):
                        content['list_items'] = widget_content.get('items', [])
                        content['usps'] = widget_content.get('items', [])[:6]

                    if widget_content.get('accordion_items'):
                        content['accordion_items'] = widget_content.get('accordion_items', [])

                    if widget_content.get('form_fields'):
                        content['fields'] = [f.get('name') or f.get('placeholder') or f.get('type') for f in widget_content.get('form_fields', [])]

                    if widget_content.get('links'):
                        content['links'] = widget_content.get('links', [])

                    if widget_content.get('images'):
                        content['images'] = widget_content.get('images', [])
                        if len(content['images']) == 1 and not content.get('src'):
                            content['src'] = content['images'][0].get('src', '')
                            content['alt_text'] = content['images'][0].get('alt', '')

                    # Store full widget content in a separate key for renderFlatGeneric
                    # (don't overwrite 'content' as that's used for text strings)
                    content['_widget_content'] = widget_content

                    # Add widget info for reference
                    content['widgets'].append({
                        'type': inferred_type,
                        'widgetType': widget_type,
                        '_inferred_type': inferred_type
                    })

            return content

        flat_sections = []

        # Process each TOP-LEVEL container as ONE visual section
        for i, top_element in enumerate(elementor_json.get('content', [])):
            if top_element.get('elType') not in ['container', 'section']:
                continue

            # Get column structure
            columns = get_column_structure(top_element)

            if columns:
                # Multi-column layout
                for col in columns:
                    # Handle background image containers (no widgets but has background image)
                    if not col['widgets'] and col.get('hasBackgroundImage'):
                        content = {
                            'id': generate_id('block'),
                            'type': 'image',
                            'color': 'slate',
                            'is_background_image': True,
                            'widgets': [{'type': 'image', 'src': col.get('backgroundImage', {}).get('url', '')}]
                        }
                        flat_sections.append({
                            'id': generate_id('sec'),
                            'width': col['width'],
                            'position': len(flat_sections),
                            'contents': [content]
                        })
                        continue
                    elif not col['widgets']:
                        continue

                    section_type = determine_section_type(col['widgets'])
                    content = create_section_content(col['widgets'], section_type)
                    content['id'] = generate_id('block')

                    flat_sections.append({
                        'id': generate_id('sec'),
                        'width': col['width'],
                        'position': len(flat_sections),
                        'contents': [content]
                    })
            else:
                # Single-column or direct widgets
                all_widgets = collect_all_widgets(top_element)
                if not all_widgets:
                    continue

                section_type = determine_section_type(all_widgets)
                content = create_section_content(all_widgets, section_type)
                content['id'] = generate_id('block')

                flat_sections.append({
                    'id': generate_id('sec'),
                    'width': '1/1',
                    'position': len(flat_sections),
                    'contents': [content]
                })

        print(f"[LayoutExtractor] Created {len(flat_sections)} visual sections from {len(elementor_json.get('content', []))} top-level containers")
        return flat_sections

    def _calculate_element_width(self, settings: dict, parent_width: str) -> str:
        """Calculate element width from settings."""
        # Try flex_size first
        if 'flex_size' in settings:
            try:
                flex = float(settings['flex_size'])
                return self._normalize_percentage_to_fraction(flex)
            except (ValueError, TypeError):
                pass

        # Try _column_size
        if '_column_size' in settings:
            try:
                size = float(settings['_column_size'])
                return self._normalize_percentage_to_fraction(size)
            except (ValueError, TypeError):
                pass

        return parent_width

    def _normalize_percentage_to_fraction(self, percent: float) -> str:
        """Convert percentage to fraction string."""
        if percent >= 95:
            return '1/1'
        elif percent >= 70:
            return '3/4'
        elif percent >= 60:
            return '2/3'
        elif percent >= 45:
            return '1/2'
        elif percent >= 30:
            return '1/3'
        elif percent >= 20:
            return '1/4'
        else:
            return '1/6'

    def _create_flat_section_from_widgets(self, widgets: list, width: str, pos: int, section_id: str) -> dict:
        """Create a flatSection from a list of widgets."""
        from .elementor_extractor import get_display_info
        import time
        import random
        import string

        def generate_id(prefix: str) -> str:
            timestamp = int(time.time() * 1000)
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
            return f"{prefix}_{timestamp}_{random_str}"

        if not widgets:
            return None

        # Find primary widget (heading or first significant widget)
        primary_widget = None
        for w in widgets:
            wt = w.get('widgetType', '')
            if wt == 'heading':
                primary_widget = w
                break
            elif wt in ['icon-list', 'testimonial-carousel', 'nested-carousel', 'form']:
                primary_widget = w
                break

        if not primary_widget:
            primary_widget = widgets[0]

        primary_type = primary_widget.get('widgetType', 'text-editor')
        display_info = get_display_info(primary_type)

        # Aggregate content from all widgets
        header = ''
        text_content = ''
        list_items = []
        images = []
        buttons = []
        carousel_items = []

        for w in widgets:
            wt = w.get('widgetType', '')
            content = w.get('content', {})

            if wt == 'heading':
                if not header:
                    header = content.get('title', '')

            elif wt == 'text-editor':
                text = content.get('text', '')
                if text:
                    text_content += text + '\n\n'

            elif wt == 'icon-list':
                items = content.get('items', [])
                list_items.extend(items)

            elif wt == 'image':
                images.append({
                    'src': content.get('src', ''),
                    'alt': content.get('alt', '')
                })

            elif wt == 'button':
                buttons.append({
                    'text': content.get('text', ''),
                    'href': content.get('href', '')
                })

            elif wt in ['testimonial-carousel', 'nested-carousel', 'media-carousel']:
                carousel_items = content.get('items', [])

        # Build section content
        block = {
            'id': generate_id('block'),
            'type': display_info['display_type'],
            'widgetType': primary_type,
            'color': display_info['color'],
            'header': header,
            'headline': header,
            'content': text_content.strip(),
            'list_items': list_items,
            'usps': list_items[:6] if list_items else [],
            'images': images,
            'buttons': buttons,
            'widgets': widgets,  # Preserve all widgets for reference
        }

        # Add type-specific fields
        if carousel_items:
            block['carousel_items'] = carousel_items

        return {
            'id': section_id,
            'width': width,
            'position': pos,
            'contents': [block]
        }

    def _map_widget_content_to_block(self, widget_type: str, content: dict) -> dict:
        """Map widget content to block format for visualization."""
        block = {}

        if widget_type == 'heading':
            block['header'] = content.get('title', '')
            block['headline'] = content.get('title', '')
            block['tag'] = content.get('tag', 'h2')

        elif widget_type == 'text-editor':
            block['content'] = content.get('text', '')
            block['paragraphs'] = content.get('paragraphs', [])

        elif widget_type == 'icon-list':
            block['list_items'] = content.get('items', [])
            block['usps'] = content.get('items', [])[:6]

        elif widget_type == 'image':
            block['src'] = content.get('src', '')
            block['alt_text'] = content.get('alt', '')

        elif widget_type == 'button':
            block['button_text'] = content.get('text', '')
            block['button_href'] = content.get('href', '')

        elif widget_type in ['form', 'wpforms', 'contact-form-7']:
            block['fields'] = content.get('fields', [])
            block['button_text'] = content.get('submit_text', 'Send')

        elif widget_type in ['testimonial-carousel', 'nested-carousel', 'media-carousel', 'slides']:
            block['carousel_items'] = content.get('items', [])
            block['total_slides'] = content.get('total_slides', 0)

        elif widget_type in ['accordion', 'toggle']:
            block['accordion_items'] = content.get('items', [])

        elif widget_type == 'tabs':
            block['tab_items'] = content.get('tabs', [])

        elif widget_type == 'flip-box':
            block['front_title'] = content.get('front_title', '')
            block['front_text'] = content.get('front_text', '')
            block['back_title'] = content.get('back_title', '')
            block['back_text'] = content.get('back_text', '')

        elif widget_type == 'testimonial':
            block['testimonial_text'] = content.get('text', '')
            block['testimonial_author'] = content.get('author', '')

        elif widget_type == 'video':
            block['video_src'] = content.get('src', '')

        elif widget_type == 'social-icons':
            block['social_icons'] = content.get('icons', [])

        elif widget_type == 'call-to-action':
            block['headline'] = content.get('title', '')
            block['subheadline'] = content.get('description', '')
            block['button_text'] = content.get('button_text', '')
            block['button_href'] = content.get('button_href', '')

        return block

    def scrape_with_meta(self, url, timeout=10, extract_layout=False, use_vision_layout=False):
        """
        Fetch and extract text content, meta tags, structured sections, AND reviews from a website.

        Args:
            url: Website URL to scrape
            timeout: Request timeout in seconds
            extract_layout: If True, also extract layout as flatSections wireframe
            use_vision_layout: If True, use AI Vision for layout detection (recommended for non-Elementor sites)

        Returns:
            dict: {
                'content': str,
                'meta_title': str or None,
                'meta_description': str or None,
                'sections': list of {'tag', 'header', 'content'},
                'reviews': list of review dicts (from Elementor testimonials etc.),
                'flat_sections': list (only if extract_layout=True),
                'builder_detected': dict (only if extract_layout=True),
            }
        """
        if not url:
            result = {'content': '', 'meta_title': None, 'meta_description': None, 'sections': [], 'reviews': [], 'review_section_position': None, 'review_iframes': []}
            if extract_layout:
                result['flat_sections'] = []
                result['builder_detected'] = None
            return result

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

            # Extract layout to flatSections if requested (do this BEFORE scrape_website modifies soup)
            flat_sections = None
            builder_detected = None
            elementor_json = None
            if extract_layout:
                try:
                    if use_vision_layout:
                        # Use AI Vision for layout detection (works on ALL websites)
                        print(f"[WebsiteScraper] Using AI Vision for layout detection...")
                        vision_analyzer = VisionLayoutAnalyzer()
                        vision_result = vision_analyzer.analyze_url(url)

                        if vision_result.get('success') and vision_result.get('flat_sections'):
                            flat_sections = vision_result['flat_sections']
                            builder_detected = {
                                'builder': 'vision',
                                'confidence': 0.95,
                                'indicators_found': ['ai_vision_analysis']
                            }
                            print(f"[WebsiteScraper] Vision layout: {len(flat_sections)} sections")
                        else:
                            print(f"[WebsiteScraper] Vision failed, falling back to HTML extraction")
                            use_vision_layout = False  # Fall back to HTML

                    if not use_vision_layout or not flat_sections:
                        # Original HTML-based extraction
                        layout_result = self.extract_layout_to_flat_sections(soup, sections, html_reviews)
                        flat_sections = layout_result.get('flat_sections', [])
                        builder_detected = layout_result.get('builder_detected')
                        elementor_json = layout_result.get('elementor_json')  # Elementor native JSON for export
                        print(f"[WebsiteScraper] Layout extraction: {len(flat_sections)} flatSections from {builder_detected.get('builder', 'unknown') if builder_detected else 'unknown'}")
                        print(f"[WebsiteScraper] elementor_json present: {elementor_json is not None}, content count: {len(elementor_json.get('content', [])) if elementor_json else 0}")

                except Exception as layout_error:
                    print(f"[WebsiteScraper] Layout extraction failed: {layout_error}")
                    import traceback
                    traceback.print_exc()
                    flat_sections = []
                    builder_detected = None

            # Now get content using existing method (which modifies soup)
            content = self.scrape_website(url, timeout)

            # Check if we need Playwright fallback
            # Conditions: content is too short OR no meaningful sections found
            needs_playwright = False
            if self.use_playwright_fallback:
                content_too_short = len(content) < self.MIN_CONTENT_LENGTH
                no_sections = len(sections) < self.MIN_SECTIONS_COUNT
                # Check if sections have content (not just headers)
                sections_have_content = any(
                    s.get('content') and len(str(s.get('content', '')).strip()) > 20
                    for s in sections
                )

                if content_too_short or (no_sections and not sections_have_content):
                    needs_playwright = True
                    print(f"[WebsiteScraper] Static scrape insufficient (content={len(content)} chars, sections={len(sections)}). Trying Playwright...")

            used_playwright = False
            if needs_playwright:
                playwright_result = self._scrape_with_playwright(url)
                if playwright_result:
                    pw_content = playwright_result.get('content', '')
                    pw_sections = playwright_result.get('sections', [])

                    # Use Playwright results if better
                    if len(pw_content) > len(content):
                        content = pw_content
                        print(f"[WebsiteScraper] Playwright returned {len(content)} chars of content")

                    if len(pw_sections) > len(sections):
                        sections = pw_sections
                        print(f"[WebsiteScraper] Playwright returned {len(sections)} sections")

                    # Use Playwright meta if we didn't get it from static scrape
                    if not meta_title and playwright_result.get('meta_title'):
                        meta_title = playwright_result.get('meta_title')
                    if not meta_description and playwright_result.get('meta_description'):
                        meta_description = playwright_result.get('meta_description')

                    # Merge reviews
                    pw_reviews = playwright_result.get('reviews', [])
                    if pw_reviews:
                        html_reviews = self._merge_reviews(html_reviews, pw_reviews)

                    used_playwright = True

            result = {
                'content': content,
                'meta_title': meta_title,
                'meta_description': meta_description,
                'sections': sections,
                'reviews': html_reviews,  # Only HTML-detected reviews (AI classification happens in batch later)
                'review_section_position': review_section_position,
                'review_iframes': review_iframes,
                'used_playwright': used_playwright
            }

            # Add layout data if extracted
            if extract_layout:
                result['flat_sections'] = flat_sections
                result['builder_detected'] = builder_detected
                if elementor_json:
                    result['elementor_json'] = elementor_json

            return result

        except Exception as e:
            print(f"Website parsing error for {url}: {e}")
            result = {'content': '', 'meta_title': None, 'meta_description': None, 'sections': [], 'reviews': [], 'review_section_position': None, 'review_iframes': []}
            if extract_layout:
                result['flat_sections'] = []
                result['builder_detected'] = None
            return result


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
                    **build_completion_kwargs(model, [{"role": "user", "content": prompt}], temperature, max_tokens),
                    timeout=120.0  # 120 sekunder timeout for store websites
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
                    **build_completion_kwargs(model, [{"role": "user", "content": prompt}], temperature, max_tokens),
                    timeout=120.0  # 120 sekunder timeout for store websites
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
                **build_completion_kwargs(model, [{"role": "user", "content": prompt}], temperature, max_tokens),
                timeout=120.0  # 120 sekunder timeout for store websites
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
                    **build_completion_kwargs(model, [{"role": "user", "content": prompt}], temperature, max_tokens),
                    timeout=120.0  # 120 sekunder timeout for store websites
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
                **build_completion_kwargs(model, [{"role": "user", "content": prompt}], temperature, max_tokens),
                timeout=120.0  # 120 sekunder timeout for store websites
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
                        max_tokens=max_tokens,
                        timeout=120.0  # 120 sekunder timeout for store websites
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

    def scrape_website(self, url, max_pages=10, client_id=None, use_playwright=False, extract_layout=True, use_vision_layout=True):
        """
        Scrape a website comprehensively.

        Args:
            url: Website URL to scrape
            max_pages: Maximum pages to scrape (10, 50, 100, or 0/None for all)
            client_id: If set, save permanently to Client model
            use_playwright: DEPRECATED - no longer used, review iframes are detected automatically
            extract_layout: If True, extract page builder layout as flatSections wireframe
            use_vision_layout: If True, use AI Vision for layout detection (default: True)

        Returns:
            Dict with scraped data structure including review_iframes and flat_sections
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

                # Only use Vision layout for the FIRST page (front page) to avoid timeout
                # Other pages use standard HTML extraction which is much faster
                use_vision_for_this_page = use_vision_layout and i == 0

                # Scrape page with meta info, sections, reviews, iframes, and layout
                scraped = self.page_scraper.scrape_with_meta(page_url, extract_layout=extract_layout, use_vision_layout=use_vision_for_this_page)

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
                        'flat_sections': scraped.get('flat_sections', []),  # Layout wireframe med korrekte kolonnebredder
                        'builder_detected': scraped.get('builder_detected'),  # Page builder info (Elementor, Divi etc.)
                        'elementor_json': scraped.get('elementor_json'),  # Elementor native JSON for export
                    }
                    pages_data[path] = page_info
                    combined_content_parts.append(f"--- {path} ---\n{content}")

            except Exception as e:
                print(f"[ComprehensiveScraper] Error scraping {page_url}: {e}")
                continue

        # Deduplicate reviews from multiple pages (same testimonials often appear on every page)
        if all_extracted_reviews:
            seen_texts = set()
            unique_reviews = []
            for review in all_extracted_reviews:
                # Use first 50 chars of text as key (same logic as _merge_reviews)
                text_key = review.get('text', '')[:50].lower().strip()
                if text_key and text_key not in seen_texts:
                    unique_reviews.append(review)
                    seen_texts.add(text_key)

            if len(unique_reviews) < len(all_extracted_reviews):
                print(f"[ComprehensiveScraper] Deduplicated reviews: {len(all_extracted_reviews)} -> {len(unique_reviews)}")
            all_extracted_reviews = unique_reviews

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
        classified_sections_by_page = {}
        if all_sections_for_ai:
            print(f"[ComprehensiveScraper] Running batch AI classification on {len(all_sections_for_ai)} sections from {len(pages_data)} pages...")

            # 1. Review classification (existing functionality)
            ai_result = self.page_scraper.classify_sections_with_ai(all_sections_for_ai)
            ai_reviews = ai_result.get('reviews', [])
            if ai_reviews:
                print(f"[ComprehensiveScraper] AI found {len(ai_reviews)} additional reviews")
                # Merge with HTML-detected reviews (avoiding duplicates)
                all_extracted_reviews = self.page_scraper._merge_reviews(all_extracted_reviews, ai_reviews)

            # 2. Section type classification (NEW)
            section_classifier = SectionClassifier()

            # Group sections by page for classification
            sections_by_page = {}
            for section in all_sections_for_ai:
                page = section.get('page', '/')
                if page not in sections_by_page:
                    sections_by_page[page] = []
                sections_by_page[page].append(section)

            # Classify sections for each page
            for page_path, page_sections in sections_by_page.items():
                page_url_full = url.rstrip('/') + page_path if page_path != '/' else url
                print(f"[ComprehensiveScraper] Classifying {len(page_sections)} sections for {page_path}...")

                classified = section_classifier.classify_sections(page_sections, page_url_full)
                classified_sections_by_page[page_path] = classified

                # Save to database if client_id provided
                if client_id:
                    section_classifier.save_classifications(client_id, page_url_full, classified)

                # Count section types for logging
                type_counts = {}
                for s in classified:
                    st = s.get('section_type', 'other')
                    type_counts[st] = type_counts.get(st, 0) + 1
                if type_counts:
                    print(f"[ComprehensiveScraper] Section types found: {type_counts}")

            # Update pages_data with classified sections
            for path, page_info in pages_data.items():
                if path in classified_sections_by_page:
                    page_info['classified_sections'] = classified_sections_by_page[path]

        # Build section type summary
        all_section_types = {}
        for path, classified in classified_sections_by_page.items():
            for s in classified:
                st = s.get('section_type', 'other')
                all_section_types[st] = all_section_types.get(st, 0) + 1

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
            'section_types_summary': all_section_types,  # Summary of all section types found
            'classified_sections_count': sum(len(v) for v in classified_sections_by_page.values()),
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
