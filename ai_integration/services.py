"""
AI Service Layer for Google Ads Builder.

Provides AI-powered content generation using OpenAI GPT-4.
"""

import json
import re
from openai import OpenAI
from django.conf import settings


class DescriptionGenerator:
    """Generate Google Ads descriptions using OpenAI GPT-4."""

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        if not api_key or api_key == 'your_openai_api_key_here':
            raise ValueError("OPENAI_API_KEY is not configured. Please set it in your .env file.")
        self.client = OpenAI(api_key=api_key)

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

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=500
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

    def generate_meta_tags(self, service_name, usps):
        """
        Generate 7 unique SEO meta titles and 7 meta descriptions.

        Args:
            service_name: Name of the service (e.g., "VVS", "Elektriker")
            usps: List of USP texts

        Returns:
            Dict with 'meta_titles' (list of 7) and 'meta_descriptions' (list of 7)
        """
        # Formatér USPs som nummereret liste
        if usps:
            usps_numbered = '\n'.join([f"{i+1}. {usp}" for i, usp in enumerate(usps[:5])])
        else:
            usps_numbered = "Ingen USP'er valgt"

        prompt = f"""Generér SEO meta tags for en {service_name} virksomhed.

Virksomhedens Unique Selling Points:
{usps_numbered}

KRAV:
1. Generér præcis 7 unikke meta titler (50-60 tegn hver)
2. Generér præcis 7 unikke meta beskrivelser (120-160 tegn hver)
3. ALLE titler og beskrivelser SKAL indeholde {{BYNAVN}} placeholder
4. Brug service navnet "{service_name}" i alle titler og beskrivelser
5. Inkorporér USP'erne naturligt i teksten
6. Variér strukturen - brug forskellige formuleringer

EKSEMPLER på meta titler (50-60 tegn):
- "Professionel {service_name} i {{BYNAVN}} - Hurtig Service"
- "{{BYNAVN}} {service_name} Ekspert - Gratis Tilbud"
- "Autoriseret {service_name} i {{BYNAVN}} - Ring Nu"

EKSEMPLER på meta beskrivelser (120-160 tegn):
- "Leder du efter professionel {service_name} i {{BYNAVN}}? Vi tilbyder hurtig service og fair priser. Ring for gratis tilbud!"
- "{service_name} eksperter i {{BYNAVN}} med mange års erfaring. Kvalitetsarbejde og tilfredse kunder. Kontakt os idag."

Returnér KUN valid JSON i dette format:
{{
    "meta_titles": ["titel1", "titel2", "titel3", "titel4", "titel5", "titel6", "titel7"],
    "meta_descriptions": ["desc1", "desc2", "desc3", "desc4", "desc5", "desc6", "desc7"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=2000
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
