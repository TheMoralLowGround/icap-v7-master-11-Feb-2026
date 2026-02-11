import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to stop excution if required env variables are not present"""

    def check_env_variable(self, variable_name):
        self.stdout.write(variable_name)
        value = os.getenv(variable_name)
        assert value != "", f"Environment variable {variable_name} can not be empty"
        self.stdout.write("OK")

    def handle(self, *args, **options):
        self.stdout.write("Checking env variables...")

        required_variables = ["DEFINITION_VERSIONS", "DEFAULT_DEFINITION_VERSION"]

        [self.check_env_variable(i) for i in required_variables]

        self.stdout.write(self.style.SUCCESS("Environment variables check completed"))
