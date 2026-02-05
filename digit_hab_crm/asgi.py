"""
Django ASGI config for digit_hab_crm project.
Supporte Django Channels pour les WebSockets
"""

import os
from django.core.asgi import get_asgi_application
from django.conf import settings
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')

# Initialiser Django ASGI application plus tôt pour s'assurer que le AppRegistry
# est rempli avant d'importer du code qui peut en avoir besoin
django_asgi_app = get_asgi_application()

# Import des routers des applications
from apps.notifications.routing import websocket_urlpatterns as notification_websocket_urlpatterns
from apps.messaging.routing import websocket_urlpatterns as messaging_websocket_urlpatterns
from apps.messaging.middleware import JWTAuthMiddleware

# Combine all WebSocket URL patterns
all_websocket_urlpatterns = notification_websocket_urlpatterns + messaging_websocket_urlpatterns

# WebSocket stack (JWT via 1er message). En DEBUG, pas de validation Origin pour l'app mobile.
ws_app = JWTAuthMiddleware(URLRouter(all_websocket_urlpatterns))
if not getattr(settings, 'DEBUG', False):
    ws_app = AllowedHostsOriginValidator(ws_app)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": ws_app,
})