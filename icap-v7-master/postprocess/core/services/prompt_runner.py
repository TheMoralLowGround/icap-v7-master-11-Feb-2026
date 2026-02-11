#!/usr/bin/env python3
"""
Standalone script to run the postprocess cron job manually.
This can be run directly from command line for testing or manual execution.
Usage: python3 -m core.services.prompt_runner
"""

import os
import sys

# Add project root to path
sys.path.append('/app')

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

import django
django.setup()

# Import the main function from tasks
from core.tasks import update_postprocess_cron


if __name__ == "__main__":
    print("Running postprocess cron job manually...")
    update_postprocess_cron()
    print("Cron job completed.")
