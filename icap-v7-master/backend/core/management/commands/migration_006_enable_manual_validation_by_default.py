from django.db import transaction
from django.core.management.base import BaseCommand
from dashboard.models import Profile


class Command(BaseCommand):
    """Django command to stop excution if required env variables are not present"""

    def handle(self, *args, **options):
        self.stdout.write("Migration Initiated...")

        # If no error occurs during the transaction,
        # then only commit changes to DB.
        with transaction.atomic():
            profiles = Profile.objects.all()

            for profile in profiles:
                print(profile)
                profile.manual_validation = True
                profile.save()

        self.stdout.write(self.style.SUCCESS("Migration completed"))
