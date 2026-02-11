import json
from utils.redis_utils import redis_instance
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from access_control.models import ProjectCountry
from core.models import Country
from .models import Project, Profile
from .serializers import ProjectSerializer

User = get_user_model()

@receiver(post_save, sender=Project)
def update_profile_keys_on_project_change(sender, instance, created, **kwargs):
    """
    Post-save signal handler for Project model.
    """

    if created:
        admin_users = User.objects.filter(is_staff=True, is_superuser=True)
        all_countries = Country.objects.all()
        
        # Create ProjectCountry instance for each admin user
        for admin_user in admin_users:
            project_country = ProjectCountry.objects.create(
                user=admin_user,
                project=instance
            )
            project_country.countries.set(all_countries)


@receiver(post_save, sender=Project)
def store_project_data(sender, instance, **kwargs):
    """Store updated project data to redis"""
    project_query = Project.objects.all()
    projects_data = ProjectSerializer(project_query, many=True).data

    serialized_data = json.dumps(projects_data)
    redis_instance.set("projects_data", serialized_data)