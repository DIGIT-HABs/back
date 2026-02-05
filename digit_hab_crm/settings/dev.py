"""
Development settings.
"""

from .base import *

# Development specific settings
DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]', '192.168.1.82', '*']


# SQLITE
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# # Database - Development
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'digit_hab_crm_dev',
#         'USER': 'postgres',
#         'PASSWORD': 'password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#         'OPTIONS': {
#         },
#     }
# }

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Celery settings
CELERY_TASK_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Development logging
# LOGGING['loggers']['django']['level'] = 'DEBUG'
# LOGGING['loggers']['digit_hab_crm']['level'] = 'DEBUG'

# Disable HTTPS
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# CORS for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# API Documentation
SPECTACULAR_SETTINGS['SWAGGER_UI_SETTINGS'] = {
    'persistAuthorization': True,
    'displayRequestDuration': True,
    'filter': True,
    'showExtensions': True,
    'showCommonExtensions': True,
}

# JWT settings for development
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(hours=24)
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=7)

# Disable authentication for development (optional)
# REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
#     'rest_framework.authentication.SessionAuthentication',
#     'rest_framework.authentication.TokenAuthentication',
# ]
# REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
#     'rest_framework.permissions.AllowAny',
# ]