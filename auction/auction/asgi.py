"""
ASGI config for auction project.
It exposes the ASGI callable as a module-level variable named ``application``.
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction.settings.prod')
django_asgi_app = get_asgi_application()


import channels.auth
import channels.routing
import channels.security.websocket
from lot import urls_ws

application = channels.routing.ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': channels.security.websocket.AllowedHostsOriginValidator(
        channels.auth.AuthMiddlewareStack(
            channels.routing.URLRouter(urls_ws.websocket_urlpatterns)
        )
    ),
})
