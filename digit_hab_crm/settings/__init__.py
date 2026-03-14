"""
Settings package initialization.
"""

import os
from decouple import config

# Set the default settings module (base.py has no DATABASES; use dev or prod)
_ENV = os.environ.get('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings.dev')
if _ENV == 'digit_hab_crm.settings':
    _ENV = 'digit_hab_crm.settings.dev'

# Import the appropriate settings
if _ENV.endswith('.dev'):
    from .dev import *
elif _ENV.endswith('.prod'):
    from .prod import *
else:
    from .base import *