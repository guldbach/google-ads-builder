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
