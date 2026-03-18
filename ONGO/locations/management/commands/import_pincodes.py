import csv
import os
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from locations.models import PincodeLocation


class Command(BaseCommand):
    help = 'Import Indian pincodes with lat/long from CSV into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=os.path.join(settings.BASE_DIR, 'data', 'pincode_with_lat-long.csv'),
            help='Path to the CSV file (default: data/pincode_with_lat-long.csv)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing PincodeLocation records before import',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear = options['clear']

        if not os.path.exists(file_path):
            raise CommandError(f"CSV file not found: {file_path}")

        if clear:
            count = PincodeLocation.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Deleted {count} existing records."))

        created = 0
        updated = 0
        skipped = 0

        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Print headers to verify (useful for debugging)
            self.stdout.write(f"CSV Headers: {', '.join(reader.fieldnames)}")

            for row in reader:
                pin = row.get('Pincode', '').strip()
                if not pin or not pin.isdigit() or len(pin) != 6:
                    skipped += 1
                    continue

                lat_str = row.get('Latitude', '').strip()
                lon_str = row.get('Longitude', '').strip()

                # Skip if coords are missing or invalid
                if not lat_str or not lon_str:
                    skipped += 1
                    continue

                try:
                    latitude = Decimal(lat_str)
                    longitude = Decimal(lon_str)
                except (InvalidOperation, ValueError):
                    skipped += 1
                    continue

                # Use update_or_create to handle duplicates (one per pincode)
                obj, is_new = PincodeLocation.objects.update_or_create(
                    pincode=pin,
                    defaults={
                        'district': row.get('District', '').strip()[:100],
                        'state': row.get('StateName', '').strip()[:100],
                        'latitude': latitude,
                        'longitude': longitude,
                    }
                )

                if is_new:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import complete!\n"
            f"Created: {created}\n"
            f"Updated: {updated}\n"
            f"Skipped (invalid/missing data): {skipped}\n"
            f"Total processed rows: {created + updated + skipped}"
        ))
