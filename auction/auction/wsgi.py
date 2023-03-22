""" WSGI config for auction project.
It exposes the WSGI callable as a module-level variable named ``application``.
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction.settings.prod')

application = get_wsgi_application()
