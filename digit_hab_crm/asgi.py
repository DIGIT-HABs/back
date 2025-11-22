"""
Django ASGI config for digit_hab_crm project.
Supporte Django Channels pour les WebSockets
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')

# Initialiser Django ASGI application plus tôt pour s'assurer que le AppRegistry
# est rempli avant d'importer du code qui peut en avoir besoin
django_asgi_app = get_asgi_application()

# Import des routers des applications
from apps.notifications.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})