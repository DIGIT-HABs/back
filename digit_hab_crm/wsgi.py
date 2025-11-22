"""
Django WSGI config for digit_hab_crm project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')

application = get_wsgi_application()