"""
Management command to populate postal codes for existing DanishCity records.
Uses the same logic as suggest_postal_code_ajax to find matching postal codes.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from campaigns.models import DanishCity, PostalCode


class Command(BaseCommand):
    help = 'Populate postal codes for DanishCity records that are missing them'

    # Cities with consolidated postal codes (multiple postal codes per city)
    MULTI_POSTAL_CITIES = ['københavn', 'frederiksberg', 'vesterbro']

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update all records, even those with existing postal codes',
        )

    def find_postal_matches(self, city_name):
        """Find all PostalCode records that match the given city name."""
        matching_postals = []
        name_lower = city_name.lower()

        # Search in dawa_name (exact match, case-insensitive)
        for postal in PostalCode.objects.filter(dawa_name__iexact=city_name):
            matching_postals.append(postal)

        # Search in display_name (exact match, case-insensitive)
        for postal in PostalCode.objects.filter(display_name__iexact=city_name):
            if postal not in matching_postals:
                matching_postals.append(postal)

        # Search in additional_names (contains, case-insensitive)
        for postal in PostalCode.objects.filter(additional_names__icontains=city_name):
            # Verify exact match in the comma-separated list
            additional = postal.get_additional_names_list()
            if any(name.lower() == name_lower for name in additional):
                if postal not in matching_postals:
                    matching_postals.append(postal)

        return matching_postals

    def calculate_region_average(self, region):
        """Calculate average postal code for a region based on existing cities."""
        existing_codes = list(
            region.cities
            .exclude(postal_code='')
            .exclude(postal_code='MULTI')
            .values_list('postal_code', flat=True)
        )

        if not existing_codes:
            return None

        numeric_codes = [int(c) for c in existing_codes if c.isdigit() and len(c) == 4]
        if not numeric_codes:
            return None

        return sum(numeric_codes) / len(numeric_codes)

    def find_closest_match(self, matches, avg):
        """Find the postal code closest to the average."""
        if not matches or avg is None:
            return matches[0] if matches else None

        return min(matches, key=lambda p: abs(int(p.code) - avg))

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes will be made\n'))

        # Get cities to process
        if force:
            cities = DanishCity.objects.all()
            self.stdout.write(f'Processing ALL {cities.count()} DanishCity records (--force)\n')
        else:
            cities = DanishCity.objects.filter(Q(postal_code='') | Q(postal_code__isnull=True))
            self.stdout.write(f'Processing {cities.count()} DanishCity records with empty postal_code\n')

        # Statistics
        stats = {
            'single_match': 0,
            'multi_postal': 0,
            'closest_match': 0,
            'no_match': 0,
            'skipped': 0,
        }

        for city in cities:
            city_name_lower = city.city_name.lower()

            # Check if this is a multi-postal city (København, Frederiksberg, Vesterbro)
            if city_name_lower in self.MULTI_POSTAL_CITIES:
                if not dry_run:
                    city.postal_code = 'MULTI'
                    city.save()
                self.stdout.write(
                    self.style.SUCCESS(f'  MULTI {city.city_name} (Region: {city.region.name})')
                )
                stats['multi_postal'] += 1
                continue

            # Find matching postal codes
            matches = self.find_postal_matches(city.city_name)

            if len(matches) == 1:
                # Single match - use it directly
                if not dry_run:
                    city.postal_code = matches[0].code
                    city.save()
                self.stdout.write(
                    self.style.SUCCESS(f'  {city.city_name} -> {matches[0].code}')
                )
                stats['single_match'] += 1

            elif len(matches) > 1:
                # Multiple matches - use region average to pick closest
                avg = self.calculate_region_average(city.region)
                closest = self.find_closest_match(matches, avg)

                if closest:
                    if not dry_run:
                        city.postal_code = closest.code
                        city.save()
                    avg_str = f', avg={int(avg)}' if avg else ''
                    self.stdout.write(
                        self.style.WARNING(
                            f'  {city.city_name} -> {closest.code} '
                            f'(valgt ud af {len(matches)}{avg_str})'
                        )
                    )
                    stats['closest_match'] += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  {city.city_name} -> INGEN MATCH (fandt {len(matches)} men kunne ikke vælge)')
                    )
                    stats['no_match'] += 1

            else:
                # No matches found
                self.stdout.write(
                    self.style.ERROR(f'  {city.city_name} -> INGEN MATCH')
                )
                stats['no_match'] += 1

        # Print summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('OPSUMMERING:')
        self.stdout.write(f"  Enkelt match:      {stats['single_match']}")
        self.stdout.write(f"  Multi-postnummer:  {stats['multi_postal']}")
        self.stdout.write(f"  Tættest match:     {stats['closest_match']}")
        self.stdout.write(f"  Ingen match:       {stats['no_match']}")
        self.stdout.write('=' * 50)

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - ingen ændringer blev gemt'))
        else:
            total_updated = stats['single_match'] + stats['multi_postal'] + stats['closest_match']
            self.stdout.write(self.style.SUCCESS(f'\n{total_updated} records opdateret'))
