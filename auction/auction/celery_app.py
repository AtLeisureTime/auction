import os
from celery import Celery
from django.conf import settings as dj_settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction.settings.prod')

celeryApp = Celery('auction', backend=dj_settings.CELERY_RESULT_BACKEND,
                   broker=dj_settings.CELERY_BROKER_URL)
# namespace='CELERY' means all celery-related configuration keys should have a `CELERY_` prefix.
celeryApp.config_from_object('django.conf:settings', namespace='CELERY')
celeryApp.autodiscover_tasks()
