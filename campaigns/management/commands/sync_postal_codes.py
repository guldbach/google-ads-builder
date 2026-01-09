"""
Management command til at synkronisere postnumre fra DAWA API.
Opretter/opdaterer PostalCode records i databasen.

Brug:
    python manage.py sync_postal_codes
    python manage.py sync_postal_codes --force  # Overskriver eksisterende dawa_name
"""
import requests
from django.core.management.base import BaseCommand
from campaigns.models import PostalCode


class Command(BaseCommand):
    help = 'Synkroniser postnumre fra DAWA API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overskriver eksisterende DAWA-navne (men ikke display_name eller additional_names)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Henter postnumre fra DAWA API...')

        try:
            response = requests.get(
                'https://dawa.aws.dk/postnumre',
                params={'format': 'json'},
                timeout=30
            )
            response.raise_for_status()
            postal_data = response.json()
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f'Fejl ved hentning fra DAWA: {e}'))
            return

        self.stdout.write(f'Fandt {len(postal_data)} postnumre')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for item in postal_data:
            code = item.get('nr')
            dawa_name = item.get('navn')

            if not code or not dawa_name:
                continue

            postal, created = PostalCode.objects.get_or_create(
                code=code,
                defaults={'dawa_name': dawa_name}
            )

            if created:
                created_count += 1
                self.stdout.write(f'  + {code} {dawa_name}')
            elif options['force'] or not postal.dawa_name:
                # Opdater kun dawa_name, behold display_name og additional_names
                postal.dawa_name = dawa_name
                postal.save(update_fields=['dawa_name', 'updated_at'])
                updated_count += 1
                self.stdout.write(f'  ~ {code} {dawa_name}')
            else:
                skipped_count += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Synkronisering færdig: {created_count} oprettet, '
            f'{updated_count} opdateret, {skipped_count} uændret'
        ))
        self.stdout.write(f'Total: {PostalCode.objects.count()} postnumre i databasen')
