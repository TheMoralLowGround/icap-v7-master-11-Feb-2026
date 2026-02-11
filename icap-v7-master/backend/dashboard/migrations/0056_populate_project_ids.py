# Manual migration script created by Nayem
from django.db import migrations, transaction, models  # Add models here

def populate_project_ids(apps, schema_editor):
    Project = apps.get_model('dashboard', 'Project')
    
    def increment_project_id(current_id):
        if not current_id:
            return 'AA1'
        
        letters = current_id[:2]
        number = int(current_id[2:])
        
        if number < 9:
            return f"{letters}{number + 1}"
        
        first_char, second_char = letters[0], letters[1]
        
        if second_char < 'Z':
            return f"{first_char}{chr(ord(second_char) + 1)}1"
        
        if first_char < 'Z':
            return f"{chr(ord(first_char) + 1)}A1"
        
        raise Exception("Maximum project ID reached")
    
    # Get all projects without project_id, ordered by creation date
    projects = Project.objects.filter(project_id='').order_by('created_at')
    
    current_id = None
    # Find the highest existing project_id if any
    existing_project = Project.objects.exclude(project_id='').order_by('-project_id').first()
    if existing_project:
        current_id = existing_project.project_id
    
    with transaction.atomic():
        for project in projects:
            current_id = increment_project_id(current_id)
            project.project_id = current_id
            project.save(update_fields=['project_id'])

def reverse_populate_project_ids(apps, schema_editor):
    # Reverse operation - set project_ids back to blank
    Project = apps.get_model('dashboard', 'Project')
    Project.objects.all().update(project_id='')

class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0055_alter_project_options_project_project_id'),
    ]

    operations = [
        migrations.RunPython(populate_project_ids, reverse_populate_project_ids),
        
        # Now add the unique constraint
        migrations.AlterField(
            model_name='project',
            name='project_id',
            field=models.CharField(
                max_length=3, 
                unique=True,
                blank=False,
                help_text="Auto-generated ID in format AA1-ZZ9"
            ),
        ),
    ]