import os
from .base import *


BASE_HOST = '127.0.0.1'
ALLOWED_HOSTS = [BASE_HOST, 'localhost']
POSTGRES_PORT = 5432

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        'HOST': BASE_HOST,
        'PORT': POSTGRES_PORT
    }
}

REDIS_HOST = BASE_HOST
REDIS_PORT = 6379

REDIS_URL = f'redis://:{os.environ.get("REDIS_PASSWORD")}@{REDIS_HOST}:{REDIS_PORT}'

CELERY_BROKER_URL = f'amqp://{os.environ.get("RABBITMQ_DEFAULT_USER")}:'\
    f'{os.environ.get("RABBITMQ_DEFAULT_PASS")}@{BASE_HOST}/'\
    f'{os.environ.get("RABBITMQ_DEFAULT_VHOST")}'
CELERY_RESULT_BACKEND = f'{REDIS_URL}/{os.environ.get("REDIS_CELERY_DB")}'
CELERY_TIMEZONE = "UTC"
# CELERYD_TIME_LIMIT = 30 * 60
CELERY_RESULT_EXPIRES = 24 * 3600
# CELERY_TASK_TRACK_STARTED = True

CHANNEL_LAYERS_BACKEND = f'{REDIS_URL}/{os.environ.get("REDIS_CHANNELS_DB")}'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [CHANNEL_LAYERS_BACKEND],
        },
    }
}
