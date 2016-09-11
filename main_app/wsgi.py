"""
WSGI config for Lan project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os, sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main_app.settings")
sys.path.append('\\'.join(os.path.realpath(__file__).split("\\")[:-2])) 
application = get_wsgi_application()
