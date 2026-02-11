# Manual migration script created by Nayem
from django.db import migrations, transaction, models

def populate_process_ids(apps, schema_editor):
    Profile = apps.get_model('dashboard', 'Profile')
    Project = apps.get_model('dashboard', 'Project')
    
    def increment_process_id(current_id, country_project_prefix):
        if not current_id:
            return f'{country_project_prefix}-1234567'
        
        # Extract the numeric part after the last hyphen
        parts = current_id.split('-')
        number = int(parts[-1])
        return f'{country_project_prefix}-{number + 1}'
    
    # Get all profiles without process_id, ordered by creation date
    profiles = Profile.objects.filter(process_id='').order_by('created_at')
    
    # Dictionary to track the last used number for each country-project combination
    last_numbers = {}
    
    # Find existing process_ids to determine the highest numbers for each prefix
    existing_profiles = Profile.objects.exclude(process_id='').order_by('process_id')
    for profile in existing_profiles:
        if profile.process_id:
            parts = profile.process_id.split('-')
            if len(parts) >= 3:
                prefix = '-'.join(parts[:-1])  # Everything except the last number
                number = int(parts[-1])
                last_numbers[prefix] = max(last_numbers.get(prefix, 1234566), number)
    
    with transaction.atomic():
        for profile in profiles:
            # Get project instance using the project field from profile
            try:
                project = Project.objects.get(name=profile.project)
                project_id = project.project_id
            except Project.DoesNotExist:
                # Handle case where project doesn't exist
                print(f"Warning: Project '{profile.project}' not found for profile {profile.id}")
                project_id = 'AA1'  # Default fallback
            
            # Create the country-project prefix (e.g., 'AF-AA1')
            country_project_prefix = f'{profile.country}-{project_id}'
            
            # Get the current highest number for this prefix
            current_number = last_numbers.get(country_project_prefix, 1234566)
            new_number = current_number + 1
            
            # Generate the new process_id
            process_id = f'{country_project_prefix}-{new_number}'
            
            # Update the profile
            profile.process_id = process_id
            profile.save(update_fields=['process_id'])
            
            # Update our tracking dictionary
            last_numbers[country_project_prefix] = new_number

def reverse_populate_process_ids(apps, schema_editor):
    # Reverse operation - set process_ids back to blank
    Profile = apps.get_model('dashboard', 'Profile')
    Profile.objects.all().update(process_id='')

class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0057_profile_process_id'),
    ]

    operations = [
        migrations.RunPython(populate_process_ids, reverse_populate_process_ids),
        
        # Now add the unique constraint
        migrations.AlterField(
            model_name='profile',
            name='process_id',
            field=models.CharField(
                max_length=14,
                unique=True,
                blank=False,
                help_text="Auto-generated ID in format COUNTRY-PROJECT_ID-NUMBER (e.g., AF-AA1-1234567)"
            ),
        ),
    ]