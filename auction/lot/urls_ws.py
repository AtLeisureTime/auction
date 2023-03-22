from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/stakes/lot/(?P<lot_id>\d+)/$', consumers.AuctnConsumer.as_asgi()),
]
