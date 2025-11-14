"""
Management command to update existing USP templates with headline variations
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from usps.models import USPMainCategory, USPTemplate


class Command(BaseCommand):
    help = 'Update existing USP templates with headline variations'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Updating USP templates with headline variations...')
        
        with transaction.atomic():
            self.update_usp_headlines()
            
        self.stdout.write(self.style.SUCCESS('✅ USP headline updates completed!'))

    def update_usp_headlines(self):
        """Update existing USP templates with headline variations"""
        
        # Get categories
        hurtig_service = USPMainCategory.objects.get(name='Hurtigt tilbud/hurtig service')
        anmeldelser = USPMainCategory.objects.get(name='Anmeldelser')
        priser = USPMainCategory.objects.get(name='Priser')
        erfaring = USPMainCategory.objects.get(name='Erfaring')
        sikkerhed = USPMainCategory.objects.get(name='Sikkerhed')
        
        # Headline data for each USP
        headline_updates = [
            # Hurtigt tilbud/hurtig service
            {
                'category': hurtig_service,
                'priority': 1,
                'text': 'Ring og få et prisoverslag direkte i telefonen',
                'short_headlines': ['Ring nu - få pris', 'Pris i telefonen', 'Ring for tilbud', 'Hurtig prisoverslag'],
                'best_for_headline': 'Ring nu - få pris',
                'best_for_description': 'Ring og få et prisoverslag direkte i telefonen - den korteste vej fra a til b'
            },
            {
                'category': hurtig_service,
                'priority': 2,
                'text': 'Vi kan være hos dig inden for 1-2 timer',
                'short_headlines': ['Hos dig på 1-2 timer', 'Akut service', 'Hurtig respons', 'Service på rekordtid'],
                'best_for_headline': 'Hos dig på 1-2 timer',
                'best_for_description': 'Vi kan være hos dig inden for 1-2 timer - perfekt til akut service og vagtudkald'
            },
            {
                'category': hurtig_service,
                'priority': 3,
                'text': 'Modtag et tilbud der holder inden for 2-24 timer',
                'short_headlines': ['Tilbud på 24 timer', 'Fast respons', 'Hurtig service', 'Tilbud inden 24t'],
                'best_for_headline': 'Tilbud på 24 timer',
                'best_for_description': 'Modtag et tilbud der holder inden for 2-24 timer - fast respons garanteret'
            },
            
            # Anmeldelser
            {
                'category': anmeldelser,
                'priority': 1,
                'text': 'Vinder af Årets Håndværker 2024',
                'short_headlines': ['Årets Håndværker 2024', 'Prisvinder', 'Anerkendt ekspert', 'Kvalitetsgaranti'],
                'best_for_headline': 'Årets Håndværker 2024',
                'best_for_description': 'Vinder af Årets Håndværker 2024 - anerkendt ekspertise og kvalitet'
            },
            {
                'category': anmeldelser,
                'priority': 2,
                'text': '4,8/5 på Trustpilot',
                'short_headlines': ['4,8/5 stjerner', 'Topbedømt', 'Høje ratings', '4,8 på Trustpilot'],
                'best_for_headline': '4,8/5 stjerner',
                'best_for_description': '4,8/5 på Trustpilot - dokumenteret høj kundetilfredshed og kvalitet'
            },
            {
                'category': anmeldelser,
                'priority': 3,
                'text': 'Vi har kun 5 Stjernede bedømmelser',
                'short_headlines': ['Kun 5 stjerner', 'Perfekte ratings', '100% tilfredse', 'Topbedømte'],
                'best_for_headline': 'Kun 5 stjerner',
                'best_for_description': 'Vi har kun 5 stjernede bedømmelser - 100% tilfredse kunder og perfekt service'
            },
            
            # Priser
            {
                'category': priser,
                'priority': 1,
                'text': 'Priser fra kun 4999',
                'short_headlines': ['Fra kun 4999 kr', 'Lave priser', 'Fra 4999,-', 'Skarp pris'],
                'best_for_headline': 'Fra kun 4999 kr',
                'best_for_description': 'Priser fra kun 4999 kr - konkurrencedygtige og gennemsigtige priser'
            },
            {
                'category': priser,
                'priority': 2,
                'text': 'Prisgaranti på {SERVICE}',
                'short_headlines': ['Prisgaranti', 'Bedste pris', 'Matcher priser', 'Pris garanti'],
                'best_for_headline': 'Prisgaranti',
                'best_for_description': 'Prisgaranti - vi matcher konkurrenternes priser og sikrer dig den bedste pris'
            },
            
            # Erfaring
            {
                'category': erfaring,
                'priority': 1,
                'text': '+15 års erfaring',
                'short_headlines': ['+15 års erfaring', 'Erfaren', 'Lang erfaring', '15+ års ekspertise'],
                'best_for_headline': '+15 års erfaring',
                'best_for_description': '+15 års erfaring - dokumenteret ekspertise og mange års praksis'
            },
            {
                'category': erfaring,
                'priority': 2,
                'text': '+10.000 løste opgaver',
                'short_headlines': ['+10.000 opgaver', 'Mange opgaver løst', 'Bred erfaring', '10k+ jobs'],
                'best_for_headline': '+10.000 opgaver',
                'best_for_description': '+10.000 løste opgaver - dokumenteret erfaring og bred ekspertise'
            },
            
            # Sikkerhed
            {
                'category': sikkerhed,
                'priority': 1,
                'text': 'Medlem af byg garantiordning',
                'short_headlines': ['Byg garanti', 'Fuld garanti', 'Sikker job', 'Garantiordning'],
                'best_for_headline': 'Byg garanti',
                'best_for_description': 'Medlem af byg garantiordning - din sikkerhed og garanti ved alle opgaver'
            },
            {
                'category': sikkerhed,
                'priority': 2,
                'text': 'Forsikret hos Tryg der dækker op til 10.000.000',
                'short_headlines': ['10 mio. forsikring', 'Fuld dækning', 'Tryg forsikret', '10M dækning'],
                'best_for_headline': '10 mio. forsikring',
                'best_for_description': 'Forsikret hos Tryg med dækning op til 10 millioner - fuld sikkerhed for alle opgaver'
            }
        ]
        
        # Update each USP template
        for update_data in headline_updates:
            try:
                usp = USPTemplate.objects.get(
                    main_category=update_data['category'],
                    priority_rank=update_data['priority']
                )
                
                usp.short_headlines = update_data['short_headlines']
                usp.best_for_headline = update_data['best_for_headline']
                usp.best_for_description = update_data['best_for_description']
                usp.save()
                
                self.stdout.write(f'✅ Updated: [{usp.priority_rank}] {usp.text[:50]}...')
                
            except USPTemplate.DoesNotExist:
                self.stdout.write(f'⚠️  USP not found: {update_data["text"][:50]}...')