"""
Management command til at seede USP data baseret på det kategoriserede USP-ark
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from usps.models import USPMainCategory, USPTemplate, USPCategoryTemplate
from campaigns.models import Industry


class Command(BaseCommand):
    help = 'Seed USP kategorier og templates baseret på det kategoriserede USP-ark'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding USP kategorier og templates...')
        
        with transaction.atomic():
            # 1. Opret hovedkategorier
            self.create_main_categories()
            
            # 2. Opret USP templates for hver kategori
            self.create_usp_templates()
            
            # 3. Opret category template for håndværkere
            self.create_category_template()
            
        self.stdout.write(self.style.SUCCESS('✅ USP seeding completed!'))

    def create_main_categories(self):
        """Opret de 5 hovedkategorier fra USP-arket"""
        
        categories = [
            {
                'name': 'Hurtigt tilbud/hurtig service',
                'description': 'Fokus på hurtig respons og service - den korteste vej fra a til b for kunden',
                'icon': '⚡',
                'color': '#8B5CF6',
                'sort_order': 1,
                'is_recommended_per_campaign': True,
                'max_selections': 1
            },
            {
                'name': 'Anmeldelser',
                'description': 'Sociale beviser og troværdighed gennem anmeldelser og priser',
                'icon': '⭐',
                'color': '#F59E0B',
                'sort_order': 2,
                'is_recommended_per_campaign': True,
                'max_selections': 1
            },
            {
                'name': 'Priser',
                'description': 'Prisgennemsigtighed og konkurrencedygtige priser',
                'icon': '💰',
                'color': '#10B981',
                'sort_order': 3,
                'is_recommended_per_campaign': True,
                'max_selections': 1
            },
            {
                'name': 'Erfaring',
                'description': 'Kompetence og erfaring der skaber tryghed hos kunden',
                'icon': '🎯',
                'color': '#3B82F6',
                'sort_order': 4,
                'is_recommended_per_campaign': True,
                'max_selections': 1
            },
            {
                'name': 'Sikkerhed',
                'description': 'Forsikring, garantier og medlemskaber der skaber tryghed',
                'icon': '🛡️',
                'color': '#EF4444',
                'sort_order': 5,
                'is_recommended_per_campaign': True,
                'max_selections': 1
            }
        ]
        
        for cat_data in categories:
            category, created = USPMainCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'✅ Created category: {category.icon} {category.name}')
            else:
                self.stdout.write(f'⚠️  Category already exists: {category.icon} {category.name}')

    def create_usp_templates(self):
        """Opret USP templates baseret på det prioriterede USP-ark"""
        
        # Hent kategorier
        hurtig_service = USPMainCategory.objects.get(name='Hurtigt tilbud/hurtig service')
        anmeldelser = USPMainCategory.objects.get(name='Anmeldelser')
        priser = USPMainCategory.objects.get(name='Priser')
        erfaring = USPMainCategory.objects.get(name='Erfaring')
        sikkerhed = USPMainCategory.objects.get(name='Sikkerhed')
        
        # Hent industrier for targeting
        elektriker, _ = Industry.objects.get_or_create(name='Elektriker')
        vvs, _ = Industry.objects.get_or_create(name='VVS')
        maler, _ = Industry.objects.get_or_create(name='Maler')
        
        # USP templates data
        usp_templates = [
            # Hurtigt tilbud/hurtig service
            {
                'category': hurtig_service,
                'priority': 1,
                'text': 'Ring og få et prisoverslag direkte i telefonen',
                'explanation': 'Den korteste vej fra a - b for kunden, og giver super god mening, hvis man har et produkt der er let at udregne prisen på og en fantastisk måde for virksomheden at vurdere om det er en kunde der har finanserne',
                'use_cases': ['let_at_udregne', 'telefon_vurdering'],
                'industries': [elektriker, vvs, maler],
                'headlines': ['Ring nu - få pris på 2 min', '{SERVICE} priser i telefon', 'Pris direkte over telefon'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                # New headline variations (max 30 chars each)
                'short_headlines': ['Ring nu - få pris', 'Pris i telefonen', 'Ring for tilbud', 'Hurtig prisoverslag'],
                'best_for_headline': 'Ring nu - få pris',
                'best_for_description': 'Ring og få et prisoverslag direkte i telefonen - den korteste vej fra a til b'
            },
            {
                'category': hurtig_service,
                'priority': 2,
                'text': 'Vi kan være hos dig inden for 1-2 timer',
                'explanation': 'Ideel ved ex. vagtudkald',
                'use_cases': ['vagtudkald', 'akut_service'],
                'industries': [vvs, elektriker],
                'headlines': ['Hos dig på 1-2 timer', 'Hurtig service {BYNAVN}', 'Akut {SERVICE} service'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['Hos dig på 1-2 timer', 'Akut service', 'Hurtig respons', 'Service på rekordtid'],
                'best_for_headline': 'Hos dig på 1-2 timer',
                'best_for_description': 'Vi kan være hos dig inden for 1-2 timer - perfekt til akut service og vagtudkald'
            },
            {
                'category': hurtig_service,
                'priority': 3,
                'text': 'Modtag et tilbud der holder inden for 2-24 timer',
                'explanation': 'Højere end 24 timer bør vi evt. søge en alternativ usp',
                'use_cases': ['tilbud_service', 'standard_respons'],
                'industries': [],
                'headlines': ['Tilbud på 24 timer', 'Hurtig tilbuds service', 'Fast respons {BYNAVN}'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['Tilbud på 24 timer', 'Fast respons', 'Hurtig service', 'Tilbud inden 24t'],
                'best_for_headline': 'Tilbud på 24 timer',
                'best_for_description': 'Modtag et tilbud der holder inden for 2-24 timer - fast respons garanteret'
            },
            
            # Anmeldelser
            {
                'category': anmeldelser,
                'priority': 1,
                'text': 'Vinder af Årets Håndværker 2024',
                'explanation': 'Stærkeste sociale bevis for ekspertise',
                'use_cases': ['pris_vinder', 'ekspertise_bevis'],
                'industries': [],
                'headlines': ['Årets Håndværker 2024', 'Prisvindende {SERVICE}', 'Anerkendt ekspertise'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['Årets Håndværker 2024', 'Prisvinder', 'Anerkendt ekspert', 'Kvalitetsgaranti'],
                'best_for_headline': 'Årets Håndværker 2024',
                'best_for_description': 'Vinder af Årets Håndværker 2024 - anerkendt ekspertise og kvalitet'
            },
            {
                'category': anmeldelser,
                'priority': 2,
                'text': '4,8/5 på Trustpilot',
                'explanation': 'Eller en hvilken som helst anden platform med høj score',
                'use_cases': ['høj_rating', 'trustpilot'],
                'industries': [],
                'headlines': ['4,8/5 stjerner', 'Topbedømt {SERVICE}', 'Høj kundetilfredshed'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['4,8/5 stjerner', 'Topbedømt', 'Høje ratings', '4,8 på Trustpilot'],
                'best_for_headline': '4,8/5 stjerner',
                'best_for_description': '4,8/5 på Trustpilot - dokumenteret høj kundetilfredshed og kvalitet'
            },
            {
                'category': anmeldelser,
                'priority': 3,
                'text': 'Vi har kun 5 Stjernede bedømmelser',
                'explanation': 'Ideel hvis kunden har for få anmeldelser på Trustpilot til at have +4,6 eller meget få bedømmelser, men kun 5 stjernede',
                'use_cases': ['perfekte_ratings', 'få_anmeldelser'],
                'industries': [],
                'headlines': ['Kun 5 stjerner', 'Perfekte anmeldelser', '100% tilfredse kunder'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['Kun 5 stjerner', 'Perfekte ratings', '100% tilfredse', 'Topbedømte'],
                'best_for_headline': 'Kun 5 stjerner',
                'best_for_description': 'Vi har kun 5 stjernede bedømmelser - 100% tilfredse kunder og perfekt service'
            },
            
            # Priser
            {
                'category': priser,
                'priority': 1,
                'text': 'Priser fra kun 4999',
                'explanation': 'Ideel hvis kunden har en relativt fornuftig fra pris eksempler kunne være frapris på et vagtudkald, pris på udskiftning af en eltavle, fastpris på maling af en lejlighed',
                'use_cases': ['fastpris', 'fra_pris', 'gennemsigtig_pris'],
                'industries': [elektriker],
                'headlines': ['Fra kun 4999 kr', 'Konkurrencedygtige priser', 'Gennemsigtige priser'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['Fra kun 4999 kr', 'Lave priser', 'Fra 4999,-', 'Skarp pris'],
                'best_for_headline': 'Fra kun 4999 kr',
                'best_for_description': 'Priser fra kun 4999 kr - konkurrencedygtige og gennemsigtige priser'
            },
            {
                'category': priser,
                'priority': 2,
                'text': 'Prisgaranti på {SERVICE}',
                'explanation': 'Denne er generelt brugt alt for lidt, specielt hvis man er i en branche hvor der er mange variabler til ens priser',
                'use_cases': ['prisgaranti', 'konkurrence_match'],
                'industries': [],
                'headlines': ['Prisgaranti', 'Matcher konkurrenter', 'Bedste pris garanti'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['Prisgaranti', 'Bedste pris', 'Matcher priser', 'Pris garanti'],
                'best_for_headline': 'Prisgaranti',
                'best_for_description': 'Prisgaranti - vi matcher konkurrenternes priser og sikrer dig den bedste pris'
            },
            
            # Erfaring
            {
                'category': erfaring,
                'priority': 1,
                'text': '+15 års erfaring',
                'explanation': 'Den absolut nemmeste og selvfølgeligt også mest kedelige hvis ikke man har +100 års erfaring',
                'use_cases': ['lang_erfaring', 'ekspertise'],
                'industries': [],
                'headlines': ['+15 års erfaring', 'Erfaren {SERVICE}', 'Mange års ekspertise'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['+15 års erfaring', 'Erfaren', 'Lang erfaring', '15+ års ekspertise'],
                'best_for_headline': '+15 års erfaring',
                'best_for_description': '+15 års erfaring - dokumenteret ekspertise og mange års praksis'
            },
            {
                'category': erfaring,
                'priority': 2,
                'text': '+10.000 løste opgaver',
                'explanation': 'Vil ofte være meget skarpere og selvfølgeligt være understøttet af ovenstående',
                'use_cases': ['mange_opgaver', 'dokumenteret_erfaring'],
                'industries': [],
                'headlines': ['+10.000 opgaver løst', 'Bredt erfaring', 'Dokumenteret ekspertise'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['+10.000 opgaver', 'Mange opgaver løst', 'Bred erfaring', '10k+ jobs'],
                'best_for_headline': '+10.000 opgaver',
                'best_for_description': '+10.000 løste opgaver - dokumenteret erfaring og bred ekspertise'
            },
            
            # Sikkerhed
            {
                'category': sikkerhed,
                'priority': 1,
                'text': 'Medlem af byg garantiordning',
                'explanation': 'Tekniq, Dansk Byggeri osv. noter gerne, at disse garantiordninger dækker op til ex. 150.000,- kroner ved fejl og mangler',
                'use_cases': ['garantiordning', 'byggegaranti'],
                'industries': [],
                'headlines': ['Byg garantiordning', 'Fuld garanti', 'Sikker investering'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['Byg garanti', 'Fuld garanti', 'Sikker job', 'Garantiordning'],
                'best_for_headline': 'Byg garanti',
                'best_for_description': 'Medlem af byg garantiordning - din sikkerhed og garanti ved alle opgaver'
            },
            {
                'category': sikkerhed,
                'priority': 2,
                'text': 'Forsikret hos Tryg der dækker op til 10.000.000',
                'explanation': 'Langt de fleste håndværksvirksomheder, har selvom de ikke er medlem af en garantiordning, en forsikring med tæt på ubegrænset dækning',
                'use_cases': ['høj_forsikring', 'tryg_forsikring'],
                'industries': [],
                'headlines': ['10 mio. forsikring', 'Fuld dækning', 'Tryg hos Tryg'],
                'placeholders': ['{SERVICE}', '{BYNAVN}'],
                'short_headlines': ['10 mio. forsikring', 'Fuld dækning', 'Tryg forsikret', '10M dækning'],
                'best_for_headline': '10 mio. forsikring',
                'best_for_description': 'Forsikret hos Tryg med dækning op til 10 millioner - fuld sikkerhed for alle opgaver'
            }
        ]
        
        # Opret USP templates
        for usp_data in usp_templates:
            defaults = {
                'text': usp_data['text'],
                'explanation': usp_data['explanation'],
                'use_cases': usp_data['use_cases'],
                'example_headlines': usp_data['headlines'],
                'placeholders_used': usp_data['placeholders'],
                'effectiveness_score': 0.8,  # Højt score som standard
                'is_active': True
            }
            
            # Add headline variations if present
            if 'short_headlines' in usp_data:
                defaults['short_headlines'] = usp_data['short_headlines']
            if 'best_for_headline' in usp_data:
                defaults['best_for_headline'] = usp_data['best_for_headline']
            if 'best_for_description' in usp_data:
                defaults['best_for_description'] = usp_data['best_for_description']
            
            usp, created = USPTemplate.objects.get_or_create(
                main_category=usp_data['category'],
                priority_rank=usp_data['priority'],
                defaults=defaults
            )
            
            if created:
                # Tilføj industrier
                if usp_data['industries']:
                    usp.ideal_for_industries.set(usp_data['industries'])
                    
                self.stdout.write(f'✅ Created USP: [{usp.priority_rank}] {usp.text[:50]}...')
            else:
                self.stdout.write(f'⚠️  USP already exists: [{usp.priority_rank}] {usp.text[:50]}...')

    def create_category_template(self):
        """Opret template for håndværkere"""
        
        template_data = {
            'name': 'Håndværker Standard 5-Pack',
            'description': 'Standard USP kategorier optimeret til håndværksbranchen',
            'auto_populate_usps': True,
            'category_data': [
                {
                    'name': 'Hurtigt tilbud/hurtig service',
                    'icon': '⚡',
                    'color': '#8B5CF6',
                    'sort_order': 1,
                    'max_selections': 1
                },
                {
                    'name': 'Anmeldelser',
                    'icon': '⭐',
                    'color': '#F59E0B',
                    'sort_order': 2,
                    'max_selections': 1
                },
                {
                    'name': 'Priser',
                    'icon': '💰',
                    'color': '#10B981',
                    'sort_order': 3,
                    'max_selections': 1
                },
                {
                    'name': 'Erfaring',
                    'icon': '🎯',
                    'color': '#3B82F6',
                    'sort_order': 4,
                    'max_selections': 1
                },
                {
                    'name': 'Sikkerhed',
                    'icon': '🛡️',
                    'color': '#EF4444',
                    'sort_order': 5,
                    'max_selections': 1
                }
            ]
        }
        
        template, created = USPCategoryTemplate.objects.get_or_create(
            name=template_data['name'],
            defaults=template_data
        )
        
        if created:
            self.stdout.write(f'✅ Created template: {template.name}')
        else:
            self.stdout.write(f'⚠️  Template already exists: {template.name}')