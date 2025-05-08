"""
WSGI config for ride_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

# Add your project directory to the path
path = '/home/abhiramt14/ride_connect'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'ride_project.settings'  # Adjust to your settings module

# Serve Django via WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()