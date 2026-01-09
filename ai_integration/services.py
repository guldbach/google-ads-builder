"""
AI Service Layer for Google Ads Builder.

Provides AI-powered content generation using OpenAI GPT-4 and Perplexity.
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from django.conf import settings


class WebsiteScraper:
    """Scrape and extract text content from websites."""

    def __init__(self, max_content_length=6000):
        self.max_content_length = max_content_length
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

            soup = BeautifulSoup(response.content, 'html.parser')

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


class USPAnalyzer:
    """Analyze website content to extract and match USPs."""

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        self.client = OpenAI(api_key=api_key)

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

        prompt = f"""Analysér følgende hjemmesidetekst og udtræk konkrete fakta der kan bruges som USP'er (Unique Selling Points).

HJEMMESIDETEKST:
{website_content[:5000]}

EKSISTERENDE USP TEMPLATES (match mod disse hvis muligt):
{templates_text}

INSTRUKTIONER:
1. Find KONKRETE FAKTA som:
   - Antal års erfaring (f.eks. "30 års erfaring")
   - Anmeldelsesdata (f.eks. "4.8/5 på Trustpilot", "1000+ anmeldelser")
   - Certificeringer og autorisationer
   - Priser og nomineringer (f.eks. "Finalist Årets Håndværker")
   - Responstider (f.eks. "Hos dig indenfor 2 timer")
   - Kundeantal eller opgaveantal

2. For HVER fundet fakta:
   - Match mod eksisterende USP templates hvis muligt
   - Udtræk værdier til variable (tal fra hjemmesiden)
   - Variable i templates er formateret som {{VARIABEL:default}}, f.eks. "{{ANTAL:+15}} års erfaring"
   - Variable index starter ved 0 for første variabel i teksten

3. For UNIKKE fakta der ikke matcher templates:
   - Foreslå som custom USP tekst (max 40 tegn)
   - Fokusér på konkrete, verificerbare claims

Returnér KUN valid JSON i dette format:
{{
    "matched_usps": [
        {{
            "usp_template_id": 15,
            "confidence": 0.92,
            "variable_values": {{"0": "30"}},
            "source_text": "citeret tekst fra hjemmesiden"
        }}
    ],
    "custom_usps": [
        {{
            "text": "Finalist Årets VVS 2024",
            "source_text": "citeret tekst"
        }}
    ],
    "extracted_facts": {{
        "years_experience": 30,
        "review_count": 1000,
        "review_rating": 4.8,
        "certifications": ["Autoriseret VVS"],
        "awards": ["Finalist Årets VVS 2024"]
    }}
}}

VIGTIGT:
- Match kun mod templates hvor du har konkret information fra hjemmesiden
- Brug de FAKTISKE tal fra hjemmesiden, ikke default værdier
- Returnér kun valid JSON"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
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

            return result

        except Exception as e:
            print(f"USP Analysis error: {e}")
            return {'matched_usps': [], 'custom_usps': [], 'extracted_facts': {}}


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

        # Try to get prompt from database
        db_prompt, model_settings = self._get_prompt_from_db('perplexity_research')

        if db_prompt:
            # Use database prompt with placeholders
            prompt = db_prompt.format(
                website_url=website_url if website_url else 'Ikke angivet',
                industries=industry_text,
                services=service_text
            )
            model = model_settings.get('model') or 'sonar'
            temperature = model_settings.get('temperature') or 0.3
            max_tokens = model_settings.get('max_tokens') or 800
        else:
            # Fallback to hardcoded prompt
            prompt = f"""Find information om denne danske virksomhed:

Website: {website_url}
Branche: {industry_text}
Services: {service_text}

Søg efter:
1. Virksomhedens historie og baggrund
2. Specialer og kernekompetencer
3. Kundeanmeldelser og omdømme (Trustpilot, Google Reviews)
4. Geografisk dækning
5. Særlige certifikater eller autorisationer

Returnér en kort opsummering (max 300 ord) på dansk med de vigtigste fund.
Medtag kun verificerbar information fra troværdige kilder."""
            model = "sonar"
            temperature = 0.3
            max_tokens = 800

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Return empty string if research fails - generation continues without it
            print(f"Perplexity research failed: {e}")
            return ""


class DescriptionGenerator:
    """Generate Google Ads descriptions using OpenAI GPT-4."""

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        if not api_key or api_key == 'your_openai_api_key_here':
            raise ValueError("OPENAI_API_KEY is not configured. Please set it in your .env file.")
        self.client = OpenAI(api_key=api_key)

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

        # Try to get prompt from database
        db_prompt, model_settings = self._get_prompt_from_db('generate_descriptions')

        if db_prompt:
            # Use database prompt with placeholders
            prompt = db_prompt.format(
                usps_numbered=usps_numbered,
                services_list=services_list,
                service_name=service_name,
                industry_name=industry_name,
                keywords_numbered=keywords_numbered
            )
            model = model_settings.get('model') or 'gpt-4.1'
            temperature = model_settings.get('temperature') or 0.8
            max_tokens = model_settings.get('max_tokens') or 500
        else:
            # Fallback to hardcoded prompt
            prompt = f"""Skriv 4 beskrivelser til google ads annoncer

Eksempler på gode beskrivelser:
1: Skal du bruge en lokal VVS'er. 4,8/5 på Trustpilot. 15 års erfaring. Ring for pris nu!
2: Et sprunget vandrør? Drømmer i om nyt badeværelse? Vi har 4.8/5 på Trustpilot. Kontakt os!
3: Alt i VVS. Skal der skiftes en radiator, et toilet eller et badeværelse. Få pris på 2 min
4: 4,8/5 på Trustpilot - +15 års erfaring - +5000 Glade kunder - Vi er hos dig om 1-3 timer!

Virksomheden har følgende Unique selling points:
{usps_numbered}

Services:
{services_list}

#Vigtigt
Eksempler er kun ment som inspiration. Du må ikke bruge nogle Unique selling points fra dem. Du skal tage udgangspunkt i kundens usp'er.

Hver beskrivelse SKAL være mellem 82 og 90 tegn. Tæl tegnene nøje!

Returnér KUN et JSON array med 4 strings:
["beskrivelse1", "beskrivelse2", "beskrivelse3", "beskrivelse4"]"""
            model = "gpt-4.1"
            temperature = 0.8
            max_tokens = 500

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content.strip()

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

        # Try to get prompt from database
        db_prompt, model_settings = self._get_prompt_from_db('generate_meta_tags')

        if db_prompt:
            # Use database prompt with placeholders
            prompt = db_prompt.format(
                service_name=service_name,
                usps_numbered=usps_numbered,
                examples_section=examples_section,
                few_shot_instruction=few_shot_instruction,
                default_examples=default_examples
            )
            model = model_settings.get('model') or 'gpt-4.1'
            temperature = model_settings.get('temperature') or 0.9
            max_tokens = model_settings.get('max_tokens') or 2000
        else:
            # Fallback to hardcoded prompt
            prompt = f"""Generér SEO meta tags for en {service_name} virksomhed.

Virksomhedens Unique Selling Points:
{usps_numbered}
{examples_section}
KRAV:
1. Generér præcis 7 unikke meta titler (50-60 tegn hver)
2. Generér præcis 7 unikke meta beskrivelser (150-160 tegn hver, vigtigt budskab i første 120 tegn)
3. ALLE titler og beskrivelser SKAL indeholde {{BYNAVN}} placeholder
4. Brug service navnet "{service_name}" i alle titler og beskrivelser
5. Inkorporér USP'erne naturligt i teksten
6. Variér strukturen - brug forskellige formuleringer
{few_shot_instruction}

{default_examples}
Returnér KUN valid JSON i dette format:
{{
    "meta_titles": ["titel1", "titel2", "titel3", "titel4", "titel5", "titel6", "titel7"],
    "meta_descriptions": ["desc1", "desc2", "desc3", "desc4", "desc5", "desc6", "desc7"]
}}"""
            model = "gpt-4.1"
            temperature = 0.9
            max_tokens = 2000

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content.strip()

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

        # Try to get prompt from database
        db_prompt, model_settings = self._get_prompt_from_db('generate_seo_meta_tags')

        if db_prompt:
            # Use database prompt with placeholders
            prompt = db_prompt.format(
                service_name=service_name,
                usps_formatted=usps_formatted,
                keywords_section=keywords_section,
                examples_section=examples_section,
                few_shot_instruction=few_shot_instruction,
                default_examples=default_examples
            )
            model = model_settings.get('model') or 'gpt-4.1'
            temperature = model_settings.get('temperature') or 0.7
            max_tokens = model_settings.get('max_tokens') or 500
        else:
            # Fallback to hardcoded prompt
            prompt = f"""Generér én SEO meta titel og én meta beskrivelse for en {service_name} virksomhed.

Virksomhedens USP'er:
{usps_formatted}
{keywords_section}{examples_section}
KRAV:
1. Meta titel: 50-65 tegn, fængende og professionel
2. Meta beskrivelse: 140-160 tegn, vigtigt budskab først
3. Brug service navnet "{service_name}" naturligt - ALDRIG kunstigt som "få din {service_name} pris"
4. Inkorporér USP'er fra listen
5. INGEN {{BYNAVN}} placeholder - kun medtag bynavn hvis det fremgår af søgeordene
{few_shot_instruction}

VIGTIGT - UNDGÅ KEYWORD STUFFING:
- Skriv naturligt dansk som en rigtig person ville skrive
- FORBUDTE formuleringer (brug ALDRIG disse):
  * "få din [service] pris" / "Ring for [service] pris"
  * "find din [service] her" / "book din [service]"
  * "[service] pris" i slutningen af en sætning
- Hvis et søgeord ikke kan bruges naturligt, så UDELAD det helt
- Brug i stedet naturlige call-to-actions som: "Ring for et tilbud", "Kontakt os i dag", "Få et uforpligtende tilbud"
- Tænk: "Ville en dansker faktisk sige det sådan?" - hvis nej, omformuler eller drop søgeordet

{default_examples}
Returnér KUN valid JSON i dette format:
{{
    "meta_title": "din meta titel her",
    "meta_description": "din meta beskrivelse her"
}}"""
            model = "gpt-4.1"
            temperature = 0.7
            max_tokens = 500

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content.strip()

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

        # Try to get prompt from database
        db_prompt, model_settings = self._get_prompt_from_db('generate_company_description')

        if db_prompt:
            # Use database prompt with placeholders
            prompt = db_prompt.format(
                website_url=website_url if website_url else 'Ikke angivet',
                industries=industries_text,
                services=services_text,
                usps=usps_text,
                geographic_areas=geo_text,
                website_content=website_section,
                online_research=research_section
            )
            model = model_settings.get('model') or 'gpt-4.1'
            temperature = model_settings.get('temperature') or 0.7
            max_tokens = model_settings.get('max_tokens') or 2000  # Increased for profile JSON
        else:
            # Fallback to hardcoded prompt
            prompt = f"""Skriv en professionel virksomhedsbeskrivelse på dansk baseret på følgende information.

VIRKSOMHEDSDATA:
- Website: {website_url if website_url else 'Ikke angivet'}
- Brancher: {industries_text}
- Services/Ydelser:
{services_text}
- Unique Selling Points (USP'er):
{usps_text}
- Geografisk dækning: {geo_text}
{website_section}
{research_section}
KRAV TIL BESKRIVELSEN:
1. Skriv en sammenhængende beskrivelse på 150-250 ord
2. Inkludér virksomhedens kerneydelser naturligt
3. Fremhæv USP'erne som styrker
4. Nævn det geografiske område hvis relevant
5. Skriv i en professionel men venlig tone
6. Undgå klichéer og tomme floskler
7. Gør beskrivelsen specifik og troværdig

KRAV TIL HOVEDPUNKTER:
1. Udtræk 3-5 korte hovedpunkter (max 10 ord hver)
2. Fokusér på de vigtigste differentierende faktorer
3. Brug konkrete tal og fakta fra USP'erne hvis muligt

Returnér KUN valid JSON i dette format:
{{
    "description": "Den fulde virksomhedsbeskrivelse her...",
    "key_points": ["Hovedpunkt 1", "Hovedpunkt 2", "Hovedpunkt 3"]
}}"""
            model = "gpt-4.1"
            temperature = 0.7
            max_tokens = 2000  # Increased for profile JSON

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content.strip()

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
                'profile': profile
            }

        except Exception as e:
            raise Exception(f"Fejl ved generering af virksomhedsbeskrivelse: {str(e)}")
