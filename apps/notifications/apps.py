"""
Application de notifications en temps réel
Intégration avec Django Channels pour WebSockets
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notifications'

    def ready(self):
        """Connecter les signaux lors de l'initialisation"""
        import apps.notifications.signals