"""
Management command til at oprette demo kampagner til test af eksport funktionalitet
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from campaigns.models import Industry, Client, Campaign, AdGroup, Keyword, Ad


class Command(BaseCommand):
    help = 'Opretter demo kampagner til test af eksport funktionalitet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Slet eksisterende demo data før oprettelse',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('Sletter eksisterende demo data...')
            Campaign.objects.filter(name__contains='Demo').delete()
            Client.objects.filter(name__contains='Demo').delete()

        # Opret demo industry hvis den ikke findes
        industry, created = Industry.objects.get_or_create(
            name='VVS/Rørarbejde',
            defaults={'description': 'VVS, rørarbejde og sanitetsinstallationer'}
        )
        if created:
            self.stdout.write(f'Oprettede industry: {industry.name}')

        # Opret demo user hvis der ikke findes nogen
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='demo',
                email='demo@example.com',
                password='demo123'
            )
            self.stdout.write('Oprettede demo user')

        # Opret demo client
        client, created = Client.objects.get_or_create(
            name='Demo Hansen VVS',
            website_url='https://www.hansen-vvs.dk',
            defaults={
                'industry': industry,
                'description': 'Demo VVS virksomhed til test',
                'created_by': user
            }
        )
        if created:
            self.stdout.write(f'Oprettede client: {client.name}')

        # Opret demo kampagne
        campaign, created = Campaign.objects.get_or_create(
            name='Demo - Hansen VVS Search Kampagne',
            client=client,
            defaults={
                'campaign_type': 'search',
                'budget_daily': 750.00,
                'target_location': 'København, Danmark',
                'target_language': 'da',
                'status': 'draft'
            }
        )
        if created:
            self.stdout.write(f'Oprettede kampagne: {campaign.name}')
        else:
            # Slet eksisterende ad groups for at starte forfra
            AdGroup.objects.filter(campaign=campaign).delete()

        # Opret ad groups med keywords og ads
        self.create_brand_ad_group(campaign)
        self.create_service_ad_group(campaign) 
        self.create_location_ad_group(campaign)

        self.stdout.write(
            self.style.SUCCESS(
                f'Demo kampagne oprettet succesfuldt!\n'
                f'Kampagne ID: {campaign.id}\n'
                f'Du kan nu teste eksport på: /campaigns/export/{campaign.id}/'
            )
        )

    def create_brand_ad_group(self, campaign):
        """Opret brand ad group"""
        ad_group = AdGroup.objects.create(
            name="Brand Keywords",
            campaign=campaign,
            default_cpc=8.00,
            priority_score=100
        )

        # Brand keywords
        brand_keywords = [
            ('hansen vvs', 'exact', 8.00),
            ('hansen vvs københavn', 'exact', 10.00),
            ('"hansen vvs"', 'phrase', 12.00),
        ]

        for keyword_text, match_type, cpc in brand_keywords:
            Keyword.objects.create(
                text=keyword_text,
                ad_group=ad_group,
                match_type=match_type,
                max_cpc=cpc
            )

        # Brand ad
        Ad.objects.create(
            ad_group=ad_group,
            headline_1="Hansen VVS",
            headline_2="Professionel VVS service", 
            headline_3="København",
            description_1="25 års erfaring med VVS og rørarbejde - Ring i dag for gratis tilbud!",
            description_2="Certificerede VVS installatører - Hurtig og pålidelig service",
            final_url="https://www.hansen-vvs.dk",
            display_path_1="vvs",
            display_path_2="koebenhavn"
        )

        self.stdout.write(f'Oprettede brand ad group med {len(brand_keywords)} keywords')

    def create_service_ad_group(self, campaign):
        """Opret service ad group"""
        ad_group = AdGroup.objects.create(
            name="VVS Services",
            campaign=campaign, 
            default_cpc=15.00,
            priority_score=90
        )

        # Service keywords
        service_keywords = [
            ('vvs rørarbejde', 'phrase', 15.00),
            ('badeværelse renovering', 'phrase', 18.00),
            ('varmepumpe installation', 'phrase', 20.00),
            ('toilet reparation', 'phrase', 12.00),
            ('radiator udskiftning', 'phrase', 14.00),
            ('køkken vvs', 'phrase', 16.00),
            ('vvs service københavn', 'phrase', 19.00),
            ('akut vvs', 'broad', 25.00),
        ]

        for keyword_text, match_type, cpc in service_keywords:
            Keyword.objects.create(
                text=keyword_text,
                ad_group=ad_group,
                match_type=match_type,
                max_cpc=cpc
            )

        # Service ad
        Ad.objects.create(
            ad_group=ad_group,
            headline_1="VVS Rørarbejde København",
            headline_2="Samme dag service",
            headline_3="Certificerede installatører",
            description_1="Alt i VVS og rørarbejde - Badeværelse, køkken, varmepumper. Ring nu!",
            description_2="Gratis tilbud og 2 års garanti på alt arbejde",
            final_url="https://www.hansen-vvs.dk/services",
            display_path_1="services",
            display_path_2="vvs"
        )

        self.stdout.write(f'Oprettede service ad group med {len(service_keywords)} keywords')

    def create_location_ad_group(self, campaign):
        """Opret lokations ad group"""
        ad_group = AdGroup.objects.create(
            name="København Områder",
            campaign=campaign,
            default_cpc=13.00,
            priority_score=80
        )

        # Location keywords
        location_keywords = [
            ('vvs østerbro', 'phrase', 16.00),
            ('vvs nørrebro', 'phrase', 15.00),
            ('vvs vesterbro', 'phrase', 15.00),
            ('vvs amager', 'phrase', 14.00),
            ('vvs frederiksberg', 'phrase', 17.00),
            ('vvs valby', 'phrase', 13.00),
            ('vvs søborg', 'phrase', 13.00),
        ]

        for keyword_text, match_type, cpc in location_keywords:
            Keyword.objects.create(
                text=keyword_text,
                ad_group=ad_group,
                match_type=match_type,
                max_cpc=cpc
            )

        # Location ad
        Ad.objects.create(
            ad_group=ad_group,
            headline_1="VVS service i København",
            headline_2="Alle bydele dækket",
            headline_3="Hansen VVS",
            description_1="Vi dækker alle Københavns bydele - Hurtig udkald og fair priser!",
            description_2="Østerbro, Nørrebro, Vesterbro, Amager, Frederiksberg m.fl.",
            final_url="https://www.hansen-vvs.dk/omraader",
            display_path_1="omraader", 
            display_path_2="koebenhavn"
        )

        self.stdout.write(f'Oprettede location ad group med {len(location_keywords)} keywords')