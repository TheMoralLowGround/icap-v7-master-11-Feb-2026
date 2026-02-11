import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

app = Celery("app")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
app.conf.broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}"

# Crontab Referance:
# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#crontab-schedules

# Specify locatin of celerybeat db (media folder)
# app.conf.beat_schedule_filename = os.path.join(
#     settings.MEDIA_ROOT, "celerybeat-schedule"
# )

app.conf.beat_schedule = {
    # Execute after every 1 minute.
    "process-outlook": {
        "task": "core.tasks.read_outlook",
        "schedule": timedelta(minutes=1),
        "options": {"queue": "outlook_queue"},
    },
    "process-basic-email": {
        "task": "core.tasks.read_basic_email",
        "schedule": timedelta(minutes=1),
        "options": {"queue": "basic_email_queue"},
    },
     "process-sharepoint": {
        "task": "core.tasks.read_sharepoint",
        "schedule": timedelta(minutes=1),
        "options": {"queue": "sharepoint_queue"},
    },
     "process-onedrive": {
        "task": "core.tasks.read_onedrive",
        "schedule": timedelta(minutes=1),
        "options": {"queue": "onedrive_queue"},
    }
}
