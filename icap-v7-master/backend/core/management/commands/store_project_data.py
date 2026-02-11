import json
from dashboard.models import Project
from utils.redis_utils import redis_instance
from dashboard.serializers import ProjectSerializer
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Store Project data into Redis"""

    def handle(self, *args, **kwargs):
        project_query = Project.objects.all()
        projects_data = ProjectSerializer(project_query, many=True).data

        serialized_data = json.dumps(projects_data)
        redis_instance.set("projects_data", serialized_data)
        self.stdout.write("Projects data cached in Redis")