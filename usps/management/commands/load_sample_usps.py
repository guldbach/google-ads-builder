from django.core.management.base import BaseCommand
from campaigns.models import Industry
from usps.models import USPCategory, USPTemplate, IndustryUSPPattern


class Command(BaseCommand):
    help = 'Load sample USP templates and patterns'

    def handle(self, *args, **options):
        self.stdout.write("Loading sample USP data...")
        
        # Create industries
        industries = {
            'kloakservice': Industry.objects.get_or_create(
                name='Kloakservice',
                defaults={'description': 'Kloakservice og afløbsreparationer'}
            )[0],
            'vvs': Industry.objects.get_or_create(
                name='VVS',
                defaults={'description': 'VVS installatører og reparationer'}
            )[0],
            'elektriker': Industry.objects.get_or_create(
                name='Elektriker',
                defaults={'description': 'El-installatører og el-reparationer'}
            )[0],
            'tømrer': Industry.objects.get_or_create(
                name='Tømrer',
                defaults={'description': 'Tømrerarbejde og byggeri'}
            )[0],
        }
        
        # Create USP categories
        categories = {
            'hastighed': USPCategory.objects.get_or_create(
                name='Hastighed',
                defaults={'description': 'USPs relateret til hurtig service'}
            )[0],
            'tilgængelighed': USPCategory.objects.get_or_create(
                name='Tilgængelighed',
                defaults={'description': 'USPs om tilgængelighed og åbningstider'}
            )[0],
            'erfaring': USPCategory.objects.get_or_create(
                name='Erfaring',
                defaults={'description': 'USPs om erfaring og ekspertise'}
            )[0],
            'garanti': USPCategory.objects.get_or_create(
                name='Garanti',
                defaults={'description': 'USPs om garanti og kvalitet'}
            )[0],
            'pris': USPCategory.objects.get_or_create(
                name='Pris',
                defaults={'description': 'USPs om priser og gratis services'}
            )[0],
            'lokalt': USPCategory.objects.get_or_create(
                name='Lokalt',
                defaults={'description': 'USPs om lokal service'}
            )[0],
        }
        
        # USP Templates for Kloakservice
        kloakservice_usps = [
            # Hastighed
            {
                'text': 'Akut service inden for 1-2 timer',
                'category': categories['hastighed'],
                'industry': industries['kloakservice'],
                'urgency_level': 'critical',
                'keywords': 'akut, 1-2 timer, hurtig, øjeblikkelig',
                'effectiveness_score': 0.9
            },
            {
                'text': 'Samme dag service',
                'category': categories['hastighed'],
                'industry': industries['kloakservice'],
                'urgency_level': 'high',
                'keywords': 'samme dag, i dag, med det samme',
                'effectiveness_score': 0.8
            },
            # Tilgængelighed
            {
                'text': 'Døgnvagt året rundt',
                'category': categories['tilgængelighed'],
                'industry': industries['kloakservice'],
                'urgency_level': 'critical',
                'keywords': '24/7, døgnvagt, altid åben, hele året',
                'effectiveness_score': 0.9
            },
            {
                'text': 'Weekend og helligdage',
                'category': categories['tilgængelighed'],
                'industry': industries['kloakservice'],
                'urgency_level': 'medium',
                'keywords': 'weekend, helligdage, lørdag, søndag',
                'effectiveness_score': 0.7
            },
            # Erfaring
            {
                'text': 'Over 25 års erfaring',
                'category': categories['erfaring'],
                'industry': industries['kloakservice'],
                'urgency_level': 'medium',
                'keywords': '25 år, erfaring, specialist, ekspert',
                'effectiveness_score': 0.6
            },
            # Garanti
            {
                'text': '2 års garanti på alt arbejde',
                'category': categories['garanti'],
                'industry': industries['kloakservice'],
                'urgency_level': 'medium',
                'keywords': 'garanti, 2 år, kvalitet, sikkerhed',
                'effectiveness_score': 0.7
            },
            # Pris
            {
                'text': 'Gratis besigtigelse og tilbud',
                'category': categories['pris'],
                'industry': industries['kloakservice'],
                'urgency_level': 'low',
                'keywords': 'gratis, besigtigelse, tilbud, uden omkostninger',
                'effectiveness_score': 0.6
            },
            {
                'text': 'Fast pris - ingen overraskelser',
                'category': categories['pris'],
                'industry': industries['kloakservice'],
                'urgency_level': 'medium',
                'keywords': 'fast pris, ingen overraskelser, forudsigeligt',
                'effectiveness_score': 0.7
            },
            # Lokalt
            {
                'text': 'Lokal kloakmester i dit område',
                'category': categories['lokalt'],
                'industry': industries['kloakservice'],
                'urgency_level': 'medium',
                'keywords': 'lokal, dit område, i nærheden, lokalt',
                'effectiveness_score': 0.6
            },
        ]
        
        # Create USP templates
        for usp_data in kloakservice_usps:
            usp, created = USPTemplate.objects.get_or_create(
                text=usp_data['text'],
                defaults=usp_data
            )
            if created:
                self.stdout.write(f"Created USP: {usp.text}")
        
        # Industry USP patterns for Kloakservice
        kloakservice_patterns = [
            {
                'pattern': r'(\d+)\s*(år|years?)\s*(erfaring|experience)',
                'description': 'Captures years of experience',
                'weight': 0.8,
                'examples': '25 års erfaring, 10 years experience'
            },
            {
                'pattern': r'(døgnvagt|24/7|24\s*timer|altid\s*åben)',
                'description': 'Captures 24/7 availability',
                'weight': 0.9,
                'examples': 'døgnvagt, 24/7, 24 timer, altid åben'
            },
            {
                'pattern': r'(hurtig|lynhurtig|samme\s*dag|øjeblikkelig|akut)',
                'description': 'Captures speed-related USPs',
                'weight': 0.8,
                'examples': 'hurtig service, samme dag, akut hjælp'
            },
            {
                'pattern': r'(gratis|uden\s*omkostninger|ingen\s*betaling)',
                'description': 'Captures free services',
                'weight': 0.7,
                'examples': 'gratis besigtigelse, uden omkostninger'
            },
            {
                'pattern': r'(\d+)\s*(års?)?\s*garanti',
                'description': 'Captures warranty information',
                'weight': 0.7,
                'examples': '2 års garanti, 5 år garanti'
            },
            {
                'pattern': r'(certificeret|autoriseret|godkendt|kvalificeret)',
                'description': 'Captures certifications',
                'weight': 0.6,
                'examples': 'certificeret, autoriseret installatør'
            },
            {
                'pattern': r'(lokal|i\s*nærheden|dit\s*område|lokalt)',
                'description': 'Captures local service',
                'weight': 0.6,
                'examples': 'lokal service, i nærheden, dit område'
            },
        ]
        
        # Create industry patterns
        for pattern_data in kloakservice_patterns:
            pattern, created = IndustryUSPPattern.objects.get_or_create(
                industry=industries['kloakservice'],
                pattern=pattern_data['pattern'],
                defaults=pattern_data
            )
            if created:
                self.stdout.write(f"Created pattern: {pattern.pattern}")
        
        # Add some generic USPs for other industries
        generic_usps = [
            {
                'text': 'Professionel service',
                'category': categories['erfaring'],
                'industry': None,  # Generic
                'urgency_level': 'medium',
                'keywords': 'professionel, kvalitet, ekspert',
                'effectiveness_score': 0.5
            },
            {
                'text': 'Konkurrencedygtige priser',
                'category': categories['pris'],
                'industry': None,
                'urgency_level': 'low',
                'keywords': 'konkurrencedygtig, billige priser, gode priser',
                'effectiveness_score': 0.5
            },
        ]
        
        for usp_data in generic_usps:
            usp, created = USPTemplate.objects.get_or_create(
                text=usp_data['text'],
                defaults=usp_data
            )
            if created:
                self.stdout.write(f"Created generic USP: {usp.text}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded sample USP data!\n'
                f'Industries: {len(industries)}\n'
                f'Categories: {len(categories)}\n'
                f'USP Templates: {USPTemplate.objects.count()}\n'
                f'Industry Patterns: {IndustryUSPPattern.objects.count()}'
            )
        )