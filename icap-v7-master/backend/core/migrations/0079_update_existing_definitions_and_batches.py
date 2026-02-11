# Generated manually on 27-07-24

from django.db import migrations


def update_existing_definitions_and_batches(apps, schema_editor):
    Profile = apps.get_model("dashboard", "Profile")
    Definition = apps.get_model("core", "Definition")
    Batch = apps.get_model("core", "Batch")

    profile_qs = Profile.objects.all()

    for profile_instance in profile_qs:
        profile_documents_qs = profile_instance.documents.all()

        for doc_instance in profile_documents_qs:
            if doc_instance.name_matching_text is None:
                doc_instance.name_matching_text = ""
                doc_instance.save()

            # Update Definition
            definition_instance = Definition.objects.get(profile_doc=doc_instance)
            definition_instance.name_matching_text = doc_instance.name_matching_text
            definition_instance.save()

            # Update Batches
            batches_qs = Batch.objects.filter(
                definition_id__iexact=definition_instance.definition_id
            ).filter(type__iexact=definition_instance.type)

            if batches_qs.exists():
                for qs in batches_qs:
                    qs.name_matching_text = doc_instance.name_matching_text
                    qs.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0078_remove_definition_unique_definition_id_and_type_and_more"),
    ]

    operations = [
        # Handle DB record changes
        migrations.RunPython(
            update_existing_definitions_and_batches,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
