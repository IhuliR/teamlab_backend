import os

from celery import Celery


os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'teamlab_backend.settings',
)

app = Celery('teamlab_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
