import os
import redis
from django.conf import settings as dj_settings

redisApp = redis.Redis(host=dj_settings.REDIS_HOST,
                       port=dj_settings.REDIS_PORT,
                       db=os.environ.get("REDIS_DB"),
                       password=os.environ.get("REDIS_PASSWORD"))
