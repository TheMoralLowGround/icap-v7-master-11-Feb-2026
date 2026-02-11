# Generated manually on 2023-08-23

from django.db import migrations


def update_existing_email_batches(apps, schema_editor):
    EmailBatch = apps.get_model("core", "EmailBatch")
    EmailToBatchLink = apps.get_model("core", "EmailToBatchLink")
    Batch = apps.get_model("core", "Batch")
    Profile = apps.get_model("dashboard", "Profile")

    email_batches = EmailBatch.objects.filter(matched_profile__isnull=True).iterator()
    for email_batch in email_batches:
        profile_instance = None

        email_batch_id = email_batch.id
        qs = EmailToBatchLink.objects.filter(email__id=email_batch_id)
        if qs.exists():
            batch_ids = list(qs.all().values_list("batch_id", flat=True))
            batch_qs = Batch.objects.filter(
                id__in=batch_ids, definition_id__isnull=False
            )
            if batch_qs.exists():
                profile_name = batch_qs.first().definition_id
                profile_qs = Profile.objects.filter(name=profile_name)
                if profile_qs.exists():
                    profile_instance = profile_qs.first()

        if profile_instance:
            email_batch.matched_profile = profile_instance
            email_batch.save()


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0009_profiledocument_unique_profile_and_doc_type"),
        ("core", "0057_emailbatch_matched_profile"),
    ]

    operations = [
        # Handle DB record changes
        migrations.RunPython(update_existing_email_batches),
    ]
