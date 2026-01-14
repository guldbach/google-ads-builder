"""
Management command to seed AI prompt templates from the existing hardcoded prompts.
"""
from django.core.management.base import BaseCommand
from ai_integration.models import AIPromptTemplate


class Command(BaseCommand):
    help = 'Seed AI prompt templates from existing hardcoded prompts'

    def handle(self, *args, **options):
        prompts_data = [
            {
                'name': 'Google Ads Beskrivelser',
                'prompt_type': 'generate_descriptions',
                'prompt_text': '''Skriv 4 beskrivelser til google ads annoncer

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
["beskrivelse1", "beskrivelse2", "beskrivelse3", "beskrivelse4"]''',
                'placeholders': [
                    {'name': '{usps_numbered}', 'description': 'Nummereret liste af USP\'er (1. USP1\\n2. USP2...)'},
                    {'name': '{services_list}', 'description': 'Bulleted liste af services/keywords'},
                    {'name': '{service_name}', 'description': 'Servicens navn (fx "Elektriker")'},
                ],
                'model_settings': {
                    'model': 'gpt-4.1',
                    'temperature': 0.8,
                    'max_tokens': 500
                }
            },
            {
                'name': 'Meta Tags (Programmatic)',
                'prompt_type': 'generate_meta_tags',
                'prompt_text': '''Generér SEO meta tags for en {service_name} virksomhed.

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
}}''',
                'placeholders': [
                    {'name': '{service_name}', 'description': 'Servicens navn (fx "Elektriker")'},
                    {'name': '{usps_numbered}', 'description': 'Nummereret liste af USP\'er'},
                    {'name': '{examples_section}', 'description': 'Few-shot eksempler sektion (hvis tilgængelig)'},
                    {'name': '{few_shot_instruction}', 'description': 'Instruktion om at følge eksempler'},
                    {'name': '{default_examples}', 'description': 'Standard eksempler (hvis ingen few-shot)'},
                    {'name': '{BYNAVN}', 'description': 'Placeholder for bynavn i output'},
                ],
                'model_settings': {
                    'model': 'gpt-4.1',
                    'temperature': 0.9,
                    'max_tokens': 2000
                }
            },
            {
                'name': 'SEO Meta Tags',
                'prompt_type': 'generate_seo_meta_tags',
                'prompt_text': '''Generér én SEO meta titel og én meta beskrivelse for en {service_name} virksomhed.

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
}}''',
                'placeholders': [
                    {'name': '{service_name}', 'description': 'Servicens navn (fx "Elektriker")'},
                    {'name': '{usps_formatted}', 'description': 'Bulleted liste af USP\'er'},
                    {'name': '{keywords_section}', 'description': 'SEO søgeord sektion (valgfri)'},
                    {'name': '{examples_section}', 'description': 'Few-shot eksempler sektion (hvis tilgængelig)'},
                    {'name': '{few_shot_instruction}', 'description': 'Instruktion om at følge eksempler'},
                    {'name': '{default_examples}', 'description': 'Standard eksempler (hvis ingen few-shot)'},
                ],
                'model_settings': {
                    'model': 'gpt-4.1',
                    'temperature': 0.7,
                    'max_tokens': 500
                }
            },
            {
                'name': 'Klassificer Anmeldelser',
                'prompt_type': 'classify_reviews',
                'prompt_text': '''Analyser disse website-sektioner og identificer hvilke der indeholder kundeanmeldelser/testimonials.

{sections_text}

En kundeanmeldelse kendetegnes ved:
- Et kundenavn efterfulgt af en kort tekst om deres oplevelse
- Første-persons perspektiv ("Vi fik...", "Jeg er...", "Vi har brugt...")
- Tilfredshedsudtryk ("Kan varmt anbefales", "Fantastisk service", "Meget tilfreds")
- Ofte korte tekster (1-3 sætninger)
- Kan indeholde stjernerating eller tilfredshedsindikatorer

For HVER sektion der er en anmeldelse, udtræk:
- section_index: Sektionens nummer
- author: Kundens navn (hvis det kan findes i overskriften eller starten af teksten)
- rating: 1-5 (estimér baseret på tonen, default 5 for positive)
- text: Selve anmeldelsesteksten (max 200 tegn)
- platform: "Website" (da det er fra kundens hjemmeside)

Returnér KUN valid JSON i dette format:
{{
    "reviews": [
        {{
            "section_index": 2,
            "author": "Peter Hansen",
            "rating": 5,
            "text": "Fantastisk service og hurtig respons...",
            "platform": "Website"
        }}
    ],
    "review_section_indices": [2, 3, 4]
}}

Hvis ingen sektioner er anmeldelser, returnér:
{{"reviews": [], "review_section_indices": []}}''',
                'placeholders': [
                    {'name': '{sections_text}', 'description': 'Formateret liste af sektioner med index, overskrift og indhold'},
                ],
                'model_settings': {
                    'model': 'gpt-4o-mini',
                    'temperature': 0.1,
                    'max_tokens': 2000
                }
            },
            {
                'name': 'Udtræk USP\'er',
                'prompt_type': 'extract_usps',
                'prompt_text': '''Analysér følgende hjemmesidetekst og udtræk konkrete fakta der kan bruges som USP'er (Unique Selling Points).

HJEMMESIDETEKST:
{website_content}

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
- Returnér kun valid JSON''',
                'placeholders': [
                    {'name': '{website_content}', 'description': 'Hjemmesidetekst (max 5000 tegn)'},
                    {'name': '{templates_text}', 'description': 'Formateret liste af eksisterende USP templates'},
                ],
                'model_settings': {
                    'model': 'gpt-4.1',
                    'temperature': 0.3,
                    'max_tokens': 2000
                }
            },
            {
                'name': 'Detekter Branche og Services',
                'prompt_type': 'detect_services',
                'prompt_text': '''Analysér følgende hjemmesidetekst og find hvilken branche virksomheden tilhører og hvilke services de tilbyder.

HJEMMESIDETEKST:
{content_for_analysis}

TILGÆNGELIGE BRANCHER:
{industry_names}

TILGÆNGELIGE SERVICES (grupperet efter branche):
{services_text}

INSTRUKTIONER:
1. Identificér FØRST hvilken branche virksomheden tilhører baseret på hjemmesideteksten
2. Hvis branchen FINDES i listen, brug PRÆCIS det branchenavn (f.eks. "Elektriker" ikke "El")
3. Hvis branchen IKKE findes i listen, angiv den korrekte branche i "suggested_industry"
4. Find hvilke specifikke services fra listen der matcher
5. Find OGSÅ services der IKKE er i listen men tydeligt tilbydes på hjemmesiden

VIGTIGT OM INDHOLDET:
- Hjemmesideteksten er struktureret med sideveje i formatet "--- /sti ---" eller "[/sti]"
- Brug disse stier til at identificere HVILKEN underside hver service blev fundet på
- Hvis servicen blev fundet på en generel side (fx /vedvarende-energi/) men der ikke er en dedikeret underside, angiv "has_dedicated_page": false

Returnér KUN valid JSON i dette format:
{{
    "detected_services": [
        {{
            "service_id": 15,
            "confidence": 0.95,
            "evidence": "citeret tekst fra hjemmesiden",
            "source_path": "/services/ladestandere/"
        }}
    ],
    "suggested_services": [
        {{
            "name": "Ladestandere",
            "industry": "Elektriker",
            "confidence": 0.9,
            "evidence": "Vi installerer ladestandere til elbiler...",
            "source_path": "/vedvarende-energi/",
            "has_dedicated_page": false
        }}
    ],
    "detected_industries": ["Elektriker"],
    "primary_industry": "Elektriker",
    "suggested_industry": null
}}

VIGTIGT:
- Tilgængelige brancher: {industry_names}
- Hvis virksomhedens branche IKKE er i listen ovenfor:
  - Sæt "detected_industries" til tom liste []
  - Sæt "suggested_industry" til den korrekte branche (f.eks. "Flyttefirma", "Tømrer", "VVS" osv.)
  - Brug "suggested_industry" som industry for suggested_services
- Hvis branchen ER i listen: brug den præcise stavemåde og sæt "suggested_industry" til null
- "detected_services": Services der MATCHER listen (brug service_id)
- "suggested_services": Services der IKKE er i listen men tydeligt tilbydes (brug navn, max 30 tegn)
- Inkludér ALLE services du finder med confidence > 0.7 (ingen begrænsning på antal)
- "source_path": URL-stien hvor servicen blev fundet (fx "/services/varmepumper/")
- "has_dedicated_page": true hvis der findes en dedikeret underside til servicen, false hvis servicen kun nævnes på en generel side
- Returnér kun valid JSON''',
                'placeholders': [
                    {'name': '{content_for_analysis}', 'description': 'Hjemmesidetekst til analyse'},
                    {'name': '{industry_names}', 'description': 'Kommasepareret liste af tilgængelige brancher'},
                    {'name': '{services_text}', 'description': 'Formateret liste af services grupperet efter branche'},
                ],
                'model_settings': {
                    'model': 'gpt-4.1',
                    'temperature': 0.2,
                    'max_tokens': 2000
                }
            },
        ]

        created_count = 0
        updated_count = 0

        for data in prompts_data:
            prompt, created = AIPromptTemplate.objects.update_or_create(
                prompt_type=data['prompt_type'],
                defaults={
                    'name': data['name'],
                    'prompt_text': data['prompt_text'],
                    'placeholders': data['placeholders'],
                    'model_settings': data['model_settings'],
                    'template': data['prompt_text'],  # Legacy field
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {prompt.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated: {prompt.name}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {created_count}, Updated: {updated_count}'
        ))
