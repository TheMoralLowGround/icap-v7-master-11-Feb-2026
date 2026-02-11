import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

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
app.conf.beat_schedule_filename = os.path.join(
    settings.MEDIA_ROOT, "celerybeat-schedule"
)

app.conf.beat_schedule = {
    # Execute daily at midnight.
    "remove-batch-status-everyday": {
        "task": "core.tasks.remove_batch_status",
        "schedule": crontab(minute=0, hour=0),
    },
    # Execute daily at midnight after 10mins.
    "remove-batch-everyday": {
        "task": "core.tasks.remove_batch",
        "schedule": crontab(minute=10, hour=0),
    },
    # Execute daily at midnight after 20mins.
    "backup-data-everyday": {
        "task": "core.tasks.backup_data",
        "schedule": crontab(minute=20, hour=0),
    },
    # Execute daily at midnight after 40mins.
    "remove-email-batch-sequences": {
        "task": "core.tasks.remove_email_batch_sequences",
        "schedule": crontab(minute=40, hour=0),
    },
    # Execute daily at midnight after 1hr.
    "disable-inactive-users": {
        "task": "core.tasks.disable_inactive_users",
        "schedule": crontab(minute=0, hour=1),
    },
}
