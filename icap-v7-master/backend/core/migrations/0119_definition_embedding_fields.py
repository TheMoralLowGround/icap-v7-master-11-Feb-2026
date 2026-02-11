# Generated migration for adding embedding storage to Definition model
# This enables database-stored embeddings for ultimate layout matching performance

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0118_alter_batch_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='definition',
            name='embedding',
            field=models.BinaryField(blank=True, help_text='Pickled numpy embedding array for layout matching', null=True),
        ),
        migrations.AddField(
            model_name='definition',
            name='embedding_model_version',
            field=models.CharField(blank=True, help_text='Model version used to generate embedding', max_length=100, null=True),
        ),
    ]
