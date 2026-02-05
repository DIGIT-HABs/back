"""
WebSocket routing for messaging app.
"""

from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/messaging/chat/(?P<conversation_id>[^/]+)/$', ChatConsumer.as_asgi()),
]
