
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import Reactor, ReactorObservation


class Command(BaseCommand):
    help = "Import historical reactor conversion and yield measurements."

    def handle(self, *args, **options):
        file_path = (
            Path(settings.BASE_DIR)
            / "data"
            / "raw_comp_mMconv_SICalc_outlierremoved_EngFeatures.xlsx"
        )

        if not file_path.exists():
            raise CommandError(f"Excel file not found: {file_path}")

        reactor = Reactor.objects.filter(pk=1).first()

        if reactor is None:
            raise CommandError("Reactor with ID 1 was not found.")

        df = pd.read_excel(file_path)

        required_columns = [
            "Result Date",
            "Conversion inner",
            "Yield inner",
        ]

        missing_columns = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise CommandError(
                f"Missing Excel columns: {missing_columns}"
            )

        df = df[required_columns].copy()
        df["Result Date"] = pd.to_datetime(
            df["Result Date"], errors="coerce"
        )

        if df.isna().any().any():
            raise CommandError(
                "Missing or invalid values found in required columns."
            )

        for column in ["Conversion inner", "Yield inner"]:
            if not df[column].between(0, 1).all():
                raise CommandError(
                    f"Values outside the range 0–1 in {column}."
                )

        if df["Result Date"].duplicated().any():
            raise CommandError(
                "Duplicate dates found in the Excel file."
            )

        created = 0
        existing = 0

        with transaction.atomic():
            for _, row in df.iterrows():
                timestamp = row["Result Date"].to_pydatetime()

                if timezone.is_naive(timestamp):
                    timestamp = timezone.make_aware(
                        timestamp,
                        timezone.get_default_timezone()
                    )

                _, was_created = (
                    ReactorObservation.objects.get_or_create(
                        reactor=reactor,
                        timestamp=timestamp,
                        defaults={
                            "conversion": float(
                                row["Conversion inner"]
                            ),
                            "yield_value": float(
                                row["Yield inner"]
                            ),
                        },
                    )
                )

                if was_created:
                    created += 1
                else:
                    existing += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete: {created} created, "
                f"{existing} already existed."
            )
        )

        self.stdout.write(
            f"Total reactor observations: "
            f"{ReactorObservation.objects.filter(reactor=reactor).count()}"
        )
