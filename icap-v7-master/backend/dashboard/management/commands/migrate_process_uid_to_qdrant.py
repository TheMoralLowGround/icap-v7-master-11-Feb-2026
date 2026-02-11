import json

from django.core.management.base import BaseCommand, CommandError

from dashboard import models
from dashboard.views import push_process_uid_migration_to_qdrant


class Command(BaseCommand):
    help = "Push profiles to Qdrant to trigger process_uid migration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-legacy",
            dest="delete_legacy",
            action="store_true",
            default=True,
            help="Delete legacy collections/metadata after migration (default).",
        )
        parser.add_argument(
            "--no-delete-legacy",
            dest="delete_legacy",
            action="store_false",
            help="Do not delete legacy collections/metadata after migration.",
        )

    def handle(self, *args, **options):
        profile_query = models.Profile.objects.all()

        if not profile_query.exists():
            raise CommandError("No profiles found for migration.")

        profiles_payload = []
        for profile in profile_query.only("process_uid", "name", "free_name", "process_id"):
            profiles_payload.append(
                {
                    "process_uid": str(profile.process_uid),
                    "name": profile.name,
                    "free_name": profile.free_name,
                    "process_id": profile.process_id,
                }
            )

        summary = push_process_uid_migration_to_qdrant(
            profiles_payload,
            delete_legacy=options.get("delete_legacy", True),
        )

        output = json.dumps(summary, indent=2)
        if summary.get("success"):
            self.stdout.write(self.style.SUCCESS(output))
            return

        self.stderr.write(self.style.ERROR(output))
        raise CommandError("Migration failed. See errors above.")
